#!/usr/bin/env python3
"""
Verify overlay package structure.

This script verifies that the overlay package contains all required
components and has the correct structure.
"""

import os
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import List, Tuple


def extract_package(package_path: Path, extract_to: Path) -> bool:
    """
    Extract package to temporary directory.
    
    Args:
        package_path: Path to package file
        extract_to: Directory to extract to
        
    Returns:
        bool: True if extraction successful
    """
    try:
        with tarfile.open(package_path, "r:gz") as tar:
            extract_to.mkdir(parents=True, exist_ok=True)
            tar.extractall(path=extract_to)
        return True
    except (tarfile.TarError, IOError, OSError) as e:
        print(f"❌ Error extracting package: {e}", file=sys.stderr)
        return False


def verify_component(path: Path, component_name: str) -> Tuple[bool, str]:
    """
    Verify a component exists.
    
    Args:
        path: Path to component
        component_name: Name for error messages
        
    Returns:
        Tuple[bool, str]: (exists, message)
    """
    if path.exists():
        if path.is_dir():
            return True, f"✅ {component_name} directory found"
        elif path.is_file():
            return True, f"✅ {component_name} file found"
        else:
            return False, f"❌ {component_name} exists but is not a file or directory"
    else:
        return False, f"❌ {component_name} missing"


def verify_overlay_structure(extract_dir: Path) -> int:
    """
    Verify overlay package structure.
    
    Args:
        extract_dir: Directory where package was extracted
        
    Returns:
        int: Number of failures (0 = all passed)
    """
    overlay_dir = extract_dir / "asus-ascent-gx10-overlay"
    
    if not overlay_dir.exists():
        print(f"❌ Overlay directory not found in package", file=sys.stderr)
        return 1
    
    failures = 0
    
    # Required directories
    required_dirs = [
        (overlay_dir / "install" / "firmware", "Firmware"),
        (overlay_dir / "install" / "kernel-modules", "Kernel modules"),
    ]
    
    # Required files
    required_files = [
        (overlay_dir / "overlay.yaml", "Overlay manifest"),
        (overlay_dir / "install" / "firmware" / "README.md", "Firmware README"),
    ]
    
    print("🔍 Verifying overlay structure...")
    print()
    
    # Check directories
    for path, name in required_dirs:
        exists, message = verify_component(path, name)
        print(message)
        if not exists:
            failures += 1
    
    # Check files
    for path, name in required_files:
        exists, message = verify_component(path, name)
        print(message)
        if not exists:
            failures += 1
    
    # Additional checks
    firmware_dir = overlay_dir / "install" / "firmware"
    if firmware_dir.exists():
        firmware_count = len(list(firmware_dir.rglob("*"))) - len(list(firmware_dir.rglob("*/")))
        if firmware_count > 0:
            print(f"✅ Found {firmware_count} firmware files")
        else:
            print("⚠️  Warning: Firmware directory is empty")
    
    modules_dir = overlay_dir / "install" / "kernel-modules"
    if modules_dir.exists():
        module_count = len(list(modules_dir.rglob("*.ko*")))
        if module_count > 0:
            print(f"✅ Found {module_count} kernel modules")
        else:
            print("⚠️  Warning: No kernel modules found")
    
    return failures


def main() -> int:
    """Main entry point."""
    try:
        # Get package path
        # Try multiple possible locations
        current_dir = Path(os.getcwd())
        possible_output_dirs = [
            current_dir / "talos" / "output",
            current_dir / "output",
            current_dir.parent / "talos" / "output",
        ]
        
        output_dir = None
        for possible_dir in possible_output_dirs:
            if possible_dir.exists():
                # Check if it has any tar.gz files
                packages = list(possible_dir.glob("*.tar.gz"))
                if packages:
                    output_dir = possible_dir
                    break
        
        if output_dir is None:
            # Try to find any output directory
            for possible_dir in possible_output_dirs:
                if possible_dir.exists():
                    output_dir = possible_dir
                    break
        
        if output_dir is None:
            # Create output directory if it doesn't exist (might be from artifact download)
            output_dir = current_dir / "talos" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find package - check both direct and subdirectories (artifact downloads create subdirs)
        packages = list(output_dir.glob("*.tar.gz"))
        if not packages:
            # Also search in subdirectories (artifact downloads may create subdirs)
            packages = list(output_dir.rglob("*.tar.gz"))
        
        if not packages:
            print(f"❌ No packages found in {output_dir}", file=sys.stderr)
            print(f"   Searched in: {output_dir} (including subdirectories)", file=sys.stderr)
            if output_dir.exists():
                print(f"   Directory exists but is empty or contains:", file=sys.stderr)
                for item in sorted(output_dir.iterdir()):
                    item_type = "dir" if item.is_dir() else "file"
                    if item.is_dir():
                        # Check what's inside subdirectories
                        sub_items = list(item.iterdir())
                        print(f"     - {item.name}/ ({item_type}, {len(sub_items)} items)", file=sys.stderr)
                        for sub_item in sorted(sub_items)[:5]:  # Show first 5 items
                            print(f"       - {sub_item.name}", file=sys.stderr)
                        if len(sub_items) > 5:
                            print(f"       ... and {len(sub_items) - 5} more", file=sys.stderr)
                    else:
                        print(f"     - {item.name} ({item_type})", file=sys.stderr)
            return 1
        
        package_path = packages[0]
        if len(packages) > 1:
            print(f"⚠️  Multiple packages found, testing first: {package_path.name}", file=sys.stderr)
        
        print(f"📦 Testing package: {package_path.name}")
        print()
        
        # List package contents
        try:
            with tarfile.open(package_path, "r:gz") as tar:
                print("📋 Package contents (first 20 entries):")
                for member in tar.getmembers()[:20]:
                    print(f"   {member.name}")
                if len(tar.getmembers()) > 20:
                    print(f"   ... and {len(tar.getmembers()) - 20} more entries")
                print()
        except tarfile.TarError as e:
            print(f"⚠️  Warning: Could not list package contents: {e}", file=sys.stderr)
        
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_to = Path(temp_dir)
            
            if not extract_package(package_path, extract_to):
                return 1
            
            # Verify structure
            failures = verify_overlay_structure(extract_to)
            
            print()
            if failures == 0:
                print("✅ Overlay package structure verified")
                return 0
            else:
                print(f"❌ Verification failed: {failures} component(s) missing", file=sys.stderr)
                return 1
        
    except Exception as e:
        print(f"❌ Error verifying package: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

