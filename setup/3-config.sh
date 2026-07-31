#!/bin/bash

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

link_dotfiles() {
  # -sf: force replace existing file/symlink.
  ln -sf "${DOTFILES_DIR}/dotfiles/.zshrc" ~/.zshrc

  mkdir -p ~/.config/git
  ln -sf "${DOTFILES_DIR}/dotfiles/git/global-ignore" ~/.config/git/ignore
  ln -sf "${DOTFILES_DIR}/dotfiles/git/global-attributes" ~/.config/git/attributes
  ln -sf "${DOTFILES_DIR}/dotfiles/git/config" ~/.gitconfig
}

set_file_association() {
  defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add \
    "{LSHandlerContentType=${1};LSHandlerRoleAll=${2};}"
}

# Write the same key to built-in and Bluetooth trackpad domains.
write_trackpad() {
  defaults write com.apple.AppleMultitouchTrackpad "$@"
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad "$@"
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
  write_trackpad Clicking -bool true
  defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
  defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

  echo '- Trackpad: map bottom right corner to right-click.'
  write_trackpad TrackpadCornerSecondaryClick -int 2
  write_trackpad TrackpadRightClick -bool true
  defaults -currentHost write NSGlobalDomain com.apple.trackpad.trackpadCornerClickBehavior -int 1
  defaults -currentHost write NSGlobalDomain com.apple.trackpad.enableSecondaryClick -bool true

  echo '- Trackpad: three-finger drag (clears conflicting drag/swipe gestures).'
  write_trackpad TrackpadThreeFingerDrag -bool true
  write_trackpad Dragging -bool false
  write_trackpad DragLock -bool false
  write_trackpad TrackpadThreeFingerHorizSwipeGesture -int 0
  write_trackpad TrackpadThreeFingerVertSwipeGesture -int 0

  echo '- Show Bluetooth in the menu bar; require password immediately on wake.'
  defaults -currentHost write com.apple.controlcenter Bluetooth -int 18
  defaults write com.apple.screensaver askForPassword -int 1
  defaults write com.apple.screensaver askForPasswordDelay -int 0

  echo '- Disable the Guest User account.'
  sudo sysadminctl -guestAccount off

  echo '- Enable Touch ID for sudo (via update-safe sudo_local, not sudo itself).'
  # Template ships on Sonoma+; without it (or a prior sudo_local) there is nothing to edit.
  if [[ ! -f /etc/pam.d/sudo_local ]]; then
    if [[ ! -f /etc/pam.d/sudo_local.template ]]; then
      echo '  skipped: /etc/pam.d/sudo_local.template missing (macOS Sonoma+ required).'
    elif ! sudo cp /etc/pam.d/sudo_local.template /etc/pam.d/sudo_local; then
      echo '  failed: could not create /etc/pam.d/sudo_local from template.'
    fi
  fi
  if [[ -f /etc/pam.d/sudo_local ]]; then
    sudo sed -i '' 's/^#auth/auth/' /etc/pam.d/sudo_local
  fi

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

  echo '- Finder: open folders in new windows, not tabs.'
  defaults write com.apple.finder FinderSpawnTab -bool false
  defaults write com.apple.finder AppleWindowTabbingMode -string manual

  echo '- Avoid creating .DS_Store files on network or USB volumes.'
  defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
  defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

  echo '- Disable disk image verification.'
  defaults write com.apple.frameworks.diskimages skip-verify -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true

  echo '- Dock: hide recents; keep Spaces in fixed order.'
  defaults write com.apple.dock show-recents -bool false
  defaults write com.apple.dock mru-spaces -bool false

  echo '- Disable click wallpaper to show desktop (Sonoma+).'
  defaults write com.apple.WindowManager EnableStandardClickToShowDesktop -bool false

  echo '- Copy email addresses as foo@bar.com instead of Foo Bar <foo@bar.com> in Mail.app.'
  defaults write com.apple.mail AddressesIncludeNameOnPasteboard -bool false

  echo '- Disable inline mail attachments (just show the icons).'
  defaults write com.apple.mail DisableInlineAttachmentViewing -bool true

  echo '- Use columns view in all Finder windows by default.'
  # Four-letter codes for the other view modes: 'icnv', 'Nlsv', 'Flwv'
  defaults write com.apple.finder FXPreferredViewStyle -string 'clmv'

  echo '- Screenshots: save to Downloads, no window shadow, no floating thumbnail.'
  defaults write com.apple.screencapture location -string "${HOME}/Downloads"
  defaults write com.apple.screencapture disable-shadow -bool true
  defaults write com.apple.screencapture show-thumbnail -bool false

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

  echo 'Disable hot corners.'
  for corner in tl tr br bl; do
    defaults write com.apple.dock "wvous-$corner-corner" -int 0
  done

  echo '- Disable power chime on connecting to power.'
  defaults write com.apple.PowerChime ChimeOnNoHardware -bool true
  killall PowerChime

  # Restart UI agents so defaults take effect (three-finger drag may still need logout).
  killall Dock Finder ControlCenter 2> /dev/null || true

  echo '- Disable Homebrew analytics.'
  brew analytics off

  echo 'Disable PNPM writing lockfiles.'
  pnpm config --global set lockfile false

  echo 'Disable the PNPM minimum release age gate.'
  # pnpm 11 defaults minimumReleaseAge to 1440 min; `pnpm config --global set` writes a
  # legacy rc that pnpm 11 ignores, so write config.yaml directly. Repo-local values win.
  pnpm_config="${HOME}/Library/Preferences/pnpm/config.yaml"
  mkdir -p "$(dirname "${pnpm_config}")"
  grep -q '^minimumReleaseAge:' "${pnpm_config}" 2> /dev/null ||
    echo 'minimumReleaseAge: 0' >> "${pnpm_config}"

  # Run (don't source): system-settings.sh traps SIGINT; sourcing would abort setup on ⌃c.
  "${DOTFILES_DIR}/setup/system-settings.sh"
}
