#!/usr/bin/env python3
"""
Build Talos image with overlay using talosctl.

This script builds a Talos Linux image with the overlay applied.
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


def verify_talosctl(talosctl_path: Path) -> bool:
    """
    Verify talosctl is working.
    
    Args:
        talosctl_path: Path to talosctl
        
    Returns:
        bool: True if talosctl works
    """
    try:
        result = subprocess.run(
            [str(talosctl_path), "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print(f"❌ talosctl version command failed:", file=sys.stderr)
            print(f"   Exit code: {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"   Error: {result.stderr}", file=sys.stderr)
            if result.stdout:
                print(f"   Output: {result.stdout}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("❌ talosctl version command timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ talosctl binary not found at: {talosctl_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error running talosctl: {e}", file=sys.stderr)
        return False


def build_image(
    talosctl_path: Path,
    overlay_dir: Path,
    arch: str,
    platform: str,
    talos_version: str,
    output_path: Path
) -> int:
    """
    Build Talos image with overlay.
    
    Args:
        talosctl_path: Path to talosctl
        overlay_dir: Path to overlay directory
        arch: Architecture (e.g., "arm64")
        platform: Platform (e.g., "metal")
        talos_version: Talos version
        output_path: Path to output image
        
    Returns:
        int: Exit code (0 for success)
    """
    # Check if talosctl supports image factory command
    try:
        result = subprocess.run(
            [str(talosctl_path), "image", "factory", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ talosctl does not support 'image factory' command", file=sys.stderr)
            print("   This may require a newer version of talosctl", file=sys.stderr)
            return 1
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ Error checking talosctl capabilities: {e}", file=sys.stderr)
        return 1
    
    # Build command
    cmd = [
        str(talosctl_path),
        "image", "factory",
        "--arch", arch,
        "--platform", platform,
        "--overlay", str(overlay_dir),
        "--output", str(output_path),
        "--version", talos_version,
    ]
    
    print(f"🔨 Building Talos image with overlay...")
    print(f"   Architecture: {arch}")
    print(f"   Platform: {platform}")
    print(f"   Talos Version: {talos_version}")
    print(f"   Overlay: {overlay_dir}")
    print(f"   Output: {output_path}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
        )
        
        if result.returncode != 0:
            print(f"❌ Image factory failed with exit code {result.returncode}", file=sys.stderr)
            return result.returncode
        
        # Verify image was created
        if not output_path.exists():
            print(f"❌ Output image not found: {output_path}", file=sys.stderr)
            return 1
        
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
        
        # Get talos directory
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "asus-ascent-gx10-overlay").exists():
            talos_dir = talos_dir.parent / "talos"
        
        if not talos_dir.exists():
            print(f"❌ Talos directory not found: {talos_dir}", file=sys.stderr)
            return 1
        
        # Find talosctl
        talosctl_path = find_talosctl()
        if not talosctl_path:
            print("❌ talosctl not found. Install it first.", file=sys.stderr)
            print("   Run: python3 scripts/ci_install_talosctl.py", file=sys.stderr)
            return 1
        
        print(f"✅ Found talosctl at: {talosctl_path}")
        print("🔍 Verifying talosctl...")
        if not verify_talosctl(talosctl_path):
            print("❌ talosctl verification failed", file=sys.stderr)
            return 1
        print("✅ talosctl verified successfully")
        
        # Find overlay directory
        overlay_dir = find_overlay_dir(talos_dir)
        if not overlay_dir:
            print("❌ Overlay directory not found!", file=sys.stderr)
            print(f"   Searched in: {talos_dir}", file=sys.stderr)
            return 1
        
        print(f"✅ Overlay found at: {overlay_dir}")
        
        # Create output directory
        output_dir = talos_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build output path
        output_path = output_dir / f"talos-{platform}-{arch}-asus-ascent.img"
        
        # Build image
        return build_image(
            talosctl_path,
            overlay_dir,
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

