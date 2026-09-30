# Contributing

Calligraphy Studio combines a React/Konva editor, an Electron desktop shell, a Capacitor Android target, a static Pages build, and an optional FastAPI glyph service. Keep platform behavior explicit.

## Development

Web:

```shell
cd apps/web
npm ci
npm run typecheck
npm run test:visual
npm run build:desktop
```

API:

```shell
cd apps/api
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Browser regression tests are documented in the README. Add screenshots for visible UI changes and test Windows, Pages-sized, and mobile layouts where relevant.

## Asset and data rules

- Every committed font, image dataset, stroke dataset, or third-party data file needs source URL, exact license, redistribution/derivative rights, and a SHA-256 record.
- Update [docs/asset-policy.md](docs/asset-policy.md) and the relevant manifest when adding source assets.
- Do not commit runtime databases, generated glyph caches, `work/`, local exports, or release bundles.
- Generated browser font derivatives must remain traceable to their source font and license.
- User-provided non-commercial fonts must stay outside the repository unless redistribution is allowed.

## Pull requests

Keep platform changes separate where possible. Schema, persistence, cache, export ZIP, and release-version changes need compatibility notes. Maintainers perform tagged multi-platform releases.

Security issues must follow [SECURITY.md](SECURITY.md), not the public issue tracker.
