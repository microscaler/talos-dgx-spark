#!/usr/bin/env python3
"""
Install talosctl binary with proper error handling.

This script downloads and installs the talosctl binary from GitHub releases.
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


def get_talos_version() -> str:
    """
    Get Talos version from environment or use default.
    
    Returns:
        str: Talos version (e.g., "v1.8.0")
    """
    version = os.environ.get("TALOS_VERSION", "v1.8.0")
    if not version.startswith("v"):
        version = f"v{version}"
    return version


def get_platform() -> str:
    """
    Get platform for talosctl binary.
    
    Returns:
        str: Platform string (e.g., "linux-amd64")
    """
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map to talosctl platform names
    if system == "linux":
        if machine in ["x86_64", "amd64"]:
            return "linux-amd64"
        elif machine in ["aarch64", "arm64"]:
            return "linux-arm64"
    elif system == "darwin":
        if machine in ["x86_64", "amd64"]:
            return "darwin-amd64"
        elif machine in ["aarch64", "arm64"]:
            return "darwin-arm64"
    
    # Default to linux-amd64 for CI
    return "linux-amd64"


def download_talosctl(version: str, platform: str, output_path: Path) -> bool:
    """
    Download talosctl binary from GitHub.
    
    Args:
        version: Talos version
        platform: Platform string
        output_path: Path to save binary
        
    Returns:
        bool: True if download successful
    """
    url = f"https://github.com/siderolabs/talos/releases/download/{version}/talosctl-{platform}"
    
    print(f"📥 Downloading talosctl from: {url}")
    
    try:
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"\r   Progress: {percent}%", end="", flush=True)
        
        urllib.request.urlretrieve(url, output_path, show_progress)
        print()  # New line after progress
        
        # Verify file was downloaded
        if not output_path.exists():
            print(f"❌ Downloaded file not found: {output_path}", file=sys.stderr)
            return False
        
        # Check file size (should be > 0)
        size = output_path.stat().st_size
        if size == 0:
            print(f"❌ Downloaded file is empty", file=sys.stderr)
            return False
        
        print(f"✅ Downloaded talosctl ({size / 1024 / 1024:.2f} MB)")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP error downloading talosctl: {e.code} {e.reason}", file=sys.stderr)
        if e.code == 404:
            print(f"   Version or platform may not exist: {version} / {platform}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"❌ URL error downloading talosctl: {e.reason}", file=sys.stderr)
        return False
    except (IOError, OSError) as e:
        print(f"❌ I/O error downloading talosctl: {e}", file=sys.stderr)
        return False


def install_talosctl(version: str) -> int:
    """
    Install talosctl binary.
    
    Args:
        version: Talos version
        
    Returns:
        int: Exit code (0 for success)
    """
    platform = get_platform()
    install_dir = Path("/usr/local/bin")
    binary_path = install_dir / "talosctl"
    
    # Create install directory if it doesn't exist
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"❌ Cannot create install directory {install_dir}: {e}", file=sys.stderr)
        return 1
    
    # Download to temporary location first
    temp_path = Path(tempfile.gettempdir()) / f"talosctl-{version}-{platform}"
    
    try:
        if not download_talosctl(version, platform, temp_path):
            return 1
        
        # Move to final location
        try:
            if binary_path.exists():
                binary_path.unlink()
            temp_path.rename(binary_path)
        except (OSError, PermissionError) as e:
            print(f"❌ Cannot install talosctl to {binary_path}: {e}", file=sys.stderr)
            print(f"   Try running with sudo or check permissions", file=sys.stderr)
            return 1
        
        # Make executable
        try:
            os.chmod(binary_path, 0o755)
        except OSError as e:
            print(f"⚠️  Warning: Could not make binary executable: {e}", file=sys.stderr)
        
        # Verify installation
        print(f"✅ talosctl installed to: {binary_path}")
        
        # Test version command
        print("\n🔍 Verifying talosctl installation...")
        try:
            result = subprocess.run(
                [str(binary_path), "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ talosctl version:")
                print(result.stdout)
            else:
                print(f"⚠️  Warning: talosctl version command failed", file=sys.stderr)
                print(f"   {result.stderr}", file=sys.stderr)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"⚠️  Warning: Could not verify talosctl: {e}", file=sys.stderr)
        
        return 0
        
    finally:
        # Clean up temp file if it still exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def main() -> int:
    """Main entry point."""
    try:
        version = get_talos_version()
        print(f"📥 Installing talosctl (version: {version})...")
        print()
        
        return install_talosctl(version)
        
    except KeyboardInterrupt:
        print("\n⚠️  Installation interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

