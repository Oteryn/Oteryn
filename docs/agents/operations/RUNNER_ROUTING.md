# Organization runner routing

Load this procedure before selecting or changing GitHub Actions runners, migrating a legacy runner workload, or considering a host-local META workload.

Product-owned host-local GitHub Actions workloads MUST use the product-isolated organization runner group and product label together:

- Platform: `platform-runners` + `oteryn-platform`;
- Atlas: `atlas-runners` + `oteryn-atlas`;
- Game: `game-runners` + `oteryn-game`.

Agents MUST NOT route new workloads by a custom label alone, MUST NOT add generic `self-hosted` eligibility, and MUST NOT introduce new workflow dependencies on the legacy `oteryn-staging` selector. `oteryn-synology-staging` is rollback-only while the organization-runner migration remains open and may be retired only after the provider closeout gates prove that it has no retained workload owner. META remains GitHub-hosted unless a separate host-local META workload is explicitly proven and authorized.

When migrating an existing `oteryn-staging` workflow, replace it with the owning product's group+label selector; do not preserve the legacy selector as a fallback in new code.

The detailed operational contract and live rollout evidence are provider-owned in `Oteryn/Oteryn-Platform/docs/operations/SYNOLOGY_ORGANIZATION_RUNNERS.md`; live GitHub organization state and provider workflow state outrank stale documentation.
