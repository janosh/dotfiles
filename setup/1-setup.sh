#!/bin/bash

bold_echo() { # Helper function for bold text.
  echo "$(tput bold)${1}$(tput sgr0)"
}

renew_sudo() { # Helper function used whenever the ensuing command needs `sudo`.
  sudo --stdin --validate <<< "${SUDO_PASSWORD}" 2> /dev/null
}

ask_details() {
  # check that SUDO_PASSWORD is not already set
  if [ -n "$SUDO_PASSWORD" ]; then
    # Ask for the administrator password upfront (to run commands that require `sudo`).
    bold_echo 'Provide sudo password (will not be echoed).'
    until sudo --non-interactive true 2> /dev/null; do # If password is wrong, keep asking.
      read -r -s SUDO_PASSWORD'?Password: '
      echo
      renew_sudo
    done
  fi

  # only set LoginwindowText if read excits non-zero (meaning not set yet)
  if defaults read /Library/Preferences/com.apple.loginwindow LoginwindowText &> /dev/null; then
    echo
    bold_echo 'User details (for lost device message lock screen):'
    read -r FULLNAME'?Full name: '
    read -r EMAIL'?Email: '
    read -r PHONE'?Phone number: '

    sudo --stdin defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText \
      "This machine belongs to ${FULLNAME}. If lost and found, contact ${EMAIL} or ${PHONE}." \
      <<< "${SUDO_PASSWORD}" 2> /dev/null
  fi
}

update_system() {
  softwareupdate --install --all
  xcode-select --install
}
