#!/usr/bin/env python3
"""
Upload ASUS Ascent repository to Google Cloud Storage.

This script uploads the complete ASUS Ascent GX10 repository structure to
Google Cloud Storage for use in Docker builds and Kubernetes node provisioning.

Usage (Public Bucket - NOT RECOMMENDED):
    python scripts/upload_asus_repo_to_gcs.py \
        --repo-path /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
        --bucket gs://asus-ascent-gb10 \
        --version 7.2.3 \
        --project microscaler \
        --make-public

Usage (Private Bucket - Authenticated Access - RECOMMENDED):
    python scripts/upload_asus_repo_to_gcs.py \
        --repo-path /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \
        --bucket gs://asus-ascent-gb10 \
        --version 7.2.3 \
        --project microscaler
    # Omit --make-public to keep bucket private
    # Use authenticated Docker builds (see Dockerfile.asus-ascent-authenticated.example)

Prerequisites:
    - gsutil must be installed and configured
    - gcloud auth must be set up with appropriate permissions
    - Bucket must exist and be accessible
    - For private buckets, use authenticated Docker builds with signed URLs or build secrets
"""

import argparse
import subprocess
import sys
from pathlib import Path


def log_info(msg):
    """Print info message."""
    print(f"ℹ️  {msg}")


def log_success(msg):
    """Print success message."""
    print(f"✅ {msg}")


def log_error(msg):
    """Print error message."""
    print(f"❌ {msg}", file=sys.stderr)


def log_warn(msg):
    """Print warning message."""
    print(f"⚠️  {msg}")


