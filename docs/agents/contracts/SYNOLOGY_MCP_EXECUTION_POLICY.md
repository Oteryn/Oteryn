# Synology MCP Agent Execution Policy

Status: active when merged to `main`.

## Purpose

Oteryn agents may use the ChatGPT developer MCP application `synology oteryn` as an additional execution and evidence source when it is available in the current conversation/workspace.

The MCP provides access to the authorized Synology environment. Its availability is a capability, not a source-of-truth override and not broader authorization.

## GitHub remains authoritative

For repository state, branches, commits, pull requests, issues, reviews, CI/checks, releases and other GitHub-hosted state, agents MUST continue to use current GitHub live state as the primary source of truth.

Agents MUST NOT use Synology MCP as a reason to skip, replace or weaken required GitHub inspection, PR workflow, review, CI, branch protection, evidence or repository-policy checks.

A local checkout, deployment, cached artifact or runtime observation on Synology does not prove current GitHub state.

## Appropriate MCP use

When authorized by the task and repository policy, agents SHOULD use `synology oteryn` for facts that are inherently local/runtime-specific, including available MCP-exposed filesystem state, disk/runtime information, deployment evidence and other Synology-local observations.

Agents may correlate Synology observations with GitHub state, but MUST identify which source establishes each fact when the distinction is material.

## Capability discovery and fallback

Before declaring Synology access unavailable, agents SHOULD discover whether `synology oteryn` is installed and callable in the current conversation. A plugin being installed does not prove that its tools are callable in that conversation.

If Synology MCP is unavailable, agents MUST continue all useful authorized GitHub/repository work and follow `AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`. MCP unavailability is a blocker only when a required Synology-local fact or operation cannot be obtained through another authorized path.

## Authorization boundaries

MCP tool availability NEVER grants permission to mutate production, deployments, services, containers, files, repositories, credentials or other state. Explicit owner/task authorization and applicable repository/organization policy remain required.

Do not expose or commit MCP tunnel credentials, API keys, tokens, secrets, private configuration or sensitive runtime data.

## Evidence and completion

Completion claims must use the appropriate authoritative evidence for each claim:

- GitHub facts: verify through GitHub live state;
- Synology/runtime facts: verify through `synology oteryn` or another explicitly authorized live runtime path;
- cross-system claims: verify both sides when both are material.

Never report a GitHub change as complete solely because a Synology deployment or checkout appears updated, and never report a runtime deployment as complete solely because GitHub CI or merge state is green.
