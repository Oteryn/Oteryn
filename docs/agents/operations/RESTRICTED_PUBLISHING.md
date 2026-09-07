# Restricted publishing-credential compatibility

Load this procedure when an already-authorized GitHub publication needs CLI/Git credential compatibility. Ordinary API-backed documentation work does not require it.

This profile applies only after the repository lifecycle has allocated an approved
task branch and existing PR. It does not grant PR-write permission to a restricted
publishing credential; PR creation remains a separately authorized control-plane action.

For an authorized write to that branch/PR, when `GH_TOKEN` and `GITHUB_TOKEN` are
unset but agent-visible `GH` is present, it may be passed transiently as
`GH_TOKEN="$GH"` to the exact authorized `gh` command. Environment mapping alone
does not authenticate `git push`: verify that the existing remote/credential path
can consume the authorized identity without exposing or persisting it. Otherwise
use another authorized repository-native write path or report the exact limitation.
Never embed the token in a remote URL or persist a new credential helper to bypass
that boundary. Credential presence expands no repository/path/task/merge/production
permission. Do not force-push; verify the remote exact head after publishing.
