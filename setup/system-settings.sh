#!/bin/bash

# Human-only System Settings steps. Automatable knobs are in configure_macos().
# Opens each pane, then waits for Enter — no need to quit System Settings between steps.

trap 'exit 0' SIGINT # exit cleanly if aborted with ⌃c

request_settings() { # Print a prompt, open a System Settings pane, wait for Enter.
  echo "$(tput setaf 5)•$(tput sgr0) ${1}"
  open "x-apple.systempreferences:${2}"
  echo -n "  Press ↵ when done… "
  read -r _
}

osascript -e 'tell application "System Settings" to quit' &> /dev/null

echo 'A few setup steps still need you. Each opens a System Settings pane; press ↵
to advance. Everything else is applied automatically by configure_macos.
'

request_settings 'Pair Bluetooth peripherals (menu bar icon is already enabled).' com.apple.BluetoothSettings
request_settings 'Download other languages under Dictation.' com.apple.Keyboard-Settings.extension
request_settings 'Check what you want synced to iCloud.' com.apple.systempreferences.AppleIDSettings
request_settings 'Sign out of Game Center if unused.' com.apple.Game-Center-Settings.extension
request_settings 'Add printers.' com.apple.Print-Scan-Settings.extension

echo 'Manual System Settings steps done.'
