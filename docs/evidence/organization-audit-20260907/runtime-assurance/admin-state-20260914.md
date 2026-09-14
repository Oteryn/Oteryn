# ADMIN-STATE read-only assurance packet — 2026-09-14

## Scope and authority

This is the first bounded `AUDIT186-RUNTIME` obligation packet. It is a handoff to `AUDIT186-LEAD`, not a canonical accounting change and not authorization to mutate organization, repository, provider, or production settings.

| Coordinate | Verified fact |
| --- | --- |
| Canonical audit | `Oteryn/Oteryn#185`, exact released baseline `2d877271afa8f177983f3c6147472372adca0ed1`; read back OPEN/DRAFT at that head on 2026-09-14 |
| Programme authority | `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d`; the immutable programme assigns `ADMIN-STATE` to `AUDIT186-RUNTIME` and prohibits administrative mutation |
| Release authority | `Oteryn/Oteryn#186` comment `5666964258`, created `2026-09-14T16:08:07Z`, token `AUDIT186_PARALLEL_RELEASE_READY` |
| Worker authority | `docs/agents/workers/AUDIT186-RUNTIME-01.md` at worker parent `efd89ee948886f52df9e5557ea8ae4dea0a4c600` |
| Canonical obligation | `docs/evidence/organization-audit-20260907/unknowns.json` at baseline `2d877271afa8f177983f3c6147472372adca0ed1`, item `ADMIN-STATE` |
| Organization identity | GitHub REST `GET /orgs/Oteryn` returned HTTP 200 on 2026-09-14 and identified organization login `Oteryn`, database ID `318116449`, node ID `O_kgDOEvYSYQ` |

The release checkpoint also records exact-head META CI run `34860587490` as SUCCESS. That is a **CI fact only**. It does not attest organization administrative settings.

## Canonical closure condition

The exact canonical closure condition is:

> Provide dated nonsecret exported settings and authorized verification; never secret values.

The canonical missing fact is “Current organization/admin security settings”; its stated effect is “No current private reporting/scanning/member/privilege attestation.”

## Read-only observation

On 2026-09-14, the authenticated repository-native GitHub REST route was used without changing settings. The public/authenticated organization record was readable, but every administrative value relevant to the closure condition was absent from that response: the returned projections for two-factor enforcement, default repository permission, member repository-creation/forking permissions, web commit signoff, and new-repository dependency graph, Dependabot, code-security, secret-scanning, and push-protection defaults were `null`.

The same authenticated route returned HTTP 403 for these narrower observations:

- `GET /orgs/Oteryn/security-managers`;
- `GET /orgs/Oteryn/outside_collaborators`;
- `GET /orgs/Oteryn/code-scanning/alerts`;
- `GET /orgs/Oteryn/secret-scanning/alerts`;
- `GET /orgs/Oteryn/dependabot/alerts`.

HTTP 403 proves only that this credential/session could not read those endpoints at observation time. It does **not** prove that a feature is enabled or disabled, that alerts exist or do not exist, or that any member has or lacks a privilege. No response bodies, names, alert records, tokens, secrets, private repository inventory, or other live private state are retained in this packet.

## Disposition

| Evidence class | Disposition | What is established |
| --- | --- | --- |
| Source | **PROVEN (bounded)** | The canonical obligation, owner route, effect, and closure wording exist at the exact audit baseline. Source text does not establish live settings. |
| CI | **PROVEN (bounded)** | Release authority reports META CI run `34860587490` successful on the canonical baseline. CI does not establish live organization settings. |
| Admin | **PROVEN (identity/readability only)** | The dated read identifies the organization and proves the general organization record was readable while the listed privileged observations were not readable in this session. |
| Runtime / telemetry / recovery | **NOT APPLICABLE to this packet** | No claim is made from these evidence classes. |
| `ADMIN-STATE` closure | **UNKNOWN / BLOCKED** | Current private-reporting, scanning, membership, and privilege configuration is not attested. Closure is blocked on a privileged, sanitized observation rather than on an implementation defect. |

The obligation must remain open. Neither source presence, a green CI run, null fields, nor denied administrative endpoints may be upgraded to administrative PASS or organization/runtime readiness.

## Smallest additional observation and recheck trigger

The smallest sufficient addition is one organization-owner-produced, dated, nonsecret evidence export (or equivalently complete authorized read-only verification) bound to organization ID `318116449` that satisfies the canonical `ADMIN-STATE` obligation **and** the ADMIN-backed finding-specific closure conditions. It must include all of the following without exposing secrets or personal/private records:

- the dated current private-reporting setting **and a verified private reporting channel** (`META-AUD-08`);
- current code-scanning capability, scan scope, explicitly excluded languages, current findings, and triage evidence, with no zero-CVE inference (`META-AUD-09`);
- the relevant membership and privilege settings needed to attest the remaining ADMIN-STATE categories;
- observation time, verifier identity/role, exact organization identity, and an immutable evidence coordinate or digest suitable for authorized verification.

A settings/status-only export that does not establish the verified private-reporting channel or the scan capability/scope/exclusions/findings/triage evidence is **insufficient** and must not close `ADMIN-STATE`. All retained evidence must remain sanitized and nonsecret.

That complete observation was **not readable with the current session credential** and administrative mutation is **not authorized**. No broader access or mutation should be requested merely to convert the obligation to PASS.

Exact recheck trigger: `AUDIT186-LEAD` records either (a) the dated sanitized owner evidence and its immutable coordinate covering every requirement above, or (b) separately authorized read-only visibility sufficient to verify every requirement above. On that event, rerun the bounded comparison, bind the result to organization ID `318116449` plus observation time/evidence digest, verify `META-AUD-08` and `META-AUD-09` closure conditions explicitly, and only then reassess `ADMIN-STATE`. Ordinary source changes, CI success, a settings-only export, or another HTTP 403 are not recheck triggers.

## Lead handoff

`AUDIT186-LEAD` should preserve `ADMIN-STATE` as open/unknown. This packet proposes no canonical ledger, report, README, coverage, unknowns, verification-index, or collection-plan edit. The only admissible future closure input is the sanitized, dated, authorized administrative evidence described above, including the finding-specific private-reporting and scanning proof rather than settings/status alone.
