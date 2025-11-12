import sys
import os
import subprocess
import traceback
import tempfile
from typing import Optional
import warnings
warnings.filterwarnings("ignore")

# ----------------------------- GLOBAL CONTENT --------------------------------
# --- PROXY CONFIGURATION (UPDATE IF NEEDED) ---
# Set the proxy URL if required. Example: "http://user:password@host:port"
# Leave as None or empty string if no proxy is needed.
PROXY_URL = ""

# ----------------------------- 1. Package Installation Check ----------------------
def _is_package_installed(import_name: str) -> bool:
    """Checks if a module/package is importable by attempting to import it."""
    try:
        # We use __import__ to check if the top-level module is available
        __import__(import_name)
        return True
    except Exception:
        # Catches ModuleNotFoundError and other potential import errors
        return False


# ----------------------------- 2. Forced PIP Installation -------------------------
def _install_pip_package(package_name: str, import_name: Optional[str] = None, timeout_sec: int = 300) -> bool:
    """
    Forces the installation (or upgrade) of a pip package to the latest version.
    This replaces the previous version and ensures the latest code is used.

    - package_name: name used with pip (e.g., 'requests')
    - import_name: module name used by 'import ...' (e.g., 'requests', defaults to package_name)
    """
    import_name = import_name or package_name

    # Informational message
    output_buffer.print(f"[PIP] Attempting to install/upgrade package: {package_name} (import as '{import_name}')")
    try:
        # Construct the pip install command with the --upgrade flag
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        command = [
            sys.executable,
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            package_name,
            "--upgrade",  # Forces upgrade to the latest version
            "--no-input",
            "--no-warn-script-location"
        ]

        # Prepare environment variables for the subprocess, including proxy settings
        env = os.environ.copy()
        if PROXY_URL:
            # Pip honors these standard environment variables for connectivity
            env['HTTP_PROXY'] = PROXY_URL
            env['HTTPS_PROXY'] = PROXY_URL
            
        # Execute the command
        result = subprocess.run(
            command,
            timeout=timeout_sec,
            capture_output=True,
            text=True,
            env=env  # Pass the modified environment with proxy settings
        )

        output_buffer.print(f"[PIP] Return code: {result.returncode}")
        # Print captured output for debugging/logging
        if result.stdout:
            output_buffer.print(f"[PIP][stdout]\n{result.stdout[:4000]}\n--- end stdout ---")
        if result.stderr:
            # Print pip's stderr output to our script's stderr
            output_buffer.print(f"[PIP][stderr]\n{result.stderr[:4000]}\n--- end stderr ---", to_stderr=True)

        if result.returncode == 0:
            # Verification step: Check if we can import the module now
            if _is_package_installed(import_name):
                output_buffer.print(f"[PIP] Successfully installed/upgraded and imported '{import_name}'.")
                return True
            else:
                # Error message - flush buffer first, then print error
                output_buffer.flush_to_stderr()
                print(f"[PIP][ERROR] Installation succeeded, but failed to import '{import_name}'.", file=sys.stderr)
                return False
        else:
            # Error message - flush buffer first, then print error
            output_buffer.flush_to_stderr()
            print(f"[PIP][ERROR] Failed to install/upgrade '{package_name}'.", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        # Error message - flush buffer first, then print error
        output_buffer.flush_to_stderr()
        print(f"[PIP][ERROR] Timeout ({timeout_sec}s) while installing/upgrading '{package_name}'.", file=sys.stderr)
        return False
    except Exception as e:
        # Error message - flush buffer first, then print error
        output_buffer.flush_to_stderr()
        print(f"[PIP][ERROR] Unexpected error while installing/upgrading '{package_name}': {e}", file=sys.stderr)
        traceback.print_exc()
        return False
