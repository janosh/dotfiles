# Add deno completions to search path
if [[ ":$FPATH:" != *":/Users/janosh/completions:"* ]]; then export FPATH="/Users/janosh/completions:$FPATH"; fi
# Set zsh theme to load.
# https://github.com/robbyrussell/oh-my-zsh/wiki/Themes
export ZSH_THEME="robbyrussell"

# shellcheck disable=SC1090
source ~/.oh-my-zsh/oh-my-zsh.sh

# --- User Configuration ---

# activate default virtualenv
# shellcheck disable=SC1090
source ~/.venv/py313/bin/activate
# shellcheck disable=SC1091
. "$HOME"/.local/bin/env

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
alias gcp='git cherry-pick'
alias gco='git checkout'
alias gm='git merge'
alias grb='git rebase'
alias glog='git log --oneline'
# Clean stale branches and non-origin remotes.
# shellcheck disable=SC2086
grcl() {
  local branch gone gh_merged prs remotes

  git fetch --prune

  gone=$(git branch -vv | awk '/: gone]/{print $1}')
  [ -n "$gone" ] && git branch -D $gone || echo "No gone branches to delete"

  for branch in $(git branch --format='%(refname:short)' | grep -vE '^(main|master)$'); do
    gh pr list --state merged --head "$branch" --json number -q '.[0]' 2>/dev/null | grep -q . && gh_merged="$gh_merged $branch"
  done
  [ -n "$gh_merged" ] && git branch -D $gh_merged || echo "No GitHub-merged branches to delete"

  prs=$(git branch --format='%(refname:short)' | grep '^pr/')
  [ -n "$prs" ] && git branch -D $prs || echo "No PR branches to delete"

  remotes=$(git remote | grep -vx origin)
  [ -n "$remotes" ] && for remote in $remotes; do git remote remove "$remote"; done || echo "No remotes to remove"
}

alias dt='deno task'
alias path='echo "${PATH//:/\n}"'
alias ssh="ssh -F ~/.ssh/config"  # https://stackoverflow.com/a/63935109
alias pt='pytest'
alias pip='uv pip'
alias code='cursor'

# Source brew-installed zsh plugins.
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
# shellcheck disable=SC1091,SC1094
. /opt/homebrew/share/zsh-history-substring-search/zsh-history-substring-search.zsh
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# https://github.com/zsh-users/zsh-autosuggestions/issues/351
ZSH_AUTOSUGGEST_CLEAR_WIDGETS+=(bracketed-paste)

. "/Users/janosh/.deno/env"
# Initialize zsh completions (added by deno install script)
autoload -Uz compinit
compinit
export PATH="$HOME/.cargo/bin:$PATH"
export UV_FROZEN=1 # equiv to --frozen, prevent uv from automatically updating the uv.lock file
alias pwt='pnpm playwright test'
alias pvt='pnpm vitest'

# Alt + arrow keys for word navigation
bindkey "^[[1;3C" forward-word      # Alt + Right Arrow
bindkey "^[[1;3D" backward-word     # Alt + Left Arrow
# Alternative bindings (if the above don't work)
bindkey "^[^[[C" forward-word       # Alt + Right Arrow (alternative)
bindkey "^[^[[D" backward-word      # Alt + Left Arrow (alternative)

# Cmd + Backspace to delete whole line
bindkey "^U" backward-kill-line
