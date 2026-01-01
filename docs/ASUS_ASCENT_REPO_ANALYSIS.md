# ASUS Ascent GX10 ISO Repository Analysis

## Overview

This document analyzes the extracted ASUS Ascent GX10 OS ISO image and provides a plan for converting it into an Ubuntu APT repository for use in custom Docker images for Kubernetes worker nodes.

**ISO Location:** `/Users/casibbald/Workspace/microscaler/asus/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64`

**ISO Details:**
- Ubuntu 24.04 (Noble) for ARM64
- Origin: NVIDIA Server
- Total repository size: ~7.6GB (pool) + 3.2MB (metadata) + 9.7MB (OEM packages)

## Repository Structure Analysis

### Existing Repository Components

The ISO already contains a **complete, properly structured Ubuntu APT repository**:

```
ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64/
├── dists/
│   └── noble/
│       ├── Release              # Repository metadata
│       ├── Release.gpg          # GPG signature
│       ├── InRelease            # Inline GPG signature
│       ├── main/
│       │   └── binary-arm64/
│       │       ├── Packages     # Package index (2.6MB)
│       │       ├── Packages.gz  # Compressed index (678KB)
│       │       └── Release
│       └── restricted/
│           └── binary-arm64/
│               ├── Packages
│               ├── Packages.gz
│               └── Release
├── pool/
│   └── main/                    # 2211 .deb packages organized by name
│       ├── a/                   # Packages starting with 'a'
│       ├── b/                   # Packages starting with 'b'
│       └── ...                  # All packages organized alphabetically
└── oemdata/
    └── debs/                    # ASUS-specific packages
        ├── asus-ascent-gx10-desktop-customize_1.0.0_all.deb (9.6MB)
        └── asus-ascent-gx10-oobe-customize_1.0.0_arm64.deb (3.6KB)
```

### Package Statistics

- **Total .deb packages:** 2,211 packages
- **Pool size:** 7.6GB
- **Metadata size:** 3.2MB
- **OEM packages:** 2 packages (ASUS-specific customizations)

### ASUS-Specific Packages

1. **asus-ascent-gx10-desktop-customize_1.0.0_all.deb**
   - Size: 9.6MB
   - Architecture: all
   - Dependencies: `dgxstation-desktop`
   - Purpose: Desktop customization for ASUS Ascent GX10

2. **asus-ascent-gx10-oobe-customize_1.0.0_arm64.deb**
   - Size: 3.6KB
   - Architecture: arm64
   - Dependencies: `dgx-oobe`
   - Purpose: Out-of-box experience (OOBE) customizations

## Repository Status

✅ **The repository is already properly structured and ready to use!**

The ISO contains:
- ✅ Complete `dists/` structure with Release files
- ✅ GPG signatures (Release.gpg, InRelease)
- ✅ Package indexes (Packages, Packages.gz)
- ✅ All .deb files organized in `pool/`
- ✅ Proper component structure (main, restricted)

## Usage Options

### Option 1: Local File-Based Repository (Development/Testing)

Use the repository directly from the filesystem:

```bash
# In Dockerfile or apt sources
echo "deb [trusted=yes] file:///path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 ./" > /etc/apt/sources.list.d/asus-ascent.list
```

**Pros:**
- No network required
- Fast access
- Works offline

**Cons:**
- Requires copying entire repository into Docker build context
- Large image size
- Not suitable for production

### Option 2: HTTP/HTTPS Repository Server (Recommended for Production)

Serve the repository via HTTP/HTTPS:

#### 2a. Simple HTTP Server (Development)

```bash
cd /Users/casibbald/Workspace/microscaler/asus/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64
python3 -m http.server 8000
```

Then in Dockerfile:
```dockerfile
RUN echo "deb [trusted=yes] http://host.docker.internal:8000 ./" > /etc/apt/sources.list.d/asus-ascent.list
```

#### 2b. Nginx Repository Server (Production)

Create an Nginx configuration to serve the repository:

```nginx
server {
    listen 80;
    server_name asus-repo.example.com;
    root /var/www/asus-repo;
    
    location / {
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
    
    # Serve .deb files with correct MIME type
    location ~ \.deb$ {
        add_header Content-Type application/octet-stream;
    }
}
```

