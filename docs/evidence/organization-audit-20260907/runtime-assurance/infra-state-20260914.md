# INFRA-STATE read-only assurance packet — 2026-09-14

## Scope and authority

This is the second sequential bounded `AUDIT186-RUNTIME` obligation packet. The clean first `ADMIN-STATE` batch is frozen at Issue #186 comment `5671807221` with disposition `UNKNOWN / BLOCKED`; this packet neither changes nor reopens it. This is a handoff to `AUDIT186-LEAD`, not a canonical accounting change or authority to access or mutate a provider or production surface.

| Coordinate | Bound authority or source identity |
| --- | --- |
| Current canonical source | `Oteryn/Oteryn#185@2f78fafbacc12723516bb7dd00376812c31385ef`, tree `44c64c60f9e71bde27ff86e7d19c77476cc07ade`; canonical checkpoint Issue #186 comment `5671661917` |
| Programme authority | `Oteryn/Oteryn#203@82bc113797ecdc70d79aee628d339136b816e15d` |
| Worker authority | `docs/agents/workers/AUDIT186-RUNTIME-01.md` in this exact worker candidate |
| Current public/source heads | META `d9419b05eb98c81279297563c11fc90e4fe708ac`; Game `775a09091743af395ecb8f1e440cb9c286bc0dd2`; Platform `84d504c98acc8134eb4c9545711010b74c987974`; Atlas `0d22a8d4378e66441502482ce715e226d487248e` |

Those four heads establish source identity only. They do not establish the release actually running, production configuration, infrastructure health, or deployment readiness.

## Canonical INFRA contract

At the canonical source above, the contract is bound exactly as follows:

| Field | Exact canonical value |
| --- | --- |
| Missing | `Private production runtime configuration` |
| Reason | `No host exception or production access used.` |
| Effect | `No infrastructure health or deployment readiness conclusion.` |
| Owner route | `Provider operations owners` |
| Closure | `Authorized read-only configuration/health snapshot with redaction and exact release.` |

No host exception or production access was requested or used for this packet.

## Bounded public source-side evidence inventory

All entries below are public source or deployment-definition evidence from `Oteryn/Oteryn-Platform@84d504c98acc8134eb4c9545711010b74c987974`. Blob identities make each observation immutable; workflow IDs identify the current public GitHub workflow records. Their presence describes intended tooling and contracts only.

| Path / identity | Evidence class | Bounded source fact |
| --- | --- | --- |
| `.github/workflows/build-synology-staging-images.yml`, blob `d3d7359d3cc9b5e939b456ac704522a418650d35`, workflow ID `319216301` | Source / deployment definition | The public staging-image workflow classifies release-relevant inputs, validates deployment contracts and Compose manifests, and defines image-build/publication jobs. This does not prove that a particular image was built, published, or deployed. |
| `.github/workflows/deploy-synology-staging.yml`, blob `eb6bb645e7cf9642137fd7d963e5a6a9d9bb3674`, workflow ID `319229654` | Source / deployment definition | The public manual staging workflow requires an exact release SHA and immutable component image digests for deploy inputs, targets the `synology-staging` environment, and invokes configuration and health validation. It does not prove a run occurred or identify live production state. |
| `.github/workflows/character-bazaar-staging-control.yml`, blob `96aa133abfea547c2d6734d9967195dfa646fb9f`, workflow ID `324376313` | Source / staging control definition | The bounded marketplace staging control resolves an exact release tag, waits for matching images, renders staging configuration, and supports guarded verification/rollback actions. It is staging-specific and proves no production deployment or health fact. |
| `.github/workflows/character-bazaar-staging-validation.yml`, blob `528b5cb71a83660b3f32635e3ec0a9b23aabe7a7`, workflow ID `324323080` | Source / validation definition | The public validation workflow checks the marketplace staging package and fail-closed Compose overlay. Definition presence is not evidence that a current run passed or that the validated package is deployed. |
| `deploy/synology/compose.yml`, blob `2c50ef034b040a4b1a590e0cdfa736b74d29a076` | Source / runtime topology definition | The staging Compose contract declares MariaDB, Redis, Platform, Canary, internal proxy, and Gateway services; dependency ordering; health checks; private-network membership; and configured published bindings. It describes intended staging topology, not observed containers, bindings, or network state. |
| `deploy/synology/scripts/release-state.sh`, blob `441cab3db65d532a31ba821511a78d3cbf879b03` | Source / release-identity contract | The script validates exact source SHAs, immutable image digests, schema compatibility identity, and rollback eligibility in release metadata. It supplies a contract for release identity but no current release record. |
| `deploy/synology/release-contract.env`, blob `63265fdd61b78ca34c4b2c361a3200dacb614e61` | Source / compatibility definition | The public staging contract declares expand-contract migration and `platform-schema-v1` compatibility. It does not establish the schema or application release in a live environment. |
| `deploy/synology/scripts/health-check.sh`, blob `cebd189c6967e6ba9d9e302a1219bbee268f7531` | Source / healthcheck contract | The script defines checks for service existence/running state, published bindings, Platform/Canary/Gateway health, internal TLS dependencies, Gateway readiness and version identity. It is a definition of observations to make, not a current observation. |

