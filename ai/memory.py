import json
import os

class Memory:

    def __init__(self, filename="jarvis_memory.json"):
        # Set path for saving memory locally
        self.filename = filename
        self.memory = self._load_from_disk()

    def _load_from_disk(self) -> dict:
        """Loads memory from a JSON file if it exists; otherwise, returns an empty dict."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as file:
                    return json.load(file)
            except Exception:
                # Fallback if file is corrupted
                return {}
        return {}

    def _save_to_disk(self):
        """Helper method to write the current memory state to the hard drive."""
        try:
            with open(self.filename, "w") as file:
                json.dump(self.memory, file, indent=4)
        except Exception as e:
            print(f"Error saving system memory to disk: {e}")

    def remember(self, key, value):
        """Stores a memory and commits it to disk instantly."""
        self.memory[key] = value
        self._save_to_disk()

    def recall(self, key):
        """Retrieves a specific memory by its key."""
        return self.memory.get(key)

    def forget(self, key):
        """Deletes a memory and updates the file on disk."""
        if key in self.memory:
            del self.memory[key]
            self._save_to_disk()
            return True
        return False

    def show_memory(self) -> dict:
        """Returns the entire memory dictionary."""
        return self.memory


# Instantiate the global memory object
jarvis_memory = Memory()