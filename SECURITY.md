# Security policy

## Supported versions

This portfolio project supports the latest revision on the default branch. It
does not provide a production SLA and must not be used for trading or order
execution.

## Reporting a vulnerability

Do not open a public issue for a suspected credential leak or exploitable
vulnerability. Use GitHub's private vulnerability reporting feature when it is
enabled for the repository. Include the affected revision, reproduction steps,
impact, and any suggested mitigation. Do not include real TopicPilot data,
credentials, private URLs, holdings, or licensed content in the report.

The maintainer should acknowledge a report within seven days and publish a
remediation timeline after triage. No monetary bounty is offered.

## Security boundaries

- The v1 API is anonymous and read-only.
- Public deployments contain synthetic data only.
- Secrets belong in local `.env` files or protected deployment environments.
- Formal Google Sheets and private TopicPilot workflows are never queried by a
  public API request.
- Demo output is educational and is not financial advice.

See [the detailed security controls](docs/security/security-controls.md) and
[public data policy](docs/policies/public-data-and-licensing.md).
