#!/bin/bash

brew_install() {
  renew_sudo

  # Install Homebrew.
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/main.sh)"

  # Add brew command to current and future shell sessions.
  eval "$(/opt/homebrew/bin/brew shellenv)"
  # shellcheck disable=SC2016
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile

  brew bundle
}
