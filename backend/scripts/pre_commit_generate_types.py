#!/usr/bin/env python
"""
Pre-commit hook script for generating TypeScript types from Django serializers.

This script is called by the pre-commit hook before each commit to ensure
TypeScript types are always in sync with Django serializers.

Usage:
    python scripts/pre_commit_generate_types.py
"""

import os
import sys
import subprocess
from datetime import datetime


def run_command(cmd, cwd=None):
    """Run a shell command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out!", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return False


def get_backend_dir():
    """Get the backend directory path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def main():
    """Main function to generate TypeScript types."""
    print("=" * 60)
    print("Generating TypeScript types from Django serializers...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    backend_dir = get_backend_dir()

    cmd = [
        sys.executable,
        "-m",
        "scripts.generate_ts_types",
        "--apps", "tenders,enterprise,crawler,vectorlib,openclaw",
        "--output", "frontend/src/types/generated"
    ]

    success = run_command(cmd, cwd=backend_dir)

    if success:
        print("\n" + "=" * 60)
        print("✅ TypeScript types generated successfully!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Failed to generate TypeScript types!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())