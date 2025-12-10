"""
Package Installation Utilities - Documentation for LLM Context

PURPOSE:
These utility functions provide robust package installation and verification for Python
scripts that need to ensure dependencies are available at runtime. They are designed
for scripts that run as subprocesses or in environments where dependencies may not be
pre-installed.

COMMON USE CASE:
Scripts distributed as single files that need to install their own dependencies
without requiring manual pip install commands or requirements.txt files.

INTEGRATION WITH OutputBuffer:
These functions use output_buffer.print() for logging. Ensure OutputBuffer is
imported and instantiated before using these functions.
"""

import sys
import os
import subprocess
import traceback
from typing import Optional
import warnings

warnings.filterwarnings("ignore")

# ----------------------------- GLOBAL CONFIGURATION --------------------------------
# --- PROXY CONFIGURATION ---
# Set this variable if your network requires a proxy for pip to download packages.
# Format: "http://user:password@host:port" or "http://host:port"
# Leave as empty string "" if no proxy is needed.
# 
# Example: PROXY_URL = "http://proxy.company.com:8080"
PROXY_URL = ""


# ----------------------------- 1. Package Installation Check ----------------------

def _is_package_installed(import_name: str) -> bool:
    """
    Check if a Python package is installed and importable.
    
    This function attempts to import a module to verify it's available in the
    current Python environment. It's used before installation attempts to avoid
    unnecessary reinstalls.
    
    Args:
        import_name (str): The module name used in import statements.
                          Example: "requests", "PIL", "cv2"
    """
    try:
        # __import__ attempts to load the module, raising an exception if unavailable
        __import__(import_name)
        return True
    except Exception:
        # Catches ModuleNotFoundError (Python 3.6+) and ImportError (older versions)
        # Also catches other import-time errors (circular imports, syntax errors, etc.)
        return False


# ----------------------------- 2. Forced PIP Installation -------------------------

def _install_pip_package(package_name: str, import_name: Optional[str] = None, 
                        timeout_sec: int = 300) -> bool:
    """
    Install or upgrade a pip package to its latest version.
    
    This function ensures a package is installed and up-to-date. It always attempts
    to upgrade to the latest version, even if the package is already installed.
    This guarantees the most recent bug fixes and features.
    
    Args:
        package_name (str): Name used with pip install (e.g., "requests", "Pillow")
        import_name (str, optional): Module name for import statement if different
                                     from package_name. Defaults to package_name.
        timeout_sec (int, optional): Maximum seconds to wait for installation.
                                    Defaults to 300 (5 minutes).
    
    Returns:
        bool: True if installation succeeded and module is importable, False otherwise    
    Requirements:
        - Requires output_buffer to be defined globally
        - Must be called with output_buffer.flush_to_stderr() on False return
    """
    # Default import_name to package_name if not specified
    import_name = import_name or package_name

    # Log the installation attempt
    output_buffer.print(f"[PIP] Attempting to install/upgrade package: {package_name} "
                       f"(import as '{import_name}')")
    
    try:
        # Step 1: Upgrade pip itself to avoid compatibility issues
        # Runs silently (output redirected to DEVNULL)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Step 2: Construct the pip install command
        command = [
            sys.executable,              # Use the current Python interpreter
            "-m", "pip",                 # Run pip as a module (more reliable)
            "--disable-pip-version-check",  # Suppress version check to reduce noise
            "install",
            package_name,
            "--upgrade",                 # Force upgrade to latest version
            "--no-input",                # Disable interactive prompts
            "--no-warn-script-location"  # Suppress script location warnings
        ]

        # Step 3: Configure proxy settings if needed
        env = os.environ.copy()
        if PROXY_URL:
            # Pip respects these standard environment variables
            env['HTTP_PROXY'] = PROXY_URL
            env['HTTPS_PROXY'] = PROXY_URL
            
        # Step 4: Execute pip install with timeout protection
        result = subprocess.run(
            command,
            timeout=timeout_sec,         # Prevent hanging on network issues
            capture_output=True,         # Capture stdout and stderr for analysis
            text=True,                   # Return strings instead of bytes
            env=env,                      # Pass environment with proxy settings
            stdin=subprocess.DEVNULL
        )

        # Step 5: Log the results
        output_buffer.print(f"[PIP] Return code: {result.returncode}")
        
        # Show stdout if there's content (truncated to 4000 chars)
        if result.stdout:
            output_buffer.print(f"[PIP][stdout]\n{result.stdout[:4000]}\n--- end stdout ---")
        
        # Show stderr if there's content (goes to stderr stream)
        if result.stderr:
            output_buffer.print(f"[PIP][stderr]\n{result.stderr[:4000]}\n--- end stderr ---", 
                              to_stderr=True)

        # Step 6: Verify installation success
        if result.returncode == 0:
            # Installation command succeeded, now verify import
            if _is_package_installed(import_name):
                output_buffer.print(f"[PIP] Successfully installed/upgraded and imported "
                                  f"'{import_name}'.")
                return True
            else:
                # Rare case: pip succeeded but import fails
                output_buffer.flush_to_stderr()
                print(f"[PIP][ERROR] Installation succeeded, but failed to import "
                     f"'{import_name}'.", file=sys.stderr)
                return False
        else:
            # Installation command failed
            output_buffer.flush_to_stderr()
            print(f"[PIP][ERROR] Failed to install/upgrade '{package_name}'.", 
                 file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        # Installation took longer than timeout_sec
        output_buffer.flush_to_stderr()
        print(f"[PIP][ERROR] Timeout ({timeout_sec}s) while installing/upgrading "
             f"'{package_name}'.", file=sys.stderr)
        return False
        
    except Exception as e:
        # Catch-all for unexpected errors (permission issues, disk full, etc.)
        output_buffer.flush_to_stderr()
        print(f"[PIP][ERROR] Unexpected error while installing/upgrading "
             f"'{package_name}': {e}", file=sys.stderr)
        traceback.print_exc()
        return False
