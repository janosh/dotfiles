# Deduplicate PATH: each entry below is prepended once per interactive shell.
typeset -U PATH path

# === Prompt (robbyrussell-style, no Oh My Zsh) ===
autoload -U colors && colors
setopt prompt_subst
_git_prompt() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return
  local ref dirty
  ref=$(git symbolic-ref --short HEAD 2>/dev/null) \
    || ref=$(git rev-parse --short HEAD 2>/dev/null) \
    || return
  [[ -n $(git status --porcelain --ignore-submodules=dirty 2>/dev/null) ]] && dirty=1
  print -n "%{$fg_bold[blue]%}git:(%{$fg[red]%}${ref//\%/%%}%{$fg[blue]%})"
  (( dirty )) && print -n " %{$fg[yellow]%}%1{✗%}"
  print -n "%{$reset_color%} "
}
PROMPT="%(?:%{$fg_bold[green]%}%1{➜%} :%{$fg_bold[red]%}%1{➜%} ) %{$fg[cyan]%}%c%{$reset_color%} \$(_git_prompt)"

# If input is not a command but matches a directory name, cd into it (bash: shopt -s autocd)
setopt autocd

# === Completion (OMZ-equivalent tweaks) ===
zmodload -i zsh/complist
WORDCHARS=''
unsetopt menu_complete flowcontrol
setopt auto_menu complete_in_word always_to_end
zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' matcher-list 'm:{[:lower:][:upper:]}={[:upper:][:lower:]}' 'r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' special-dirs true
zstyle ':completion:*' use-cache yes
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME:-$HOME/.cache}/zsh/completions"
zstyle ':completion:*:cd:*' tag-order local-directories directory-stack path-directories
mkdir -p "${XDG_CACHE_HOME:-$HOME/.cache}/zsh/completions"
autoload -Uz compinit && compinit
autoload -U +X bashcompinit && bashcompinit

# Shared py314 venv (no per-project .venv). Export VIRTUAL_ENV so `uv run` reuses it
# instead of a bare uv-managed interpreter. Check -x on python, not -d on the dir:
# a brew Python upgrade can leave a dangling symlink (see notes/to-self.md).
if [[ -x ~/.venv/py314/bin/python ]]; then
  export VIRTUAL_ENV="$HOME/.venv/py314"
  export PATH="$VIRTUAL_ENV/bin:$PATH"
fi
# shellcheck disable=SC1091
[[ -f "$HOME"/.local/bin/env ]] && . "$HOME"/.local/bin/env

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
# `git push` (gp) and `gh pr create` with automatic gh-account failover:
# on a permission error, retry across all other `gh auth` logins.
_gh_failover() {
  emulate -L zsh
  setopt no_multios  # else `1>&3` alongside the pipe makes zsh duplicate stdout
  local tmp; tmp=$(mktemp) || { "$@"; return $?; }
  # GitHub masks 403 as 404 on private repos so as not to leak their existence, so an
  # unauthorized account reports "Repository not found" and never looks like a denial.
  local perm_re='permission|403|denied|authentication failed|repository not found'
  local -i ret  # not `status`: that name is read-only in zsh (mirrors $?)
  # run cmd with stdout/stdin on the tty, stderr shown live AND captured for inspection
  { "$@" 2>&1 1>&3 | tee "$tmp" >&2; ret=${pipestatus[1]}; } 3>&1
  if (( ret != 0 )) && grep -qiE "$perm_re" "$tmp"; then
    local auth; auth=$(command gh auth status 2>/dev/null)
    local active; active=$(print -r -- "$auth" | awk '/account /{u=$0;sub(/.*account /,"",u);sub(/ .*/,"",u)} /Active account: true/{print u; exit}')
    local -a accts; accts=("${(@f)$(print -r -- "$auth" | sed -nE 's/.*account ([^ ]+).*/\1/p')}")
    local acct
    for acct in $accts; do
      [[ -z $acct || $acct == $active ]] && continue
      print -r -u2 -- "🔑 gh: '${active:-?}' denied — retrying as '$acct'…"
      command gh auth switch --user "$acct" >/dev/null 2>&1 || continue
      { "$@" 2>&1 1>&3 | tee "$tmp" >&2; ret=${pipestatus[1]}; } 3>&1
      (( ret == 0 )) && break
      grep -qiE "$perm_re" "$tmp" || break  # different error -> stop retrying
    done
  fi
  rm -f "$tmp"
  return $ret
}
# Credential helper for github.com/gist is set in git/config (gh, not osxkeychain).
gp() { _gh_failover git push "$@"; }
gh() {
  if [[ $1 == pr && $2 == create ]]; then
    _gh_failover command gh "$@"
  else
    command gh "$@"
  fi
}
alias gb='git branch'
alias gsw='git switch'
alias gcp='git cherry-pick'
alias gco='git checkout'
alias gm='git merge'
alias grb='git rebase'
alias glog='git log --oneline'
# Rank repo files by net lines added over git history.
# Resolve repo via ~/.zshrc symlink. --no-project + unset UV_FROZEN: stdlib-only script
# must not sync a .venv from the cwd's pyproject (UV_FROZEN warns without a project).
glines() {
  local repo=${${functions_source[glines]}:A:h:h}
  env -u UV_FROZEN uv run --no-project "${repo}/scripts/git_line_rank.py" "$@"
}
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

alias path='echo "${PATH//:/\n}"'
alias pt='pytest'
alias pip='uv pip'
alias code='cursor'

# Source brew-installed zsh plugins (syntax-highlighting last).
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
# shellcheck disable=SC1091,SC1094
. /opt/homebrew/share/zsh-history-substring-search/zsh-history-substring-search.zsh
# shellcheck disable=SC1094,SC1091
. /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# https://github.com/zsh-users/zsh-autosuggestions/issues/351
ZSH_AUTOSUGGEST_CLEAR_WIDGETS+=(bracketed-paste)

export PATH="$HOME/.cargo/bin:$PATH"
export UV_FROZEN=1 # equiv to --frozen, prevent uv from automatically updating the uv.lock file
export PNPM_CONFIG_LOCKFILE=false # don't read or write pnpm-lock.yaml

# Option+←/→/Delete word motion (Terminal "Use Option as Meta key"). bindkey -e:
# emacs mode already has ^[b/^[f/^[^?; these are the terminal-specific sequences.
bindkey -e
() {
  local seq
  for seq in '\e\e[D' '\e\eOD' '^[[1;3D' '^[[1;9D'; do bindkey "$seq" backward-word; done
  for seq in '\e\e[C' '\e\eOC' '^[[1;3C' '^[[1;9C'; do bindkey "$seq" forward-word; done
}
bindkey '^[[3;3~' kill-word
bindkey '^U' backward-kill-line # Cmd+Delete (Terminal sends Ctrl+U)
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
[[ -n $terminfo[kcuu1] ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
[[ -n $terminfo[kcud1] ]] && bindkey "$terminfo[kcud1]" history-substring-search-down

# Vite+ bin (https://viteplus.dev)
. "$HOME/.vite-plus/env"
