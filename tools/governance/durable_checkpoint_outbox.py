"""Durable compare-and-swap checkpoints and idempotent dispatch reservations.

The bounded-execution guard deliberately does not treat fields supplied in an
execution snapshot as a transaction proof. A caller that wants to execute a
consuming or security-sensitive action must supply an adapter backed by a
durable store. This module provides the small protocol the guard needs and a
SQLite reference implementation suitable for a control-plane service.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Protocol


@dataclasses.dataclass(frozen=True)
class Reservation:
    """Outcome of attempting one durable action reservation."""

    committed: bool
    reservation_key: str
    reason: str


@dataclasses.dataclass(frozen=True)
class CheckpointRecord:
    """Recoverable durable checkpoint returned to a takeover worker."""

    checkpoint: str
    snapshot: dict[str, Any]


@dataclasses.dataclass(frozen=True)
class PendingReservation:
    """One atomically claimed durable dispatch recovered by a takeover worker."""

    reservation_key: str
    repository: str
    task_id: str
    expected_checkpoint: str | None
    next_checkpoint: str
    action: str
    scope: tuple[str, ...]


class CheckpointOutboxAdapter(Protocol):
    """Atomically advance recoverable checkpoints and dispatch reservations."""

    def reserve(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        next_snapshot: dict[str, Any],
        action: str,
        scope: tuple[str, ...],
    ) -> Reservation: ...

    def transition(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        next_snapshot: dict[str, Any],
        reason: str,
        scope: tuple[str, ...],
    ) -> Reservation: ...

    def load_checkpoint(self, repository: str, task_id: str) -> CheckpointRecord | None: ...

    def claim_pending_dispatch(
        self, repository: str, task_id: str
    ) -> PendingReservation | None: ...

    def claim_dispatch(self, reservation_key: str) -> bool: ...

    def acknowledge_dispatch(self, reservation_key: str) -> bool: ...


def _canonical_snapshot(snapshot: dict[str, Any]) -> str:
    if not isinstance(snapshot, dict):
        raise ValueError("checkpoint snapshot must be an object")
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


NONMATERIAL_CHECKPOINT_FIELDS = frozenset({"updated_at", "narration"})


def checkpoint_digest(snapshot: dict[str, Any]) -> str:
    """Hash durable material execution identity, excluding observer-only metadata."""

    if not isinstance(snapshot, dict):
        raise ValueError("checkpoint snapshot must be an object")
    material = {
        key: value
        for key, value in snapshot.items()
        if key not in NONMATERIAL_CHECKPOINT_FIELDS
    }
    payload = json.dumps(
        material, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validated_snapshot_payload(snapshot: dict[str, Any], expected_digest: str) -> str:
    payload = _canonical_snapshot(snapshot)
    if checkpoint_digest(snapshot) != expected_digest:
        raise ValueError("checkpoint digest does not match material snapshot identity")
    return payload


def _canonical_scope_json(scope: tuple[str, ...]) -> str:
    if not isinstance(scope, tuple) or not all(
        isinstance(item, str) and item for item in scope
    ):
        raise ValueError("reservation scope must be a tuple of non-empty strings")
    return json.dumps(list(scope), separators=(",", ":"), ensure_ascii=True)


def _parse_scope_json(scope_json: str) -> tuple[str, ...]:
    if not isinstance(scope_json, str):
        raise ValueError("pending reservation scope is unavailable")
    try:
        payload = json.loads(scope_json)
    except json.JSONDecodeError as error:
        raise ValueError("pending reservation scope is malformed") from error
    if not isinstance(payload, list) or not all(
        isinstance(item, str) and item for item in payload
    ):
        raise ValueError("pending reservation scope must be a string list")
    scope = tuple(payload)
    if _canonical_scope_json(scope) != scope_json:
        raise ValueError("pending reservation scope is not canonical")
    return scope


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

    Every committed checkpoint stores both its canonical digest and serialized
    snapshot. A takeover can therefore reconstruct the exact durable state.
    Legacy digest-only rows fail closed through ``load_checkpoint``.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bounded_execution_checkpoint (
                    repository TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    checkpoint TEXT NOT NULL,
                    snapshot_json TEXT,
                    PRIMARY KEY (repository, task_id)
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(bounded_execution_checkpoint)"
                ).fetchall()
            }
            if "snapshot_json" not in columns:
                connection.execute(
                    "ALTER TABLE bounded_execution_checkpoint ADD COLUMN snapshot_json TEXT"
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bounded_execution_outbox (
                    reservation_key TEXT PRIMARY KEY,
                    repository TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    expected_checkpoint TEXT,
                    next_checkpoint TEXT,
                    action TEXT NOT NULL,
                    scope_json TEXT,
                    sequence_no INTEGER,
                    acknowledged INTEGER NOT NULL DEFAULT 0,
                    invalidated INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL CHECK (status IN ('committed', 'dispatched'))
                )
                """
            )
            outbox_columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(bounded_execution_outbox)"
                ).fetchall()
            }
            for column, definition in (
                ("expected_checkpoint", "TEXT"),
                ("next_checkpoint", "TEXT"),
                ("scope_json", "TEXT"),
                ("sequence_no", "INTEGER"),
                ("acknowledged", "INTEGER NOT NULL DEFAULT 0"),
                ("invalidated", "INTEGER NOT NULL DEFAULT 0"),
            ):
                if column not in outbox_columns:
                    connection.execute(
                        f"ALTER TABLE bounded_execution_outbox ADD COLUMN {column} {definition}"
                    )

    def seed_checkpoint(
        self,
        repository: str,
        task_id: str,
        checkpoint: str,
        *,
        snapshot: dict[str, Any],
    ) -> None:
        """Install one recoverable trusted checkpoint; replacement is forbidden."""

        snapshot_json = _validated_snapshot_payload(snapshot, checkpoint)
        with closing(self._connect()) as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO bounded_execution_checkpoint(
                        repository, task_id, checkpoint, snapshot_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (repository, task_id, checkpoint, snapshot_json),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("checkpoint already exists; reseeding is forbidden") from error

    def _advance_checkpoint(
        self,
        connection: sqlite3.Connection,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        snapshot_json: str,
    ) -> bool:
        row = connection.execute(
            """
            SELECT checkpoint
            FROM bounded_execution_checkpoint
            WHERE repository = ? AND task_id = ?
            """,
            (repository, task_id),
        ).fetchone()
        actual = row[0] if row is not None else None
        if actual != expected_checkpoint:
            return False
        if row is None:
            connection.execute(
                """
                INSERT INTO bounded_execution_checkpoint(
                    repository, task_id, checkpoint, snapshot_json
                ) VALUES (?, ?, ?, ?)
                """,
                (repository, task_id, next_checkpoint, snapshot_json),
            )
            return True
        updated = connection.execute(
            """
            UPDATE bounded_execution_checkpoint
            SET checkpoint = ?, snapshot_json = ?
            WHERE repository = ? AND task_id = ? AND checkpoint = ?
            """,
            (
                next_checkpoint,
                snapshot_json,
                repository,
                task_id,
                expected_checkpoint,
            ),
        )
        return updated.rowcount == 1

    def reserve(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        next_snapshot: dict[str, Any],
        action: str,
        scope: tuple[str, ...],
    ) -> Reservation:
        snapshot_json = _validated_snapshot_payload(next_snapshot, next_checkpoint)
        scope_json = _canonical_scope_json(scope)
        key = _reservation_key(
            repository,
            task_id,
            expected_checkpoint,
            next_checkpoint,
            action,
            scope,
        )
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            replay = connection.execute(
                "SELECT reservation_key FROM bounded_execution_outbox WHERE reservation_key = ?",
                (key,),
            ).fetchone()
            if replay is not None:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "reservation_replay")
            checkpoint_row = connection.execute(
                "SELECT checkpoint FROM bounded_execution_checkpoint WHERE repository = ? AND task_id = ?",
                (repository, task_id),
            ).fetchone()
            actual_checkpoint = checkpoint_row[0] if checkpoint_row is not None else None
            if actual_checkpoint != expected_checkpoint:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "checkpoint_cas_conflict")
            scope_json = _canonical_scope_json(scope)
            if action == "run_loop_breaker_audit":
                repeated_scope = connection.execute(
                    """
                    SELECT 1 FROM bounded_execution_outbox
                    WHERE repository = ? AND task_id = ? AND action = ?
                      AND scope_json = ? AND COALESCE(invalidated, 0) = 0
                    LIMIT 1
                    """,
                    (repository, task_id, action, scope_json),
                ).fetchone()
                if repeated_scope is not None:
                    connection.execute("ROLLBACK")
                    return Reservation(False, key, "loop_breaker_audit_generation_replay")
            in_flight = connection.execute(
                """
                SELECT 1 FROM bounded_execution_outbox
                WHERE repository = ? AND task_id = ?
                  AND COALESCE(invalidated, 0) = 0
                  AND (status = 'committed' OR (status = 'dispatched' AND COALESCE(acknowledged, 0) = 0))
                LIMIT 1
                """,
                (repository, task_id),
            ).fetchone()
            if in_flight is not None:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "dispatch_in_flight")
            if not self._advance_checkpoint(
                connection,
                repository=repository,
                task_id=task_id,
                expected_checkpoint=expected_checkpoint,
                next_checkpoint=next_checkpoint,
                snapshot_json=snapshot_json,
            ):
                connection.execute("ROLLBACK")
                return Reservation(False, key, "checkpoint_cas_conflict")
            sequence_row = connection.execute(
                """
                SELECT COALESCE(MAX(sequence_no), 0) + 1
                FROM bounded_execution_outbox
                WHERE repository = ? AND task_id = ?
                """,
                (repository, task_id),
            ).fetchone()
            sequence_no = int(sequence_row[0])
            connection.execute(
                """
                INSERT INTO bounded_execution_outbox(
                    reservation_key, repository, task_id, expected_checkpoint,
                    next_checkpoint, action, scope_json, sequence_no, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'committed')
                """,
                (
                    key,
                    repository,
                    task_id,
                    expected_checkpoint,
                    next_checkpoint,
                    action,
                    scope_json,
                    sequence_no,
                ),
            )
            connection.execute("COMMIT")
        return Reservation(True, key, "reservation_committed")

    def transition(
        self,
        *,
        repository: str,
        task_id: str,
        expected_checkpoint: str | None,
        next_checkpoint: str,
        next_snapshot: dict[str, Any],
        reason: str,
        scope: tuple[str, ...],
    ) -> Reservation:
        """Atomically persist a recoverable checkpoint without dispatch work."""

        snapshot_json = _validated_snapshot_payload(next_snapshot, next_checkpoint)
        key = _reservation_key(
            repository,
            task_id,
            expected_checkpoint,
            next_checkpoint,
            f"transition:{reason}",
            scope,
        )
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            checkpoint_row = connection.execute(
                "SELECT checkpoint FROM bounded_execution_checkpoint WHERE repository = ? AND task_id = ?",
                (repository, task_id),
            ).fetchone()
            actual_checkpoint = checkpoint_row[0] if checkpoint_row is not None else None
            if actual_checkpoint != expected_checkpoint:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "checkpoint_cas_conflict")
            dispatched = connection.execute(
                """
                SELECT 1 FROM bounded_execution_outbox
                WHERE repository = ? AND task_id = ?
                  AND status = 'dispatched'
                  AND COALESCE(acknowledged, 0) = 0
                  AND COALESCE(invalidated, 0) = 0
                LIMIT 1
                """,
                (repository, task_id),
            ).fetchone()
            if dispatched is not None:
                connection.execute("ROLLBACK")
                return Reservation(False, key, "dispatch_in_flight")
            connection.execute(
                """
                UPDATE bounded_execution_outbox
                SET invalidated = 1
                WHERE repository = ? AND task_id = ?
                  AND status = 'committed'
                  AND COALESCE(invalidated, 0) = 0
                """,
                (repository, task_id),
            )
            if not self._advance_checkpoint(
                connection,
                repository=repository,
                task_id=task_id,
                expected_checkpoint=expected_checkpoint,
                next_checkpoint=next_checkpoint,
                snapshot_json=snapshot_json,
            ):
                connection.execute("ROLLBACK")
                return Reservation(False, key, "checkpoint_cas_conflict")
            connection.execute("COMMIT")
        return Reservation(True, key, "transition_committed")

    def load_checkpoint(self, repository: str, task_id: str) -> CheckpointRecord | None:
        """Return the exact durable checkpoint, failing closed on corrupt legacy state."""

        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT checkpoint, snapshot_json
                FROM bounded_execution_checkpoint
                WHERE repository = ? AND task_id = ?
                """,
                (repository, task_id),
            ).fetchone()
        if row is None:
            return None
        checkpoint, snapshot_json = row
        if not isinstance(snapshot_json, str) or not snapshot_json:
            raise ValueError("recoverable checkpoint snapshot is unavailable")
        try:
            snapshot = json.loads(snapshot_json)
        except json.JSONDecodeError as error:
            raise ValueError("recoverable checkpoint snapshot is malformed") from error
        if not isinstance(snapshot, dict):
            raise ValueError("recoverable checkpoint snapshot must be an object")
        canonical = _canonical_snapshot(snapshot)
        if canonical != snapshot_json:
            raise ValueError("recoverable checkpoint snapshot is not canonical JSON")
        if checkpoint_digest(snapshot) != checkpoint:
            raise ValueError("recoverable checkpoint material digest mismatch")
        return CheckpointRecord(checkpoint=checkpoint, snapshot=snapshot)

    def claim_pending_dispatch(
        self, repository: str, task_id: str
    ) -> PendingReservation | None:
        """Atomically claim the oldest recoverable dispatch for one task.

        This crash-recovery path does not require the reservation key returned
        to the previous process. Legacy committed rows without complete metadata
        fail closed instead of being skipped or guessed.
        """

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT reservation_key, expected_checkpoint, next_checkpoint,
                           action, scope_json, sequence_no
                    FROM bounded_execution_outbox
                    WHERE repository = ? AND task_id = ? AND status = 'committed'
                      AND COALESCE(invalidated, 0) = 0
                    ORDER BY CASE WHEN sequence_no IS NULL THEN 0 ELSE 1 END,
                             sequence_no ASC, reservation_key ASC
                    LIMIT 1
                    """,
                    (repository, task_id),
                ).fetchone()
                if row is None:
                    connection.execute("ROLLBACK")
                    return None

                (
                    reservation_key,
                    expected_checkpoint,
                    next_checkpoint,
                    action,
                    scope_json,
                    sequence_no,
                ) = row
                if (
                    not isinstance(reservation_key, str)
                    or not reservation_key
                    or (
                        expected_checkpoint is not None
                        and not isinstance(expected_checkpoint, str)
                    )
                    or not isinstance(next_checkpoint, str)
                    or not next_checkpoint
                    or not isinstance(action, str)
                    or not action
                    or not isinstance(sequence_no, int)
                    or isinstance(sequence_no, bool)
                    or sequence_no < 1
                ):
                    raise ValueError(
                        "pending reservation metadata is unavailable or malformed"
                    )
                scope = _parse_scope_json(scope_json)
                expected_key = _reservation_key(
                    repository,
                    task_id,
                    expected_checkpoint,
                    next_checkpoint,
                    action,
                    scope,
                )
                if reservation_key != expected_key:
                    raise ValueError("pending reservation key integrity check failed")

                updated = connection.execute(
                    """
                    UPDATE bounded_execution_outbox
                    SET status = 'dispatched'
                    WHERE reservation_key = ? AND status = 'committed'
                      AND COALESCE(invalidated, 0) = 0
                    """,
                    (reservation_key,),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("pending reservation claim conflict")
                connection.execute("COMMIT")
                return PendingReservation(
                    reservation_key=reservation_key,
                    repository=repository,
                    task_id=task_id,
                    expected_checkpoint=expected_checkpoint,
                    next_checkpoint=next_checkpoint,
                    action=action,
                    scope=scope,
                )
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def claim_dispatch(self, reservation_key: str) -> bool:
        """Grant exactly one dispatcher the committed reservation."""

        with closing(self._connect()) as connection:
            updated = connection.execute(
                """
                UPDATE bounded_execution_outbox
                SET status = 'dispatched'
                WHERE reservation_key = ? AND status = 'committed'
                  AND COALESCE(invalidated, 0) = 0
                """,
                (reservation_key,),
            )
        return updated.rowcount == 1

    def acknowledge_dispatch(self, reservation_key: str) -> bool:
        """Acknowledge completion so the task may reserve its next action."""

        with closing(self._connect()) as connection:
            updated = connection.execute(
                """
                UPDATE bounded_execution_outbox
                SET acknowledged = 1
                WHERE reservation_key = ?
                  AND status = 'dispatched'
                  AND COALESCE(acknowledged, 0) = 0
                """,
                (reservation_key,),
            )
        return updated.rowcount == 1
