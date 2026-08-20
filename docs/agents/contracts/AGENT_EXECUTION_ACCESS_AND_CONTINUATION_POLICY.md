# Agent Execution Access and Continuation Policy

Status: active contract.

## Purpose

Agents operating in the Oteryn ecosystem must distinguish execution capability, permission boundaries, unknown state and verified completion.

A missing capability must not be confused with completed analysis, and an unknown state must not be reported as a blocker without verification.

## Access discovery before blocking

Before reporting:

- "I don't have access";
- "I cannot inspect the repository";
- "execution is blocked";

an agent MUST:

1. inspect available tools and execution capabilities;
2. check available authentication/context;
3. determine whether the limitation is:
   - missing tool;
   - missing permission;
   - temporary failure;
   - repository policy restriction.

A generic access disclaimer without capability discovery is invalid.

## Capability classification

Agents must classify the current environment:

### Execution available

The agent may inspect, modify, test and perform allowed repository operations.

### Read-only

The agent may inspect, audit and report findings but MUST NOT claim implementation completion.

### No external capability

The agent may prepare patches, commands and handoff instructions, but must state the exact missing capability.

## Autonomous continuation mode

When instructed to continue, finish, complete or proceed autonomously, an agent MUST:

1. verify current repository truth;
2. continue from the current state;
3. perform safe reversible actions;
4. avoid restarting completed work;
5. stop only for missing permissions, safety boundaries, irreversible owner decisions or contradictory authority sources.

## Missing capability recovery

If execution is temporarily unavailable, the agent MUST NOT stop at a generic explanation.

The agent should:

1. identify the exact missing capability;
2. continue analysis and validation where possible;
3. prepare the smallest executable change set;
4. define the exact next execution step;
5. resume implementation when capability becomes available.

## Truth hierarchy

Authority order:

1. current repository state;
2. current CI and checks;
3. current policies and contracts;
4. current PR/task records;
5. previous agent reports.

Previous handoffs are evidence to verify, not authority.

## Agent handoff verification

Continuation agents MUST verify current HEAD, branches, PRs, CI, protection rules, ownership and evidence artifacts.

## Completion reporting

Reports MUST separate:

- FACT: directly verified;
- UNKNOWN: unavailable information;
- BLOCKER: specific missing capability or permission.

Unknown is not automatically a blocker. Agents MUST NOT claim DONE without verification.

## Anti-false-stop rule

A failed assumption about access is itself a failed execution path.

Agents must discover available capabilities before stopping and continue useful work whenever possible.
