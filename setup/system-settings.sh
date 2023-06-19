#!/bin/bash

# --- Helper functions ---

trap 'exit 0' SIGINT # exit cleanly if aborted with ⌃c

request() { # Output a message and open an app.
  local message="${1}"
  local app="${2}"
  shift 2

  echo "$(tput setaf 5)•$(tput sgr0) ${message}"
  open -Wa "${app}" --args "$@" # Don't continue until app closes.
}

request_preferences() { # 'request' for System Preferences.
  request "${1}" 'System Preferences'
}

preferences_pane() { # Open 'System Preferences' in specified pane.
  osascript -e "tell application \"System Preferences\"
    reveal pane \"${1}\"
    activate
  end tell" &> /dev/null
}

preferences_pane_anchor() { # Open 'System Preferences' in specified pane and tab.
  osascript -e "tell application \"System Preferences\"
    reveal anchor \"${1}\" of pane \"${2}\"
    activate
  end tell" &> /dev/null
}

# Auto-close any open System Preferences panes, to prevent them from
# overriding settings we’re about to change
osascript -e 'tell application "System Preferences" to quit'

# --- Main script ---
echo "This scripts requires manual interaction. It opens the appropriate System Settings panels, informs what needs to be done, and pauses until System Settings is closed.
  Unless prefixed with the message 'ALL TABS', all changes can be performed in the opened tab.
  After the changes are done, close the app and the script will continue.
" | sed -E 's/ {2}//'

preferences_pane 'com.apple.preferences.Bluetooth'
request_preferences 'Add Bluetooth peripherals and show Bluetooth in menu bar.'

preferences_pane 'com.apple.preference.trackpad'
request_preferences 'Set Trackpad preferences.'

preferences_pane 'com.apple.preference.mouse'
request_preferences 'Set Mouse preferences.'

preferences_pane_anchor 'Mouse' 'com.apple.preference.universalaccess'
request_preferences 'Under "Trackpad Options…", enable three finger drag.'

preferences_pane_anchor 'Dictation' 'com.apple.preference.keyboard'
request_preferences 'Download other languages.'

preferences_pane 'com.apple.preferences.AppleIDPrefPane'
request_preferences "Check what you want synced to iCloud."

preferences_pane 'com.apple.preferences.internetaccounts'
request_preferences 'Remove Game Center.'

preferences_pane 'com.apple.preferences.users'
request_preferences 'Turn off Guest User account.'

preferences_pane 'com.apple.preference.printfax'
request_preferences 'Add printers.'

preferences_pane 'com.apple.preference.security'
request_preferences 'Set delay after sleep before prompting for password on wake.'
