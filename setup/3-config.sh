#!/bin/bash

configure_zsh() {
  # Install Oh My Zsh first so it does not overwrite our linked .zshrc.
  # KEEP_ZSHRC: never replace an existing .zshrc. RUNZSH/CHSH: don't start a
  # subshell or prompt for a login shell change mid-script.
  if [[ ! -d "${HOME}/.oh-my-zsh" ]]; then
    KEEP_ZSHRC=yes RUNZSH=no CHSH=no \
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
  fi

  # Symlink .zshrc from dotfiles to home directory.
  # -sf: force replace existing file/symlink.
  ln -sf "${DOTFILES_DIR}/dotfiles/.zshrc" ~/.zshrc
}

configure_agents() {
  local dev_dir agents_md repo dest skill
  dev_dir=$(dirname "${DOTFILES_DIR}")
  agents_md="${DOTFILES_DIR}/agents/AGENTS.md"

  # Codex and Claude Code inherit AGENTS.md up the directory tree, so one link at the
  # common parent of all repos covers them.
  ln -sfn "${agents_md}" "${dev_dir}/AGENTS.md"

  # Cursor does not walk up past the workspace root, so every repo needs its own link.
  # Repos that ship their own AGENTS.md are left alone.
  # -e "${repo}.git": worktrees and submodules have a .git file, not a directory.
  # -L on the target as well: -e alone is false for a dangling link, and ln would fail.
  for repo in "${dev_dir}"/*/; do
    if [[ -e "${repo}.git" && ! -e "${repo}AGENTS.md" && ! -L "${repo}AGENTS.md" ]]; then
      ln -s "${agents_md}" "${repo}AGENTS.md"
    fi
  done

  # Cursor, Codex and Claude Code read global skills from separate directories but share
  # the SKILL.md format, so the same skill dirs can be linked into all three.
  for dest in ~/.cursor/skills ~/.agents/skills ~/.claude/skills; do
    mkdir -p "${dest}"
    for skill in "${DOTFILES_DIR}"/agents/skills/*/; do
      skill=${skill%/} # glob leaves a trailing slash, strip it to get the skill name
      # -n: replace an existing skill symlink instead of linking inside the dir it points to.
      ln -sfn "${skill}" "${dest}/${skill##*/}"
    done
  done
}

configure_login_items() {
  # Rectangle/Maccy need login items; SMAppService has no CLI, so System Events
  # (prompts once for Automation access).
  local app_name app_path
  for app_name in Rectangle Maccy; do
    app_path="/Applications/${app_name}.app"
    if [[ ! -d "${app_path}" ]]; then
      echo "- Skipping ${app_name} login item, not installed at ${app_path}."
      continue
    fi
    echo "- Adding ${app_name} to login items."
    osascript \
      -e 'tell application "System Events"' \
      -e "if not (exists login item \"${app_name}\") then" \
      -e "make login item at end with properties {path:\"${app_path}\", hidden:false}" \
      -e 'end if' \
      -e 'end tell' > /dev/null ||
      echo "  failed: grant Automation access to System Events, then rerun."
  done
}

configure_git() {
  # Symlink global gitignore/attributes into default location.
  mkdir -p ~/.config/git
  ln -sf "${DOTFILES_DIR}/dotfiles/git/global-ignore" ~/.config/git/ignore
  ln -sf "${DOTFILES_DIR}/dotfiles/git/global-attributes" ~/.config/git/attributes

  # Symlink git config into home directory.
  ln -sf "${DOTFILES_DIR}/dotfiles/git/config" ~/.gitconfig
}

set_file_association() {
  # helper function to set file association based on extension
  defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add \
  "{LSHandlerContentType=${1};LSHandlerRoleAll=${2};}"
}

