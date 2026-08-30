# Security Policy

## Supported versions

This is a small research tool maintained on a best-effort basis. Only the latest
release receives fixes.

| Version | Supported |
| ------- | --------- |
| 2.1.x   | ✅        |
| < 2.1   | ❌        |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Use GitHub's private reporting instead:
[Report a vulnerability](https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/security/advisories/new).

Please include a description of the issue, reproduction steps, and the version and
platform you saw it on. Expect an acknowledgement within about two weeks — this is a
side project, not a staffed product, so response times are best-effort.

## What this tool does with your data

Worth understanding before you run it, and relevant to what counts as a
vulnerability here:

- **It discovers and reports your own public IP address**, and by extension your ISP,
  ASN and BGP prefix. This information is displayed on your terminal and written to
  any export file or map you generate. Exports and generated maps are gitignored by
  default, but be careful about sharing them.
- **It makes outbound requests to third parties**: Fast.com (Netflix) for the OCA
  candidate list, `thealeph.ai` for geolocation, Team Cymru's whois service for
  ASN/ISP lookup, and Nominatim (OpenStreetMap) as a geocoding fallback. Those
  services see your IP address and the queries you make. Their privacy policies
  apply.
- **It shells out to the `whois` binary** with hostname and IP arguments derived
  from DNS responses. Report any way to influence that invocation beyond an IP
  address as a vulnerability.
- **It performs DNS resolution** of Netflix OCA hostnames.

It does not require credentials, does not send telemetry, and stores nothing outside
files you explicitly ask it to write.

## Scope

In scope:

- Command or argument injection, including via the `whois` subprocess.
- Path traversal in the export or map output paths.
- Unsafe deserialisation or parsing of third-party API responses.
- Accidental disclosure of the user's IP or network details beyond what is
  documented above.
- Dependency vulnerabilities with a plausible exploitation path in this tool.

Out of scope:

- The fact that the tool reveals your own public IP address — that is its purpose.
- Vulnerabilities in third-party services (Fast.com, TheAleph, Nominatim, Team
  Cymru); report those to their respective maintainers.
- Findings from automated scanners with no demonstrated impact.

## Automated scanning

CI runs bandit over `src/` and Trivy over the Docker image, both advisory. Dependency
updates are handled by Dependabot.
