# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases before 2.1.0 predate this changelog and were reconstructed from the git
history and the `v1.0.0`/`v2.0.0` tags, so their entries summarise the work rather
than list every change.

## [Unreleased]

### Removed

- The Codecov upload step. It required a `CODECOV_TOKEN` that was never
  configured, so it silently did nothing, and a coverage badge is not worth
  publishing at 24%. Coverage is still reported in the CI job log via
  `--cov-report=term-missing`, and `uv run pytest --cov=netflix_oca_locator`
  gives the same numbers locally. Worth revisiting once `api/` and `cli/` have
  real test coverage.

### Changed

- Reformatted the Python samples in `docs/THEALEPH_IPV6_SUPPORT.md`. Ruff 0.16
  formats code blocks inside Markdown, which older versions did not.

## [2.1.0] - 2026-08-30

2.1.0 was never actually released: the version string existed only as a stale
`Dockerfile` label while `pyproject.toml` still said 2.0.0. This release resolves
that drift and combines the July 2025 IPv6 work with a repository hygiene pass.

### Added

- **IPv6 support** with intelligent DNS resolution (`api/dns_resolver.py`): selects
  A or AAAA records based on the OCA domain naming convention, with NAT64 detection
  and handling. See [docs/THEALEPH_IPV6_SUPPORT.md](docs/THEALEPH_IPV6_SUPPORT.md).
  (Developed 2025-07-22.)
- PTR record validation before querying TheAleph, so IPv6-form records are not sent
  to an endpoint that cannot decode them. (Developed 2025-07-22.)
- `CONTRIBUTING.md`, `CHANGELOG.md`, `AGENTS.md`, `SECURITY.md` and
  `CODE_OF_CONDUCT.md`. The README had linked to a non-existent `CONTRIBUTING.md`.
- `.pre-commit-config.yaml` with ruff lint and format hooks. The README had told
  contributors to run `pre-commit install` without a configuration existing.
- `.github/dependabot.yml` for GitHub Actions and Python dependency updates.
- Issue and pull request templates.
- `[project.optional-dependencies].dev`, so `pip install -e ".[dev]"` installs the
  development tools as documented. They were previously only declared under
  `[tool.uv] dev-dependencies`.
- A `.dockerignore`, so the Docker build context excludes `.git`, `.venv` and tests.

### Changed

- Restored full HTTPS for TheAleph API requests. (Developed 2025-07-22.)
- **Minimum Python is now 3.10.** Python 3.9 reached end-of-life in October 2025.
  The CI matrix is now 3.10–3.13.
- `uv.lock` is now tracked in git, so CI installs the same dependency versions that
  are tested locally instead of re-resolving on every run.
- The mypy CI step is advisory (`continue-on-error`) rather than a blocking gate,
  pending a fix for the pre-existing type errors. This unblocks the `build` and
  `integration-test` jobs, which had never run because they sit behind
  `needs: [lint, test]`.
- All GitHub Actions bumped to current majors (`checkout` v4→v7, `upload-artifact`
  v4→v7, `download-artifact` v4→v8, `setup-uv` v4→v10, `codecov-action` v4→v7).
  `trivy-action` is pinned to a release tag instead of `@master`.
- The Docker workflow builds a single-platform image with `load: true` so the smoke
  tests can actually run, with multi-architecture builds verified in a separate job.
- Dependency vulnerability monitoring moved from `safety` (which requires
  authentication since 3.x and was therefore a no-op in CI) to Dependabot.
- Coverage flags removed from the pytest `addopts`, so a bare `pytest` run no longer
  requires pytest-cov or writes `htmlcov/` and `coverage.xml` into the working tree.

### Fixed

- All four `[project.urls]` entries pointed at the wrong GitHub account.
- `codecov-action` was passed `file:`, an input removed in v4, so coverage uploads
  were silently doing nothing. It is now `files:`.
- The Docker workflow's smoke tests could never pass: the image was built
  multi-platform with `push: false` and no `load: true`, so it never entered the
  local daemon.
- The Docker Hub login step errored on every push event because
  `DOCKER_USERNAME`/`DOCKER_PASSWORD` were unset — and nothing was ever pushed.
  Removed.
- Trivy SARIF upload failed under the default read-only token; the job now requests
  `security-events: write`.
- Three failing tests in `tests/test_utils/test_aleph_geocoding.py`. All were test
  harness bugs: `AsyncMock` used for the synchronous `httpx.Response` API, mock
  payloads in a shape `_parse_aleph_response` never accepted, and a stale assertion
  that `HybridGeocodeService` calls TheAleph only once (it retries with Netflix's
  ASN 2906 before falling back to geopy).
- Version drift between `pyproject.toml` (2.0.0) and the Dockerfile label (2.1.0).
- The `aleph_ssl_verify` setting defaulted to `False` and was described as "disabled
  due to cert issues", but `AlephGeocodeService` has hardcoded `verify=True` since
  HTTPS was restored in 2.1.0 and never reads the setting. The declared default now
  matches actual behaviour, so the config no longer advertises TLS verification as
  off when it is on. No runtime behaviour changed.

The Docker build itself was independently repaired in #6 and #7 — the missing
`LICENSE`/`README.md` in the builder stage and the `yourusername` placeholder in
`org.opencontainers.image.source`.

### Removed

- `main.py`, a leftover `uv init` stub that printed "Hello from
  netflix-oca-servers-locator!" and was never the entry point.
- `bandit-report.json`, a stale committed CI artifact that CI regenerates on
  every run.
- The session-scoped `event_loop` fixture, removed in pytest-asyncio 1.x.
- Roughly 120 lines of Node.js/Next.js/Gatsby/Storybook boilerplate from
  `.gitignore`.

## [2.0.0] - 2025-07-20

Complete rewrite from a standalone script into an installable Python package.

### Added

- `src/` layout package with a `netflix-oca-locator` console entry point.
- Typer-based CLI with `main`, `version` and `info` commands, and Rich terminal
  output with progress indication.
- Pydantic v2 models (`OCAServer`, `ISPInfo`, `PublicIPInfo`, `OCALocatorResult`)
  and pydantic-settings configuration under the `NETFLIX_OCA_` environment prefix.
- Async HTTP via httpx with tenacity-based retries.
- **Geolocation via TheAleph**, an LLM-based DNS PTR decoder (Thiagarajan, Carisimo,
  Bustamante — ACM CoNEXT 2025), with a hybrid fallback to geopy/Nominatim.
- Export to JSON, CSV, XLSX and Markdown.
- Interactive HTML maps via folium.
- Docker support: multi-stage Alpine build, non-root user, compose file.
- Test suite (pytest), ruff lint/format, mypy configuration and GitHub Actions CI.

### Changed

- ISP/ASN enrichment now performs a per-OCA ASN lookup rather than only resolving
  the user's own network.

## [1.0.0] - 2025-04-16

The standalone script, as it stood before the 2.0 rewrite. Tagged retroactively.

Its development spans the whole pre-package history of the project:

- **2017-10-04** — initial commit: Fast.com token scraping and OCA discovery.
- **2020-04** — DNS resolution of OCA hostnames, host ISP information via Team
  Cymru whois, and Python 3 compatibility (contributed via PR #2).
- **2024-02** — general cleanup; MIT license added.
- **2025-04-16** — improved output readability.

[Unreleased]: https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/releases/tag/v1.0.0
