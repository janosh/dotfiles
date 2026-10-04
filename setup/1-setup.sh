#!/usr/bin/env zsh
# zsh, not bash: ask_details uses zsh's `read VAR'?prompt'` form below

renew_sudo() { # Keep sudo ticket alive using the password captured in ask_details.
  sudo --stdin --validate <<< "${SUDO_PASSWORD}" 2> /dev/null
}

ask_details() {
  # Ask for the sudo password upfront unless SUDO_PASSWORD is already set.
  if [ -z "$SUDO_PASSWORD" ]; then
    echo "$(tput bold)Provide sudo password (will not be echoed).$(tput sgr0)"
    until sudo --non-interactive true 2> /dev/null; do # If password is wrong, keep asking.
      read -r -s SUDO_PASSWORD'?Password: '
      echo
      renew_sudo
    done
  fi

  # Lost-device lock screen message, unless one is already set.
  if ! defaults read /Library/Preferences/com.apple.loginwindow LoginwindowText &> /dev/null; then
    echo
    echo "$(tput bold)User details (for lost device message lock screen):$(tput sgr0)"
    read -r FULLNAME'?Full name: '
    read -r EMAIL'?Email: '
    read -r PHONE'?Phone number: '

    sudo --stdin defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText \
      "This machine belongs to ${FULLNAME}. If lost and found, contact ${EMAIL} or ${PHONE}." \
      <<< "${SUDO_PASSWORD}" 2> /dev/null
  fi
}
