# Security Policy

## Repository boundary

`Oteryn/Oteryn` is a public ecosystem coordination repository. It must contain only public-safe coordination metadata and documentation.

Do not commit or paste:

- passwords, access tokens, API keys, private keys, certificates or cookies;
- `.env` files or production connection strings;
- private deployment state or protected-environment values;
- personal data, database dumps, backups or live account/session data;
- proprietary/raw Game or client runtime assets;
- product runtime source merely to coordinate a release.

## Security-sensitive ecosystem changes

Changes that affect authentication/session contracts, package provenance, release integrity, repository migration, deployment boundaries or cross-repository trust must preserve explicit provider ownership and immutable evidence. Material `UNKNOWN` or `CONFLICT` state is not a passing release condition.

## Reporting

Do not publish an active credential or other secret in a public issue, pull request, discussion or commit. Use GitHub's private security-reporting facilities when available for the affected repository, or contact the repository owner through a private channel without reproducing the secret publicly.

If sensitive material is discovered in repository history, stop ordinary processing and treat revocation/rotation plus history-remediation scope as a separate security incident. Removing a visible line from the latest commit does not by itself revoke an exposed credential.