#### 2c. Kubernetes Ingress (Cloud-Native)

Deploy the repository as a Kubernetes service with Ingress:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: asus-repo-nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        root /usr/share/nginx/html;
        autoindex on;
        location / {
            try_files $uri $uri/ =404;
        }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asus-repo-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: asus-repo-server
  template:
    metadata:
      labels:
        app: asus-repo-server
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        volumeMounts:
        - name: repo-data
          mountPath: /usr/share/nginx/html
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: repo-data
        persistentVolumeClaim:
          claimName: asus-repo-pvc
      - name: nginx-config
        configMap:
          name: asus-repo-nginx-config
```

### Option 3: Include OEM Packages in Main Repository

Add the ASUS-specific packages to the main repository structure:

```bash
# Create OEM component in repository
mkdir -p dists/noble/oem/binary-arm64
mkdir -p pool/oem

# Copy ASUS packages to pool
cp oemdata/debs/*.deb pool/oem/

# Regenerate Packages index
cd dists/noble/oem/binary-arm64
dpkg-scanpackages ../../../../pool/oem /dev/null > Packages
gzip -c Packages > Packages.gz

# Update Release file (add OEM component)
# This requires regenerating the Release file with apt-ftparchive
```

### Option 4: Public Cloud Storage (AWS S3 / GCP Cloud Storage)

Host the repository on public cloud storage for global accessibility and scalability.

#### Repository Size Breakdown

- **Pool (packages):** 7.6 GB
- **Metadata (dists):** 3.2 MB
- **OEM packages:** 9.7 MB
- **Total:** ~7.6 GB (rounded for calculations)

#### AWS S3 Pricing Analysis

**Storage Costs (S3 Standard, US East - N. Virginia):**
- Storage: $0.023 per GB per month
- Monthly storage cost: 7.6 GB × $0.023 = **$0.175/month**
- Annual storage cost: **$2.10/year**

**Data Transfer Costs:**
- First 10 TB/month: $0.09 per GB
- Next 40 TB/month: $0.085 per GB
- Over 50 TB/month: $0.07 per GB

**Request Costs:**
- GET requests: $0.0004 per 1,000 requests
- PUT requests: $0.005 per 1,000 requests

**Cost Scenarios:**

| Scenario | Monthly Downloads | Data Transfer | Monthly Cost | Annual Cost |
|----------|------------------|---------------|--------------|-------------|
| **Low Usage** | 10 full downloads | 76 GB | $0.18 (storage) + $6.84 (transfer) = **$7.02** | **$84.24** |
| **Medium Usage** | 50 full downloads | 380 GB | $0.18 (storage) + $34.20 (transfer) = **$34.38** | **$412.56** |
| **High Usage** | 100 full downloads | 760 GB | $0.18 (storage) + $68.40 (transfer) = **$68.58** | **$822.96** |
| **Very High Usage** | 500 full downloads | 3.8 TB | $0.18 (storage) + $342.00 (transfer) = **$342.18** | **$4,106.16** |

**Note:** These scenarios assume full repository downloads. In practice, apt only downloads needed packages, reducing transfer costs significantly.

**Realistic Usage Pattern (Partial Package Downloads):**
- Average Docker build downloads ~500MB of packages (not full 7.6GB)
- 100 builds/month = 50 GB transfer
- Monthly cost: $0.18 (storage) + $4.50 (transfer) = **$4.68**
- Annual cost: **$56.16**

#### GCP Cloud Storage Pricing Analysis

**Storage Costs (Standard Storage, US-Central1 - Iowa):**
- Storage: $0.020 per GB per month
- Monthly storage cost: 7.6 GB × $0.020 = **$0.152/month**
- Annual storage cost: **$1.82/year**

**Data Transfer Costs:**
- First 1 TB/month: $0.12 per GB
- Next 9 TB/month: $0.11 per GB
- Over 10 TB/month: $0.08 per GB

**Request Costs:**
- Class A operations (writes): $0.05 per 10,000 operations
- Class B operations (reads): $0.004 per 10,000 operations

**Cost Scenarios:**

| Scenario | Monthly Downloads | Data Transfer | Monthly Cost | Annual Cost |
|----------|------------------|---------------|--------------|-------------|
| **Low Usage** | 10 full downloads | 76 GB | $0.15 (storage) + $9.12 (transfer) = **$9.27** | **$111.24** |
| **Medium Usage** | 50 full downloads | 380 GB | $0.15 (storage) + $45.60 (transfer) = **$45.75** | **$549.00** |
| **High Usage** | 100 full downloads | 760 GB | $0.15 (storage) + $91.20 (transfer) = **$91.35** | **$1,096.20** |
| **Very High Usage** | 500 full downloads | 3.8 TB | $0.15 (storage) + $456.00 (transfer) = **$456.15** | **$5,473.80** |

**Realistic Usage Pattern (Partial Package Downloads):**
- Average Docker build downloads ~500MB of packages
- 100 builds/month = 50 GB transfer
- Monthly cost: $0.15 (storage) + $6.00 (transfer) = **$6.15**
- Annual cost: **$73.80**

#### Cost Comparison Summary

| Provider | Storage/Year | Low Usage/Year | Medium Usage/Year | High Usage/Year | Realistic Usage/Year |
|----------|-------------|----------------|-------------------|-----------------|----------------------|
| **AWS S3** | $2.10 | $84.24 | $412.56 | $822.96 | $56.16 |
| **GCP Cloud Storage** | $1.82 | $111.24 | $549.00 | $1,096.20 | $73.80 |
| **Winner** | GCP (8% cheaper) | AWS (24% cheaper) | AWS (25% cheaper) | AWS (25% cheaper) | AWS (24% cheaper) |

**Key Findings:**
- **Storage costs are negligible** (~$2/year) - the main cost is data transfer
- **AWS S3 is cheaper for data transfer** ($0.09/GB vs $0.12/GB for first tier)
- **GCP has slightly cheaper storage** but higher transfer costs
- **Realistic usage is much cheaper** than full repository downloads

#### Cost Optimization Strategies

1. **Use CloudFront / Cloud CDN**
   - AWS CloudFront: $0.085/GB (first 10 TB) - saves 5.6% vs direct S3
   - GCP Cloud CDN: $0.08/GB (first 10 TB) - saves 33% vs direct GCS
   - **CDN makes GCP competitive** for high-traffic scenarios

2. **Implement Caching**
   - Use apt caching proxy (apt-cacher-ng) in your infrastructure
   - Reduces redundant downloads by 80-90%
   - Can reduce costs by 80-90% for repeated builds

3. **Use Infrequent Access Storage Classes**
   - AWS S3 Standard-IA: $0.0125/GB/month (storage) but $0.01/GB retrieval fee
   - Only cost-effective if accessed <1x/month
   - **Not recommended** for active repository

4. **Regional Optimization**
   - Store repository in same region as build infrastructure
   - Reduces data transfer costs (intra-region is cheaper/free)
   - Use multi-region replication only if needed

5. **Compress Repository**
   - Repository already uses Packages.gz (compressed indexes)
   - .deb files are already compressed
   - **Limited additional savings** possible

6. **Selective Package Hosting**
   - Only host ASUS-specific packages in cloud
   - Use standard Ubuntu repositories for common packages
   - Reduces storage from 7.6GB to ~10MB (OEM packages only)
   - **Annual cost: <$1** for storage + minimal transfer

#### Implementation Options

**Option A: Full Repository in Cloud**
- Upload entire 7.6GB repository
- Pros: Complete isolation, all packages available
- Cons: Higher storage and transfer costs
- **Best for:** Organizations needing complete control

**Option B: ASUS Packages Only in Cloud**
- Upload only `oemdata/debs/` (~10MB)
- Use standard Ubuntu repos for everything else
- Pros: Minimal cost, leverages Ubuntu CDN
- Cons: Requires internet access to Ubuntu repos
- **Annual cost: <$5** for realistic usage
- **Best for:** Cost-conscious deployments

**Option C: Hybrid Approach**
- Host ASUS packages in cloud
- Mirror frequently-used packages locally
- Use standard Ubuntu repos for rest
- **Best for:** Balanced cost and performance

#### Setup Instructions

**Note:** We are using **GCP Cloud Storage** as our primary repository host at `gs://asus-ascent-gb10/7.2.3`. The AWS S3 example below is provided as an alternative option.

**GCP Cloud Storage Setup (Primary):**
```bash
# Upload repository using the provided script
python scripts/upload_asus_repo_to_gcs.py \
    --repo-path /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    --bucket gs://asus-ascent-gb10 \
    --version 7.2.3 \
    --make-public

# Use in Dockerfile
RUN echo "deb [trusted=yes] https://storage.googleapis.com/asus-ascent-gb10/7.2.3/ ./" > /etc/apt/sources.list.d/asus-ascent.list
```

**AWS S3 Setup (Alternative):**
```bash
# Create S3 bucket
aws s3 mb s3://asus-ascent-repo --region us-east-1

# Enable static website hosting
aws s3 website s3://asus-ascent-repo --index-document index.html

# Upload repository
aws s3 sync /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    s3://asus-ascent-repo/ --exclude "*.git/*"

# Make public (or use CloudFront with signed URLs)
aws s3api put-bucket-policy --bucket asus-ascent-repo --policy file://bucket-policy.json

# Use in Dockerfile
RUN echo "deb [trusted=yes] http://asus-ascent-repo.s3-website-us-east-1.amazonaws.com ./" > /etc/apt/sources.list.d/asus-ascent.list
```

**GCP Cloud Storage Setup:**

**Option 1: Using the provided script (Recommended):**
```bash
# Upload repository using the automated script
# Project defaults to 'microscaler' (GCP console: https://console.cloud.google.com/storage/browser/asus-ascent-gb10?project=microscaler)
python scripts/upload_asus_repo_to_gcs.py \
    --repo-path /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    --bucket gs://asus-ascent-gb10 \
    --version 7.2.3 \
    --project microscaler
# Note: Omit --make-public to keep bucket private (recommended)

# The script will:
# - Set GCP project to 'microscaler' (if not already set)
# - Validate repository structure
# - Check gsutil and gcloud authentication
# - Upload repository with parallel processing
# - Set permissions if --make-public is used (⚠️  not recommended - huge cost risk)
# - Display the repository URL for use in Dockerfiles
```

**Option 2: Manual setup:**
```bash
# Create bucket (if it doesn't exist)
gsutil mb -l us-central1 gs://asus-ascent-gb10

# Upload repository to versioned path
gsutil -m rsync -r -d \
    /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
    gs://asus-ascent-gb10/7.2.3/

# ⚠️  WARNING: Making bucket public can result in HUGE costs!
# Data transfer: $0.12/GB - 100 downloads of 7.6GB = $91.20/month
# RECOMMENDED: Keep bucket private and use authenticated access instead
# gsutil -m iam ch allUsers:objectViewer gs://asus-ascent-gb10/7.2.3

# Use in Dockerfile (only if bucket is public)
RUN echo "deb [trusted=yes] https://storage.googleapis.com/asus-ascent-gb10/7.2.3/ ./" > /etc/apt/sources.list.d/asus-ascent.list
```

**⚠️  IMPORTANT: Public Bucket Cost Warning**

Making the bucket public exposes it to the world and can result in **significant data transfer costs**:
- **GCS Data Transfer:** $0.12/GB for downloads
- **Example:** 100 full repository downloads (7.6GB each) = **$91.20/month**
- **Risk:** Unauthorized access or bot traffic can cause unexpected costs

**✅ RECOMMENDED: Keep bucket private and use authenticated access** (see below)

**Repository URL (if public):** `https://storage.googleapis.com/asus-ascent-gb10/7.2.3/`

#### Authenticated Access (Private Buckets) - RECOMMENDED

**Yes, Docker builds can use authenticated GCS buckets for deb sources.** However, `apt` doesn't natively support HTTP authentication headers. Here are the recommended approaches:

**Option 1: Signed URLs (Recommended for Private Buckets)**

**Step 1: Create Service Account Key**

First, create a service account and download its key:

```bash
# Option A: Use the helper script (recommended)
bash scripts/create_gcp_service_account_key.sh

# Option B: Manual creation
gcloud config set project microscaler
gcloud iam service-accounts create asus-repo-access \
    --display-name="ASUS Repository Access"
gcloud projects add-iam-policy-binding microscaler \
    --member="serviceAccount:asus-repo-access@microscaler.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
gcloud iam service-accounts keys create asus-repo-service-account-key.json \
    --iam-account=asus-repo-access@microscaler.iam.gserviceaccount.com
```

This creates `asus-repo-service-account-key.json` with Storage Object Viewer permissions.

**Step 2: Generate Signed URL**

Generate time-limited signed URLs that can be used in Docker builds:

```bash
# Generate signed URL for the repository root (valid for 1 hour)
# Note: You need to sign the base path, not individual files
gsutil signurl -d 1h asus-repo-service-account-key.json \
    gs://asus-ascent-gb10/7.2.3/

# Or extract just the URL:
SIGNED_URL=$(gsutil signurl -d 1h asus-repo-service-account-key.json \
    gs://asus-ascent-gb10/7.2.3/ | grep -o 'https://[^?]*' | head -1)
echo "Signed URL: ${SIGNED_URL}"
```

**Step 3: Use in Dockerfile**

```dockerfile
ARG REPO_SIGNED_URL
RUN echo "deb [trusted=yes] ${REPO_SIGNED_URL} ./" > /etc/apt/sources.list.d/asus-ascent.list
```

**Step 4: Build with Signed URL**

```bash
# Generate signed URL
SIGNED_URL=$(gsutil signurl -d 1h asus-repo-service-account-key.json \
    gs://asus-ascent-gb10/7.2.3/ | grep -o 'https://[^?]*' | head -1)

# Build Docker image
docker build \
    --build-arg REPO_SIGNED_URL="${SIGNED_URL}/" \
    -t asus-ascent-base:24.04 \
    -f dockerfiles/Dockerfile.asus-ascent-authenticated.example .
```

**Note:** 
- Signed URLs expire (default 1 hour), so regenerate for each build
- The signed URL must point to the repository root directory, not individual files
- Add trailing `/` to the URL when using in apt sources

**Option 2: Pre-download Packages with Build Secrets**

**Step 1: Create Service Account Key** (same as Option 1, Step 1 above)

**Step 2: Use Docker build secrets** to authenticate and download packages:

```dockerfile
# syntax=docker/dockerfile:1.4
FROM ubuntu:24.04

# Install gcloud CLI for authentication
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates && \
    curl https://sdk.cloud.google.com | bash && \
    export PATH=$PATH:/root/google-cloud-sdk/bin

# Authenticate using build secret
RUN --mount=type=secret,id=gcp_credentials \
    export GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp_credentials && \
    gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS && \
    # Download repository metadata
    gsutil cp gs://asus-ascent-gb10/7.2.3/dists/noble/Release /tmp/Release && \
    gsutil cp gs://asus-ascent-gb10/7.2.3/dists/noble/Release.gpg /tmp/Release.gpg && \
    # Create local repository structure
    mkdir -p /var/cache/apt/archives && \
    # Download specific packages as needed
    gsutil -m cp gs://asus-ascent-gb10/7.2.3/pool/main/a/accountsservice/*.deb /var/cache/apt/archives/ || true

# Install from local cache
RUN apt-get update && \
    apt-get install -y \
        asus-ascent-gx10-desktop-customize \
        asus-ascent-gx10-oobe-customize
```

**Build with credentials:**
```bash
docker build \
    --secret id=gcp_credentials,src=/path/to/service-account-key.json \
    -t asus-ascent-base:24.04 .
```

**Option 3: Authenticated Proxy Service**

Deploy a lightweight proxy service that handles GCS authentication:

```dockerfile
FROM ubuntu:24.04

# Use authenticated proxy that handles GCS auth
RUN echo "deb [trusted=yes] http://repo-proxy.internal:8080/gcs/asus-ascent-gb10/7.2.3/ ./" > \
    /etc/apt/sources.list.d/asus-ascent.list
```

The proxy service authenticates with GCS and serves the repository to apt.

**Option 4: Make Bucket Public (⚠️  NOT RECOMMENDED - High Cost Risk)**

**⚠️  WARNING:** Making the bucket public can result in **huge unexpected costs**:
- Exposes 7.6GB repository to the world
- Data transfer: $0.12/GB for external downloads
- Example: 100 downloads = $91.20/month
- Risk of unauthorized access or bot traffic

```bash
# ⚠️  Only use if you understand the cost implications
gsutil -m iam ch allUsers:objectViewer gs://asus-ascent-gb10/7.2.3
```

**This is the simplest approach but:**
- ❌ Removes access control
- ❌ Can result in unexpected costs
- ❌ No audit trail of who accesses the repository
- ✅ **Use authenticated access instead** (Options 1-3 above)

**Security Recommendations:**

1. **Use Service Accounts:** Create dedicated service accounts with minimal permissions (Storage Object Viewer)
2. **Rotate Credentials:** Regularly rotate service account keys
3. **Use IAM Conditions:** Restrict access by IP, time, or other conditions
4. **Monitor Access:** Enable GCS audit logs to track access
5. **Signed URLs:** For CI/CD, generate signed URLs with short expiration times
6. **Build Secrets:** Never commit credentials; always use Docker build secrets

**Best Practice for Production:**

For production Docker builds, use **Option 1 (Signed URLs)** or **Option 3 (Authenticated Proxy)**:
- Generate signed URLs in CI/CD pipeline
- Or deploy a lightweight proxy service in your infrastructure
- Keep credentials out of Docker images
- Maintain audit trail of access

**Example Dockerfile:** See `dockerfiles/Dockerfile.asus-ascent-authenticated.example` for a complete example demonstrating both signed URL and build secret approaches.

#### Recommendation

For **cost optimization**, use **Option B (ASUS Packages Only)**:
- Upload only the 2 ASUS-specific packages (~10MB)
- Use standard Ubuntu repositories for all other packages
- **Estimated annual cost: <$5** for realistic usage
- Leverages Ubuntu's global CDN infrastructure
- Minimal maintenance required

For **complete control and isolation**, use **Option A (Full Repository)**:
- Upload entire 7.6GB repository
- **Estimated annual cost: $50-100** for realistic usage
- No dependency on external Ubuntu repositories
- Full control over package versions

## Docker Image Creation Strategy

### Base Image Options

#### Option A: Ubuntu 24.04 Base + ASUS Repository

```dockerfile
FROM ubuntu:24.04

# Add ASUS repository (GCS bucket)
RUN echo "deb [trusted=yes] https://storage.googleapis.com/asus-ascent-gb10/7.2.3/ ./" > /etc/apt/sources.list.d/asus-ascent.list && \
    apt-get update && \
    apt-get install -y \
        asus-ascent-gx10-desktop-customize \
        asus-ascent-gx10-oobe-customize \
    && rm -rf /var/lib/apt/lists/*

# Install additional packages as needed
RUN apt-get update && \
    apt-get install -y \
        <your-packages> \
    && rm -rf /var/lib/apt/lists/*
```

#### Option B: Extract from Casper Filesystem (Full System Image)

The ISO contains complete filesystem images in `casper/`:

- `ubuntu-server-minimal.squashfs` - Minimal server image
- `ubuntu-server-minimal.ubuntu-server.squashfs` - Full server image
- `ubuntu-server-minimal.ubuntu-server.installer.kernel.squashfs` - Kernel image

You can extract and use these:

```bash
# Extract squashfs
unsquashfs casper/ubuntu-server-minimal.ubuntu-server.squashfs

# Import as Docker image
sudo tar -C squashfs-root -c . | docker import - asus-ascent-base:24.04
```

**Note:** This gives you the exact system image but is larger and less flexible.

### Recommended Approach: Multi-Stage Build

```dockerfile
# Stage 1: Base with ASUS repository
FROM ubuntu:24.04 AS asus-base

ARG REPO_URL=https://storage.googleapis.com/asus-ascent-gb10/7.2.3
ARG REPO_TRUSTED=yes

# Configure ASUS repository
# Default: GCS bucket at https://storage.googleapis.com/asus-ascent-gb10/7.2.3
# Override with --build-arg REPO_URL=<your-url> for local development
RUN echo "deb [trusted=${REPO_TRUSTED}] ${REPO_URL}/ ./" > /etc/apt/sources.list.d/asus-ascent.list && \
    apt-get update

# Stage 2: Install ASUS packages
FROM asus-base AS asus-customized

RUN apt-get install -y \
        asus-ascent-gx10-desktop-customize \
        asus-ascent-gx10-oobe-customize \
    && rm -rf /var/lib/apt/lists/*

# Stage 3: Application-specific image
FROM asus-customized AS k8s-worker

# Install Kubernetes node requirements
RUN apt-get update && \
    apt-get install -y \
        containerd \
        kubelet \
        kubeadm \
        kubectl \
        <other-required-packages> \
    && rm -rf /var/lib/apt/lists/*

# Configure for Kubernetes
COPY k8s-node-config/ /etc/kubernetes/
```

## Implementation Plan

### Phase 1: Repository Server Setup

1. **Set up HTTP repository server**
   - Deploy Nginx or Apache to serve the repository
   - Configure proper MIME types for .deb files
   - Set up access controls if needed

2. **Test repository accessibility**
   ```bash
   curl http://repo-server/dists/noble/Release
   curl http://repo-server/pool/main/a/accountsservice/accountsservice_23.13.9-2ubuntu6_arm64.deb
   ```

3. **Verify GPG signatures** (optional but recommended)
   - Extract GPG key from ISO if available
   - Configure apt to verify signatures

### Phase 2: Docker Image Creation

1. **Create base Dockerfile**
   - Start with Ubuntu 24.04
   - Add ASUS repository
   - Install ASUS-specific packages

2. **Build and test image**
   ```bash
   docker build -t asus-ascent-base:24.04 -f Dockerfile.asus-base .
   docker run --rm asus-ascent-base:24.04 dpkg -l | grep asus
   ```

3. **Create Kubernetes node image**
   - Extend base image with Kubernetes components
   - Test on ASUS Ascent hardware

### Phase 3: Integration with Kubernetes

1. **Create custom node image**
   - Include all ASUS-specific drivers and packages
   - Configure for Kubernetes worker node

2. **Deploy to ASUS Ascent nodes**
   - Use image in node provisioning
   - Verify hardware compatibility

3. **Ongoing maintenance**
   - Update repository when new ASUS packages are available
   - Rebuild images with security updates

## Repository Maintenance

### Adding New Packages

```bash
# Add new .deb to pool
cp new-package.deb pool/main/n/newpackage/

# Regenerate Packages index
cd dists/noble/main/binary-arm64
dpkg-scanpackages ../../../../pool/main /dev/null > Packages
gzip -c Packages > Packages.gz

# Update Release file
cd ../../..
apt-ftparchive release . > Release
```

### Updating Repository Metadata

The repository uses standard Debian/Ubuntu tools:

- `dpkg-scanpackages` - Generate Packages files
- `apt-ftparchive` - Generate Release files
- `gpg` - Sign Release files

## Security Considerations

1. **GPG Verification**
   - Extract GPG key from ISO
   - Configure apt to verify package signatures
   - Use `[signed-by=/usr/share/keyrings/asus-keyring.gpg]` in sources.list

2. **Access Control**
   - Restrict repository access if serving over network
   - Use HTTPS with certificates
   - Implement authentication if needed

3. **Package Verification**
   - Verify package checksums match Packages file
   - Check package dependencies
   - Audit ASUS-specific packages

## Next Steps

1. ✅ **Analysis Complete** - Repository structure understood
2. ✅ **Upload script created** - `scripts/upload_asus_repo_to_gcs.py` ready for GCS upload
3. ⏭️ **Upload to GCS** - Run upload script to `gs://asus-ascent-gb10/7.2.3`
4. ⏭️ **Create Dockerfile** - Build base image with ASUS packages
5. ⏭️ **Test on hardware** - Verify compatibility on ASUS Ascent nodes
6. ⏭️ **Integrate with Kubernetes** - Create worker node images

## References

- [Debian Repository Format](https://wiki.debian.org/DebianRepository/Format)
- [Ubuntu Archive Structure](https://help.ubuntu.com/community/Repositories/Ubuntu)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Kubernetes Node Images](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)

