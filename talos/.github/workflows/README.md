# Talos Overlay CI/CD

This directory contains GitHub Actions workflows for building and testing the Talos overlay for ASUS Ascent GX10.

## Workflows

### `talos-overlay.yml`

Main workflow for building Talos overlay packages and generating custom Talos images.

**Triggers:**
- Push to `main` or `develop` branches (when `talos/**` files change)
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

1. **build-overlay** - Builds the overlay package
   - Verifies overlay components (firmware, kernel modules)
   - Builds overlay package using `build_overlay.sh`
   - Uploads package as artifact

2. **build-talos-image** - Generates Talos images with overlay
   - Downloads overlay package artifact
   - Uses Docker-in-Docker with Talos Image Factory
   - Builds ARM64 images for metal platform
   - Uploads images as artifacts
   - Optionally uploads to GitHub Releases (on main branch)

3. **test-overlay** - Tests overlay package structure
   - Verifies package can be extracted
   - Checks for required components
   - Validates directory structure

## Docker-in-Docker (DinD)

The workflow uses Docker-in-Docker to:
- Avoid cross-compilation issues on macOS
- Build ARM64 images using QEMU emulation
- Run Talos Image Factory in a containerized environment

### Local Execution with GitHub ARC

To run workflows locally using GitHub Actions Runner Controller (ARC):

```bash
# Install ARC (if not already installed)
# See: https://github.com/actions/actions-runner-controller

# Run workflow locally
act -W .github/workflows/talos-overlay.yml
```

### Requirements

- **Git LFS**: All binary files (firmware, kernel modules) are tracked via Git LFS
- **Docker**: Required for DinD builds
- **QEMU**: For ARM64 emulation on x86_64 runners
- **Talos Image Factory**: Installed in container or via Go

## Manual Workflow Dispatch

You can manually trigger the workflow with custom parameters:

1. Go to Actions → Build Talos Overlay → Run workflow
2. Set parameters:
   - **version**: Overlay version (default: 1.0.0)
   - **build_image**: Whether to build Talos image (default: true)

## Artifacts

The workflow produces:

1. **Overlay Package**: `talos-overlay-package` artifact
   - Contains the complete overlay structure
   - Ready for use with Talos Image Factory

2. **Talos Images**: `talos-image-{platform}-{arch}` artifacts
   - Custom Talos Linux images with overlay applied
   - Ready for flashing to hardware

## GitHub Releases

On the `main` branch, successful builds automatically:
- Create GitHub Releases with Talos images
- Tag releases as `talos-overlay-{version}`
- Include installation instructions

## Troubleshooting

### Git LFS Files Missing

If firmware or kernel modules are missing:
```bash
# Ensure Git LFS is installed and files are pulled
git lfs install
git lfs pull
```

### Docker-in-Docker Issues

If DinD fails:
- Check runner has Docker socket access
- Verify QEMU is properly set up for ARM64
- Ensure privileged mode is enabled (for self-hosted runners)

### Talos Image Factory Errors

If image factory fails:
- Check Talos version compatibility
- Verify overlay structure is correct
- Ensure all required components are present

## Security Considerations

- Overlay packages contain NVIDIA proprietary firmware and drivers
- Images are built in isolated Docker containers
- Artifacts are stored securely in GitHub Actions
- Releases require appropriate permissions

