#!/usr/bin/env python3
"""nsync picker — Spotlight-launchable password picker with live search."""
import subprocess, sys, os, json, time

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "bin", "python3")

# If not running from venv, re-exec with venv python
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON, __file__] + sys.argv[1:])

from nsync import auth, config, store, sync

import tkinter as tk


def load_entries():
    cfg = config.load()
    creds = auth.authenticate(cfg)
    remote = sync.pull_store(creds, cfg)
    if remote is None:
        return {}
    return remote["entries"]


def type_out(text):
    time.sleep(0.5)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(["osascript", "-e",
        f'tell application "System Events" to keystroke "{escaped}"'], check=False)


class Picker:
    def __init__(self, entries: dict):
        self.entries = entries
        self.paths = sorted(entries.keys())

        self.root = tk.Tk()
        self.root.title("nsync")
        self.root.attributes("-topmost", True)
        self.root.geometry("500x400")

        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 400) // 3
        self.root.geometry(f"+{x}+{y}")

        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.entry = tk.Entry(self.root, textvariable=self.search_var, font=("Menlo", 16))
        self.entry.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.entry.focus_set()

        # Results list
        self.listbox = tk.Listbox(self.root, font=("Menlo", 13), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self._populate(self.paths)

        # Bindings
        self.entry.bind("<Return>", self._on_select)
        self.entry.bind("<Down>", lambda e: self._move(1))
        self.entry.bind("<Up>", lambda e: self._move(-1))
        self.listbox.bind("<Double-Button-1>", self._on_select)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.root.mainloop()

    def _populate(self, paths):
        self.listbox.delete(0, tk.END)
        for p in paths:
            self.listbox.insert(tk.END, p)
        if paths:
            self.listbox.selection_set(0)

    def _on_search(self, *_):
        q = self.search_var.get().lower()
        filtered = [p for p in self.paths if q in p.lower()]
        self._populate(filtered)

    def _move(self, delta):
        sel = self.listbox.curselection()
        idx = (sel[0] + delta) if sel else 0
        idx = max(0, min(idx, self.listbox.size() - 1))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.see(idx)

    def _on_select(self, _=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        path = self.listbox.get(sel[0])
        value = self.entries[path].split("\n")[0]
        self.root.destroy()
        # Output to stdout — the .app launcher handles typing
        print(value, end="", flush=True)


if __name__ == "__main__":
    entries = load_entries()
    if not entries:
        print("No entries found.")
        sys.exit(1)
    Picker(entries)
