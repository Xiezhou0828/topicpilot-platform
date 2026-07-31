# Public data and licensing policy

## Policy

The public repository, CI logs, Docker images, deployment, screenshots, videos,
Power BI files, and downloadable exports contain synthetic data only. Passing a
schema check does not make data safe to publish; every artifact must also pass
classification and content review.

## Allowed public content

- Artificial stock identifiers, names, prices, scores, dates, and relationships
  created specifically for this repository.
- Synthetic strategy candidates and performance values that cannot be mistaken
  for recommendations or reconstructed into private results.
- Source code, migrations, tests, diagrams, and documentation owned by the
  project and covered by the repository license.
- Short factual references to public software/service documentation with links.

## Prohibited public content

- Google service-account files, API tokens, cookies, deploy hooks, database
  credentials, private R2 URLs, or signed URLs.
- Real holdings, transactions, account balances, watchlists, annotations, or
  personally identifying information.
- Raw Google Sheet exports or private formal-workflow output.
- Licensed quote history, vendor feeds, broker API payloads, or datasets whose
  redistribution terms are unknown.
- Full or substantial news/article text, analyst reports, paid research, or
  copyrighted transcripts.
- Customer/client names, internal endpoints, local user paths, and private
  operational logs.
- Real stock values relabeled as “synthetic” without independently generating
  them.

## Synthetic-data requirements

Synthetic fixtures must:

1. Be generated independently for the demo and carry a public-safe
   classification in `manifest.json`.
2. Use visibly fictional identifiers/names or prominently label every public
   surface as synthetic.
3. Preserve realistic nulls and referential relationships for engineering tests
   without reproducing real investment output.
4. Avoid current real-world predictions, recommendations, news text, and exact
   private strategy results.
5. Include no credentials, private paths, or environment-specific URLs.

## Code and data licensing

Repository source code is offered under the MIT License. MIT applies only to
copyrightable material the repository owner has permission to license. It does
not grant rights to third-party trademarks, market data, news, or vendor APIs.

Synthetic fixture files created for this project may be used with the code
under MIT unless a fixture directory states a different license. Any future
third-party data requires a documented source, license, attribution, allowed
uses, redistribution analysis, and expiry/removal process before inclusion.

## Publication checklist

- [ ] Manifest classification is public-safe and source kind is synthetic.
- [ ] Gitleaks passes across full reachable Git history.
- [ ] No prohibited filename or private path is present.
- [ ] Search for credentials, email addresses, account/Sheet IDs, signed URLs,
      and provider hostnames returns only approved documentation examples.
- [ ] Values and labels are visibly synthetic and not copied from formal data.
- [ ] Screenshots, videos, `.pbix`, CSV exports, and CI artifacts are reviewed.
- [ ] Public UI includes a synthetic-data/not-financial-advice warning.
- [ ] A second reviewer signs off before first public deployment.

## Incident response

If prohibited content is published, remove access, rotate credentials when
applicable, preserve evidence privately, clean active artifacts/history, and
complete a new review before republishing. Follow [SECURITY.md](../../SECURITY.md)
for vulnerability reporting.