def check_gsutil():
    """Check if gsutil is available."""
    try:
        result = subprocess.run(
            ["gsutil", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def check_gcloud_auth():
    """Check if gcloud authentication is configured."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        # Check if there's an active account
        if "ACTIVE" in result.stdout:
            return True
        return False
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def set_gcp_project(project: str) -> bool:
    """Set the GCP project for gcloud/gsutil operations."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "set", "project", project],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        return False


def get_current_project() -> str:
    """Get the current GCP project."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def validate_repo_structure(repo_path: Path) -> bool:
    """Validate that the repository structure is correct."""
    required_paths = [
        'dists/noble/Release',
        'dists/noble/main/binary-arm64/Packages',
        'pool/main',
        'oemdata/debs',
    ]
    
    for path in required_paths:
        full_path = repo_path / path
        if not full_path.exists():
            log_error(f"Required path not found: {full_path}")
            return False
    
    log_success(f"Repository structure validated at {repo_path}")
    return True


def check_bucket_exists(bucket_path: str) -> bool:
    """Check if the GCS bucket exists and is accessible."""
    try:
        # Extract bucket name from gs:// path
        bucket_name = bucket_path.replace("gs://", "").split("/")[0]
        result = subprocess.run(
            ["gsutil", "ls", f"gs://{bucket_name}"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def upload_repository(repo_path: Path, bucket_path: str, version: str, dry_run: bool = False):
    """Upload the repository to GCS."""
    # Construct full destination path
    destination = f"{bucket_path.rstrip('/')}/{version}/"
    
    log_info(f"Source: {repo_path}")
    log_info(f"Destination: {destination}")
    
    if dry_run:
        log_warn("DRY RUN MODE - No files will be uploaded")
        log_info("Would run: gsutil -m rsync -r -d <source> <destination>")
        return True
    
    # Use gsutil rsync for efficient upload
    # -m: parallel processing (multi-threaded)
    # -r: recursive
    # -d: delete files in destination that don't exist in source
    # -x: exclude patterns (if needed)
    cmd = [
        "gsutil",
        "-m",  # Multi-threaded for faster upload
        "rsync",
        "-r",  # Recursive
        "-d",  # Delete destination files not in source
        str(repo_path),
        destination
    ]
    
    log_info("Starting upload (this may take a while for 7.6GB)...")
    log_info("Using parallel upload (-m) for faster transfer")
    
    try:
        # Run with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output
        for line in process.stdout:
            print(line, end="")
        
        process.wait()
        
        if process.returncode == 0:
            log_success(f"Repository uploaded successfully to {destination}")
            return True
        else:
            log_error(f"Upload failed with exit code {process.returncode}")
            return False
            
    except Exception as e:
        log_error(f"Failed to upload repository: {e}")
        return False


def set_bucket_permissions(bucket_path: str, version: str, make_public: bool = False):
    """Set bucket permissions for repository access."""
    destination = f"{bucket_path.rstrip('/')}/{version}/"
    
    if not make_public:
        log_info("Repository will be private (recommended for cost control)")
        log_info("Use authenticated Docker builds (see Dockerfile.asus-ascent-authenticated.example)")
        return True
    
    log_warn("⚠️  WARNING: Making repository PUBLIC - this exposes it to the world!")
    log_warn("⚠️  This can result in HUGE data transfer costs if accessed externally!")
    log_warn("⚠️  Estimated cost: $0.12/GB for data transfer out of GCS")
    log_warn("⚠️  7.6GB repository × 100 downloads = $91.20/month in transfer costs")
    log_warn("⚠️  Consider using authenticated access instead (signed URLs or build secrets)")
    log_info("Setting bucket permissions for public read access...")
    
    try:
        # Make objects publicly readable
        cmd = [
            "gsutil",
            "-m",
            "iam",
            "ch",
            "allUsers:objectViewer",
            destination
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        log_success("Repository is now publicly readable")
        return True
        
    except subprocess.CalledProcessError as e:
        log_warn(f"Failed to set public permissions: {e}")
        log_info("You can set permissions manually with:")
        log_info(f"  gsutil -m iam ch allUsers:objectViewer {destination}")
        return False


def get_repository_url(bucket_path: str, version: str) -> str:
    """Get the public URL for the repository."""
    bucket_name = bucket_path.replace("gs://", "").split("/")[0]
    return f"https://storage.googleapis.com/{bucket_name}/{version}/"


def main():
    parser = argparse.ArgumentParser(
        description='Upload ASUS Ascent repository to Google Cloud Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload repository to GCS
  python scripts/upload_asus_repo_to_gcs.py \\
      --repo-path /path/to/ASUS-Ascent-GX10-OS-7.2.3-3-20251007074705-arm64 \\
      --bucket gs://asus-ascent-gb10 \\
      --version 7.2.3

  # Dry run to see what would be uploaded
  python scripts/upload_asus_repo_to_gcs.py \\
      --repo-path /path/to/repo \\
      --bucket gs://asus-ascent-gb10 \\
      --version 7.2.3 \\
      --dry-run

  # Upload and make publicly accessible (⚠️  WARNING: Can result in huge costs!)
  # NOT RECOMMENDED - Use authenticated access instead
  python scripts/upload_asus_repo_to_gcs.py \\
      --repo-path /path/to/repo \\
      --bucket gs://asus-ascent-gb10 \\
      --version 7.2.3 \\
      --make-public
        """
    )
    
    parser.add_argument(
        '--repo-path',
        type=Path,
        required=True,
        help='Path to the extracted ASUS Ascent ISO repository'
    )
    
    parser.add_argument(
        '--bucket',
        type=str,
        required=True,
        help='GCS bucket path (e.g., gs://asus-ascent-gb10)'
    )
    
    parser.add_argument(
        '--version',
        type=str,
        default='7.2.3',
        help='Version string to use as subdirectory (default: 7.2.3)'
    )
    
    parser.add_argument(
        '--project',
        type=str,
        default='microscaler',
        help='GCP project ID (default: microscaler)'
    )
    
    parser.add_argument(
        '--make-public',
        action='store_true',
        help='⚠️  WARNING: Make repository publicly readable. This exposes the bucket to the world and can result in HUGE data transfer costs if accessed externally. Use authenticated access instead (see Dockerfile.asus-ascent-authenticated.example).'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    
    args = parser.parse_args()
    
    # Validate repository path
    if not args.repo_path.exists():
        log_error(f"Repository path does not exist: {args.repo_path}")
        sys.exit(1)
    
    if not args.repo_path.is_dir():
        log_error(f"Repository path is not a directory: {args.repo_path}")
        sys.exit(1)
    
    # Check prerequisites
    log_info("Checking prerequisites...")
    
    if not check_gsutil():
        log_error("gsutil is not installed or not in PATH")
        log_info("Install gsutil: https://cloud.google.com/storage/docs/gsutil_install")
        sys.exit(1)
    
    log_success("gsutil is available")
    
    if not check_gcloud_auth():
        log_error("gcloud authentication is not configured")
        log_info("Run: gcloud auth login")
        sys.exit(1)
    
    log_success("gcloud authentication is configured")
    
    # Set GCP project
    current_project = get_current_project()
    if current_project != args.project:
        log_info(f"Setting GCP project to: {args.project}")
        if set_gcp_project(args.project):
            log_success(f"GCP project set to: {args.project}")
        else:
            log_warn(f"Failed to set project to {args.project}, using current project: {current_project}")
            log_info("You can set it manually with: gcloud config set project microscaler")
    else:
        log_success(f"Using GCP project: {args.project}")
    
    # Validate bucket
    if not args.dry_run:
        if not check_bucket_exists(args.bucket):
            log_error(f"Bucket does not exist or is not accessible: {args.bucket}")
            log_info(f"Create bucket with: gsutil mb {args.bucket}")
            sys.exit(1)
        
        log_success(f"Bucket is accessible: {args.bucket}")
    
    # Validate repository structure
    if not validate_repo_structure(args.repo_path):
        log_error("Repository structure validation failed")
        log_info("Please ensure you have extracted the complete ISO")
        sys.exit(1)
    
    # Upload repository
    if not upload_repository(args.repo_path, args.bucket, args.version, args.dry_run):
        sys.exit(1)
    
    # Set permissions if requested (with cost warning)
    if args.make_public and not args.dry_run:
        print("\n" + "="*60)
        print("⚠️  COST WARNING: Making repository PUBLIC")
        print("="*60)
        print("This will expose your 7.6GB repository to the world.")
        print("Data transfer costs: $0.12/GB for downloads")
        print("Example: 100 full downloads = $91.20/month")
        print("\nRecommended: Use authenticated access instead")
        print("See: dockerfiles/Dockerfile.asus-ascent-authenticated.example")
        print("="*60 + "\n")
        set_bucket_permissions(args.bucket, args.version, make_public=True)
    
    # Show usage information
    repo_url = get_repository_url(args.bucket, args.version)
    
    print("\n" + "="*60)
    print("Repository Upload Complete")
    print("="*60)
    print(f"\nRepository URL: {repo_url}")
    
    if args.make_public:
        print(f"\n⚠️  Repository is PUBLIC - monitor data transfer costs!")
        print(f"\nTo use in Dockerfile (public access):")
        print(f'  RUN echo "deb [trusted=yes] {repo_url} ./" > /etc/apt/sources.list.d/asus-ascent.list')
    else:
        print(f"\n✅ Repository is PRIVATE - use authenticated access")
        print(f"\nTo use in Dockerfile (authenticated):")
        print(f"  See: dockerfiles/Dockerfile.asus-ascent-authenticated.example")
        print(f"  Or use signed URLs: gsutil signurl -d 1h key.json gs://asus-ascent-gb10/7.2.3/...")
    
    print(f"\nTo test repository access:")
    if args.make_public:
        print(f"  curl {repo_url}dists/noble/Release")
    else:
        print(f"  gsutil cat {args.bucket.rstrip('/')}/{args.version}/dists/noble/Release")
    print("="*60)


if __name__ == '__main__':
    main()

