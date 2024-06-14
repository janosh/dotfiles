# Set zsh theme to load.
# https://github.com/robbyrussell/oh-my-zsh/wiki/Themes
export ZSH_THEME="robbyrussell"

# shellcheck disable=SC1090
source ~/.oh-my-zsh/oh-my-zsh.sh

# --- User Configuration ---

# activate default virtualenv
# shellcheck disable=SC1090
source ~/.venv/py312/bin/activate

alias ga='git add'
alias gc='git commit'
alias gca='git commit --amend'
alias gcan='git commit --amend --no-edit'
alias gt='git tag'
alias gst='git stash'
alias gl='git pull'
alias gf='git fetch'
alias gr='git remote'
alias grv='git remote -v'
alias gp='git push'
alias gb='git branch'
alias gsw='git switch'
alias gco='git checkout'
alias gm='git merge'
alias grb='git rebase'
alias glog='git log --oneline'
alias grcl='git branch -D $(git branch | grep "pr/") && git remote | grep -v origin | xargs -n 1 git remote remove && git fetch --prune'

alias path='echo "${PATH//:/\n}"'
alias ssh="ssh -F ~/.ssh/config"  # https://stackoverflow.com/a/63935109
alias pt='pytest'
alias pip='uv pip'

# Source brew-installed zsh plugins.
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
# shellcheck disable=SC1091,SC1094
. /opt/homebrew/share/zsh-history-substring-search/zsh-history-substring-search.zsh
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# https://github.com/zsh-users/zsh-autosuggestions/issues/351
ZSH_AUTOSUGGEST_CLEAR_WIDGETS+=(bracketed-paste)
