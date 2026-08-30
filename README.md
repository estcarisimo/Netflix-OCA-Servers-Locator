# 🌐 Netflix OCA Locator

A modern, feature-rich CLI tool to discover Netflix's Open Connect Appliances (OCAs) allocated to your network. Built with Python, this tool provides detailed insights into Netflix's content delivery infrastructure and helps you understand how Netflix optimizes streaming performance for your location.

[![CI](https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/actions/workflows/ci.yml/badge.svg)](https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/actions/workflows/ci.yml)
[![Docker](https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/actions/workflows/docker.yml/badge.svg)](https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/actions/workflows/docker.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🔍 **Automatic OCA Discovery**: Identifies Netflix OCAs serving your network
- 🌍 **Enhanced Geolocation**: Advanced location resolution using TheAleph API with fallback to standard geocoding
- 📊 **Rich Terminal Output**: Beautiful CLI with colors, emojis, and tables
- 📁 **Multiple Export Formats**: JSON, CSV, Excel, and Markdown exports
- 🗺️ **Interactive Maps**: Generate HTML maps showing OCA locations
- 🐳 **Docker Support**: Ephemeral containers with auto-cleanup and volume mounting
- ⚡ **Async Performance**: Fast, concurrent API calls
- 🔒 **Robust Error Handling**: Comprehensive retry logic and graceful degradation
- 📝 **Detailed Logging**: Configurable logging with file output
- ⚙️ **Flexible Configuration**: Environment variables and settings files

## 🚀 Quick Start

### Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/estcarisimo/Netflix-OCA-Servers-Locator.git
cd Netflix-OCA-Servers-Locator
uv sync
```

Traditional pip installation:

```bash
git clone https://github.com/estcarisimo/Netflix-OCA-Servers-Locator.git
cd Netflix-OCA-Servers-Locator
pip install -e .
```

> **Note:** this package is not published to PyPI — `pip install netflix-oca-locator`
> will not work. Install from a clone, as shown above.

### System Requirements

- Python 3.10 or higher
- The `whois` command-line tool:

  ```bash
  # Ubuntu/Debian
  sudo apt-get install whois

  # macOS — included with the OS at /usr/bin/whois
  brew install whois   # only if you want a newer version

  # Alpine
  apk add whois

  # Windows (via WSL or Git Bash)
  # whois is usually available by default
  ```

## 📖 Usage

### Basic Usage

```bash
source .venv/bin/activate
```

```bash
# Discover OCAs for your network
netflix-oca-locator main

# Quiet mode (minimal output)
netflix-oca-locator main --quiet

# Enable debug logging
netflix-oca-locator main --debug
```

### Export Results

```bash
# Export to JSON
netflix-oca-locator main --output json --output-file results.json

# Export to CSV
netflix-oca-locator main --output csv

# Export to Excel with multiple sheets
netflix-oca-locator main --output xlsx

# Export to Markdown
netflix-oca-locator main --output markdown
```

### Generate Maps

```bash
# Generate interactive HTML map
netflix-oca-locator main --map

# Generate and open map in browser
netflix-oca-locator main --open-map
```

### Additional Commands

```bash
# Show version information
netflix-oca-locator version

# Show detailed application info
netflix-oca-locator info

# Show help
netflix-oca-locator --help
```

### 🐳 Docker Usage

#### Quick Docker Setup

```bash
# Build the Docker image
docker build -t netflix-oca-locator .

# Run with output preservation
docker run --rm -v $(pwd)/output:/app/output netflix-oca-locator main

# Export to JSON
docker run --rm -v $(pwd)/results:/app/output netflix-oca-locator main --output json

# Generate map and export data
docker run --rm -v $(pwd)/maps:/app/output netflix-oca-locator main --map --output csv
```

#### Using the Helper Script

```bash
# Make the script executable
chmod +x run-docker.sh

# Basic usage
./run-docker.sh run

# Export to JSON with custom output directory
./run-docker.sh -o /tmp/oca-results run --output json

# Generate map with debug mode
./run-docker.sh -d run --map --output csv

# Build image only
./run-docker.sh build

# Interactive shell for debugging
./run-docker.sh shell
```

#### Docker Compose

```bash
# Basic run
docker-compose run --rm netflix-oca-locator main --output json

# With environment variables
NETFLIX_OCA_DEBUG=true docker-compose run --rm netflix-oca-locator main --debug

# Development mode
docker-compose --profile dev run --rm netflix-oca-locator-dev
```

#### Docker Features

- **Ephemeral Containers**: Automatically removed after execution
- **Volume Mounting**: Preserve output files on host system
- **Environment Variables**: Configure via Docker environment
- **Multi-architecture**: Supports AMD64 and ARM64
- **Lightweight**: Optimized Alpine Linux base (<100MB)
- **Security**: Non-root user execution

## 🔧 Configuration

### Geocoding Configuration

The application supports multiple geocoding providers for enhanced location accuracy:

- **hybrid** (default): Uses TheAleph API first, falls back to standard geocoding
- **aleph**: Uses only TheAleph API for geocoding
- **geopy**: Uses only standard geocoding (Nominatim)

```bash
# Set geocoding provider
export NETFLIX_OCA_GEOCODING_PROVIDER=hybrid
```

### Environment Variables

Configure the application using environment variables with the `NETFLIX_OCA_` prefix:

```bash
export NETFLIX_OCA_DEBUG=true
export NETFLIX_OCA_LOG_LEVEL=DEBUG
export NETFLIX_OCA_LOG_FILE=/var/log/netflix-oca.log
export NETFLIX_OCA_REQUEST_TIMEOUT=60
export NETFLIX_OCA_MAX_RETRIES=5
export NETFLIX_OCA_GEOCODING_PROVIDER=hybrid
```

### Configuration File

Create a `.env` file in the project directory:

```env
NETFLIX_OCA_DEBUG=false
NETFLIX_OCA_LOG_LEVEL=INFO
NETFLIX_OCA_SHOW_EMOJI=true
NETFLIX_OCA_MAP_ZOOM=4
NETFLIX_OCA_EXPORT_PATH=./exports
NETFLIX_OCA_GEOCODING_PROVIDER=hybrid
```

## 🏗️ Architecture

The application is built with a modular architecture:

```text
src/netflix_oca_locator/
├── api/                    # External API integrations
│   ├── fast_com.py         # Fast.com API client
│   ├── ip_services.py      # IP and ISP lookup services
│   └── dns_resolver.py     # IPv4/IPv6 DNS resolution and NAT64 handling
├── cli/                    # Command-line interface
│   └── interface.py        # Typer-based CLI
├── core/                   # Business logic
│   ├── models.py           # Pydantic data models
│   └── oca_locator.py      # Main orchestration logic
├── utils/                  # Utility modules
│   ├── aleph_geocoding.py  # TheAleph client and hybrid fallback chain
│   ├── formatters.py       # Export formatters
│   ├── geocoding.py        # Location services
│   ├── logging.py          # Logging configuration
│   └── mapping.py          # Map generation
└── config/                 # Configuration management
    └── settings.py         # Pydantic settings
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/estcarisimo/Netflix-OCA-Servers-Locator.git
cd Netflix-OCA-Servers-Locator

# Install with development dependencies
uv sync --dev
# ...or, without uv:  pip install -e ".[dev]"

# Install pre-commit hooks (ruff lint + format on staged files)
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=netflix_oca_locator --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_core/test_models.py -v
```

Tests never make real network calls. Coverage currently sits at about 24%,
concentrated in `core/models.py` and `config/settings.py` — the CLI and the `api/`
clients are not covered yet, and contributions there are especially welcome.

### Code Quality

```bash
# Lint with ruff
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy src/
```

`ruff check` and `ruff format` are enforced in CI. `mypy` is **advisory**: there is
a backlog of pre-existing type errors, so the CI step does not fail on them. Please
don't add new ones. See [CONTRIBUTING.md](CONTRIBUTING.md) for the details.

### Building

```bash
# Build package
uv build

# Test installation
uv pip install dist/*.whl
```

## 📊 Example Output

```text
╔═══════════════════════════════════════════════════════════╗
║         🌐 Netflix OCA Locator v2.1.0 🌐                  ║
║                                                           ║
║  Discover Netflix's Open Connect Appliances serving       ║
║  your network for optimal streaming performance           ║
╚═══════════════════════════════════════════════════════════╝

🌐 Your Network Information
┌─────────────────────────────────────────────────────────┐
│ Public IP: 203.0.113.1                                 │
│ ISP: Example ISP                                       │
│ AS Number: AS64512                                     │
│ Country: US                                            │
│ BGP Prefix: 203.0.113.0/24                           │
└─────────────────────────────────────────────────────────┘

🌐 Netflix OCA Servers Allocated to Your Network
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Domain                                           ┃ IP Address      ┃ Location       ┃ IATA ┃ ASN  ┃ Provider        ┃ Method   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ ipv4-c006-mke002-wiscnet-isp.1.oca.nflxvideo.net │ 205.213.110.229 │ Unknown        │ -    │ 2381 │ WISCNET1-AS, US │ thealeph │
│ ipv4-c211-ord001-dev-ix.1.oca.nflxvideo.net      │ 45.57.120.66    │ 📍 Chicago, IL │ ORD  │ 2906 │ AS-SSI, US      │ thealeph │
│ ipv4-c152-ord003-ix.1.oca.nflxvideo.net          │ 23.246.37.204   │ 📍 Chicago, IL │ ORD  │ 2906 │ AS-SSI, US      │ thealeph │
│ ipv4-c158-ord003-ix.1.oca.nflxvideo.net          │ 23.246.36.133   │ 📍 Chicago, IL │ ORD  │ 2906 │ AS-SSI, US      │ thealeph │
│ ipv4-c153-ord001-dev-ix.1.oca.nflxvideo.net      │ 45.57.121.13    │ 📍 Chicago, IL │ ORD  │ 2906 │ AS-SSI, US      │ thealeph │
└──────────────────────────────────────────────────┴─────────────────┴────────────────┴──────┴──────┴─────────────────┴──────────┘

Found 5 OCA server(s)
```

## 🤝 Contributing

We welcome contributions! Please see the [Contributing Guidelines](CONTRIBUTING.md)
for setup instructions, the development workflow, and what to include in a bug report.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Project documentation

| Document | Contents |
| --- | --- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup, workflow, PR expectations |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [AGENTS.md](AGENTS.md) | Guidance for AI coding agents working in this repo |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting, and what data this tool handles |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [docs/THEALEPH_IPV6_SUPPORT.md](docs/THEALEPH_IPV6_SUPPORT.md) | IPv6 and NAT64 implementation notes |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- [Netflix TechBlog: Building Fast.com](https://medium.com/netflix-techblog/building-fast-com-4857fe0f8adb)
- [Netflix Open Connect](https://openconnect.netflix.com/)
- [Netflix ISP Speed Index](https://ispspeedindex.netflix.com/)

## 🙏 Acknowledgements

- **Netflix** for providing the Fast.com infrastructure that makes this tool possible
- **Team Cymru** for WHOIS services that provide ASN and ISP information
- **TheAleph.ai** for enhanced geocoding and network intelligence services
- **The Python Community** for excellent libraries that power this application

### Enhanced Geocoding Attribution

This application uses **TheAleph API** (<https://thealeph.ai>) for enhanced geocoding and location resolution of network infrastructure. TheAleph provides superior accuracy for CDN and network node geolocation compared to standard geocoding services.

#### TheAleph Research Citation

TheAleph is based on cutting-edge research in DNS PTR record analysis using Large Language Models:

**Paper**: *"The Aleph: Decoding DNS PTR Records With Large Language Models"*
**Authors**: Kedar Thiagarajan, Esteban Carisimo, and Fabián E. Bustamante
**Conference**: ACM CoNEXT, December 2025
**Link**: [https://estcarisimo.github.io/assets/pdf/papers/2025-the-aleph.pdf](https://estcarisimo.github.io/assets/pdf/papers/2025-the-aleph.pdf)

#### Integration Details

This implementation leverages TheAleph's ability to analyze PTR records and ASN information to provide enhanced location resolution for Netflix OCA servers. The system combines:

- DNS PTR record analysis for infrastructure mapping
- ASN (Autonomous System Number) correlation for network topology understanding
- Large Language Model inference for location extraction from network naming conventions
- Fallback to traditional geocoding services for comprehensive coverage

#### Advanced Features

The application includes advanced networking support and security features:

- **IPv6 Support**: Intelligent handling of IPv6 domains with NAT64 detection and PTR record analysis
- **HTTPS Security**: Full SSL certificate validation for secure API communications
- **Hybrid Fallback**: Multi-tier fallback system ensuring reliable location resolution

For comprehensive technical details about IPv6 support, NAT64 handling, and implementation specifications, see the [Technical Documentation](docs/THEALEPH_IPV6_SUPPORT.md).

**Note**: TheAleph API integration now uses full HTTPS security with SSL certificate validation enabled.

---

**Note**: This tool is for educational and network analysis purposes. Please use responsibly and in accordance with Netflix's terms of service.
