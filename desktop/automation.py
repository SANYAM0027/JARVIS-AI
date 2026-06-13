import subprocess
import logging

def handle_system_macro(command: str) -> str:
    """
    Processes core OS automation requests.
    Examples: 'mute system', 'volume up', 'lock screen'
    """
    command_lower = command.lower()

    try:
        # --- VOLUME OPERATIONS ---
        if "mute" in command_lower:
            subprocess.run(["osascript", "-e", "set volume with output muted"], check=True)
            return "Audio outputs muted, Sir."
            
        elif "unmute" in command_lower:
            subprocess.run(["osascript", "-e", "set volume without output muted"], check=True)
            return "Audio outputs restored, Sir."

        elif "volume up" in command_lower or "increase volume" in command_lower:
            # Increase current volume by roughly 10%
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)"], check=True)
            return "Volume elevated, Sir."

        elif "volume down" in command_lower or "decrease volume" in command_lower:
            # Decrease current volume by roughly 10%
            subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10)"], check=True)
            return "Volume reduced, Sir."

        # --- SYSTEM POWER/LOCK ---
        elif "lock" in command_lower and "screen" in command_lower:
            # Instantly locks the macOS user session screen
            subprocess.run(["open", "-a", "ScreenSaverEngine"], check=True)
            return "Securing workstation. Display matrix locked, Sir."

        elif "sleep mac" in command_lower or "sleep system" in command_lower:
            subprocess.run(["osascript", "-e", 'tell application "Finder" to sleep'], check=True)
            return "Putting the system to sleep, Sir."

    except Exception as e:
        logging.error(f"Automation macro execution failure: {e}")
        return "Internal automation pipeline error, Sir."

    return "Command recognized but no matching system automation macro found, Sir."