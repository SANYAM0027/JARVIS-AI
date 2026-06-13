# ui/animations.py
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget

class UIAnimator:

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 400):
        widget.setWindowOpacity(0.0)
        widget.show()                          # ← THIS is what most people miss
        widget.raise_()
        widget.activateWindow()

        anim = QPropertyAnimation(widget, b"windowOpacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        # Keep reference so GC doesn't kill it mid-animation
        widget._fade_anim = anim

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300, on_finished=None):
        anim = QPropertyAnimation(widget, b"windowOpacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(widget.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)

        if on_finished:
            anim.finished.connect(on_finished)

        anim.start()
        widget._fade_anim = anim