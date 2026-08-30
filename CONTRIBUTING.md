# Contributing to Netflix OCA Locator

Thanks for your interest in improving this project. It started in 2017 as a small
script and is now a packaged CLI tool, so contributions of all sizes are welcome —
including documentation fixes and test coverage.

Please also read the [Code of Conduct](CODE_OF_CONDUCT.md).

## Requirements

- **Python 3.10 or newer.** Python 3.9 support was dropped after it reached
  end-of-life in October 2025.
- **The `whois` command-line binary.** ISP/ASN enrichment shells out to Team Cymru's
  whois interface, so lookups fail without it.
  - macOS: included with the OS (`/usr/bin/whois`)
  - Debian/Ubuntu: `sudo apt-get install whois`
  - Alpine: `apk add whois`
- [uv](https://docs.astral.sh/uv/) is recommended but not required.

## Setting up

With uv (recommended — it installs the exact versions pinned in `uv.lock`):

```bash
git clone https://github.com/estcarisimo/Netflix-OCA-Servers-Locator.git
cd Netflix-OCA-Servers-Locator
uv sync --dev
uv run pre-commit install
```

With pip:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Verify the CLI is wired up:

```bash
uv run netflix-oca-locator version
uv run netflix-oca-locator info
```

## Development workflow

```bash
uv run pytest                       # run the test suite
uv run pytest --cov=netflix_oca_locator --cov-report=term-missing
uv run ruff check .                 # lint
uv run ruff format .                # format
uv run mypy src/                    # type check (see the caveat below)
```

`pre-commit` runs ruff's linter and formatter on staged files, so if you installed
the hooks you should rarely see a lint failure in CI.

### A note on mypy

**`mypy src/` currently reports roughly 33 errors, and the CI type-check step is
deliberately non-blocking.** These are pre-existing and predate this policy; some
of them point at genuine bugs (for example, `api/fast_com.py` constructs an
`OCAServer` without all of its required fields) that need behavioural review rather
than a mechanical annotation pass.

Two asks:

- **Do not add new type errors.** Compare `uv run mypy src/` before and after your
  change.
- **Fixing existing ones is very welcome**, ideally as a focused PR per module so
  the behavioural changes are easy to review. When the count reaches zero we can
  drop `continue-on-error` from the workflow.

### A note on test coverage

Coverage is currently about **24%**. `core/models.py` and `config/settings.py` are
well covered; the CLI, the API clients (`api/`), and the exporters are not covered
at all. Tests that raise coverage in those modules are one of the most useful
contributions available.

Tests must not make real network calls — mock the HTTP client. See
`tests/conftest.py` for the shared fixtures, in particular `mock_httpx_client` and
`mock_httpx_response`. Note that `httpx.Response.json()` and `raise_for_status()`
are *synchronous*: use a `MagicMock` for the response and reserve `AsyncMock` for
the client.

## Project layout

```
src/netflix_oca_locator/
├── cli/interface.py        Typer app: the `main`, `version` and `info` commands
├── core/
│   ├── models.py           Pydantic models (OCAServer, ISPInfo, OCALocatorResult)
│   └── oca_locator.py      Orchestration; the create_locator() factory
├── api/
│   ├── fast_com.py         Fast.com token scraping and OCA candidate discovery
│   ├── ip_services.py      Public IP lookup and Team Cymru whois ASN/ISP lookup
│   └── dns_resolver.py     IPv4/IPv6 resolution, A vs AAAA selection
├── utils/
│   ├── aleph_geocoding.py  TheAleph API client and the hybrid fallback chain
│   ├── geocoding.py        geopy/Nominatim geocoding and IATA city lookup
│   ├── formatters.py       JSON/CSV/XLSX/Markdown export
│   ├── mapping.py          folium interactive HTML maps
│   └── logging.py          loguru configuration
└── config/settings.py      pydantic-settings, `NETFLIX_OCA_` env prefix
```

`docs/THEALEPH_IPV6_SUPPORT.md` covers IPv6 and NAT64 handling in detail.

### Measurement code is intentionally stable

`api/` and `utils/aleph_geocoding.py` implement the measurement methodology and are
sensitive to the behaviour of third-party endpoints (Fast.com, TheAleph, Team
Cymru, Nominatim). Please don't refactor them opportunistically as part of an
unrelated change. Behavioural changes there should come with a clear rationale and,
where possible, a test.

## Pull requests

1. Branch from `master`.
2. Keep the change focused; separate mechanical cleanups from behavioural changes.
3. Make sure `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .`
   all pass.
4. Add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for anything
   user-visible.
5. Describe what you changed and why. If it affects measurement results, say how you
   verified it.

### Commit messages

New commits should follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add IPv6 support to the DNS resolver
fix: handle empty PTR records from TheAleph
docs: correct the install instructions
chore: bump ruff to 0.12
test: cover the CSV exporter
ci: run the matrix on Python 3.13
```

The history before 2025 predates this convention; no need to worry about it.

## Reporting bugs

Open an issue using the bug report template. Because results depend on your network
location and on live third-party services, please include:

- the command you ran and the full output of `netflix-oca-locator --debug`
- your OS and `netflix-oca-locator version`
- your approximate location and ISP/ASN, if you're comfortable sharing it

Please redact your public IP address if you'd rather not publish it.

For security issues, do **not** open a public issue — see [SECURITY.md](SECURITY.md).

## Academic context

The geolocation approach uses TheAleph, described in a paper published at ACM CoNEXT
2025 (Thiagarajan, Carisimo, Bustamante). If you use this tool in research, a
citation is appreciated.
