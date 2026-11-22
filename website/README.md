# Publish the Ex Herbario websites

Use two GitHub Pages repositories so each site has its own custom domain. This guide assumes both repositories are owned by `dzlatkovic`.

| Domain | GitHub repository | Pages source |
| --- | --- | --- |
| `docs.exherbario.org` | `dzlatkovic/exherbario` | GitHub Actions |
| `exherbario.org` | `dzlatkovic/exherbarium-website` | Deploy from a branch, `main`, `/ (root)` |

## Preview

Run from the HERBAR checkout:

```sh
python -m pip install -r requirements-docs.txt
python -m mkdocs build --strict
python -m mkdocs serve --dev-addr 127.0.0.1:8001
```

In a second terminal, run `python -m http.server 8002 --bind 127.0.0.1 --directory website/landing` to preview the homepage. The links between the two sites use their public domain names.

## Configure GitHub Pages

1. Verify `exherbario.org` under your GitHub account’s **Settings → Pages** using the TXT record GitHub gives you. Keep this TXT record in DNS.
2. In **exherbario → Settings → Pages**, select **GitHub Actions**. When the documentation changes reach `main`, the documentation workflow builds and publishes the site. You can also run **Documentation site** manually from the Actions tab. Set the custom domain to `docs.exherbario.org`.
3. Create a public `exherbarium-website` repository and copy the files inside `website/landing/`, including `.nojekyll`, to the root of its `main` branch. In **Settings → Pages**, select **Deploy from a branch**, then `main` and `/ (root)`. Set the custom domain to `exherbario.org`. GitHub will add a `CNAME` file to that branch. Keep it when updating the homepage.
4. Set the DNS records below. After GitHub reports the DNS checks passed and the certificates are ready, enable **Enforce HTTPS** for both repositories. Open both URLs and follow the links between them.

## DNS records

| Name | Type | Value |
| --- | --- | --- |
| `@` | `A` | `185.199.108.153` |
| `@` | `A` | `185.199.109.153` |
| `@` | `A` | `185.199.110.153` |
| `@` | `A` | `185.199.111.153` |
| `docs` | `CNAME` | `dzlatkovic.github.io` |
| `www` (optional redirect) | `CNAME` | `dzlatkovic.github.io` |

Review existing address records at `@`, `docs` and `www` before making the change. The TXT record for domain verification is specific to your GitHub account.

[GitHub Pages domain setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) · [Domain ownership verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages)
