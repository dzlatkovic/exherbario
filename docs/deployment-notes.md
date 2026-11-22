# Deployment notes (not yet tested)

Not published on the documentation site. These describe the container image and a demo instance, which have not
been deployed yet. Move them into operations.md once they have been tried.

## Deploying with Docker

The repository's `Dockerfile` runs the migrations and then starts the app on `$PORT` (8000 by default). The
database, uploads and photographs live in `DATA_DIR`; mount a persistent volume there, or every redeploy starts
empty.

| Variable | Value |
| --- | --- |
| `DATA_DIR` | `/data` (the volume's mount path) |
| `DATABASE_URL` | `sqlite:////data/herbar.db` (four slashes: an absolute path) |
| `PUBLIC_BASE_URL` | The public address, e.g. `https://demo.exherbario.org` |
| `USER_SECRET` | A random value of at least 32 bytes, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

The proxy in front of the app (Railway's, or Caddy/nginx on a faculty server) handles HTTPS. Uvicorn trusts its
forwarded headers so that links and secure cookies use `https`.

## A public demo on Railway

A demo instance sets `DEMO_MODE=true`. In that mode the app:

- shows a banner on every page and asks search engines not to index it;
- lists the demo accounts and their password (`DEMO_PASSWORD`, default `herbar-demo`) on the sign-in page;
- keeps publishing locally: no DOI registration, no Zenodo mirror and no Darwin Core Archive for GBIF;
- seeds itself with synthetic data when its database is empty, and resets every day at `DEMO_RESET_HOUR` UTC
  (default 3; `-1` turns the reset off).

Steps on Railway (the Hobby plan, which allows a custom domain):

1. Create a project, choose **Deploy from GitHub repo**, and select the repository. Railway builds the `Dockerfile`.
2. Add a **volume** to the service, mounted at `/data`.
3. Set the variables in the table above, plus `DEMO_MODE=true`.
4. Under **Settings → Networking**, add the custom domain `demo.exherbario.org`. Then create the CNAME record that
   Railway shows at your DNS provider. Railway issues the certificate.
5. Deploy. The first start seeds the demo; open the address and sign in with a demo account.

To start the demo again by hand, open the service's shell and run `python -m app.demo reset`. Every demo command
refuses to run unless `DEMO_MODE` is on, so a real instance cannot be wiped.

The seed looks taxa up in GBIF and compounds in PubChem. To make it work without network access, run
`python -m app.demo record` once on a machine that is online, and commit `app/demo_data/lookups.json`; after that,
`python -m app.demo reset --offline` uses only the recorded answers.

Never run a demo and real data in the same instance: the demo's accessions and identifiers are not permanent.
