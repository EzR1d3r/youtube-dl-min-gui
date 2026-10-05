"""Small hover hints for Tkinter widgets."""

import tkinter as tk
from tkinter import ttk


class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.timer = None
        self.window = None
        widget.bind("<Enter>", self._schedule, add="+")
        for event in ("<Leave>", "<ButtonPress>", "<Destroy>"):
            widget.bind(event, self._hide, add="+")

    def _schedule(self, event=None):
        self._hide()
        self.timer = self.widget.after(500, self._show)

    def _show(self):
        self.timer = None
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.window.geometry(f"+{x}+{y}")
        ttk.Label(self.window, text=self.text, padding=6, relief="solid", borderwidth=1).pack()

    def _hide(self, event=None):
        if self.timer is not None:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.window is not None:
            self.window.destroy()
            self.window = None
