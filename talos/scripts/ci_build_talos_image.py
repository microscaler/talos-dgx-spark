#!/usr/bin/env python3
"""
Build Talos image with overlay using Docker imager.

This script builds a Talos Linux image with the overlay applied using
the official Talos imager Docker image from ghcr.io/siderolabs/imager.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_talosctl() -> Optional[Path]:
    """
    Find talosctl binary.
    
    Returns:
        Optional[Path]: Path to talosctl or None
    """
    # Check common locations
    locations = [
        Path("/usr/local/bin/talosctl"),
        Path("/usr/bin/talosctl"),
        Path.home() / ".local" / "bin" / "talosctl",
    ]
    
    # Also check PATH
    import shutil
    talosctl_path = shutil.which("talosctl")
    if talosctl_path:
        locations.insert(0, Path(talosctl_path))
    
    for location in locations:
        if location.exists() and location.is_file():
            # Check if executable
            if os.access(location, os.X_OK):
                return location
    
    return None


def find_overlay_dir(talos_dir: Path) -> Optional[Path]:
    """
    Find overlay directory.
    
    Args:
        talos_dir: Path to talos directory
        
    Returns:
        Optional[Path]: Path to overlay directory or None
    """
    overlay_name = "asus-ascent-gx10-overlay"
    
    # Check direct location
    overlay_dir = talos_dir / overlay_name
    if overlay_dir.exists() and overlay_dir.is_dir():
        return overlay_dir
    
    # Search recursively
    for path in talos_dir.rglob(overlay_name):
        if path.is_dir():
            return path
    
    return None


# Note: We no longer use talosctl for building images, we use Docker imager instead
# The verify_talosctl function is kept for potential future use but not currently called


def build_overlay_image(overlay_dir: Path, overlay_name: str) -> str:
    """
    Build overlay as OCI image.
    
    Args:
        overlay_dir: Path to overlay directory
        overlay_name: Name of the overlay
        
    Returns:
        str: Image reference (e.g., "local/asus-ascent-gx10-overlay:latest")
    """
    import tempfile
    import shutil
    
    # Create a temporary Dockerfile for the overlay
    dockerfile_content = f"""FROM scratch
