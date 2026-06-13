import sys
import logging
import datetime
import requests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

from voice.speak import speak
from voice.listen import listen
from ui.dashboard import JarvisAnalyticsHUD
from ui.animations import UIAnimator
from desktop import apps, automation, files


# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("JARVIS")


# ── Constants ──────────────────────────────────────────────────────────────────
EXIT_KEYWORDS = frozenset(["exit", "quit", "goodbye", "shutdown jarvis", "go to sleep"])

HUD_SHOW_TRIGGERS = frozenset([
    "show the dashboard", "open dashboard", "show the window",
    "show hud", "display hud", "bring up dashboard",
])
HUD_HIDE_TRIGGERS = frozenset([
    "hide the dashboard", "close dashboard", "hide the window",
    "hide hud", "close hud",
])
APP_TRIGGERS  = frozenset(["open", "launch", "start", "run"])
SYS_TRIGGERS  = frozenset(["volume", "mute", "lock screen", "brightness", "screenshot"])

BOOT_BANNER = """
╔═══════════════════════════════════════════════════════╗
║          ⚡  J.A.R.V.I.S  RUNTIME  ACTIVE  ⚡         ║
║        Just A Rather Very Intelligent System          ║
╚═══════════════════════════════════════════════════════╝
"""


# ── Helpers ────────────────────────────────────────────────────────────────────
def _time_greeting() -> str:
    hour = datetime.datetime.now().hour
    if 5  <= hour < 12: return "Good Morning"
    if 12 <= hour < 17: return "Good Afternoon"
    if 17 <= hour < 21: return "Good Evening"
    return "Good Night"


def _fetch_context() -> tuple[str, int]:
    """
    Returns (city, temp_celsius).
    Falls back gracefully to Gurugram defaults on any network failure.
    """
    try:
        geo  = requests.get("https://ipapi.co/json/", timeout=4).json()
        city = geo.get("city", "Gurugram")
        lat  = geo.get("latitude",  28.4595)
        lon  = geo.get("longitude", 77.0266)

        url  = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )
        temp = round(
            requests.get(url, timeout=4).json()["current_weather"]["temperature"]
        )
        return city, temp

    except Exception as exc:
        log.warning("Weather fetch failed — using defaults. (%s)", exc)
        return "Gurugram", 32


def _build_briefing(greeting: str, city: str, temp: int) -> str:
    now = datetime.datetime.now().strftime("%I:%M %p")
    return (
        f"{greeting}, Sir. The time is {now}. "
        f"You are in {city}, currently {temp}°C outside. "
        f"All systems are fully operational. "
        f"How may I assist you today?"
    )


def _is_long_or_code(text: str) -> bool:
    return "```" in text or len(text) > 250


def _matches(command: str, triggers: frozenset) -> bool:
    return any(t in command for t in triggers)


# ── Command Router ─────────────────────────────────────────────────────────────
class CommandRouter:
    """
    Pure-logic dispatcher — no Qt, no threads.
    Returns a (spoken_reply, hud_signal, status_text) tuple.

    hud_signal: "show" | "hide" | None
    """

    def dispatch(self, raw: str) -> dict:
        cmd = raw.strip().lower()

        # ── Exit ──────────────────────────────────────────────────────────────
        if any(k in cmd for k in EXIT_KEYWORDS):
            return {
                "action":  "exit",
                "speak":   "Going offline. Have a productive day, Sir.",
                "hud":     "hide",
                "status":  None,
            }

        # ── HUD visibility ────────────────────────────────────────────────────
        if _matches(cmd, HUD_SHOW_TRIGGERS):
            return {
                "action":  "hud_show",
                "speak":   "Displaying primary analytics interface, Sir.",
                "hud":     "show",
                "status":  "Connection established // Live telemetry stream active",
            }

        if _matches(cmd, HUD_HIDE_TRIGGERS):
            return {
                "action":  "hud_hide",
                "speak":   "Closing telemetry interface.",
                "hud":     "hide",
                "status":  None,
            }

        # ── App launch ────────────────────────────────────────────────────────
        if _matches(cmd, APP_TRIGGERS):
            return {
                "action":  "app",
                "speak":   None,          # set after calling apps.open_application
                "hud":     None,
                "status":  "Deploying application binary...",
                "cmd_raw": raw,
            }

        # ── System macros ─────────────────────────────────────────────────────
        if _matches(cmd, SYS_TRIGGERS):
            return {
                "action":  "sys",
                "speak":   None,
                "hud":     None,
                "status":  "Executing system macro...",
                "cmd_raw": raw,
            }

        # ── AI fallback ───────────────────────────────────────────────────────
        return {
            "action":  "ai",
            "speak":   None,
            "hud":     None,
            "status":  "Cognitive core processing...",
            "cmd_raw": raw,
        }


