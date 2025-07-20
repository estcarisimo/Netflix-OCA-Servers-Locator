#!/bin/bash

# Netflix OCA Locator - Docker Runner Script
# Simplified interface for running the application in Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="netflix-oca-locator"
CONTAINER_NAME="netflix-oca-locator-$(date +%s)"
OUTPUT_DIR="${SCRIPT_DIR}/docker-output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_usage() {
    cat << EOF
🌐 Netflix OCA Locator - Docker Runner

USAGE:
    $0 [OPTIONS] [COMMAND] [ARGS...]

OPTIONS:
    -h, --help          Show this help message
    -b, --build         Force rebuild the Docker image
    -o, --output DIR    Set custom output directory (default: ./docker-output)
    -d, --debug         Enable debug mode
    -v, --verbose       Verbose Docker output

COMMANDS:
    run                 Run OCA locator (default)
    build              Build Docker image only
    clean              Remove Docker image and containers
    shell              Start interactive shell in container
    version            Show version information
    info               Show application information

EXAMPLES:
    # Basic usage
    $0 run

    # Export to JSON with custom output directory
    $0 -o /tmp/oca-results run --output json

    # Generate map with debug mode
    $0 -d run --map --output csv

    # Build image
    $0 build

    # Interactive shell for debugging
    $0 shell

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        print_info "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        print_info "Please start Docker daemon"
        exit 1
    fi
}

build_image() {
    print_info "Building Docker image..."
    if [ "$VERBOSE" = true ]; then
        docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    else
        docker build -t "$IMAGE_NAME" "$SCRIPT_DIR" > /dev/null 2>&1
    fi
    print_success "Docker image built successfully"
}

cleanup_containers() {
    print_info "Cleaning up old containers..."
    docker ps -a --filter "name=netflix-oca-locator" --format "{{.Names}}" | xargs -r docker rm -f > /dev/null 2>&1 || true
}

# Parse command line arguments
COMMAND=""
BUILD=false
DEBUG=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        run|build|clean|shell|version|info)
            COMMAND="$1"
            shift
            break
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="run"
            fi
            break
            ;;
    esac
done

# Default command
if [ -z "$COMMAND" ]; then
    COMMAND="run"
fi

# Check Docker
check_docker

# Handle commands
case "$COMMAND" in
    build)
        build_image
        exit 0
        ;;
    clean)
        print_info "Cleaning up Docker resources..."
        cleanup_containers
        docker rmi "$IMAGE_NAME" 2>/dev/null || true
        print_success "Cleanup completed"
        exit 0
        ;;
    version|info)
        # Quick run for version/info
        docker run --rm "$IMAGE_NAME" "$COMMAND" 2>/dev/null || {
            print_warning "Image not found, building..."
            build_image
            docker run --rm "$IMAGE_NAME" "$COMMAND"
        }
        exit 0
        ;;
    shell)
        print_info "Starting interactive shell..."
        mkdir -p "$OUTPUT_DIR"
        docker run --rm -it \
            -v "$OUTPUT_DIR:/app/output" \
            --entrypoint sh \
            "$IMAGE_NAME"
        exit 0
        ;;
    run)
        # Build image if it doesn't exist or if forced
        if [ "$BUILD" = true ] || ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
            build_image
        fi

        # Prepare environment
        mkdir -p "$OUTPUT_DIR"
        
        # Set up Docker environment variables
        ENV_ARGS=""
        if [ "$DEBUG" = true ]; then
            ENV_ARGS="-e NETFLIX_OCA_DEBUG=true -e NETFLIX_OCA_LOG_LEVEL=DEBUG"
        fi

        print_info "Starting Netflix OCA Locator in Docker..."
        print_info "Output directory: $OUTPUT_DIR"
        
        # Run container
        docker run --rm \
            --name "$CONTAINER_NAME" \
            -v "$OUTPUT_DIR:/app/output" \
            $ENV_ARGS \
            "$IMAGE_NAME" \
            main "$@"
        
        print_success "Container execution completed"
        print_info "Check $OUTPUT_DIR for output files"
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac