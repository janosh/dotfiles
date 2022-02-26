#!/bin/sh

# --- Helper functions ---

trap 'exit 0' SIGINT # exit cleanly if aborted with ⌃c

request() { # Output a message and open an app.
  local message="${1}"
  local app="${2}"
  shift 2

  echo "$(tput setaf 5)•$(tput sgr0) ${message}"
  open -Wa "${app}" --args "$@" # Don't continue until app closes.
}

request_preferences() { # 'request' for System Preferences.
  request "${1}" 'System Preferences'
}

preferences_pane() { # Open 'System Preferences' in specified pane.
  osascript -e "tell application \"System Preferences\"
    reveal pane \"${1}\"
    activate
  end tell" &> /dev/null
}

preferences_pane_anchor() { # Open 'System Preferences' in specified pane and tab.
  osascript -e "tell application \"System Preferences\"
    reveal anchor \"${1}\" of pane \"${2}\"
    activate
  end tell" &> /dev/null
}

set_file_association() {
  defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSHandlers -array-add \
  "{LSHandlerContentType=${1};LSHandlerRoleAll=${2};}"
}

# Initial message when starting the script.
echo "After running the main install script, this script will help configure the rest of macOS. It is divided into two parts:

  - Commands that will change settings without needing intervention.
  - Commands that will require manual interaction.

  The 1st part will simply report what it is doing.

  The 2nd part will open the appropriate panels/apps, inform what needs to be done, and pause.
  Unless prefixed with the message 'ALL TABS', all changes can be performed in the opened tab.
  After the changes are done, close the app and the script will continue.
" | sed -E 's/ {2}//'

# Ask for 'sudo' authentication.
if sudo --non-interactive true 2> /dev/null; then
  read -r -s -n0 -p "$(tput bold)Some commands require 'sudo', but it seems you have already authenticated. When you’re ready to continue, press ↵.$(tput sgr0)"
  echo
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

echo '- Disable the prompt "Are you sure you want to open this application?".'
defaults write com.apple.LaunchServices/com.apple.launchservices.secure LSQuaratine -bool false

echo '- Disable the Gatekeeper prompt "{appname} cannot be opened because it is from an unidentified developer".'
sudo spctl --master-disable

echo '- Prevent Gatekeeper from re-enabling itself after 30 days.'
# Changes System Preferences > Security & Privacy > General > Allow apps downloaded from.
sudo defaults write /Library/Preferences/com.apple.security GKAutoRearm -bool false

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
set_file_association public.mpeg-4 org.videolan.vlc
set_file_association public.html com.google.chrome
# /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework\
# /Versions/A/Support/lsregister -kill -r -domain local -domain system -domain user

echo 'Customize VLC settings'
# Ensure the settings file exists (not created on install but on launch)
# by calling vlc with an invalid value for the interface option.
# Does nothing except create and populate the file
# ~/Library/Preferences/org.videolan.vlc/vlcrc
vlc -I none
echo '- Enable dark mode.'
sed -i '' -E 's/#?macosx-interfacestyle=0/macosx-interfacestyle=1/' ~/Library/Preferences/org.videolan.vlc/vlcrc
echo '- Disable icon changes (like Christmas icon).'
sed -i '' -E 's/#?macosx-icon-change=1/macosx-icon-change=0/' ~/Library/Preferences/org.videolan.vlc/vlcrc
# use sed with double quotes for variable replacement and pipe as separator
# since variable contains forward slashes (https://askubuntu.com/a/508174)
echo '- Set ~/Desktop as snapshot save location.'
sed -i '' -E "s|#?snapshot-path=.*|snapshot-path=$HOME/Desktop/|" ~/Library/Preferences/org.videolan.vlc/vlcrc
echo '- Set JPG as snapshot file type.'
sed -i '' -E 's/#?snapshot-format=.*/snapshot-format=jpg/' ~/Library/Preferences/org.videolan.vlc/vlcrc

echo 'Install iTerm dynamic profile.'
# All the settings in 'Keyboard Map' correspond to the 'Natural Text Editing' preset.
mkdir -p ~/Library/Application\ Support/iTerm2/DynamicProfiles
ln -f dotfiles/iterm-profile.json ~/Library/Application\ Support/iTerm2/DynamicProfiles
echo '- Make custom profile the default.'
defaults write com.googlecode.iterm2 "Default Bookmark Guid" "73964F77-3452-4112-BE05-8A8F1ED9B50D"

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

# --- 2nd part ---
# Find values for System Preferences by opening the desired pane and running the following AppleScript:
# tell application "System Preferences" to return anchors of current pane

echo

# Auto-close any open System Preferences panes, to prevent them from
# overriding settings we’re about to change
osascript -e 'tell application "System Preferences" to quit'

preferences_pane 'com.apple.preferences.Bluetooth'
request_preferences 'Add Bluetooth peripherals and show Bluetooth in menu bar.'

preferences_pane 'com.apple.preference.trackpad'
request_preferences 'Set Trackpad preferences.'

preferences_pane 'com.apple.preference.mouse'
request_preferences 'Set Mouse preferences.'

preferences_pane_anchor 'Mouse' 'com.apple.preference.universalaccess'
request_preferences 'Under "Trackpad Options…", enable three finger drag.'

preferences_pane_anchor 'Dictation' 'com.apple.preference.keyboard'
request_preferences 'Download other languages.'

preferences_pane 'com.apple.preferences.AppleIDPrefPane'
request_preferences "Check what you want synced to iCloud."

preferences_pane 'com.apple.preferences.internetaccounts'
request_preferences 'Remove Game Center.'

preferences_pane 'com.apple.preferences.users'
request_preferences 'Turn off Guest User account.'

preferences_pane 'com.apple.preference.printfax'
request_preferences 'Add printers.'

preferences_pane 'com.apple.preference.security'
request_preferences 'Set delay after sleep before prompting for password on wake.'

echo 'Setup NPM publishing without one-time passwords.'
read -r NPM_TOKEN'?Enter your NPM publish token (see 1Password): '
echo "//registry.npmjs.org/:_authToken=$NPM_TOKEN" >> ~/.npmrc