No workflow run, image publication, deployment, artifact, or production-health result is claimed as `PROVEN`: this packet did not identify exact current public evidence sufficient to bind any such event to the release actually running.

## Evidence classification and disposition

| Evidence class | Disposition | What is established or missing |
| --- | --- | --- |
| Public source / deployment definitions | **PROVEN (bounded)** | The exact files and declared contracts above exist at the pinned Platform commit. They establish intended staging release identity, topology, deployment, and healthcheck behavior only. |
| CI / build / publication | **UNKNOWN for a live release** | No exact public run or artifact evidence in this packet binds a successful build or publication to the release actually running. Even a green run or published artifact would remain CI/publication evidence, not live production proof. |
| Private production configuration and environment/secrets | **UNKNOWN / BLOCKED** | No authorized sanitized snapshot establishes intended-versus-observed production configuration. No environment or secret value was read or retained. |
| Exact release actually running | **UNKNOWN / BLOCKED** | No current commit, image digest, or artifact digest is bound to an observed production deployment. |
| Host / container / service health | **UNKNOWN / BLOCKED** | No authorized current observation establishes host state, container identity/running state, service healthchecks, or required dependencies. |
| Ingress / routing / network state | **UNKNOWN / BLOCKED** | No authorized current observation establishes external ingress, internal routing, bindings, reachability, or network health. |
| Operational deployment readiness | **UNKNOWN / BLOCKED** | Source/workflow presence, staging definitions, artifacts, or green CI cannot establish operational or production readiness. |
| `INFRA-STATE` closure | **UNKNOWN / BLOCKED** | The canonical redacted, exact-release configuration/health snapshot is absent. |

`INFRA-STATE = UNKNOWN / BLOCKED`. No production access, host exception, SSH, private environment read, secret, raw private log, deployment mutation, or provider write was requested or used. Source definitions must not be promoted into live truth.

## Smallest sufficient future closure evidence

The smallest sufficient closure input is one dated, sanitized, owner-produced snapshot, or a separately authorized read-only configuration/health snapshot, bound to the exact audited release by commit, immutable image digest, or artifact digest as applicable. It must contain only the nonsecret operational facts necessary to establish:

- observation time and provider/environment role, without a person's identity;
- exact release identity for each applicable deployed component;
- redacted intended-versus-observed configuration and topology sufficient to compare the deployment with its exact source contract;
- service and healthcheck state; and
- the health of required dependencies, routing, and ingress for the audited release.

The retained snapshot must explicitly exclude secret values, credentials or tokens, personal identifiers, raw private logs, and private hostnames or IP addresses unless a particular hostname or address is strictly necessary to the bounded conclusion and separately approved. Evidence should use roles and redacted stable labels rather than personal or private infrastructure identifiers.

A valid one-time healthy snapshot would establish only bounded INFRA configuration and health for the exact release, environment role, and observation time it records. It would **not** prove SLO or telemetry coverage, sustained availability, failure yield, recovery behavior, RPO/RTO, or broader product readiness. `LIVE-TELEMETRY` and `RECOVERY` remain separate OPEN obligations.

The sufficient snapshot is not currently authorized/readable in this lane. Provider operations owners may produce it, or a separately authorized reader may perform the bounded read-only observation; neither route authorizes mutation.

## Exact recheck triggers and lead handoff

Recheck `INFRA-STATE` only upon one of these events:

1. receipt of the sufficient authorized sanitized snapshot described above;
2. a change to the exact release or source contract before such evidence is used, requiring the snapshot/comparison to be rebound; or
3. a disposition from the provider-operations owner route.

CI or source churn alone must not close `INFRA-STATE`. On a trigger, `AUDIT186-LEAD` must verify the authorization, redaction boundary, exact-release binding, observation time, and complete bounded health/configuration content before reassessing the obligation. This packet closes no obligation and proposes no canonical report, accounting, README, coverage, unknowns, index, verification-index, or collection-plan change.
