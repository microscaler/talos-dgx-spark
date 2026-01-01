# Talos Overlay for ASUS Ascent GX10

This directory contains the design and implementation of a Talos Linux overlay for ASUS Ascent GX10 nodes, enabling GPU support and hardware-specific configurations.

## Overview

The ASUS Ascent GX10 overlay customizes Talos Linux to support:
- NVIDIA GPU drivers and kernel modules
- Hardware-specific firmware
- Boot-time configurations
- System-level optimizations

## Directory Structure

```
talos/
├── README.md                          # This file
├── docs/                              # Documentation
│   ├── OVERLAY_DESIGN.md             # Overlay design specification
│   ├── IMPLEMENTATION_PLAN.md        # Step-by-step implementation guide
│   └── TESTING.md                    # Testing procedures
├── asus-ascent-gx10-overlay/         # Main overlay directory
│   ├── install/                      # Installation components
│   │   ├── kernel-modules/           # NVIDIA kernel modules
│   │   ├── firmware/                 # Hardware firmware blobs
│   │   └── boot/                     # Boot-time configurations
│   ├── files/                        # Files to install
│   │   ├── etc/modprobe.d/          # Module configuration
│   │   ├── etc/modules-load.d/       # Auto-load modules
│   │   └── usr/local/bin/            # Custom scripts
│   └── installer/                     # Overlay installer implementation
├── scripts/                          # Helper scripts
│   ├── extract_kernel_modules.sh     # Extract modules from ASUS repo
│   ├── extract_firmware.sh           # Extract firmware blobs
│   └── build_overlay.sh              # Build overlay package
└── config/                           # Configuration files
    ├── overlay.yaml                  # Overlay metadata
    └── kernel-config.patch           # Kernel configuration patches
```

## Quick Start

### Prerequisites

- **Git LFS** - Required for tracking binary files (firmware, kernel modules, packages)
  ```bash
  git lfs install  # If not already installed
  git lfs pull     # Download LFS-tracked files after clone
  ```
- Talos Image Factory access or local setup
- ASUS Ascent repository access (GCS bucket: `gs://asus-ascent-gb10/7.2.3`)
- Go toolchain (for overlay installer)
- Kernel module extraction tools

### Git LFS Setup

This repository uses Git LFS to track large binary files. See [GIT_LFS_SETUP.md](GIT_LFS_SETUP.md) for details.

**Important:** After cloning, run `git lfs pull` to download binary files.

### Building the Overlay

```bash
# Extract kernel modules from ASUS repository
./scripts/extract_kernel_modules.sh

# Extract firmware blobs
./scripts/extract_firmware.sh

# Build the overlay
./scripts/build_overlay.sh
```

### Using with Talos Image Factory

```bash
# Generate custom Talos image with overlay
talosctl image factory \
    --arch arm64 \
    --overlay ./asus-ascent-gx10-overlay \
    --output ./output/talos-asus-ascent-amd64.tar.gz
```

## Implementation Status

- [x] Overlay structure design ✅
- [x] Directory structure created ✅
- [x] Extraction scripts created ✅
- [x] Build script created ✅
- [x] Configuration files created ✅
- [x] Overlay installer skeleton ✅
- [x] Documentation created ✅
- [ ] Kernel module extraction (ready to run)
- [ ] Firmware extraction (ready to run)
- [ ] Overlay installer implementation (skeleton ready)
- [ ] Testing on hardware

## References

- [Talos Image Factory](https://github.com/siderolabs/image-factory)
- [Talos Overlays](https://github.com/siderolabs/overlays/)
- [ASUS Ascent Repository Analysis](../docs/ASUS_ASCENT_REPO_ANALYSIS.md)
- [Component Audit](../docs/ASUS_ASCENT_TALOS_OVERLAY_AUDIT.md)

