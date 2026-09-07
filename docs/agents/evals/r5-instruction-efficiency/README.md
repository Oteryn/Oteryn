# R5 post-merge instruction-efficiency isolated trials

Tracks META Issue #164. This pack completes the behavioral A/B portion of the read-only R5 qualification without reopening #142 or modifying provider repositories.

## Low-cost execution

Run each alias in a **fresh ordinary Chat outside the Oteryn project**, with no prior R5 files/conclusions in that chat. Use the same configuration for every arm; recommended: **GPT-5.6 Sol, Medium**. Do not use Work/Astra or subagents for these trials.

Run each pair back-to-back so live-state drift is minimized. Do not discuss results between arms. Do not run the reviewer until all intended arm outputs have been collected.

Each exact alias is indexed in its own isolated arm file. The arm sees only its own provider/ref and the neutral `TRIAL_PROTOCOL.md`; it must not inspect sibling arms.

## Aliases

Game:
- `Oteryn: R5Q G1A`
- `Oteryn: R5Q G1B`
- `Oteryn: R5Q G2A`
- `Oteryn: R5Q G2B`
- `Oteryn: R5Q G3A`
- `Oteryn: R5Q G3B`
- `Oteryn: R5Q G4A`
- `Oteryn: R5Q G4B`

Platform:
- `Oteryn: R5Q P1A`
- `Oteryn: R5Q P1B`
- `Oteryn: R5Q P2A`
- `Oteryn: R5Q P2B`
- `Oteryn: R5Q P3A`
- `Oteryn: R5Q P3B`
- `Oteryn: R5Q P4A`
- `Oteryn: R5Q P4B`

Atlas:
- `Oteryn: R5Q A1A`
- `Oteryn: R5Q A1B`
- `Oteryn: R5Q A2A`
- `Oteryn: R5Q A2B`
- `Oteryn: R5Q A3A`
- `Oteryn: R5Q A3B`

Final reviewer:
- `Oteryn: R5Q review`

## Pair order

Use: G1 A/B → G2 A/B → G3 A/B → G4 A/B → P1 A/B → P2 A/B → P3 A/B → P4 A/B → A1 A/B → A2 A/B → A3 A/B.

One pair is enough initially. Repeat a pair once only when a material difference may be stochastic, an arm makes an unexpected mistake, or the verdict depends on one ambiguous run.

## Collection

Keep each `trial_result` block together with its task answer. The reviewer needs the outputs from both arms; if it cannot access them directly, paste or upload them. Missing arms remain `NOT_EVALUATED` and cannot be inferred from repository size.

The trial pack itself is on-demand evaluation material. It is not an always-loaded provider instruction surface and grants no repository, production, merge, Remote Desktop or paid-service authority.
