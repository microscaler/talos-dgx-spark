#!/usr/bin/env python3
"""
Extract overlay package and verify structure.

This script extracts the overlay package and verifies the overlay directory
is present and valid.
"""

import os
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional


def find_package(output_dir: Path) -> Optional[Path]:
    """
    Find overlay package in output directory.
    
    Args:
        output_dir: Directory containing packages
        
    Returns:
        Optional[Path]: Path to package or None if not found
    """
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}", file=sys.stderr)
        return None
    
    # Look for .tar.gz files
    packages = list(output_dir.glob("*.tar.gz"))
    
    if not packages:
        print(f"❌ No .tar.gz packages found in {output_dir}", file=sys.stderr)
        return None
    
    if len(packages) > 1:
        print(f"⚠️  Warning: Multiple packages found, using first: {packages[0].name}", file=sys.stderr)
    
    return packages[0]


def extract_package(package_path: Path, extract_to: Path) -> bool:
    """
    Extract overlay package.
    
    Args:
        package_path: Path to package file
        extract_to: Directory to extract to
        
    Returns:
        bool: True if extraction successful
    """
    try:
        print(f"📦 Extracting package: {package_path.name}")
        
        with tarfile.open(package_path, "r:gz") as tar:
            # Verify it's a valid tar file
            try:
                tar.getmembers()
            except tarfile.TarError as e:
                print(f"❌ Invalid tar file: {e}", file=sys.stderr)
                return False
            
            # Extract to parent directory
            extract_to.mkdir(parents=True, exist_ok=True)
            tar.extractall(path=extract_to)
        
        print(f"✅ Package extracted to: {extract_to}")
        return True
        
    except tarfile.TarError as e:
        print(f"❌ Error extracting tar file: {e}", file=sys.stderr)
        return False
    except (IOError, OSError) as e:
        print(f"❌ I/O error extracting package: {e}", file=sys.stderr)
        return False


def find_overlay_dir(search_dir: Path) -> Optional[Path]:
    """
    Find asus-ascent-gx10-overlay directory.
    
    Args:
        search_dir: Directory to search in
        
    Returns:
        Optional[Path]: Path to overlay directory or None
    """
    overlay_name = "asus-ascent-gx10-overlay"
    
    # Check direct children
    overlay_dir = search_dir / overlay_name
    if overlay_dir.exists() and overlay_dir.is_dir():
        return overlay_dir
    
    # Search recursively
    for path in search_dir.rglob(overlay_name):
        if path.is_dir():
            return path
    
    return None


def verify_overlay_structure(overlay_dir: Path) -> bool:
    """
    Verify overlay directory structure.
    
    Args:
        overlay_dir: Path to overlay directory
        
    Returns:
        bool: True if structure is valid
    """
    required_dirs = [
        overlay_dir / "install" / "firmware",
        overlay_dir / "install" / "kernel-modules",
    ]
    
    missing = []
    for req_dir in required_dirs:
        if not req_dir.exists():
            missing.append(str(req_dir.relative_to(overlay_dir)))
    
    if missing:
        print(f"⚠️  Warning: Missing directories: {', '.join(missing)}", file=sys.stderr)
        return False
    
    return True


def main() -> int:
    """Main entry point."""
    try:
        # Get directories
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "output").exists():
            talos_dir = talos_dir.parent / "talos"
        
        output_dir = talos_dir / "output"
        
        # Find package
        package_path = find_package(output_dir)
        if not package_path:
            return 1
        
        # Extract package
        extract_to = talos_dir.parent if talos_dir.parent.name != "talos" else talos_dir
        if not extract_package(package_path, extract_to):
            return 1
        
        # Find overlay directory
        overlay_dir = find_overlay_dir(extract_to)
        if not overlay_dir:
            print("❌ Overlay directory not found after extraction!", file=sys.stderr)
            print(f"   Searched in: {extract_to}", file=sys.stderr)
            return 1
        
        # Verify structure
        if not verify_overlay_structure(overlay_dir):
            print("⚠️  Warning: Overlay structure incomplete", file=sys.stderr)
        
        # Output overlay directory for GitHub Actions
        github_env = os.environ.get("GITHUB_ENV")
        if github_env:
            try:
                with open(github_env, "a") as f:
                    # Use relative path from talos directory
                    rel_path = overlay_dir.relative_to(talos_dir) if overlay_dir.is_relative_to(talos_dir) else overlay_dir
                    f.write(f"OVERLAY_DIR={rel_path}\n")
            except (IOError, OSError) as e:
                print(f"⚠️  Warning: Could not write to GITHUB_ENV: {e}", file=sys.stderr)
        
        print(f"📦 Extracted overlay to: {overlay_dir}")
        
        # List overlay contents
        try:
            print("\n📋 Overlay directory contents:")
            for item in sorted(overlay_dir.iterdir()):
                if item.is_dir():
                    print(f"   📁 {item.name}/")
                elif item.is_file():
                    size = item.stat().st_size
                    print(f"   📄 {item.name} ({size} bytes)")
        except (OSError, PermissionError):
            pass  # Ignore listing errors
        
        return 0
        
    except Exception as e:
        print(f"❌ Error extracting package: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

