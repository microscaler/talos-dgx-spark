#!/bin/bash
# Extract firmware blobs from ASUS repository
#
# This script extracts firmware from the ASUS Ascent GX10 repository
# and prepares them for use in the Talos overlay.
#
# Usage:
#   ./scripts/extract_firmware.sh [output-dir]
#
# Prerequisites:
#   - ASUS repository accessible (local or GCS)
#   - dpkg-deb installed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TALOS_DIR="${PROJECT_ROOT}/talos"
OUTPUT_DIR="${1:-${TALOS_DIR}/asus-ascent-gx10-overlay/install/firmware}"

# ASUS repository location
REPO_URL="${ASUS_REPO_URL:-https://storage.googleapis.com/asus-ascent-gb10/7.2.3}"
REPO_PATH="${ASUS_REPO_PATH:-}"

# Target firmware packages
FIRMWARE_PACKAGES=(
    "nvidia-firmware-580"
    "linux-firmware"
)

echo "🔧 Extracting Firmware Blobs"
echo "============================"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory structure
mkdir -p "${OUTPUT_DIR}/nvidia"
mkdir -p "${OUTPUT_DIR}/linux-firmware"

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
    
    # Copy NVIDIA firmware
    if [ -d "${extract_dir}/lib/firmware/nvidia" ]; then
        echo "   Copying NVIDIA firmware..."
        cp -r "${extract_dir}/lib/firmware/nvidia"/* "${OUTPUT_DIR}/nvidia/" || true
    fi
    
    # Copy general Linux firmware
    if [ -d "${extract_dir}/lib/firmware" ]; then
        echo "   Copying Linux firmware..."
        # Exclude nvidia directory to avoid duplicates
        find "${extract_dir}/lib/firmware" -mindepth 1 -maxdepth 1 ! -name nvidia -exec cp -r {} "${OUTPUT_DIR}/linux-firmware/" \; || true
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
    for package in "${FIRMWARE_PACKAGES[@]}"; do
        extract_from_local "${REPO_PATH}" "${package}" || true
    done
elif [ -n "${REPO_URL}" ]; then
    echo "Using remote repository: ${REPO_URL}"
    for package in "${FIRMWARE_PACKAGES[@]}"; do
        extract_from_remote "${REPO_URL}" "${package}" || true
    done
else
    echo "❌ Error: No repository specified"
    echo "Set ASUS_REPO_PATH for local repository or ASUS_REPO_URL for remote"
    exit 1
fi

echo ""
echo "✅ Firmware extraction complete"
echo "Firmware extracted to: ${OUTPUT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Verify firmware paths"
echo "  2. Test firmware loading"
echo "  3. Update overlay configuration"

