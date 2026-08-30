# AGENTS.md

Guidance for AI coding agents working in this repository. Humans should read
[CONTRIBUTING.md](CONTRIBUTING.md), which covers the same ground in more detail.

## What this project is

A CLI tool that discovers which Netflix Open Connect Appliances (OCAs) are allocated
to the user's network, then enriches them with ASN/ISP data and geolocation. It is a
network *measurement* tool: much of its behaviour depends on live third-party
services, which constrains how it can be tested and refactored.

## Commands

```bash
uv sync --dev                     # install (uses the tracked uv.lock)
uv run pytest                     # 22 tests, ~2s, no network access
uv run ruff check .               # lint  — must be clean
uv run ruff format .              # format — must be clean
uv run mypy src/                  # ~33 pre-existing errors; advisory only
uv run netflix-oca-locator info   # local-only, safe to run
uv run netflix-oca-locator main   # makes real outbound network calls
```

Requires Python ≥3.10 and the `whois` binary on `PATH`.

## Layout

| Path | Role |
| --- | --- |
| `cli/interface.py` | Typer app: `main`, `version`, `info`; all Rich output |
| `core/models.py` | Pydantic v2 models; the only fully covered module |
| `core/oca_locator.py` | Orchestration; `create_locator()` factory |
| `api/fast_com.py` | Fast.com token scrape + OCA candidate discovery |
| `api/ip_services.py` | Public IP lookup; Team Cymru whois subprocess |
| `api/dns_resolver.py` | IPv4/IPv6 resolution, A vs AAAA selection, NAT64 |
| `utils/aleph_geocoding.py` | TheAleph API client + `HybridGeocodeService` (largest module) |
| `utils/geocoding.py` | geopy/Nominatim fallback, IATA lookup |
| `utils/formatters.py` | JSON/CSV/XLSX/Markdown export |
| `utils/mapping.py` | folium HTML maps |
| `config/settings.py` | pydantic-settings, `NETFLIX_OCA_` env prefix |

## Constraints

**Treat `api/` and `utils/aleph_geocoding.py` as stable.** They encode the
measurement methodology and are coupled to the observed behaviour of Fast.com,
TheAleph, Team Cymru and Nominatim. Do not refactor them opportunistically while
doing unrelated work. Changing them requires a stated rationale.

**Never make real network calls in tests.** Mock the HTTP client. `httpx.Response`
has a *synchronous* `.json()` and `.raise_for_status()` — use `MagicMock` for the
response and `AsyncMock` only for the client. Getting this wrong produces
`RuntimeWarning: coroutine ... was never awaited` and a confusing `None` result;
it has already caused three broken tests once.

**Do not "fix" the mypy errors as a drive-by.** They are known, the CI step is
`continue-on-error`, and at least one (`api/fast_com.py` constructing an
`OCAServer` without all required fields) is a real bug needing behavioural review.
Fix them deliberately, ideally one module per PR — but never introduce new ones.

**`uv.lock` is tracked.** CI installs from it via `uv sync --dev`, so it pins what
CI actually tests. Do not add it back to `.gitignore`. The Dockerfile does *not*
copy it — that stage uses `uv pip install`, which ignores lockfiles.

## Conventions

- Lint and format with ruff only (line length 100). No black, no flake8.
- NumPy-style docstrings, as used throughout the existing modules.
- [Conventional Commits](https://www.conventionalcommits.org/) for new commits.
- User-visible changes get an entry under `## [Unreleased]` in
  [CHANGELOG.md](CHANGELOG.md).
- The version appears in `pyproject.toml`, `src/netflix_oca_locator/__init__.py`
  and the `Dockerfile` label — keep all three in sync.

## Gotchas

- Coverage is ~24%; the CLI and `api/` modules are at 0%. Do not describe the test
  suite as comprehensive.
- The package is **not** published to PyPI. Install is from source.
- `netflix-oca-locator main` output varies by network location and by what live
  services return, so it is not reproducible between runs or machines.
