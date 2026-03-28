#!/usr/bin/env bash
# pass-nsync.bash — pass wrapper for trusted Arch laptop
# Source this in .bashrc/.zshrc: source /path/to/pass-nsync.bash
#
# Wraps `pass` to auto-sync with nsync cloud store:
#   - Before `pass show`: pull from cloud, show diff, ask approval
#   - After `pass insert/edit/rm`: push changes to cloud

_nsync_pull_and_approve() {
    echo "[nsync] Checking for pending cloud changes..."
    nsync approve 2>/dev/null
}

_nsync_push() {
    echo "[nsync] Pushing to cloud..."
    nsync import-pass 2>/dev/null && echo "[nsync] ✓ Synced"
}

pass() {
    case "$1" in
        show|"")
            _nsync_pull_and_approve
            command pass "$@"
            ;;
        insert|edit|generate)
            command pass "$@"
            local rc=$?
            [ $rc -eq 0 ] && _nsync_push
            return $rc
            ;;
        rm)
            command pass "$@"
            local rc=$?
            [ $rc -eq 0 ] && _nsync_push
            return $rc
            ;;
        *)
            command pass "$@"
            ;;
    esac
}
