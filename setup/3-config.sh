#!/bin/bash

configure_agents() {
  local dev_dir agents_md cursor_skills repo dest skill
  dev_dir=$(dirname "${DOTFILES_DIR}")
  agents_md="${DOTFILES_DIR}/agents/AGENTS.md"
  cursor_skills="${DOTFILES_DIR}/.cursor/skills"

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

  # Cursor discovers repo skills at .cursor/skills; keep the source in agents/skills.
  mkdir -p "${DOTFILES_DIR}/.cursor" ~/.cursor
  ln -sfn "../agents/skills" "${cursor_skills}"
  ln -sfn "${cursor_skills}" ~/.cursor/skills

  # Codex and Claude Code read global skills from separate directories but share
  # the SKILL.md format, so the same skill dirs can be linked into both.
  for dest in ~/.agents/skills ~/.claude/skills; do
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

# Sync Keyboard text replacements (defaults + KeyboardServices DB; DB wins on Tahoe).
configure_text_replacements() {
  echo '- Keyboard: sync text replacements.'
  python3 - "${DOTFILES_DIR}/dotfiles/text-replacements.json" <<'PY'
import json, plistlib, sqlite3, subprocess, sys, time, uuid
from pathlib import Path
repls = json.loads(Path(sys.argv[1]).read_text())
tmp = Path("/tmp/tr-import.plist")
tmp.write_bytes(plistlib.dumps({"NSUserDictionaryReplacementItems": [
  {"on": 1, "replace": k, "with": v} for k, v in repls.items()]}))
subprocess.check_call(["defaults", "import", "-g", str(tmp)]); tmp.unlink()
ts = time.time() - 978307200  # CFAbsoluteTime
with sqlite3.connect(Path.home() / "Library/KeyboardServices/TextReplacements.db") as con:
  con.execute(f"DELETE FROM ZTEXTREPLACEMENTENTRY WHERE ZSHORTCUT IN ({','.join('?' * len(repls))})", tuple(repls))
  pk0 = con.execute("SELECT IFNULL(MAX(Z_PK), 0) FROM ZTEXTREPLACEMENTENTRY").fetchone()[0]
  rows = [(pk0 + i, 1, 1, 1, 0, ts, v, k, str(uuid.uuid4()).upper(), None) for i, (k, v) in enumerate(repls.items(), 1)]
  con.executemany("INSERT INTO ZTEXTREPLACEMENTENTRY VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
  con.execute("UPDATE Z_PRIMARYKEY SET Z_MAX = ? WHERE Z_ENT = 1", (pk0 + len(rows),))
subprocess.call(["killall", "keyboardservicesd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
PY
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

  # More options at https://github.com/mathiasbynens/dotfiles/blob/main/.macos.

  # === Terminal ===
  echo '- Terminal: use the dark Pro profile for startup and new windows.'
  defaults write com.apple.Terminal 'Default Window Settings' -string 'Pro'
  defaults write com.apple.Terminal 'Startup Window Settings' -string 'Pro'

  # === General UI ===
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

  configure_text_replacements

  echo '- Disable Resume after reboot system-wide.'
  defaults write com.apple.systempreferences NSQuitAlwaysKeepsWindows -bool false

  echo '- Prevent Safari from auto-opening "safe" files after download.'
  defaults write com.apple.Safari AutoOpenSafeDownloads -bool false

  echo '- Set Help Viewer windows to non-floating mode.'
  defaults write com.apple.helpviewer DevMode -bool true

  echo '- Enable full keyboard access for all controls (Tab in modal dialogs).'
  defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

  echo '- Set languages and metric units.'
  defaults write NSGlobalDomain AppleLanguages -array "en_US" "de_DE"
  defaults write NSGlobalDomain AppleMetricUnits -bool true

  echo '- Show language menu in the top right corner of the boot screen.'
  sudo defaults write /Library/Preferences/com.apple.loginwindow showInputMenu -bool true

  # === Trackpad ===
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

  # Four-finger vertical swipe: down = App Exposé, up = Mission Control. Three-finger
  # vert is 0 above so four-finger wins. Dock flags gate whether each action runs.
  echo '- Trackpad: four-finger swipe down for App Exposé (up for Mission Control).'
  write_trackpad TrackpadFourFingerVertSwipeGesture -int 2
  defaults -currentHost write NSGlobalDomain com.apple.trackpad.fourFingerVertSwipeGesture -int 2
  defaults write com.apple.dock showAppExposeGestureEnabled -bool true
  defaults write com.apple.dock showMissionControlGestureEnabled -bool true

  # === Security / accounts ===
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

  # === Finder ===
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

  echo '- Use columns view in all Finder windows by default.'
  # Other view modes: 'icnv', 'Nlsv', 'Flwv'
  defaults write com.apple.finder FXPreferredViewStyle -string 'clmv'

  echo '- Avoid creating .DS_Store files on network or USB volumes.'
  defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
  defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

  echo '- Disable disk image verification.'
  defaults write com.apple.frameworks.diskimages skip-verify -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true
  defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true

  # === Dock / desktop ===
  echo '- Dock: hide recents; keep Spaces in fixed order.'
  defaults write com.apple.dock show-recents -bool false
  defaults write com.apple.dock mru-spaces -bool false

  echo '- Disable click wallpaper to show desktop (Sonoma+).'
  defaults write com.apple.WindowManager EnableStandardClickToShowDesktop -bool false

  echo 'Disable hot corners.'
  for corner in tl tr br bl; do
    defaults write com.apple.dock "wvous-$corner-corner" -int 0
  done

  # === Mail / screenshots ===
  echo '- Copy email addresses as foo@bar.com instead of Foo Bar <foo@bar.com> in Mail.app.'
  defaults write com.apple.mail AddressesIncludeNameOnPasteboard -bool false

  echo '- Disable inline mail attachments (just show the icons).'
  defaults write com.apple.mail DisableInlineAttachmentViewing -bool true

  echo '- Screenshots: save to Downloads, no window shadow, no floating thumbnail.'
  defaults write com.apple.screencapture location -string "${HOME}/Downloads"
  defaults write com.apple.screencapture disable-shadow -bool true
  defaults write com.apple.screencapture show-thumbnail -bool false

  # === Launch Services ===
  echo '- Disable the "Are you sure you want to open this application?" dialog.'
  defaults write com.apple.LaunchServices LSQuarantine -bool false

  # File associations (requires restart). https://apple.stackexchange.com/a/123834
  # Cursor's CFBundleIdentifier; matches `alias code=cursor` in .zshrc.
  set_file_association net.daringfireball.markdown com.todesktop.230313mzl4w4u92
  set_file_association public.plain-text com.todesktop.230313mzl4w4u92
  set_file_association public.html com.brave.Browser

  echo '- Disable power chime on connecting to power.'
  defaults write com.apple.PowerChime ChimeOnNoHardware -bool true
  killall PowerChime

  # Restart UI agents so defaults take effect (three-finger drag may still need logout).
  killall Dock Finder ControlCenter 2> /dev/null || true

  # === Tooling ===
  echo '- Disable Homebrew analytics.'
  brew analytics off

  echo '- Fix brew share perms so zsh compinit does not warn about insecure directories.'
  # https://docs.brew.sh/Shell-Completion#configuring-completions-in-zsh
  [[ -d /opt/homebrew/share ]] && chmod go-w /opt/homebrew/share
  [[ -d /opt/homebrew/share/zsh ]] && chmod -R go-w /opt/homebrew/share/zsh

  echo '- Disable PNPM lockfiles and the minimum release age gate.'
  # pnpm 11 ignores `pnpm config --global set` (legacy rc); write config.yaml it reads.
  # Repo-local values still win. Interactive shells also set PNPM_CONFIG_LOCKFILE in .zshrc.
  pnpm_config="${HOME}/Library/Preferences/pnpm/config.yaml"
  mkdir -p "$(dirname "${pnpm_config}")"
  grep -q '^lockfile:' "${pnpm_config}" 2> /dev/null || echo 'lockfile: false' >> "${pnpm_config}"
  grep -q '^minimumReleaseAge:' "${pnpm_config}" 2> /dev/null ||
    echo 'minimumReleaseAge: 0' >> "${pnpm_config}"

  # Run (don't source): system-settings.sh traps SIGINT; sourcing would abort setup on ⌃c.
  "${DOTFILES_DIR}/setup/system-settings.sh"
}