# ── Voice Worker ───────────────────────────────────────────────────────────────
class JarvisVoiceWorker(QThread):
    """
    Runs entirely on a background QThread.
    All GUI mutations go through Qt signals — never direct widget calls.
    """
    sig_show_hud     = pyqtSignal(str)   # status text
    sig_hide_hud     = pyqtSignal()
    sig_update_status = pyqtSignal(str)
    sig_log_line     = pyqtSignal(str)   # optional: feed into HUD log

    def __init__(self, parent=None):
        super().__init__(parent)
        self._router = CommandRouter()
        self._running = True

    # ── Boot ──────────────────────────────────────────────────────────────────
    def _boot(self):
        greeting      = _time_greeting()
        city, temp    = _fetch_context()
        briefing      = _build_briefing(greeting, city, temp)

        log.info("BRIEFING: %s", briefing)
        self.sig_update_status.emit(f"Boot complete // {city}  {temp}°C")
        speak(briefing)

    # ── Main Loop ─────────────────────────────────────────────────────────────
    def run(self):
        self._boot()

        while self._running:
            try:
                command = listen()
                if not command:
                    continue

                log.info("[USER] %s", command)
                result = self._router.dispatch(command)
                self._execute(result, command)

            except Exception as exc:
                log.error("Worker exception: %s", exc, exc_info=True)

        QApplication.quit()

    def stop(self):
        self._running = False

    # ── Executor ──────────────────────────────────────────────────────────────
    def _execute(self, result: dict, raw: str):
        action = result["action"]

        # Emit HUD visibility signal first (non-blocking)
        if result.get("hud") == "show":
            self.sig_show_hud.emit(result.get("status", ""))
        elif result.get("hud") == "hide":
            self.sig_hide_hud.emit()

        # Emit status update if present
        if result.get("status") and result.get("hud") != "show":
            self.sig_update_status.emit(result["status"])

        # Speak canned reply if set
        if result.get("speak"):
            speak(result["speak"])

        # ── Side-effectful actions ─────────────────────────────────────────
        if action == "exit":
            self._running = False

        elif action == "app":
            reply = apps.open_application(raw)
            log.info("[JARVIS] %s", reply)
            speak(reply)

        elif action == "sys":
            reply = automation.handle_system_macro(raw)
            log.info("[JARVIS] %s", reply)
            speak(reply)

        elif action == "ai":
            self._run_ai(raw)

    def _run_ai(self, raw: str):
        from ai.brain import process_command   # lazy import keeps boot fast
        response = process_command(raw)
        log.info("[AI] %s", response[:120])
        self.sig_log_line.emit(response[:80] + ("…" if len(response) > 80 else ""))

        if _is_long_or_code(response):
            speak("I've displayed the output on screen for your review, Sir.")
        else:
            speak(response)


# ── Application Bootstrap ──────────────────────────────────────────────────────
def _wire_signals(worker: JarvisVoiceWorker, hud: JarvisAnalyticsHUD):
    """Connects worker signals to main-thread HUD slots."""

    def on_show(status: str):
        hud.update_status(status)
        hud.setWindowOpacity(0.0)
        hud.show()
        hud.raise_()
        hud.activateWindow()
        UIAnimator.fade_in(hud)

    def on_hide():
        UIAnimator.fade_out(hud, on_finished=hud.hide)

    def on_status(text: str):
        hud.update_status(text)

    def on_log(line: str):
        # Feeds live AI output into the HUD log ticker
        hud.update_status(line)

    worker.sig_show_hud.connect(on_show)
    worker.sig_hide_hud.connect(on_hide)
    worker.sig_update_status.connect(on_status)
    worker.sig_log_line.connect(on_log)


def main():
    print(BOOT_BANNER)

    app    = QApplication(sys.argv)
    hud    = JarvisAnalyticsHUD()
    worker = JarvisVoiceWorker()

    _wire_signals(worker, hud)
    worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()