import subprocess
import sys
import logging

def speak(text: str):
    """
    Converts a text string into an immediate voice broadcast using 
    the native macOS 'say' terminal engine.
    """
    if not text:
        return

    try:
        # Use macOS native 'say' utility
        # The text is fed directly into the system voice layer
        subprocess.run(["say", text], check=True)
        
    except FileNotFoundError:
        # Fallback security safety net if running on a non-Mac machine
        logging.warning("Native macOS 'say' utility not found. Printing to console instead.")
        print(f"[*VOICE OUT*]: {text}")
        
    except Exception as e:
        logging.error(f"Speech synthesis output thread failure: {e}")