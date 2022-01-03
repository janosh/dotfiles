#!/bin/sh

bold_echo() { # Helper function for bold text.
  echo "$(tput bold)${1}$(tput sgr0)"
}

renew_sudo() { # Helper function used whenever the ensuing command needs `sudo`.
  sudo --stdin --validate <<< "${SUDO_PASSWORD}" 2> /dev/null
}

ask_details() {
  # Ask for the administrator password upfront (to run commands that require `sudo`).
  bold_echo 'Provide sudo password (will not be echoed).'
  until sudo --non-interactive true 2> /dev/null; do # If password is wrong, keep asking.
    read -r -s SUDO_PASSWORD'?Password: '
    echo
    renew_sudo
  done

  echo
  bold_echo 'User details (for git + who to contact message on lost device lock screen):'
  if [ -f .user-details ]; then
    # parse .user-details as shell script to export environment variables
    # shellcheck disable=SC1091
    source .user-details
    echo "Using cached user details:"
    echo "  Full name: ${FULLNAME}"
    echo "  Email: ${EMAIL}"
    echo "  Github handle: ${GITHUB_HANDLE}"
  else
    echo 'Will be cached in .user-details.'

    read -r FULLNAME'?Your full name: '
    read -r EMAIL'?Your email: '
    read -r GITHUB_HANDLE'?Your Github handle: '
    echo "FULLNAME='${FULLNAME}'" > .user-details
    echo "EMAIL=${EMAIL}" >> .user-details
    echo "GITHUB_HANDLE=${GITHUB_HANDLE}" >> .user-details
  fi

  echo
  bold_echo 'Contact information to display on lock screen if device is lost:'
  echo 'Uses name and email from above.'
  read -r PHONE'?Phone number: '
  sudo --stdin defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText \
    "This machine belongs to ${FULLNAME}. If lost and found, contact ${EMAIL} or ${PHONE}" \
    <<< "${SUDO_PASSWORD}" 2> /dev/null
}

update_system() {
  softwareupdate --install --all
  xcode-select --install
}