COPY . /overlay/
"""
    
    # Create temp directory for Docker build context
    with tempfile.TemporaryDirectory() as temp_dir:
        dockerfile_path = Path(temp_dir) / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        
        # Copy overlay directory to temp dir
        temp_overlay = Path(temp_dir) / "overlay"
        shutil.copytree(overlay_dir, temp_overlay, dirs_exist_ok=True)
        
        # Build the overlay image
        image_ref = f"local/{overlay_name}:latest"
        print(f"📦 Building overlay as OCI image: {image_ref}")
        
        result = subprocess.run(
            [
                "docker", "build",
                "-t", image_ref,
                "-f", str(dockerfile_path),
                str(temp_dir)
            ],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to build overlay image:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise RuntimeError("Failed to build overlay image")
        
        print(f"✅ Overlay image built: {image_ref}")
        return image_ref


def build_image(
    overlay_image_ref: str,
    overlay_name: str,
    arch: str,
    platform: str,
    talos_version: str,
    output_path: Path
) -> int:
    """
    Build Talos image with overlay using Docker imager.
    
    Args:
        overlay_image_ref: OCI image reference for the overlay
        overlay_name: Name of the overlay
        arch: Architecture (e.g., "arm64")
        platform: Platform (e.g., "metal")
        talos_version: Talos version
        output_path: Path to output image
        
    Returns:
        int: Exit code (0 for success)
    """
    # Check if Docker is available
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("❌ Docker is not available", file=sys.stderr)
            return 1
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker is not installed or not accessible", file=sys.stderr)
        return 1
    
    # Prepare paths
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert paths to absolute for Docker volume mounting
    output_dir_abs = output_dir.resolve()
    
    # Use Docker buildx with Talos imager
    # The imager expects overlay-image (OCI image) and overlay-name
    imager_image = f"ghcr.io/siderolabs/imager:{talos_version}"
    
    # Pull overlay image from Docker Hub if not already local
    print(f"📥 Ensuring overlay image is available: {overlay_image_ref}")
    verify_result = subprocess.run(
        ["docker", "image", "inspect", overlay_image_ref],
        capture_output=True,
        text=True,
    )
    if verify_result.returncode != 0:
        print(f"   Image not found locally, pulling from registry...")
        pull_result = subprocess.run(
            ["docker", "pull", overlay_image_ref],
            capture_output=False,
            text=True,
        )
        if pull_result.returncode != 0:
            print(f"❌ Failed to pull overlay image: {overlay_image_ref}", file=sys.stderr)
            return 1
        print(f"✅ Overlay image pulled successfully")
    else:
        print(f"✅ Overlay image found locally")
    
    # Build command using Docker buildx (Talos build tools)
    # This uses the imager container with proper buildx integration
    # Mount Docker socket so imager can access local overlay image from host
    # Use profile name (e.g., "metal") as first arg and --output-kind image to build disk image
    # (not "installer" which builds container image)
    cmd = [
        "docker", "run", "--rm", "-t",
        "--platform", f"linux/{arch}",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", f"{output_dir_abs}:/out",
        imager_image,
        platform,  # Profile name (e.g., "metal")
        "--arch", arch,
        "--output-kind", "image",  # Build disk image, not installer container
        "--overlay-image", overlay_image_ref,
        "--overlay-name", overlay_name,
        "--output", "/out",
    ]
    
    print(f"🔨 Building Talos image with overlay...")
    print(f"   Architecture: {arch}")
    print(f"   Platform: {platform}")
    print(f"   Talos Version: {talos_version}")
    print(f"   Imager Image: {imager_image}")
    print(f"   Overlay Image: {overlay_image_ref}")
    print(f"   Overlay Name: {overlay_name}")
    print(f"   Output Directory: {output_dir}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
        )
        
        if result.returncode != 0:
            print(f"❌ Image build failed with exit code {result.returncode}", file=sys.stderr)
            return result.returncode
        
        # The imager outputs files with a specific naming pattern
        # Look for the generated image file
        # Talos imager typically outputs: talos-{platform}-{arch}.img or similar
        possible_names = [
            output_path.name,
            f"talos-{platform}-{arch}.img",
            f"talos-{arch}-{platform}.img",
            f"disk.raw",
        ]
        
        found_image = None
        for name in possible_names:
            candidate = output_dir / name
            if candidate.exists():
                found_image = candidate
                break
        
        # If not found by name, look for any .img file
        if not found_image:
            img_files = list(output_dir.glob("*.img"))
            if img_files:
                found_image = img_files[0]
        
        if not found_image:
            print(f"❌ Output image not found in {output_dir}", file=sys.stderr)
            print(f"   Searched for: {', '.join(possible_names)}", file=sys.stderr)
            print(f"   Files in output directory:", file=sys.stderr)
            for f in output_dir.iterdir():
                print(f"     - {f.name}", file=sys.stderr)
            return 1
        
        # If the found image is different from expected, rename it
        if found_image != output_path:
            print(f"📦 Found image: {found_image.name}, moving to {output_path.name}")
            found_image.rename(output_path)
        
        size = output_path.stat().st_size
        if size == 0:
            print(f"❌ Output image is empty: {output_path}", file=sys.stderr)
            return 1
        
        print()
        print(f"✅ Talos image built successfully")
        print(f"   Image: {output_path.name} ({size / 1024 / 1024:.2f} MB)")
        
        return 0
        
    except subprocess.TimeoutExpired:
        print("❌ Image build timed out", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Build interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Error building image: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point."""
    try:
        # Get parameters from environment
        arch = os.environ.get("ARCH", "arm64")
        platform = os.environ.get("PLATFORM", "metal")
        talos_version = os.environ.get("TALOS_VERSION", "v1.8.0")
        overlay_image_ref = os.environ.get("OVERLAY_IMAGE")
        overlay_name = os.environ.get("OVERLAY_NAME", "asus-ascent-gx10-overlay")
        
        # If overlay image not provided, try to build locally (fallback)
        if not overlay_image_ref:
            print("⚠️  OVERLAY_IMAGE not set, attempting to build overlay locally...")
            talos_dir = Path(os.getcwd())
            if (talos_dir / "talos").exists():
                talos_dir = talos_dir / "talos"
            elif not (talos_dir / "asus-ascent-gx10-overlay").exists():
                talos_dir = talos_dir.parent / "talos"
            
            overlay_dir = find_overlay_dir(talos_dir)
            if not overlay_dir:
                print("❌ Overlay directory not found and OVERLAY_IMAGE not set!", file=sys.stderr)
                return 1
            
            try:
                overlay_image_ref = build_overlay_image(overlay_dir, overlay_name)
            except Exception as e:
                print(f"❌ Failed to build overlay image: {e}", file=sys.stderr)
                return 1
        else:
            print(f"✅ Using overlay image from registry: {overlay_image_ref}")
        
        # Get talos directory for output
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "asus-ascent-gx10-overlay").exists():
            talos_dir = talos_dir.parent / "talos"
        
        if not talos_dir.exists():
            print(f"❌ Talos directory not found: {talos_dir}", file=sys.stderr)
            return 1
        
        # Create output directory
        output_dir = talos_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build output path
        output_path = output_dir / f"talos-{platform}-{arch}-asus-ascent.img"
        
        # Build image using Docker imager
        return build_image(
            overlay_image_ref,
            overlay_name,
            arch,
            platform,
            talos_version,
            output_path
        )
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

