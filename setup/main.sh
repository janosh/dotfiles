#!/usr/bin/env zsh

# Override to bootstrap from a fork:
#   DOTFILES_REPO=https://github.com/me/dotfiles.git zsh -c "$(curl -fsSL ...)"
readonly DOTFILES_REPO="${DOTFILES_REPO:-https://github.com/janosh/dotfiles.git}"
# Canonical checkout path used when bootstrapping via curl (no local clone yet).
: "${DOTFILES_DIR:=${HOME}/dev/dotfiles}"
# :A makes it absolute. A relative path would resolve against the wrong directory
# once we cd into the checkout.
DOTFILES_DIR=${DOTFILES_DIR:A}

# %x is this script's own path, which is empty when the body arrived over a pipe rather
# than as a file. PWD covers being run from the repo root or from inside setup/.
setup_dir=
for dir in "${${(%):-%x}:A:h}" "${PWD}/setup" "${PWD}"; do
  [[ -f "${dir}/1-setup.sh" ]] && setup_dir=${dir} && break
done

# Prefer an existing local checkout; otherwise clone to ~/dev/dotfiles so Brewfile
# and symlinks have a real tree to work from (curl-piped main.sh has no files on disk).
ensure_dotfiles_checkout() {
  if [[ -n ${setup_dir} ]]; then
    DOTFILES_DIR=${setup_dir:h}
  else
    # On a pristine Mac /usr/bin/git is only a stub that prompts to install the
    # Command Line Tools, so there is nothing to clone with until those exist.
    if ! xcode-select -p &> /dev/null; then
      xcode-select --install
      print -u2 'setup: finish the Command Line Tools install, then run this again.'
      exit 1
    fi

    mkdir -p "${DOTFILES_DIR:h}"
    if [[ -d "${DOTFILES_DIR}/.git" ]]; then
      git -C "${DOTFILES_DIR}" pull --ff-only || exit 1
    else
      git clone "${DOTFILES_REPO}" "${DOTFILES_DIR}" || exit 1
    fi
    setup_dir="${DOTFILES_DIR}/setup"
  fi
  export DOTFILES_DIR
}

install() {
  ensure_dotfiles_checkout
  cd "${DOTFILES_DIR}" || exit 1

  # The numbered scripts define functions only, so source them all before running any.
  for script in 1-setup.sh 2-apps.sh 3-config.sh; do
    source "${setup_dir}/${script}" || exit 1
  done

  ask_details

  brew_install
  brew_bundle_checklist
  gh_auth_login

  link_dotfiles
  configure_agents
  configure_login_items
  configure_macos

  brew cleanup
  sed -i '' -E '/^Password: /d;/#.*%/d;/\* \[new/d;/Cloning into/d;/Execute post install script?/d' "${ERROR_LOG}"
  echo "All automated scripts have finished. 'stderr' has been logged to '${ERROR_LOG}'."
}

# Run and log errors to file (but still show them when they happen).
readonly ERROR_LOG="${HOME}/Desktop/install_errors.log"
install 2>&1 | tee "${ERROR_LOG}"
# Without this the script always reports tee's status, hiding a failed install.
exit "${pipestatus[1]}"
