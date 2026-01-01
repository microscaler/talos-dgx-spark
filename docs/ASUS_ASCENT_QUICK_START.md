# ASUS Ascent Repository - Quick Start Guide

## Quick Summary

The ASUS Ascent GX10 ISO already contains a **complete, ready-to-use Ubuntu APT repository** with:
- ✅ 2,211 .deb packages (7.6GB)
- ✅ Proper repository metadata
- ✅ 2 ASUS-specific customization packages
- ✅ Ubuntu 24.04 (Noble) for ARM64

**No conversion needed** - just serve it and use it!

## Quick Start Options

### Option A: Local HTTP Server (Development)

**Step 1: Start Repository Server**
```bash
# Using the provided Python script
python scripts/setup_asus_repo_server.py \
    --repo-path /Users/casibbald/Workspace/microscaler/asus/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    --port 8000

# Or using Python's built-in server
cd /Users/casibbald/Workspace/microscaler/asus/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64
python3 -m http.server 8000
```

**Step 2: Build Docker Image**
```bash
docker build \
    --build-arg REPO_URL=http://host.docker.internal:8000 \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-base.example .
```

**Step 3: Verify Installation**
```bash
docker run --rm asus-ascent-base:24.04 dpkg -l | grep asus
```

### Option B: Google Cloud Storage (Production)

**Step 1: Upload Repository to GCS (Private Bucket - Recommended)**
```bash
# Upload to gs://asus-ascent-gb10/7.2.3 (keeps bucket private)
# Project defaults to 'microscaler' - matches GCP console project
python scripts/upload_asus_repo_to_gcs.py \
    --repo-path /Users/casibbald/Workspace/microscaler/asus/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    --bucket gs://asus-ascent-gb10 \
    --version 7.2.3 \
    --project microscaler
# Note: Omit --make-public to keep bucket private and avoid huge costs
# Project: https://console.cloud.google.com/storage/browser/asus-ascent-gb10?project=microscaler
```

**Step 2: Build Docker Image with Authenticated Access**
```bash
# Option 1: Use signed URL (recommended)
SIGNED_URL=$(gsutil signurl -d 1h service-account-key.json \
    gs://asus-ascent-gb10/7.2.3/dists/noble/Release | grep -o 'https://[^ ]*')

docker build \
    --build-arg REPO_SIGNED_URL="${SIGNED_URL}" \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-authenticated.example .

# Option 2: Use build secrets
docker build \
    --secret id=gcp_credentials,src=/path/to/service-account-key.json \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-authenticated.example .
```

**Step 3: Verify Installation**
```bash
docker run --rm asus-ascent-base:24.04 dpkg -l | grep asus
```

**⚠️  Cost Warning:** If you use `--make-public`, the bucket will be exposed to the world and can result in huge data transfer costs ($0.12/GB). Use authenticated access instead.

## Repository Structure

```
ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64/
├── dists/noble/          # Repository metadata (already generated!)
├── pool/main/            # 2,211 .deb packages
└── oemdata/debs/         # 2 ASUS-specific packages
```

## ASUS-Specific Packages

1. **asus-ascent-gx10-desktop-customize** (9.6MB)
   - Desktop customizations for ASUS Ascent GX10

2. **asus-ascent-gx10-oobe-customize** (3.6KB)
   - Out-of-box experience customizations

## Usage in Dockerfile

**Production (GCS):**
```dockerfile
# Add repository from GCS
RUN echo "deb [trusted=yes] https://storage.googleapis.com/asus-ascent-gb10/7.2.3/ ./" > /etc/apt/sources.list.d/asus-ascent.list && \
    apt-get update

# Install ASUS packages
RUN apt-get install -y \
        asus-ascent-gx10-desktop-customize \
        asus-ascent-gx10-oobe-customize
```

**Local Development:**
```dockerfile
# Add repository from local server
RUN echo "deb [trusted=yes] http://host.docker.internal:8000 ./" > /etc/apt/sources.list.d/asus-ascent.list && \
    apt-get update

# Install ASUS packages
RUN apt-get install -y \
        asus-ascent-gx10-desktop-customize \
        asus-ascent-gx10-oobe-customize
```

## Production Deployment

For production, deploy the repository as a Kubernetes service:

1. Create PersistentVolume with repository data
2. Deploy Nginx service to serve repository
3. Expose via Ingress or NodePort
4. Use repository URL in Docker builds

See `docs/ASUS_ASCENT_REPO_ANALYSIS.md` for detailed implementation.

## Authenticated Access

For private GCS buckets, Docker builds can use authenticated access:

**Step 1: Create Service Account Key**

First, create a service account and download its key:

```bash
# Use the helper script (recommended)
bash scripts/create_gcp_service_account_key.sh

# This creates: asus-repo-service-account-key.json
```

**Option 1: Signed URLs (Recommended)**
```bash
# Generate signed URL for repository root
SIGNED_URL=$(gsutil signurl -d 1h asus-repo-service-account-key.json \
    gs://asus-ascent-gb10/7.2.3/ | grep -o 'https://[^?]*' | head -1)

# Build with signed URL
docker build \
    --build-arg REPO_SIGNED_URL="${SIGNED_URL}/" \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-authenticated.example .
```

**Option 2: Build Secrets**
```bash
docker build \
    --secret id=gcp_credentials,src=asus-repo-service-account-key.json \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-authenticated.example .
```

**Important:**
- Keep `asus-repo-service-account-key.json` secure - never commit to git
- Add it to `.gitignore`
- Signed URLs expire after 1 hour (regenerate for each build)

See `docs/ASUS_ASCENT_REPO_ANALYSIS.md` for detailed authentication options.

## Files Created

- `docs/ASUS_ASCENT_REPO_ANALYSIS.md` - Complete analysis and implementation guide
- `dockerfiles/Dockerfile.asus-ascent-base.example` - Base image example (public GCS)
- `dockerfiles/Dockerfile.asus-ascent-authenticated.example` - Authenticated GCS access example
- `dockerfiles/Dockerfile.asus-ascent-k8s-worker.example` - Kubernetes worker image example
- `scripts/setup_asus_repo_server.py` - Local HTTP repository server script
- `scripts/upload_asus_repo_to_gcs.py` - GCS upload script for production deployment

