#!/usr/bin/env python3
"""
Extract overlay version from package filename.

This script extracts the version from the overlay package filename
and outputs it for GitHub Actions.
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional


def extract_version_from_filename(filename: str) -> Optional[str]:
    """
    Extract version from package filename.
    
    Expected format: asus-ascent-gx10-overlay-1.0.0.tar.gz
    
    Args:
        filename: Package filename
        
    Returns:
        Optional[str]: Version string or None if not found
    """
    # Pattern: overlay-{version}.tar.gz
    pattern = r'overlay-(\d+\.\d+\.\d+(?:-.*)?)\.tar\.gz'
    match = re.search(pattern, filename)
    
    if match:
        return match.group(1)
    
    return None


def find_package(output_dir: Path) -> Optional[Path]:
    """
    Find overlay package in output directory.
    
    Args:
        output_dir: Directory containing packages
        
    Returns:
        Optional[Path]: Path to package or None
    """
    if not output_dir.exists():
        return None
    
    packages = list(output_dir.glob("*.tar.gz"))
    if not packages:
        return None
    
    return packages[0]


def main() -> int:
    """Main entry point."""
    try:
        # Get output directory
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "output").exists():
            talos_dir = talos_dir.parent / "talos"
        
        output_dir = talos_dir / "output"
        
        # Find package
        package_path = find_package(output_dir)
        if not package_path:
            print("⚠️  No package found, using default version", file=sys.stderr)
            version = "1.0.0"
        else:
            # Extract version from filename
            version = extract_version_from_filename(package_path.name)
            if not version:
                print(f"⚠️  Could not extract version from {package_path.name}, using default", file=sys.stderr)
                version = "1.0.0"
        
        print(f"📦 Overlay version: {version}")
        
        # Output to GitHub Actions
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            try:
                with open(github_output, "a") as f:
                    f.write(f"version={version}\n")
            except (IOError, OSError) as e:
                print(f"⚠️  Warning: Could not write to GITHUB_OUTPUT: {e}", file=sys.stderr)
        else:
            print("⚠️  GITHUB_OUTPUT not set, skipping output file write", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error extracting version: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

