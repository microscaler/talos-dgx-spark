#!/usr/bin/env python3
"""
Build Talos overlay package with proper error handling.

This script builds the overlay package using the build_overlay.sh script
and verifies the output.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_build_script(talos_dir: Path) -> Optional[Path]:
    """
    Find the build_overlay.sh script.
    
    Args:
        talos_dir: Path to talos directory
        
    Returns:
        Optional[Path]: Path to build script or None if not found
    """
    script_path = talos_dir / "scripts" / "build_overlay.sh"
    if script_path.exists():
        return script_path
    
    # Try alternative locations
    alt_paths = [
        talos_dir.parent / "talos" / "scripts" / "build_overlay.sh",
        Path("scripts") / "build_overlay.sh",
    ]
    
    for alt_path in alt_paths:
        if alt_path.exists():
            return alt_path
    
    return None


def verify_package(talos_dir: Path, version: str) -> bool:
    """
    Verify overlay package was created.
    
    Args:
        talos_dir: Path to talos directory
        version: Overlay version
        
    Returns:
        bool: True if package exists and is valid
    """
    output_dir = talos_dir / "output"
    package_name = f"asus-ascent-gx10-overlay-{version}.tar.gz"
    package_path = output_dir / package_name
    
    if not package_path.exists():
        print(f"❌ Overlay package not found: {package_path}", file=sys.stderr)
        return False
    
    # Check file size (should be > 0)
    try:
        size = package_path.stat().st_size
        if size == 0:
            print(f"❌ Package file is empty: {package_path}", file=sys.stderr)
            return False
        
        # Check if it's a valid tar.gz
        result = subprocess.run(
            ["tar", "-tzf", str(package_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Package is not a valid tar.gz: {package_path}", file=sys.stderr)
            print(f"   Error: {result.stderr}", file=sys.stderr)
            return False
        
        print(f"✅ Package verified: {package_name} ({size / 1024 / 1024:.2f} MB)")
        return True
        
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"❌ Error verifying package: {e}", file=sys.stderr)
        return False


def build_overlay(talos_dir: Path, version: str) -> int:
    """
    Build overlay package.
    
    Args:
        talos_dir: Path to talos directory
        version: Overlay version
        
    Returns:
        int: Exit code (0 for success)
    """
    script_path = find_build_script(talos_dir)
    
    if not script_path:
        print(f"❌ Build script not found in {talos_dir}", file=sys.stderr)
        return 1
    
    # Make script executable
    try:
        os.chmod(script_path, 0o755)
    except OSError as e:
        print(f"⚠️  Warning: Could not make script executable: {e}", file=sys.stderr)
    
    # Change to talos directory
    original_cwd = os.getcwd()
    try:
        os.chdir(talos_dir)
        
        print(f"🔨 Building overlay package (version: {version})...")
        print(f"   Script: {script_path}")
        print()
        
        # Run build script
        result = subprocess.run(
            [str(script_path), version],
            capture_output=False,  # Show output in real-time
            text=True,
        )
        
        if result.returncode != 0:
            print(f"❌ Build script failed with exit code {result.returncode}", file=sys.stderr)
            return result.returncode
        
        # Verify package was created
        if not verify_package(Path("."), version):
            return 1
        
        # List output directory
        output_dir = Path("output")
        if output_dir.exists():
            print()
            print("📦 Output directory contents:")
            for item in sorted(output_dir.iterdir()):
                if item.is_file():
                    size = item.stat().st_size
                    print(f"   {item.name} ({size / 1024 / 1024:.2f} MB)")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error building overlay: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        os.chdir(original_cwd)


def main() -> int:
    """Main entry point."""
    try:
        # Get version from environment or argument
        version = os.environ.get("OVERLAY_VERSION")
        if not version:
            if len(sys.argv) > 1:
                version = sys.argv[1]
            else:
                version = "1.0.0"
        
        # Get talos directory
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "scripts" / "build_overlay.sh").exists():
            talos_dir = talos_dir.parent / "talos"
        
        if not talos_dir.exists():
            print(f"❌ Talos directory not found: {talos_dir}", file=sys.stderr)
            return 1
        
        return build_overlay(talos_dir, version)
        
    except KeyboardInterrupt:
        print("\n⚠️  Build interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

