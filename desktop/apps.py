import subprocess
import logging

# Map common verbal names to official macOS application names
APP_MAPPING = {
    "chrome": "Google Chrome",
    "brave": "Brave Browser",
    "safari": "Safari",
    "spotify": "Spotify",
    "terminal": "Terminal",
    "finder": "Finder",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "notes": "Notes",
    "calculator": "Calculator"
}

def open_application(command: str) -> str:
    """
    Parses a voice command to open a matching macOS application.
    Example: 'open spotify' or 'launch chrome'
    """
    command_lower = command.lower()
    
    for key, app_name in APP_MAPPING.items():
        if key in command_lower:
            try:
                # Execute macOS native launch command: open -a "Application Name"
                subprocess.Popen(["open", "-a", app_name])
                return f"Opening {app_name}, Sir."
            except Exception as e:
                logging.error(f"Failed to open app {app_name}: {e}")
                return f"I encountered an error trying to launch {app_name}, Sir."
                
    return "Application signature not found in my operational database, Sir."

def close_application(command: str) -> str:
    """
    Parses a voice command to cleanly close/quit a running application.
    Example: 'close chrome' or 'quit spotify'
    """
    command_lower = command.lower()
    
    for key, app_name in APP_MAPPING.items():
        if key in command_lower:
            try:
                # Use AppleScript to gracefully quit applications natively
                applescript = f'tell application "{app_name}" to quit'
                subprocess.run(["osascript", "-e", applescript], check=True)
                return f"Terminating process thread for {app_name}, Sir."
            except subprocess.CalledProcessError:
                # Fallback forced kill command if AppleScript fails
                try:
                    subprocess.run(["pkill", "-f", app_name], check=True)
                    return f"Forcibly terminated {app_name}, Sir."
                except Exception:
                    return f"Application {app_name} does not appear to be running, Sir."
                    
    return "Application signature not recognized, Sir."