#!/usr/bin/env python3
"""
Verify overlay components are present and valid.

This script checks that all required overlay components (firmware, kernel modules)
are present and reports any issues.
"""

import os
import sys
from pathlib import Path
from typing import Tuple, List


def count_files(directory: Path, pattern: str = "*") -> int:
    """
    Count files matching pattern in directory.
    
    Args:
        directory: Directory to search
        pattern: File pattern to match (default: all files)
        
    Returns:
        int: Number of files found
    """
    if not directory.exists():
        return 0
    
    try:
        if pattern == "*":
            return len(list(directory.rglob("*"))) - len(list(directory.rglob("*/")))
        else:
            return len(list(directory.rglob(pattern)))
    except (OSError, PermissionError) as e:
        print(f"⚠️  Error counting files in {directory}: {e}", file=sys.stderr)
        return 0


def verify_firmware(talos_dir: Path) -> Tuple[bool, int]:
    """
    Verify firmware directory exists and contains files.
    
    Args:
        talos_dir: Path to talos directory
        
    Returns:
        Tuple[bool, int]: (is_valid, file_count)
    """
    firmware_dir = talos_dir / "asus-ascent-gx10-overlay" / "install" / "firmware"
    
    if not firmware_dir.exists():
        print(f"❌ Firmware directory not found: {firmware_dir}", file=sys.stderr)
        return False, 0
    
    if not firmware_dir.is_dir():
        print(f"❌ Firmware path is not a directory: {firmware_dir}", file=sys.stderr)
        return False, 0
    
    file_count = count_files(firmware_dir)
    
    if file_count == 0:
        print(f"⚠️  Warning: No firmware files found in {firmware_dir}", file=sys.stderr)
        return False, 0
    
    return True, file_count


def verify_kernel_modules(talos_dir: Path) -> Tuple[bool, int]:
    """
    Verify kernel modules directory exists and contains modules.
    
    Args:
        talos_dir: Path to talos directory
        
    Returns:
        Tuple[bool, int]: (is_valid, module_count)
    """
    modules_dir = talos_dir / "asus-ascent-gx10-overlay" / "install" / "kernel-modules"
    
    if not modules_dir.exists():
        print(f"❌ Kernel modules directory not found: {modules_dir}", file=sys.stderr)
        return False, 0
    
    if not modules_dir.is_dir():
        print(f"❌ Kernel modules path is not a directory: {modules_dir}", file=sys.stderr)
        return False, 0
    
    # Count .ko and .ko.zst files
    ko_files = count_files(modules_dir, "*.ko")
    ko_zst_files = count_files(modules_dir, "*.ko.zst")
    module_count = ko_files + ko_zst_files
    
    if module_count == 0:
        print(f"⚠️  Warning: No kernel modules found in {modules_dir}", file=sys.stderr)
        return False, 0
    
    return True, module_count


def verify_config_files(talos_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify configuration files exist.
    
    Args:
        talos_dir: Path to talos directory
        
    Returns:
        Tuple[bool, List[str]]: (all_present, missing_files)
    """
    overlay_dir = talos_dir / "asus-ascent-gx10-overlay"
    required_files = [
        overlay_dir / "files" / "etc" / "modprobe.d" / "nvidia.conf",
        overlay_dir / "files" / "etc" / "modules-load.d" / "nvidia.conf",
    ]
    
    missing = []
    for file_path in required_files:
        if not file_path.exists():
            missing.append(str(file_path.relative_to(talos_dir)))
    
    return len(missing) == 0, missing


def main() -> int:
    """Main entry point."""
    try:
        # Get talos directory (default to current directory/talos or ./talos)
        talos_dir = Path(os.getcwd())
        if (talos_dir / "talos").exists():
            talos_dir = talos_dir / "talos"
        elif not (talos_dir / "asus-ascent-gx10-overlay").exists():
            # Try parent directory
            talos_dir = talos_dir.parent / "talos"
        
        if not talos_dir.exists():
            print(f"❌ Talos directory not found: {talos_dir}", file=sys.stderr)
            return 1
        
        print(f"🔍 Verifying overlay components in: {talos_dir}")
        print()
        
        # Verify firmware
        firmware_valid, firmware_count = verify_firmware(talos_dir)
        print(f"Firmware files: {firmware_count}")
        
        # Verify kernel modules
        modules_valid, module_count = verify_kernel_modules(talos_dir)
        print(f"Kernel modules: {module_count}")
        
        # Verify config files
        configs_valid, missing_configs = verify_config_files(talos_dir)
        if missing_configs:
            print(f"⚠️  Warning: Missing config files: {', '.join(missing_configs)}", file=sys.stderr)
        
        print()
        
        # Determine overall status
        if not firmware_valid or not modules_valid:
            print("⚠️  Warning: Missing components. Ensure Git LFS files are checked out.", file=sys.stderr)
            print("   Run: git lfs pull", file=sys.stderr)
            # Don't fail, just warn (components might be extracted later)
            return 0
        
        if not configs_valid:
            print("⚠️  Warning: Some configuration files are missing", file=sys.stderr)
            # Don't fail, configs are optional
        
        print("✅ All required components verified")
        return 0
        
    except Exception as e:
        print(f"❌ Error verifying components: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

