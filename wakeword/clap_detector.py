import time
import numpy as np
import sounddevice as sd

# Configuration Parameters
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024       # Process audio in fast, lightweight chunks (~23ms)
THRESHOLD = 0.5         # Adjust sensitivity (0.0 to 1.0)
MIN_GAP = 0.15          # Minimum time between two claps (prevents echo/double counts)
MAX_GAP = 0.8           # Maximum time allowed between the first and second clap


class ClapDetector:
    def __init__(self):
        self.last_clap_time = 0
        self.clap_detected_flag = False

    def audio_callback(self, indata, frames, time_info, status):
        """This function handles processing chunks of audio as they arrive in real-time."""
        if status:
            print(f"Status Warning: {status}", flush=True)

        # Get absolute peak energy of the current audio chunk
        peak = np.max(np.abs(indata))

        if peak > THRESHOLD:
            current_time = time.time()
            gap = current_time - self.last_clap_time

            # If the noise happens too fast after the last one, it's the same clap vibrating
            if gap < MIN_GAP:
                return

            # Check if this second clap falls into the perfect "Double Clap" window
            if MIN_GAP <= gap <= MAX_GAP:
                print(f"\n[SYSTEM] Double clap pattern recognized. (Gap: {gap:.2f}s)")
                self.clap_detected_flag = True
                # Reset clock so a 3rd clap doesn't instantly trigger a 2nd double clap
                self.last_clap_time = 0 
            else:
                # It's a valid loud clap, but it's the first one. Start the timer.
                self.last_clap_time = current_time

    def start_detection(self):
        """Starts a non-blocking background stream listening for the pattern."""
        print("⚡ JARVIS CLAP SENSOR ONLINE (Listening for double clap...)")
        self.clap_detected_flag = False
        
        # Open an input stream tracking the background voice engine's preferred rate
        with sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE
        ):
            # Keep running until a double clap flips the flag
            while not self.clap_detected_flag:
                time.sleep(0.05)
                
        return True


if __name__ == "__main__":
    detector = ClapDetector()
    while True:
        if detector.start_detection():
            print("🚀 Triggering JARVIS execution sequence!")
            print("-" * 50)
            time.sleep(2)  # Short pause before turning the sensor back on