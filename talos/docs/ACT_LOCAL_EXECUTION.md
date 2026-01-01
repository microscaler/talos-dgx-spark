# Running Talos Overlay Workflow Locally with ACT

This document explains how to run the Talos overlay GitHub Actions workflow locally using [ACT](https://github.com/nektos/act).

## What is ACT?

ACT is a tool that allows you to run GitHub Actions workflows locally using Docker. This is useful for:
- Testing workflow changes before pushing
- Debugging workflow issues
- Running workflows without GitHub Actions runner time

## Installation

### macOS

```bash
brew install act
```

### Linux

```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Windows

```powershell
choco install act-cli
```

## ACT Exclusions

The workflow uses `if: ${{ !env.ACT }}` to skip steps that don't work or aren't needed locally:

### Skipped Steps

1. **Docker Setup Actions** - Docker Buildx and QEMU setup (ACT uses its own Docker)
2. **GitHub Container Registry Login** - Not needed for local builds
3. **Artifact Uploads** - Artifacts are saved locally instead
4. **Metadata Extraction** - Docker metadata action (not needed locally)
5. **GitHub Releases** - Releases are only created on GitHub Actions

### Fallback Steps

For steps that download artifacts, ACT fallback steps check for local files instead:

- **Extract overlay package**: Checks if overlay is already built locally
- **Download artifacts**: Verifies local package exists

## Running the Workflow

### Basic Usage

```bash
# Run the entire workflow
act -W .github/workflows/talos-overlay.yml

# Run a specific job
act -j build-overlay -W .github/workflows/talos-overlay.yml

# Run with workflow_dispatch event
act workflow_dispatch -W .github/workflows/talos-overlay.yml
```

### With Inputs

```bash
# Run with custom version
act workflow_dispatch \
  -W .github/workflows/talos-overlay.yml \
  --input version=1.2.0 \
  --input build_image=true
```

### Environment Variables

ACT automatically sets `ACT=true` when running, which triggers the exclusions.

You can also set custom environment variables:

```bash
act -W .github/workflows/talos-overlay.yml \
  -e TALOS_VERSION=v1.8.0 \
  -e OVERLAY_VERSION=1.0.0
```

## Prerequisites for Local Execution

### 1. Git LFS Files

Ensure Git LFS files are checked out:

```bash
git lfs install
git lfs pull
```

### 2. Docker and Docker Buildx

ACT requires Docker to be running. The workflow uses Docker buildx for building OCI images:

```bash
# Check Docker is running
docker ps

# Verify Docker buildx is available
docker buildx version

# Start Docker if needed (macOS)
open -a Docker
```

**Note:** The overlay is built as an OCI image during the workflow, so no pre-build is needed.

## Workflow Jobs

### build-overlay-and-image

Builds the overlay as an OCI image and then builds the Talos Linux image with it.

**Local execution (ACT):**
- ✅ Verifies overlay components
- ✅ Builds overlay as OCI image locally (`local/talos-overlay-asus-ascent-gx10:latest`)
- ✅ Builds Talos image using Docker buildx with the overlay OCI image
- ⚠️  Skips Docker registry login (uses local images)
- ⚠️  Skips artifact upload (images saved locally)
- ⚠️  Skips GitHub Releases

**Output:**
- Overlay OCI image: `local/talos-overlay-asus-ascent-gx10:latest` (in Docker)
- Talos image: `talos/output/talos-{platform}-{arch}-asus-ascent.img`

**Key difference:** The overlay is now built as an OCI image (not a tar.gz package), which is then used directly by the Talos imager to build the final image.

## Troubleshooting

### ACT Can't Find Docker

```bash
# Ensure Docker is running
docker ps

# ACT may need Docker socket access
export ACT_DOCKER_SOCKET=/var/run/docker.sock
```

### Missing Git LFS Files

```bash
# Pull LFS files
git lfs pull

# Verify files exist
ls -lh talos/asus-ascent-gx10-overlay/install/firmware/ | head -5
```

### Python Scripts Fail

```bash
# Ensure Python 3.11+ is installed
python3 --version

# Make scripts executable
chmod +x talos/scripts/ci_*.py

# Test script directly
python3 talos/scripts/ci_verify_components.py
```

### Overlay Image Not Found

The overlay is built as an OCI image during the workflow. If it fails:

```bash
# Check if overlay directory exists
ls -la talos/asus-ascent-gx10-overlay/

# Verify Docker can build images
docker build --help

# Try building overlay manually
cd talos
cat > /tmp/overlay.Dockerfile <<EOF
FROM scratch
COPY asus-ascent-gx10-overlay /overlay/
EOF
docker build -f /tmp/overlay.Dockerfile -t local/talos-overlay-asus-ascent-gx10:latest .
```

### Docker Buildx Issues

If Docker buildx fails:

```bash
# Create buildx builder if needed
docker buildx create --name mybuilder --use

# Verify buildx is working
docker buildx inspect --bootstrap

# For ARM64 builds, ensure QEMU is available (ACT handles this)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

**Note:** The workflow uses the Talos imager (`ghcr.io/siderolabs/imager`) which handles cross-platform builds, so you don't need talosctl installed locally.

## ACT Configuration

You can create an `.actrc` file in the repository root to configure ACT:

```bash
# .actrc
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
```

## Limitations

1. **GitHub Secrets**: ACT can't access GitHub secrets. Use environment variables or `.secrets` file
2. **Self-Hosted Runners**: ACT doesn't support self-hosted runner features
3. **Matrix Strategies**: Some matrix builds may not work perfectly
4. **Artifact Persistence**: Artifacts are stored in ACT's temporary directories

## Example: Full Local Build

```bash
# 1. Pull Git LFS files
git lfs pull

# 2. Verify Docker is running
docker ps

# 3. Run workflow with ACT (builds overlay as OCI image, then Talos image)
act workflow_dispatch \
  -W .github/workflows/talos-overlay.yml \
  --input version=1.0.0 \
  --input build_image=true

# 4. Check outputs
ls -lh talos/output/

# 5. Verify overlay OCI image was created
docker images | grep talos-overlay

# 6. (Optional) Test the overlay image
docker run --rm local/talos-overlay-asus-ascent-gx10:latest ls /overlay/
```

## References

- [ACT Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [BRRTRouter ACT Pattern](../BRRTRouter/.github/workflows/ci.yml)