configure_macos() {
  echo "This function configures macOS defaults."

  # Ask for 'sudo' authentication.
  if sudo --non-interactive true 2> /dev/null; then
    # Plain `read` only: this file is sourced by zsh, whose read has no -n/-p.
    echo -n "$(tput bold)Some commands require 'sudo', but it seems you have already authenticated. When you’re ready to continue, press ↵.$(tput sgr0)"
    read -r _
  else
    echo -n "$(tput bold)When you’re ready to continue, insert your password. This is done upfront for the commands that require 'sudo'.$(tput sgr0) "
    sudo --validate
  fi

  # --- 1st part ---
  # More options at https://github.com/mathiasbynens/dotfiles/blob/main/.macos.

  echo '- Expand save panel by default.'
  defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
  defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

  echo '- Expand print panel by default.'
  defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
  defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

  echo '- Automatically quit printer app once the print jobs complete.'
  defaults write com.apple.print.PrintingPrefs "Quit When Finished" -bool true

  echo '- Save to disk (not to iCloud) by default.'
  defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false

  echo '- Disable smart quotes.'
  defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false

  echo '- Disable Resume after reboot system-wide.'
  defaults write com.apple.systempreferences NSQuitAlwaysKeepsWindows -bool false

  echo '- Prevent Safari from auto-opening "safe" files after download.'
  defaults write com.apple.Safari AutoOpenSafeDownloads -bool false

  echo '- Set Help Viewer windows to non-floating mode.'
  defaults write com.apple.helpviewer DevMode -bool true

  echo '- Enable full keyboard access for all controls. In particular, enable Tab in modal dialogs.'
  defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

  echo '- Trackpad: enable tap to click for this user and for the login screen.'
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
  defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
  defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

  echo '- Trackpad: map bottom right corner to right-click.'
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadCornerSecondaryClick -int 2
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadRightClick -bool true
  defaults -currentHost write NSGlobalDomain com.apple.trackpad.trackpadCornerClickBehavior -int 1
  defaults -currentHost write NSGlobalDomain com.apple.trackpad.enableSecondaryClick -bool true

  echo '- Set Home as the default location for new Finder windows.'
  defaults write com.apple.finder NewWindowTarget -string 'PfLo'
  defaults write com.apple.finder NewWindowTargetPath -string "file://${HOME}/"

  echo '- Show all filename extensions in Finder.'
  defaults write NSGlobalDomain AppleShowAllExtensions -bool true

  echo '- Disable the warning when changing a file extension.'
  defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false

  echo '- In Finder searches, search the current folder by default.'
  defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

  echo '- Show path bar at bottom edge of Finder windows.'
  defaults write com.apple.finder ShowPathbar -bool true

  echo '- Avoid creating .DS_Store files on network or USB volumes.'
  defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
  defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

  echo '- Disable disk image verification.'
  defaults write com.apple.frameworks.diskimages skip-verify -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true

  echo '- Do not show recent applications in Dock.'
  defaults write com.apple.dock show-recents -bool false

  echo '- Copy email addresses as foo@bar.com instead of Foo Bar <foo@bar.com> in Mail.app.'
  defaults write com.apple.mail AddressesIncludeNameOnPasteboard -bool false

  echo '- Disable inline mail attachments (just show the icons).'
  defaults write com.apple.mail DisableInlineAttachmentViewing -bool true

  echo '- Use columns view in all Finder windows by default.'
  # Four-letter codes for the other view modes: 'icnv', 'Nlsv', 'Flwv'
  defaults write com.apple.finder FXPreferredViewStyle -string 'clmv'

  echo '- Disable box shadow around screenshots of windows.'
  defaults write com.apple.screencapture disable-shadow -bool true

  echo '- Disable showing screenshots as floating thumbnails before saving as file.'
  defaults write com.apple.screencapture show-thumbnail -bool FALSE

  echo '- Set languages and metric units.'
  defaults write NSGlobalDomain AppleLanguages -array "en_US" "de_DE"
  defaults write NSGlobalDomain AppleMetricUnits -bool true

  echo '- Show language menu in the top right corner of the boot screen.'
  sudo defaults write /Library/Preferences/com.apple.loginwindow showInputMenu -bool true

  echo '- Disable the "Are you sure you want to open this application?" dialog.'
  defaults write com.apple.LaunchServices LSQuarantine -bool false

  # Change default file associations (requires restart).
  # See https://apple.stackexchange.com/a/123834.
  set_file_association net.daringfireball.markdown com.microsoft.vscode
  set_file_association public.plain-text com.microsoft.vscode
  set_file_association public.html com.brave.Browser
  # /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework\
  # /Versions/A/Support/lsregister -kill -r -domain local -domain system -domain user

  echo 'Disable hot corners.'
  for corner in tl tr br bl; do
    defaults write com.apple.dock "wvous-$corner-corner" -int 0
  done

  echo '- Disable power chime (the sound effect on connecting to power source).'
  defaults write com.apple.PowerChime ChimeOnNoHardware -bool true
  killall PowerChime
  # use following command to re-enable:
  # defaults write com.apple.PowerChime ChimeOnAllHardware -bool true
  # open /System/Library/CoreServices/PowerChime.app &

  # restart Dock and Finder for above 'defaults write' changes to take effect.
  killall Dock Finder

  echo 'Disable PNPM writing lockfiles.'
  pnpm config --global set lockfile false

  echo 'Disable the PNPM minimum release age gate.'
  # pnpm 11 defaults minimumReleaseAge to 1440 min, refusing to resolve any release
  # younger than a day. `pnpm config --global set` writes a legacy rc file that pnpm 11
  # no longer reads, so write the config file it does read. Repos that set the value
  # themselves (e.g. hardened work monorepos) still win over this.
  pnpm_config="${HOME}/Library/Preferences/pnpm/config.yaml"
  mkdir -p "$(dirname "${pnpm_config}")"
  grep -q '^minimumReleaseAge:' "${pnpm_config}" 2> /dev/null ||
    echo 'minimumReleaseAge: 0' >> "${pnpm_config}"

  # Run (don't source) the manual System Settings steps: the script traps SIGINT to
  # exit, which sourcing would leak into this shell and abort the whole setup on ⌃c.
  "${DOTFILES_DIR}/setup/system-settings.sh"
}
