#!/usr/bin/env zsh

# Where the setup scripts come from when this one was piped into `zsh -c` and there is no
# checkout on disk. Override to bootstrap from a fork or a branch:
#   DOTFILES_RAW_BASE=.../janosh/dotfiles/some-branch/setup zsh -c "$(curl -sSL ...)"
readonly RAW_BASE="${DOTFILES_RAW_BASE:-https://raw.githubusercontent.com/janosh/dotfiles/main/setup}"

# %x is this script's own path, which is empty when the body arrived over a pipe rather
# than as a file. PWD covers being run from the repo root or from inside setup/.
setup_dir=
for dir in "${${(%):-%x}:A:h}" "${PWD}/setup" "${PWD}"; do
  [[ -f "${dir}/1-setup.sh" ]] && setup_dir=${dir} && break
done

# Fetching into a variable rather than `source <(curl ...)`: process substitution hands
# source an empty file on a failed download, which would look like an empty script and
# only surface later as "command not found" for every function it should have defined.
load_setup() {
  if [[ -n ${setup_dir} ]]; then
    source "${setup_dir}/${1}"
    return
  fi
  local body
  if ! body=$(curl -fsSL "${RAW_BASE}/${1}"); then
    print -u2 "setup: could not fetch ${1} from ${RAW_BASE}"
    exit 1
  fi
  eval "${body}"
}

install() {
  # Source all install scripts.
  load_setup 1-setup.sh
  load_setup 2-apps.sh
  load_setup 3-config.sh
  load_setup 4-cleanup.sh

  ask_details
  # update_system # takes too long, do manually

  brew_install

  configure_zsh
  configure_git
  configure_macos

  brew cleanup
  cleanup_error_log
  final_message
}

# Run and log errors to file (but still show them when they happen).
readonly ERROR_LOG="${HOME}/Desktop/install_errors.log"
install 2>&1 | tee "${ERROR_LOG}"
