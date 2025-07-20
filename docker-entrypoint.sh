#!/bin/sh

# Netflix OCA Locator - Docker Entrypoint Script
# This script handles the ephemeral container execution with proper cleanup

set -e

# Default output directory
OUTPUT_DIR="/app/output"

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up container..."
    # Only preserve files in the output directory
    # Everything else will be destroyed when container is removed
}

# Function to show usage
show_usage() {
    echo "🌐 Netflix OCA Locator - Ephemeral Docker Container"
    echo ""
    echo "Usage: docker run [docker-options] netflix-oca-locator [app-options]"
    echo ""
    echo "Docker Options (mount volumes to preserve output):"
    echo "  -v /host/path:/app/output    Mount directory for output files"
    echo "  -e NETFLIX_OCA_DEBUG=true   Enable debug mode"
    echo "  --rm                        Auto-remove container (recommended)"
    echo ""
    echo "Application Options:"
    echo "  main                         Locate Netflix OCAs"
    echo "  --help                       Show application help"
    echo "  --output FORMAT              Export format (json, csv, xlsx, markdown)"
    echo "  --output-file FILE           Output file path (saved to /app/output/)"
    echo "  --map                        Generate interactive map"
    echo "  --debug                      Enable debug logging"
    echo "  --quiet                      Minimal output"
    echo ""
    echo "Examples:"
    echo "  # Basic usage with output preservation"
    echo "  docker run --rm -v \$(pwd)/output:/app/output netflix-oca-locator main"
    echo ""
    echo "  # Export results to JSON"
    echo "  docker run --rm -v \$(pwd)/results:/app/output netflix-oca-locator main --output json"
    echo ""
    echo "  # Generate map and export data"
    echo "  docker run --rm -v \$(pwd)/maps:/app/output netflix-oca-locator main --map --output csv"
    echo ""
    echo "  # Debug mode with environment variable"
    echo "  docker run --rm -e NETFLIX_OCA_DEBUG=true -v \$(pwd)/output:/app/output netflix-oca-locator main --debug"
    echo ""
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Handle special cases
case "$1" in
    --help|-h|help)
        show_usage
        exit 0
        ;;
    version|--version)
        python -m netflix_oca_locator version
        exit 0
        ;;
    info|--info)
        python -m netflix_oca_locator info
        exit 0
        ;;
    main)
        # Shift to remove 'main' and pass remaining args
        shift
        echo "🚀 Starting Netflix OCA Locator..."
        echo "📁 Output directory: $OUTPUT_DIR"
        echo "🔧 Arguments: $*"
        
        # Adjust output file paths to use the output directory
        args=""
        while [ $# -gt 0 ]; do
            case "$1" in
                --output-file)
                    shift
                    if [ $# -gt 0 ]; then
                        # Ensure output file is in the output directory
                        filename=$(basename "$1")
                        args="$args --output-file $OUTPUT_DIR/$filename"
                        shift
                    fi
                    ;;
                *)
                    args="$args $1"
                    shift
                    ;;
            esac
        done
        
        # Execute the main application
        export NETFLIX_OCA_EXPORT_PATH="$OUTPUT_DIR"
        python -m netflix_oca_locator main $args
        
        echo "✅ Execution completed successfully"
        echo "📂 Check output directory for results"
        exit 0
        ;;
    *)
        if [ "$1" = "" ]; then
            show_usage
            exit 0
        else
            # Pass through any other commands directly
            echo "🔄 Passing command to netflix-oca-locator: $*"
            python -m netflix_oca_locator "$@"
            exit $?
        fi
        ;;
esac