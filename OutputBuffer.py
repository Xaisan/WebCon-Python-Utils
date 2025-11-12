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

import sys


class OutputBuffer:
    """
    Manages output messages with dual-stream capability.
    
    This class buffers all messages printed to STDOUT and can replay them to STDERR
    when errors occur. This ensures visibility of all diagnostic messages even when
    the parent process only displays STDERR content.
    
    Attributes:
        messages (list): Internal buffer storing all printed messages
    
    Methods:
        print(message, to_stderr=False): Print and buffer a message
        flush_to_stderr(): Dump all buffered messages to STDERR
    """
    
    def __init__(self):
        """Initialize an empty message buffer."""
        self.messages = []
    
    def print(self, message: str, to_stderr: bool = False):
        """
        Print a message and store it in the buffer.
        
        Args:
            message (str): The message to print and buffer
            to_stderr (bool): If True, print directly to STDERR instead of STDOUT.
                            Use this for messages that are already errors.
        
        Behavior:
            - Message is always added to the internal buffer
            - Message is printed immediately to the specified stream
            - flush=True ensures immediate output (no buffering delay)
        
        Example:
            output_buffer.print("[INFO] Starting process...")  # Goes to STDOUT
            output_buffer.print("[WARN] Issue detected", to_stderr=True)  # Goes to STDERR
        """
        msg_str = str(message)
        self.messages.append(msg_str)
        if to_stderr:
            print(msg_str, file=sys.stderr, flush=True)
        else:
            print(msg_str, flush=True)
    
    def flush_to_stderr(self):
        """
        Dump all buffered STDOUT messages to STDERR.
        
        Call this method immediately before writing error messages to STDERR.
        This ensures that all diagnostic messages printed to STDOUT are visible
        even when the parent process only shows STDERR.
        
        Behavior:
            - Writes a visual separator for clarity
            - Replays all buffered messages to STDERR
            - Does nothing if buffer is empty
        
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
