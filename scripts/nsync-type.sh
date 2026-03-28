#!/usr/bin/env bash
# nsync-type.sh — Fuzzy-pick an entry and type it out.
# Bind this to Ctrl+Space via Hammerspoon, Karabiner, or macOS Shortcuts.
# Requires: fzf (brew install fzf)
NSYNC="$(dirname "$0")/../cli/.venv/bin/nsync"
ENTRY=$("$NSYNC" ls | fzf --prompt="nsync> " --height=40%)
[ -n "$ENTRY" ] && "$NSYNC" get -t "$ENTRY"
