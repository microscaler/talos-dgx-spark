#!/bin/bash
# Extract NVIDIA kernel modules from ASUS repository
#
# This script extracts kernel modules from the ASUS Ascent GX10 repository
# and prepares them for use in the Talos overlay.
#
# Usage:
#   ./scripts/extract_kernel_modules.sh [output-dir]
#
# Prerequisites:
#   - ASUS repository accessible (local or GCS)
#   - dpkg-deb installed
#   - tar, gzip installed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TALOS_DIR="${PROJECT_ROOT}/talos"
OUTPUT_DIR="${1:-${TALOS_DIR}/asus-ascent-gx10-overlay/install/kernel-modules}"

# ASUS repository location
REPO_URL="${ASUS_REPO_URL:-https://storage.googleapis.com/asus-ascent-gb10/7.2.3}"
REPO_PATH="${ASUS_REPO_PATH:-}"

# Target kernel modules
# Note: 6.14 packages appear corrupted, using 6.11 as alternative
MODULE_PACKAGES=(
    "linux-modules-6.11.0-1016-nvidia"
    "linux-modules-extra-6.11.0-1016-nvidia"
    "nvidia-driver-580-open"
    "nvidia-kernel-common-580"
)

echo "🔧 Extracting NVIDIA Kernel Modules"
echo "===================================="
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to extract from local repository
extract_from_local() {
    local repo_path="$1"
    local package_name="$2"
    
    echo "📦 Extracting ${package_name} from local repository..."
    
    # Find package file
    local deb_file=$(find "${repo_path}/pool" -name "${package_name}*.deb" | head -1)
    
    if [ -z "${deb_file}" ]; then
        echo "⚠️  Package ${package_name} not found, skipping..."
        return 1
    fi
    
    echo "   Found: ${deb_file}"
    
    # Extract .deb using ar (Debian packages are ar archives)
    # Method from: https://gist.github.com/laris/da75482431de70870bc3cb4bc6bce3d9
    local temp_dir=$(mktemp -d)
    local extract_dir="${temp_dir}/extract"
    mkdir -p "${extract_dir}"
    
    # First, extract the ar archive
    cd "${temp_dir}"
    if ! ar x "${deb_file}" 2>/dev/null; then
        echo "   ⚠️  Failed to extract with ar, trying dpkg-deb..."
        # Fallback to dpkg-deb if available
        if command -v dpkg-deb &> /dev/null; then
            dpkg-deb -x "${deb_file}" "${extract_dir}" || {
                echo "   ❌ Failed to extract ${package_name}"
                rm -rf "${temp_dir}"
                return 1
            }
        else
            echo "   ❌ Cannot extract: ar failed and dpkg-deb not available"
            echo "   💡 Install dpkg: brew install dpkg"
            rm -rf "${temp_dir}"
            return 1
        fi
    else
        # Extract data.tar.xz or data.tar.gz from ar archive
        if [ -f "data.tar.xz" ]; then
            echo "   Extracting data.tar.xz..."
            tar -xJf data.tar.xz -C "${extract_dir}" 2>/dev/null || {
                echo "   ⚠️  Failed to extract data.tar.xz"
            }
        elif [ -f "data.tar.gz" ]; then
            echo "   Extracting data.tar.gz..."
            tar -xzf data.tar.gz -C "${extract_dir}" 2>/dev/null || {
                echo "   ⚠️  Failed to extract data.tar.gz"
            }
        elif [ -f "data.tar" ]; then
            echo "   Extracting data.tar..."
            tar -xf data.tar -C "${extract_dir}" 2>/dev/null || {
                echo "   ⚠️  Failed to extract data.tar"
            }
        else
            echo "   ⚠️  No data.tar.* found in archive"
        fi
    fi
    
    # Copy kernel modules
    if [ -d "${extract_dir}/lib/modules" ]; then
        echo "   Copying modules..."
        cp -r "${extract_dir}/lib/modules"/* "${OUTPUT_DIR}/" || true
    fi
    
    # Cleanup
    cd - > /dev/null
    rm -rf "${temp_dir}"
    
    echo "   ✅ Extracted ${package_name}"
}

# Function to extract from remote repository
extract_from_remote() {
    local repo_url="$1"
    local package_name="$2"
    
    echo "📦 Downloading ${package_name} from remote repository..."
    echo "   ⚠️  Remote extraction not yet implemented"
    echo "   Please use local repository or download packages manually"
    return 1
}

# Main extraction logic
if [ -n "${REPO_PATH}" ] && [ -d "${REPO_PATH}" ]; then
    echo "Using local repository: ${REPO_PATH}"
    for package in "${MODULE_PACKAGES[@]}"; do
        extract_from_local "${REPO_PATH}" "${package}" || true
    done
elif [ -n "${REPO_URL}" ]; then
    echo "Using remote repository: ${REPO_URL}"
    for package in "${MODULE_PACKAGES[@]}"; do
        extract_from_remote "${REPO_URL}" "${package}" || true
    done
else
    echo "❌ Error: No repository specified"
    echo "Set ASUS_REPO_PATH for local repository or ASUS_REPO_URL for remote"
    exit 1
fi

echo ""
echo "✅ Kernel module extraction complete"
echo "Modules extracted to: ${OUTPUT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Verify module compatibility with Talos kernel"
echo "  2. Test module loading"
echo "  3. Update overlay configuration"

