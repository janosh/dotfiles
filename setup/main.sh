#!/bin/bash

install() {
  # Source all install scripts.
  source setup/1-setup.sh
  source setup/2-apps.sh
  source setup/3-config.sh
  source setup/4-cleanup.sh

  ask_details
  # update_system # takes too long, do manually

  brew_install

  configure_macos
  configure_zsh
  configure_git
  configure_ssh

  brew cleanup
  cleanup_error_log
  final_message
}

# Run and log errors to file (but still show them when they happen).
readonly ERROR_LOG="${HOME}/Desktop/install_errors.log"
install 2>&1 | tee "${ERROR_LOG}"
