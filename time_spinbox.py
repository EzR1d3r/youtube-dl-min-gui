"""A time spinbox displaying HH:MM:SS:CC and storing integer milliseconds."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import tkinter as tk
from tkinter import ttk


def seconds_to_milliseconds(seconds: float) -> int:
    """Round seconds to the nearest hundredth without binary-float arithmetic."""
    try:
        value = Decimal(str(seconds))
    except InvalidOperation as error:
        raise ValueError("Expected a finite, nonnegative time") from error
    if not value.is_finite() or value < 0:
        raise ValueError("Expected a finite, nonnegative time")
    return int((value * 100).to_integral_value(rounding=ROUND_HALF_UP)) * 10


def format_time(milliseconds: int) -> str:
    if isinstance(milliseconds, bool) or not isinstance(milliseconds, int) or milliseconds < 0:
        raise ValueError("Expected nonnegative integer milliseconds")
    hundredths = (milliseconds + 5) // 10
    seconds, fraction = divmod(hundredths, 100)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{fraction:02d}"


def parse_time(text: str) -> int:
    match = re.fullmatch(r"([0-9]{2,}):([0-9]{2}):([0-9]{2}):([0-9]{2})", text.strip())
    if match is None:
        raise ValueError("Expected HH:MM:SS:CC")
    hours, minutes, seconds, hundredths = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutes and seconds must be below 60")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + hundredths * 10


def time_step(state: int) -> int:
    """Tk modifier masks: Control takes priority over Shift."""
    if state & 0x0004:
        return 100
    if state & 0x0001:
        return 60_000
    return 1000


class TimeSpinbox(ttk.Spinbox):
    def __init__(self, master, *, textvariable: tk.StringVar, maximum_ms: int, **kwargs):
        self.variable = textvariable
        self.maximum_ms = maximum_ms
        self._milliseconds: int = parse_time(self.variable.get())
        super().__init__(master, textvariable=self.variable, width=14, **kwargs)
        self.variable.trace_add("write", self._text_changed)
        self.bind("<ButtonPress-1>", self._arrow_clicked)
        for modifier in ["", "Shift-", "Control-", "Control-Shift-"]:
            self.bind(f"<{modifier}Up>", lambda event: self._step(1, event.state))
            self.bind(f"<{modifier}Down>", lambda event: self._step(-1, event.state))
        self.bind("<<Increment>>", lambda event: self._step(1, event.state))
        self.bind("<<Decrement>>", lambda event: self._step(-1, event.state))
        self.bind("<FocusOut>", self._commit)
        self.bind("<Return>", self._commit)

    def get_milliseconds(self) -> int:
        value = parse_time(self.variable.get())
        if value > self.maximum_ms:
            raise ValueError("Time exceeds the file duration")
        return value

    def _text_changed(self, *args) -> None:
        try:
            self._milliseconds = self.get_milliseconds()
        except ValueError:
            pass

    def _commit(self, event) -> None:
        self._text_changed()
        self.variable.set(format_time(self._milliseconds))

    def _step(self, direction: int, state: int) -> str:
        if self.instate(["disabled"]) or self.instate(["readonly"]):
            return "break"
        self._text_changed()
        value = max(0, min(self.maximum_ms, self._milliseconds + direction * time_step(state)))
        self.variable.set(format_time(value))
        return "break"

    def _arrow_clicked(self, event):
        element = self.identify(event.x, event.y)
        if "uparrow" in element:
            return self._step(1, event.state)
        if "downarrow" in element:
            return self._step(-1, event.state)
