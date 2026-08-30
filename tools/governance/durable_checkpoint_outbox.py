"""Durable compare-and-swap checkpoints and idempotent dispatch reservations.

The bounded-execution guard deliberately does not treat fields supplied in an
execution snapshot as a transaction proof.  A caller that wants to execute a
consuming or security-sensitive action must supply an adapter backed by a
durable store.  This module provides the small protocol the guard needs and a
SQLite reference implementation suitable for a control-plane service.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Protocol


@dataclasses.dataclass(frozen=True)
class Reservation:
    """Outcome of attempting one durable action reservation."""

    committed: bool
    reservation_key: str
    reason: str


class CheckpointOutboxAdapter(Protocol):
    """Atomically advance a checkpoint and create one dispatch reservation."""

    def reserve(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        action: str,
        scope: tuple[str, ...],
    ) -> Reservation: ...

    def claim_dispatch(self, reservation_key: str) -> bool: ...


def _reservation_key(
    repository: str,
    task_id: str,
    expected_checkpoint: str | None,
    next_checkpoint: str,
    action: str,
    scope: tuple[str, ...],
) -> str:
    payload = {
        "repository": repository,
        "task_id": task_id,
        "expected_checkpoint": expected_checkpoint,
        "next_checkpoint": next_checkpoint,
        "action": action,
        "scope": list(scope),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SqliteCheckpointOutbox:
    """SQLite durable adapter with atomic CAS and a unique dispatch outbox.

    A control plane seeds a trusted checkpoint before operating an existing
    task.  A first checkpoint (``expected_checkpoint is None``) is also
    supported for a new task.  Replays return the same deterministic key but
    never grant another dispatch claim.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bounded_execution_checkpoint (
                    repository TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    checkpoint TEXT NOT NULL,
                    PRIMARY KEY (repository, task_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bounded_execution_outbox (
                    reservation_key TEXT PRIMARY KEY,
                    repository TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('committed', 'dispatched'))
                )
                """
            )

    def seed_checkpoint(self, repository: str, task_id: str, checkpoint: str) -> None:
        """Install a control-plane checkpoint for a task before its first CAS.

        The operation intentionally refuses replacement: reseeding would erase
        the very CAS lineage this adapter protects.
        """

        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO bounded_execution_checkpoint(repository, task_id, checkpoint) VALUES (?, ?, ?)",
                    (repository, task_id, checkpoint),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("checkpoint already exists; reseeding is forbidden") from error

    def reserve(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        action: str,
        scope: tuple[str, ...],
    ) -> Reservation:
        key = _reservation_key(
            repository,
            task_id,
            expected_checkpoint,
            next_checkpoint,
            action,
            scope,
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            replay = connection.execute(
                "SELECT reservation_key FROM bounded_execution_outbox WHERE reservation_key = ?",
                (key,),
            ).fetchone()
            if replay is not None:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "reservation_replay")

            row = connection.execute(
                "SELECT checkpoint FROM bounded_execution_checkpoint WHERE repository = ? AND task_id = ?",
                (repository, task_id),
            ).fetchone()
            actual = row[0] if row is not None else None
            if actual != expected_checkpoint:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "checkpoint_cas_conflict")

            if row is None:
                connection.execute(
                    "INSERT INTO bounded_execution_checkpoint(repository, task_id, checkpoint) VALUES (?, ?, ?)",
                    (repository, task_id, next_checkpoint),
                )
            else:
                updated = connection.execute(
                    """
                    UPDATE bounded_execution_checkpoint
                    SET checkpoint = ?
                    WHERE repository = ? AND task_id = ? AND checkpoint = ?
                    """,
                    (next_checkpoint, repository, task_id, expected_checkpoint),
                )
                if updated.rowcount != 1:
                    connection.execute("ROLLBACK")
                    return Reservation(False, key, "checkpoint_cas_conflict")

            connection.execute(
                """
                INSERT INTO bounded_execution_outbox(reservation_key, repository, task_id, action, status)
                VALUES (?, ?, ?, ?, 'committed')
                """,
                (key, repository, task_id, action),
            )
            connection.execute("COMMIT")
        return Reservation(True, key, "reservation_committed")

    def claim_dispatch(self, reservation_key: str) -> bool:
        """Grant exactly one dispatcher the committed reservation."""

        with self._connect() as connection:
            updated = connection.execute(
                """
                UPDATE bounded_execution_outbox
                SET status = 'dispatched'
                WHERE reservation_key = ? AND status = 'committed'
                """,
                (reservation_key,),
            )
        return updated.rowcount == 1
