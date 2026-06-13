import os
import shutil
import logging

# Define your targeted user paths dynamically
DESKTOP_PATH = os.path.expanduser("~/Desktop")

# Clean target directories for organizing clutter
EXT_MAPPING = {
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Installers": [".dmg", ".pkg", ".zip", ".tar.gz"],
    "Code Files": [".py", ".js", ".html", ".css", ".json", ".sh"]
}

def organize_desktop() -> str:
    """
    Scans your desktop folder and moves ungrouped items into 
    clean sub-directories by their file extension.
    """
    if not os.path.exists(DESKTOP_PATH):
        return "Unable to locate target path configuration, Sir."

    moved_count = 0
    
    try:
        for item in os.listdir(DESKTOP_PATH):
            item_path = os.path.join(DESKTOP_PATH, item)
            
            # Skip folders or system configuration files (.DS_Store)
            if os.path.isdir(item_path) or item.startswith("."):
                continue
                
            _, file_ext = os.path.splitext(item).lower()
            
            # Find destination folder based on extension
            for folder_name, extensions in EXT_MAPPING.items():
                if file_ext in extensions:
                    dest_dir = os.path.join(DESKTOP_PATH, folder_name)
                    
                    # Lazy create destination directory if it doesn't exist
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    # Safely move file
                    shutil.move(item_path, os.path.join(dest_dir, item))
                    moved_count += 1
                    break
                    
        if moved_count > 0:
            return f"Desktop optimization sequence complete. Moved {moved_count} items into organized archives, Sir."
        return "Desktop architecture is already pristine. No actions required, Sir."

    except Exception as e:
        logging.error(f"File management operation failure: {e}")
        return "File operational thread crashed during organization sweep, Sir."