#!/bin/bash

# Guided manual steps in System Settings (macOS Ventura+).
# Opens each pane via x-apple.systempreferences URL, then waits until System Settings is closed.

trap 'exit 0' SIGINT # exit cleanly if aborted with ⌃c

request_settings() { # Print a prompt, open a System Settings pane, wait until the app quits.
  local message=$1 pane=$2

  echo "$(tput setaf 5)•$(tput sgr0) ${message}"
  open "x-apple.systempreferences:${pane}"
  open -Wa 'System Settings'
}

# Close any already-open System Settings so pane opens are not overridden.
osascript -e 'tell application "System Settings" to quit' &> /dev/null

echo 'This script requires manual interaction. It opens one System Settings pane at a time and
says what to change. Close the app when done and the script continues with the next pane.
'

request_settings 'Add Bluetooth peripherals and show Bluetooth in menu bar.' com.apple.BluetoothSettings
request_settings 'Set Trackpad preferences.' com.apple.Trackpad-Settings.extension
request_settings 'Set Mouse preferences.' com.apple.Mouse-Settings.extension
request_settings 'Enable three finger drag under Pointer Control → Trackpad Options….' com.apple.Accessibility-Settings.extension
request_settings 'Download other languages under Dictation.' com.apple.Keyboard-Settings.extension
request_settings 'Check what you want synced to iCloud.' com.apple.systempreferences.AppleIDSettings
request_settings 'Sign out of Game Center if unused.' com.apple.Game-Center-Settings.extension
request_settings 'Turn off Guest User account.' com.apple.Users-Groups-Settings.extension
request_settings 'Add printers.' com.apple.Print-Scan-Settings.extension
request_settings 'Set delay after sleep before prompting for password on wake.' com.apple.Lock-Screen-Settings.extension
