#!/bin/bash

brew_install() {
  renew_sudo

  # Install Homebrew if missing.
  if ! command -v brew > /dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi

  # Add brew command to current and future shell sessions.
  eval "$(/opt/homebrew/bin/brew shellenv)"
  # shellcheck disable=SC2016
  grep -qF 'brew shellenv' ~/.zprofile 2> /dev/null ||
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile

  brew bundle --file="${DOTFILES_DIR}/Brewfile"

  # Standalone installers, not brew: a brew-managed uv ties venvs to brew's Python, which
  # has broken them on upgrade before (see notes/to-self.md).
  curl -LsSf https://astral.sh/uv/install.sh | sh
  curl -LsSf https://github.com/j178/prek/releases/latest/download/prek-installer.sh | sh

  # Default virtualenv that .zshrc activates and agents/AGENTS.md points agents at.
  # --managed-python: uv's own interpreter, so brew upgrades can't invalidate it.
  [[ -d ~/.venv/py314 ]] ||
    ~/.local/bin/uv venv --managed-python --python 3.14 ~/.venv/py314
}

# Report Brewfile entries that did not install and why they usually don't.
brew_bundle_checklist() {
  local output
  if output=$(brew bundle check --verbose --file="${DOTFILES_DIR}/Brewfile" 2>&1); then
    echo 'All Brewfile dependencies are installed.'
    return
  fi

  # Missing entries are listed as '→ ...'. Anything else means the check itself failed.
  echo 'Some Brewfile dependencies did not install:'
  grep '^→' <<< "${output}" || echo "${output}"

  [[ ${output} == *'→ Cask'* ]] &&
    echo "Casks that ship a .pkg run 'sudo installer', which needs a password typed at a terminal."
  [[ ${output} == *'→ App'* ]] &&
    echo 'App Store apps need you signed in: open App Store.app and sign in, then retry.'

  echo "Retry with: brew bundle --file='${DOTFILES_DIR}/Brewfile'"
}

gh_auth_login() {
  if ! command -v gh > /dev/null || gh auth status > /dev/null 2>&1; then
    echo 'Skipping GitHub login (gh not installed or already authenticated).'
    return
  fi

  # Browser-based device flow. Also sets git's credential helper to gh.
  gh auth login --hostname github.com --git-protocol https --web
}
