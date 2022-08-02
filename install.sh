#!/bin/bash

install() {
  # Source all install scripts.
  source setup-steps/1-setup.sh
  source setup-steps/2-apps.sh
  source setup-steps/3-config.sh
  source setup-steps/4-cleanup.sh

  caffeinate & # Prevent computer from going to sleep during setup.
  ask_details
  update_system

  brew_install

  configure_zsh
  configure_git
  symlink_custom_scripts
  configure_ssh

  brew cleanup
  cleanup_error_log
  killall caffeinate # Allow computer to go back to sleep.
  final_message
}

# Run and log errors to file (but still show them when they happen).
readonly ERROR_LOG="${HOME}/Desktop/install_errors.log"
install 2>&1 | tee "${ERROR_LOG}"
