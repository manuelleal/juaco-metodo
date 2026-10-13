#!/bin/sh
# Lanzador portable de guardia.py (hook PreToolUse de Claude Code): python3 en Linux/macOS, python en Windows + Git Bash.
# exec conserva el stdin del hook y el código de salida (2 = bloquear).
F="$(dirname "$0")/guardia.py"
if command -v python3 >/dev/null 2>&1 && python3 -c "" >/dev/null 2>&1; then
  exec python3 "$F"
fi
exec python "$F"
