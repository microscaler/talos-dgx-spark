#!/usr/bin/env python3
"""
Extract overlay version from GitHub Actions inputs or use default.

This script extracts the overlay version from GitHub Actions workflow inputs
and outputs it in a format that can be used by subsequent workflow steps.
"""

import os
import sys
from pathlib import Path


def extract_version() -> str:
    """
    Extract version from GitHub Actions input or use default.
    
    Returns:
        str: Version string (e.g., "1.0.0")
    """
    # Get version from GitHub Actions input
    # For workflow_dispatch, inputs are passed via GITHUB_INPUT_VERSION env var
    # For other triggers, we use default
    version_input = os.environ.get("GITHUB_INPUT_VERSION", "")
    
    # Also check command line argument
    if len(sys.argv) > 1:
        version_input = sys.argv[1]
    
    if version_input and version_input.strip():
        version = version_input.strip()
    else:
        version = "1.0.0"
    
    return version


def output_github_action(version: str) -> None:
    """
    Output version to GitHub Actions output file.
    
    Args:
        version: Version string to output
    """
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        print("⚠️  GITHUB_OUTPUT not set, skipping output file write", file=sys.stderr)
        return
    
    try:
        with open(github_output, "a") as f:
            f.write(f"version={version}\n")
    except (IOError, OSError) as e:
        print(f"❌ Failed to write to GITHUB_OUTPUT: {e}", file=sys.stderr)
        sys.exit(1)


def validate_version(version: str) -> bool:
    """
    Validate version format (semantic versioning).
    
    Args:
        version: Version string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    # Simple semantic version pattern: X.Y.Z or X.Y.Z-*
    pattern = r'^\d+\.\d+\.\d+(-.*)?$'
    return bool(re.match(pattern, version))


def main() -> int:
    """Main entry point."""
    try:
        version = extract_version()
        
        if not validate_version(version):
            print(f"⚠️  Warning: Version '{version}' doesn't match semantic versioning pattern", file=sys.stderr)
            print(f"   Using anyway, but consider using format: X.Y.Z", file=sys.stderr)
        
        print(f"📦 Overlay version: {version}")
        
        output_github_action(version)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error extracting version: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

