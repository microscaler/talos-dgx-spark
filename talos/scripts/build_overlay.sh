#!/bin/bash
# Build ASUS Ascent GX10 Talos overlay package
#
# This script builds the overlay package from extracted components
# and prepares it for use with Talos Image Factory.
#
# Usage:
#   ./scripts/build_overlay.sh [version]
#
# Output:
#   asus-ascent-gx10-overlay-<version>.tar.gz

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TALOS_DIR="${PROJECT_ROOT}/talos"
OVERLAY_DIR="${TALOS_DIR}/asus-ascent-gx10-overlay"
VERSION="${1:-1.0.0}"
OUTPUT_DIR="${TALOS_DIR}/output"
OUTPUT_FILE="${OUTPUT_DIR}/asus-ascent-gx10-overlay-${VERSION}.tar.gz"

echo "🔨 Building ASUS Ascent GX10 Talos Overlay"
echo "=========================================="
echo "Version: ${VERSION}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Verify overlay structure
echo "📋 Verifying overlay structure..."

required_dirs=(
    "${OVERLAY_DIR}/install/kernel-modules"
    "${OVERLAY_DIR}/install/firmware"
    "${OVERLAY_DIR}/install/boot"
    "${OVERLAY_DIR}/files/etc/modprobe.d"
    "${OVERLAY_DIR}/files/etc/modules-load.d"
    "${OVERLAY_DIR}/installer"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "${dir}" ]; then
        echo "⚠️  Warning: Directory missing: ${dir}"
    fi
done

# Check for components
echo "🔍 Checking for components..."

if [ ! -f "${OVERLAY_DIR}/files/etc/modprobe.d/nvidia.conf" ]; then
    echo "⚠️  Warning: nvidia.conf not found"
fi

if [ ! -f "${OVERLAY_DIR}/files/etc/modules-load.d/nvidia.conf" ]; then
    echo "⚠️  Warning: modules-load.d/nvidia.conf not found"
fi

# Check for kernel modules (including compressed .ko.zst files)
module_count=$(find "${OVERLAY_DIR}/install/kernel-modules" -name "*.ko" -o -name "*.ko.zst" 2>/dev/null | wc -l | tr -d ' ')
if [ "${module_count}" -eq 0 ]; then
    echo "⚠️  Warning: No kernel modules found. Run extract_kernel_modules.sh first"
else
    echo "✅ Found ${module_count} kernel modules (including compressed .ko.zst)"
fi

# Check for firmware
firmware_count=$(find "${OVERLAY_DIR}/install/firmware" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "${firmware_count}" -eq 0 ]; then
    echo "⚠️  Warning: No firmware found. Run extract_firmware.sh first"
else
    echo "✅ Found ${firmware_count} firmware files"
fi

# Build installer (if Go is available)
if command -v go &> /dev/null; then
    echo "🔧 Building overlay installer..."
    cd "${OVERLAY_DIR}/installer"
    if [ -f "go.mod" ]; then
        go build -o "${OVERLAY_DIR}/installer/bin/installer" ./installer.go || {
            echo "⚠️  Warning: Failed to build installer (this is OK if Talos SDK not available)"
        }
    fi
    cd "${PROJECT_ROOT}"
fi

# Create overlay manifest
echo "📝 Creating overlay manifest..."
cat > "${OVERLAY_DIR}/overlay.yaml" <<EOF
name: asus-ascent-gx10
version: ${VERSION}
description: Talos overlay for ASUS Ascent GX10 with NVIDIA GPU support
architectures:
  - arm64
components:
  kernel_modules: ${module_count}
  firmware: ${firmware_count}
EOF

# Package overlay
echo "📦 Packaging overlay..."
cd "${TALOS_DIR}"
tar -czf "${OUTPUT_FILE}" \
    --exclude='.git' \
    --exclude='.gitkeep' \
    --exclude='*.tmp' \
    --exclude='*.log' \
    asus-ascent-gx10-overlay/

echo ""
echo "✅ Overlay build complete!"
echo "Package: ${OUTPUT_FILE}"
echo ""
echo "Next steps:"
echo "  1. Test overlay with Talos Image Factory"
echo "  2. Generate custom Talos image"
echo "  3. Test on ASUS Ascent GX10 hardware"

