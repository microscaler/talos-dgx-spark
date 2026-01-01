# Talos DGX Spark Overlay

This repository contains the Talos Linux overlay for ASUS Ascent GX10 (DGX Spark) nodes, enabling GPU support and hardware-specific configurations.

## Overview

The ASUS Ascent GX10 overlay customizes Talos Linux to support:
- NVIDIA GPU drivers and kernel modules
- Hardware-specific firmware
- Boot-time configurations
- System-level optimizations

## Quick Start

See [talos/README.md](talos/README.md) for detailed documentation.

## Repository Structure

```
.
├── talos/                          # Main Talos overlay directory
│   ├── asus-ascent-gx10-overlay/  # Overlay components
│   ├── scripts/                    # Build and CI scripts
│   ├── docs/                       # Documentation
│   └── output/                     # Build outputs
├── docs/                           # Additional documentation
│   ├── ASUS_ASCENT_REPO_ANALYSIS.md
│   ├── ASUS_ASCENT_QUICK_START.md
│   └── ASUS_ASCENT_TALOS_OVERLAY_AUDIT.md
└── .github/workflows/              # CI/CD workflows
    └── talos-overlay.yml           # Build workflow
```

## Git LFS

This repository uses Git LFS to track large binary files (firmware, kernel modules, packages).

**Important:** After cloning, run:
```bash
git lfs install
git lfs pull
```

See [talos/GIT_LFS_SETUP.md](talos/GIT_LFS_SETUP.md) for details.

## Building

### Local Build

```bash
cd talos
python3 scripts/ci_build_overlay.py
```

### CI/CD

The repository includes GitHub Actions workflows for automated builds. See [talos/docs/CI_CD_SETUP.md](talos/docs/CI_CD_SETUP.md) for details.

## Copyright

All firmware and kernel modules are the copyright property of NVIDIA Corporation. See:
- [talos/asus-ascent-gx10-overlay/install/firmware/README.md](talos/asus-ascent-gx10-overlay/install/firmware/README.md)
- [talos/asus-ascent-gx10-overlay/install/kernel-modules/README.md](talos/asus-ascent-gx10-overlay/install/kernel-modules/README.md)

