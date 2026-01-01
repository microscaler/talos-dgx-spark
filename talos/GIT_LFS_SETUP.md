# Git LFS Setup for Talos Overlay

## Overview

This directory contains large binary files (firmware, kernel modules, overlay packages) that are tracked using Git LFS (Large File Storage) to keep the repository size manageable.

## Git LFS Configuration

Git LFS is configured in the root `.gitattributes` file with the following patterns:

### Tracked File Types

- **Kernel Modules**: `*.ko`, `*.ko.zst`
- **Firmware**: `*.bin`, `*.bin.zst`, `*.fw`, `*.fw.zst`
- **Overlay Packages**: `talos/output/*.tar.gz`
- **Archives**: `*.tar.gz`, `*.tar.xz`, `*.tar.bz2`, `*.zip`
- **Debian Packages**: `*.deb`
- **Images**: `*.img`, `*.iso`

### Directory-Specific Tracking

- `talos/asus-ascent-gx10-overlay/install/firmware/**` - All firmware files
- `talos/asus-ascent-gx10-overlay/install/kernel-modules/**` - All kernel modules

## Current Binary Files

### Firmware
- **Location**: `asus-ascent-gx10-overlay/install/firmware/`
- **Size**: ~881 MB
- **File Count**: 4,807 files
- **Types**: `.bin`, `.bin.zst`

### Kernel Modules
- **Location**: `asus-ascent-gx10-overlay/install/kernel-modules/`
- **Size**: ~29 MB
- **File Count**: 1,058 modules
- **Types**: `.ko.zst` (compressed with zstd)

### Overlay Packages
- **Location**: `output/`
- **Size**: ~868 MB per package
- **Type**: `.tar.gz`

## Usage

### Initial Setup

Git LFS should already be initialized. If not:

```bash
git lfs install
```

### Adding Files

Files matching the patterns in `.gitattributes` will automatically be tracked by Git LFS:

```bash
git add talos/asus-ascent-gx10-overlay/install/firmware/
git add talos/asus-ascent-gx10-overlay/install/kernel-modules/
git add talos/output/*.tar.gz
```

### Checking LFS Files

```bash
# List all LFS-tracked files
git lfs ls-files

# Check LFS status
git lfs status
```

### Cloning Repository

When cloning the repository, ensure Git LFS is installed:

```bash
# Install Git LFS (if not already installed)
# macOS: brew install git-lfs
# Linux: See https://git-lfs.github.com/

# Clone repository (LFS files will be downloaded automatically)
git clone <repository-url>
cd DCops
git lfs pull
```

## File Size Considerations

### Repository Impact

Without Git LFS, these binary files would significantly bloat the repository:
- Firmware: 881 MB
- Kernel Modules: 29 MB
- Overlay Package: 868 MB
- **Total**: ~1.8 GB per commit

With Git LFS, only pointer files (~130 bytes each) are stored in the repository, with actual files stored in LFS storage.

### LFS Storage

Git LFS files are stored separately from the main repository. When you clone or pull, LFS files are downloaded on-demand. This keeps the repository size small while allowing access to all files when needed.

## Troubleshooting

### Files Not Being Tracked

If binary files are not being tracked by LFS:

1. Check `.gitattributes` includes the file pattern
2. Ensure Git LFS is installed: `git lfs version`
3. Re-initialize if needed: `git lfs install`
4. Re-add files: `git add -f <file>`

### LFS Files Not Downloading

If LFS files don't download automatically:

```bash
# Manually pull LFS files
git lfs pull

# Or fetch specific files
git lfs fetch
git lfs checkout
```

### Checking File Status

```bash
# See which files are LFS pointers
git lfs ls-files

# Check if a specific file is tracked
git lfs track "*.bin"
```

## Best Practices

1. **Commit `.gitattributes`** - Always commit the `.gitattributes` file to ensure all contributors use LFS
2. **Monitor LFS Usage** - Large LFS repositories may have storage limits
3. **Use .gitignore Appropriately** - Don't ignore files that should be tracked by LFS
4. **Document Large Files** - Keep this document updated when adding new binary file types

## References

- [Git LFS Documentation](https://git-lfs.github.com/)
- [Git LFS Tutorial](https://github.com/git-lfs/git-lfs/wiki/Tutorial)
- [Git LFS Patterns](https://github.com/git-lfs/git-lfs/blob/main/docs/api/authentication.md)

