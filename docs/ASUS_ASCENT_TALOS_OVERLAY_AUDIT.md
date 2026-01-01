# ASUS Ascent GX10 - Talos Overlay vs Kubernetes Container Component Audit

## Overview

This document categorizes components from the NVIDIA ASUS Ascent GX10 distribution into:
1. **Talos Overlay Components** - Required for base Talos Linux installation (system-level, boot-time, hardware-specific)
2. **Kubernetes Container Components** - Required for runtime in containers on Talos nodes (application-level, user-space)

**Reference:**
- [Talos Image Factory](https://github.com/siderolabs/image-factory) - Custom Talos image generation
- [Talos Overlays](https://github.com/siderolabs/overlays/) - Overlay system for customizing Talos

## Talos Overlay System

Talos overlays allow customization of the base Talos Linux image by:
- Adding kernel modules and firmware
- Modifying system configurations
- Installing hardware-specific drivers
- Customizing boot parameters
- Adding system-level binaries and libraries

Overlays are applied during image generation, not at runtime.

## Component Categorization

### Category 1: Talos Overlay Components (System-Level)

These components must be part of the Talos base image and cannot run in containers.

| Component | Package/File | Purpose | Priority | Notes |
|-----------|--------------|---------|----------|-------|
| **Kernel Modules** | Various kernel packages | Hardware drivers (NVIDIA, network, storage) | **CRITICAL** | Must be in Talos kernel |
| **Firmware** | `linux-firmware`, `firmware-*` packages | Hardware firmware blobs | **CRITICAL** | Required for hardware initialization |
| **Boot Configuration** | `oem-iso-cfg.sh` | Boot-time customization script | **HIGH** | Runs during system initialization |
| **NVIDIA Drivers** | `nvidia-driver-*`, `nvidia-kernel-*` | GPU driver kernel modules | **CRITICAL** | Required for GPU access |
| **System Libraries** | `libnvidia-*`, `libcuda*` | NVIDIA CUDA runtime libraries | **HIGH** | Required for GPU compute |
| **Hardware Detection** | `udev` rules, `hwdata` | Hardware identification and configuration | **HIGH** | System-level hardware management |
| **Network Drivers** | Network driver modules | Network interface drivers | **CRITICAL** | Required for network connectivity |
| **Storage Drivers** | Storage driver modules | Disk/storage drivers | **CRITICAL** | Required for disk access |

### Category 2: Kubernetes Container Components (Application-Level)

These components can run in containers and don't need to be in the Talos base image.

| Component | Package/File | Purpose | Priority | Notes |
|-----------|--------------|---------|----------|-------|
| **Desktop Customization** | `asus-ascent-gx10-desktop-customize` | Desktop wallpapers, themes | **LOW** | Not needed for headless Kubernetes |
| **OOBE Customization** | `asus-ascent-gx10-oobe-customize` | Out-of-box experience UI | **LOW** | Not needed for automated deployment |
| **CUDA Toolkit** | `cuda-toolkit-*`, `cuda-runtime-*` | CUDA development tools | **MEDIUM** | Can be in container images |
| **NVIDIA Container Runtime** | `nvidia-container-toolkit` | Container GPU access | **HIGH** | Required for GPU containers |
| **Application Libraries** | User-space libraries | Application dependencies | **MEDIUM** | Can be in container images |
| **Development Tools** | `gcc`, `make`, `python3-dev` | Build tools | **LOW** | Only needed in dev containers |
| **Monitoring Tools** | `htop`, `nvidia-smi` (user-space) | System monitoring | **MEDIUM** | Can be in monitoring containers |

### Category 3: Hybrid Components (Both Overlay and Container)

Some components may need parts in both places.

| Component | Talos Overlay Part | Container Part | Notes |
|-----------|-------------------|----------------|-------|
| **NVIDIA Drivers** | Kernel modules | User-space libraries | Kernel modules in overlay, libs in containers |
| **Network Configuration** | Driver modules | Network policy tools | Drivers in overlay, tools in containers |
| **Storage Management** | Storage drivers | Storage operators | Drivers in overlay, operators in containers |

## Detailed Component Analysis

### ASUS-Specific Packages

#### 1. `asus-ascent-gx10-desktop-customize_1.0.0_all.deb` (9.6MB)

**Contents:**
- `/usr/share/backgrounds/asus-ascent-gx10-wallaper-3840-2160.png` (10MB wallpaper)
- `/usr/share/glib-2.0/schemas/90_oem-settings.gschema.override` (GNOME settings)
- `/usr/share/gnome-background-properties/asus-ascent-gx10-wallpapers.xml` (Wallpaper config)

**Categorization:** ❌ **NOT NEEDED for Talos/Kubernetes**
- Desktop customization only
- Not applicable to headless Kubernetes nodes
- Can be ignored for Talos deployment

#### 2. `asus-ascent-gx10-oobe-customize_1.0.0_arm64.deb` (3.6KB)

**Contents:**
- `/opt/nvidia/dgx-oobe-customizations/brand.webp` (Branding image)
- `/opt/nvidia/dgx-oobe-customizations/customize.json` (OOBE configuration)
- `/opt/nvidia/dgx-oobe-customizations/device.webp` (Device image)
- `/opt/nvidia/dgx-oobe-customizations/eulas/*.md` (EULA files)
- `/opt/nvidia/dgx-oobe-customizations/settings.env` (Settings)

**Categorization:** ❌ **NOT NEEDED for Talos/Kubernetes**
- OOBE (Out-of-Box Experience) UI only
- Not applicable to automated Talos deployment
- Can be ignored for Talos deployment

### NVIDIA Components (From Main Repository)

#### Kernel-Level Components (Talos Overlay Required)

| Package Pattern | Purpose | Talos Overlay | Container |
|----------------|---------|---------------|-----------|
| `nvidia-kernel-*` | Kernel modules | ✅ **REQUIRED** | ❌ |
| `nvidia-driver-*` | Driver packages | ✅ **REQUIRED** | ❌ |
| `linux-firmware-nvidia` | GPU firmware | ✅ **REQUIRED** | ❌ |
| `nvidia-modprobe` | Module loading | ✅ **REQUIRED** | ❌ |

#### User-Space Components (Container Optional)

| Package Pattern | Purpose | Talos Overlay | Container |
|----------------|---------|---------------|-----------|
| `libnvidia-*` | CUDA libraries | ⚠️ **MAYBE** | ✅ **RECOMMENDED** |
| `cuda-toolkit-*` | CUDA development | ❌ | ✅ **OPTIONAL** |
| `nvidia-container-toolkit` | Container GPU | ❌ | ✅ **REQUIRED** |
| `nvidia-smi` | GPU monitoring | ❌ | ✅ **OPTIONAL** |

## Talos Overlay Implementation Strategy

### Required Overlay Components

Based on the analysis, the following components are **REQUIRED** in a Talos overlay:

1. **NVIDIA Kernel Modules**
   - All `nvidia-kernel-*` packages
   - Kernel modules for GPU access
   - Must be compiled for Talos kernel version

2. **NVIDIA Firmware**
   - `linux-firmware-nvidia` or equivalent
   - GPU firmware blobs
   - Required for hardware initialization

3. **System Drivers**
   - Network driver modules
   - Storage driver modules
   - Any ASUS-specific hardware drivers

4. **Boot Configuration**
   - Kernel command-line parameters
   - Module loading configuration
   - Hardware-specific boot settings

### Overlay Structure (Proposed)

```
asus-ascent-gx10-overlay/
├── install/
│   ├── kernel-modules/          # NVIDIA and hardware kernel modules
│   ├── firmware/                # Hardware firmware blobs
│   └── boot/                    # Boot-time configurations
├── files/
│   ├── etc/modprobe.d/          # Module configuration
│   └── etc/modules-load.d/      # Auto-load modules
└── installer/                   # Custom installer (if needed)
```

## Kubernetes Container Strategy

### Container Image Requirements

For containers running on ASUS Ascent Talos nodes:

1. **NVIDIA Container Runtime**
   - `nvidia-container-toolkit` in base container images
   - Required for GPU access from containers

2. **CUDA Libraries** (if needed)
   - `libcuda`, `libnvidia-*` libraries
   - Can be in application containers or sidecar

3. **Monitoring Tools** (optional)
   - `nvidia-smi` in monitoring containers
   - GPU metrics collection

### Container Base Image Strategy

```dockerfile
# Base image for GPU-enabled containers
FROM nvidia/cuda:12.0.0-base-ubuntu24.04

# Or use NVIDIA Container Toolkit
FROM ubuntu:24.04
RUN apt-get update && \
    apt-get install -y nvidia-container-toolkit && \
    rm -rf /var/lib/apt/lists/*
```

## Implementation Recommendations

### Phase 1: Talos Overlay Creation

1. **Extract Kernel Modules**
   - Identify all NVIDIA kernel modules
   - Extract modules compatible with Talos kernel version
   - Package as Talos overlay

2. **Extract Firmware**
   - Identify all NVIDIA firmware blobs
   - Package firmware in overlay
   - Ensure firmware paths match Talos structure

3. **Create Overlay Installer**
   - Implement overlay.Installer interface
   - Handle module loading
   - Configure boot parameters

### Phase 2: Container Image Creation

1. **Base Container Images**
   - Create GPU-enabled base images
   - Include NVIDIA Container Toolkit
   - Include CUDA runtime libraries

2. **Application Containers**
   - Use GPU-enabled base images
   - Include application-specific CUDA libraries
   - Configure GPU access

### Phase 3: Integration

1. **Talos Image Generation**
   - Use Talos Image Factory with custom overlay
   - Generate custom Talos images for ASUS Ascent
   - Test boot and hardware detection

2. **Kubernetes Deployment**
   - Deploy GPU-enabled containers
   - Verify GPU access from containers
   - Test CUDA workloads

## NVIDIA Package Inventory

### Kernel-Level Packages (Talos Overlay Required)

Based on repository analysis, the following NVIDIA packages are available:

#### Kernel Modules (CRITICAL for Talos Overlay)

| Package | Kernel Version | Talos Overlay | Container | Notes |
|---------|---------------|---------------|-----------|-------|
| `linux-modules-6.11.0-1016-nvidia` | 6.11.0-1016 | ✅ **REQUIRED** | ❌ | Base NVIDIA modules |
| `linux-modules-6.14.0-1008-nvidia` | 6.14.0-1008 | ✅ **REQUIRED** | ❌ | Base NVIDIA modules |
| `linux-modules-6.14.0-1008-nvidia-64k` | 6.14.0-1008 (64k) | ✅ **REQUIRED** | ❌ | 64k page size variant |
| `linux-modules-extra-6.11.0-1016-nvidia` | 6.11.0-1016 | ✅ **REQUIRED** | ❌ | Extra NVIDIA modules |
| `linux-modules-extra-6.14.0-1008-nvidia` | 6.14.0-1008 | ✅ **REQUIRED** | ❌ | Extra NVIDIA modules |
| `linux-modules-extra-6.14.0-1008-nvidia-64k` | 6.14.0-1008 (64k) | ✅ **REQUIRED** | ❌ | Extra modules (64k) |
| `linux-modules-nvidia-580-open-6.11.0-1016-nvidia` | 6.11.0-1016 | ✅ **REQUIRED** | ❌ | Open-source NVIDIA modules |
| `linux-modules-nvidia-580-open-nvidia-hwe-24.04` | HWE 24.04 | ✅ **REQUIRED** | ❌ | HWE kernel modules |
| `linux-modules-nvidia-fs-6.11.0-1016-nvidia` | 6.11.0-1016 | ✅ **REQUIRED** | ❌ | Filesystem modules |

**⚠️ Important:** Talos uses its own kernel. These modules must be:
1. Recompiled for Talos kernel version, OR
2. Extracted and adapted for Talos kernel, OR
3. Replaced with Talos-compatible NVIDIA modules

#### Driver Packages

| Package | Type | Talos Overlay | Container | Notes |
|---------|------|---------------|-----------|-------|
| `nvidia-driver-580-open` | Driver package | ✅ **REQUIRED** | ❌ | Open-source driver (580.x) |
| `nvidia-kernel-source-580-open` | Source | ⚠️ **MAYBE** | ❌ | Kernel source (for recompilation) |
| `nvidia-kernel-common-580` | Common files | ✅ **REQUIRED** | ❌ | Common kernel files |
| `nvidia-kernel-defaults` | Defaults | ✅ **REQUIRED** | ❌ | Kernel defaults |
| `nvidia-persistenced` | Daemon | ⚠️ **MAYBE** | ❌ | GPU persistence daemon |
| `nvidia-xconfig` | Config tool | ❌ | ❌ | X11 config (not needed) |
| `nvidia-grub-params` | Boot params | ✅ **REQUIRED** | ❌ | Boot-time GPU config |
| `nvidia-relaxed-ordering` | Kernel feature | ✅ **REQUIRED** | ❌ | Kernel optimization |

#### Firmware Packages

| Package | Type | Talos Overlay | Container | Notes |
|---------|------|---------------|-----------|-------|
| `nvidia-firmware-580` | GPU firmware | ✅ **REQUIRED** | ❌ | GPU firmware blobs |
| `nvidia-firmware-580-580.95.05` | GPU firmware | ✅ **REQUIRED** | ❌ | Specific firmware version |
| `linux-firmware` | System firmware | ✅ **REQUIRED** | ❌ | General Linux firmware |
| `firmware-sof-signed` | Audio firmware | ⚠️ **MAYBE** | ❌ | Audio firmware (if needed) |
| `nvidia-spark-mlnx-firmware-manager` | Mellanox | ⚠️ **MAYBE** | ❌ | Network firmware manager |

### CUDA Packages (Container Optional)

| Package | Type | Talos Overlay | Container | Notes |
|---------|------|---------------|-----------|-------|
| `cuda-toolkit-13-0` | Development | ❌ | ✅ **OPTIONAL** | Full CUDA toolkit |
| `cuda-libraries-13-0` | Runtime | ❌ | ✅ **RECOMMENDED** | CUDA runtime libs |
| `cuda-cudart-13-0` | Runtime | ❌ | ✅ **RECOMMENDED** | CUDA runtime |
| `cuda-nvml-dev-13-0` | Development | ❌ | ✅ **OPTIONAL** | NVML dev headers |
| `cuda-driver-dev-13-0` | Development | ❌ | ✅ **OPTIONAL** | Driver dev headers |

### NVIDIA System Packages

| Package | Type | Talos Overlay | Container | Notes |
|---------|------|---------------|-----------|-------|
| `nvidia-dgx-telemetry` | Monitoring | ❌ | ✅ **OPTIONAL** | DGX telemetry |
| `nvidia-ib-umad-loader` | InfiniBand | ⚠️ **MAYBE** | ❌ | InfiniBand support |
| `nvidia-ipmisol` | IPMI | ❌ | ❌ | IPMI tools |
| `nvidia-console-settings` | Console | ⚠️ **MAYBE** | ❌ | Console configuration |
| `nvidia-no-systemd-suspend` | Power | ⚠️ **MAYBE** | ❌ | Power management |

### OEM Configuration Packages

| Package | Type | Talos Overlay | Container | Notes |
|---------|------|---------------|-----------|-------|
| `nvidia-oem-config-*` | OEM config | ❌ | ❌ | Ubuntu OEM config (not Talos) |
| `nvidia-lvfs-config` | LVFS | ❌ | ❌ | Linux Vendor Firmware Service |

## Component Summary Table

| Component Type | Talos Overlay | Kubernetes Container | Notes |
|----------------|---------------|---------------------|-------|
| **Kernel Modules** | ✅ Required | ❌ Not applicable | Must match Talos kernel |
| **Firmware** | ✅ Required | ❌ Not applicable | Hardware initialization |
| **NVIDIA Drivers (kernel)** | ✅ Required | ❌ Not applicable | GPU kernel modules |
| **NVIDIA Libraries (user-space)** | ⚠️ Optional | ✅ Recommended | CUDA runtime |
| **NVIDIA Container Toolkit** | ❌ Not needed | ✅ Required | Container GPU access |
| **CUDA Toolkit** | ❌ Not needed | ✅ Optional | Development tools |
| **CUDA Runtime Libraries** | ❌ Not needed | ✅ Recommended | Application runtime |
| **Desktop Customization** | ❌ Not needed | ❌ Not needed | Ignore for Kubernetes |
| **OOBE Customization** | ❌ Not needed | ❌ Not needed | Ignore for Kubernetes |
| **Network Drivers** | ✅ Required | ❌ Not applicable | System-level |
| **Storage Drivers** | ✅ Required | ❌ Not applicable | System-level |
| **NVIDIA Grub Params** | ✅ Required | ❌ Not applicable | Boot-time GPU config |
| **NVIDIA Persistenced** | ⚠️ Optional | ❌ Not applicable | GPU persistence daemon |

## Next Steps

1. ✅ **Audit Complete** - Components categorized
2. ⏭️ **Extract Kernel Modules** - Identify and extract NVIDIA kernel modules
3. ⏭️ **Create Talos Overlay** - Build overlay following Talos overlay structure
4. ⏭️ **Test Overlay** - Validate overlay with Talos Image Factory
5. ⏭️ **Create Container Images** - Build GPU-enabled container base images
6. ⏭️ **Integration Testing** - Test full stack on ASUS Ascent hardware

## References

- [Talos Image Factory](https://github.com/siderolabs/image-factory) - Image generation service
- [Talos Overlays](https://github.com/siderolabs/overlays/) - Overlay system documentation
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) - GPU container access
- [ASUS Ascent Repository Analysis](./ASUS_ASCENT_REPO_ANALYSIS.md) - Repository structure

