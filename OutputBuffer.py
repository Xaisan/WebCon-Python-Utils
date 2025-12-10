"""
OutputBuffer Class - Documentation for LLM Context

PURPOSE:
This class solves the problem of losing STDOUT messages when errors occur in subprocess
environments where STDERR presence causes STDOUT to be ignored. It buffers all STDOUT
messages and can replay them to STDERR when errors occur.

USE CASE:
When a Python script is run as a subprocess and the parent process only shows STDERR
when errors occur (ignoring STDOUT), this class ensures all diagnostic messages are
visible during error conditions.

USAGE PATTERN:
1. Create a global instance at the start of your script
2. Replace all print() calls with output_buffer.print()
3. Call output_buffer.flush_to_stderr() before writing any error to STDERR
4. This ensures all previous STDOUT messages are also written to STDERR
"""

import sys, io

if isinstance(sys.stdout, io.TextIOWrapper) and sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
if isinstance(sys.stderr, io.TextIOWrapper) and sys.version_info >= (3, 7):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

class OutputBuffer:   
    def __init__(self):
        """Initialize an empty message buffer."""
        self.messages = []
    
    def print(self, message: str, to_stderr: bool = False):
        """
        Print a message and store it in the buffer.
        
        Example:
            output_buffer.print("[INFO] Starting process...")  # Goes to STDOUT
            output_buffer.print("[WARN] Issue detected", to_stderr=True)  # Goes to STDERR
        """
        msg_str = str(message)
        self.messages.append(msg_str)
        
        stream = sys.stderr if to_stderr else sys.stdout
        try:
            print(msg_str, file=stream, flush=True)
        except UnicodeEncodeError:
            # Fallback: replace un-encodable characters instead of crashing
            encoding = getattr(stream, "encoding", None) or "utf-8"
            safe = msg_str.encode(encoding, errors="replace").decode(encoding, errors="replace")
            print(safe, file=stream, flush=True)
    
    def flush_to_stderr(self):
        """
        Dump all buffered STDOUT messages to STDERR.      
        When to use:
            - Before sys.exit(1) with error message
            - In except blocks before printing traceback
            - Before any critical error message to STDERR
        
        Example:
            if critical_error:
                output_buffer.flush_to_stderr()  # Dump all previous STDOUT
                print("FATAL ERROR: ...", file=sys.stderr)  # Now print error
                sys.exit(1)
        """
        if self.messages:
            print("\n" + "="*80, file=sys.stderr)
            print("[OUTPUT BUFFER] Dumping all stdout messages to stderr due to error:", 
                  file=sys.stderr)
            print("="*80, file=sys.stderr)
            for msg in self.messages:
                print(msg, file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr, flush=True)
