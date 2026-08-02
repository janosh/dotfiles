# Deduplicate PATH: each entry below is prepended once per interactive shell.
typeset -U PATH path

# === Options ===
setopt autocd prompt_subst

# === Prompt (robbyrussell-style) ===
autoload -U colors && colors
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

# === Completion ===
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
# On fpath before compinit. configure_macos chmods /opt/homebrew/share (compinit insecure-dir warn).
[[ -d /opt/homebrew/share/zsh-completions ]] && fpath=(/opt/homebrew/share/zsh-completions $fpath)
autoload -Uz compinit && compinit
autoload -U +X bashcompinit && bashcompinit

# === Environment ===
# Shared py314 venv. Check -x on python: brew upgrades can leave a dangling symlink.
if [[ -x ~/.venv/py314/bin/python ]]; then
  export VIRTUAL_ENV="$HOME/.venv/py314"
  export PATH="$VIRTUAL_ENV/bin:$PATH"
fi
export PATH="$HOME/.cargo/bin:$PATH"
# No uv.lock in repos: refuse lock writes; don't sync a project .venv on `uv run`.
export UV_FROZEN=1
export UV_NO_SYNC=1
export PNPM_CONFIG_LOCKFILE=false
# shellcheck disable=SC1091
[[ -f "$HOME"/.local/bin/env ]] && . "$HOME"/.local/bin/env
[[ -r "$HOME/.vite-plus/env" ]] && . "$HOME/.vite-plus/env" # https://viteplus.dev

# === Plugins (syntax-highlighting last) ===
# shellcheck disable=SC1091,SC1094
for _zsh_plugin in zsh-autosuggestions zsh-history-substring-search zsh-syntax-highlighting; do
  [[ -r /opt/homebrew/share/$_zsh_plugin/$_zsh_plugin.zsh ]] &&
    . /opt/homebrew/share/$_zsh_plugin/$_zsh_plugin.zsh
done
unset _zsh_plugin
ZSH_AUTOSUGGEST_CLEAR_WIDGETS+=(bracketed-paste) # https://github.com/zsh-users/zsh-autosuggestions/issues/351

# === Key bindings ===
bindkey -e # Option as Meta: terminal sequences below (emacs mode already has ^[b/^[f)
() {
  local seq
  for seq in '\e\e[D' '\e\eOD' '^[[1;3D' '^[[1;9D'; do bindkey "$seq" backward-word; done
  for seq in '\e\e[C' '\e\eOC' '^[[1;3C' '^[[1;9C'; do bindkey "$seq" forward-word; done
}
bindkey '^[[3;3~' kill-word
bindkey '^U' backward-kill-line # Cmd+Delete
if (( $+functions[history-substring-search-up] )); then
  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down
  [[ -n $terminfo[kcuu1] ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
  [[ -n $terminfo[kcud1] ]] && bindkey "$terminfo[kcud1]" history-substring-search-down
fi

# === Shared aliases / gp failover ===
_dotfiles_dir=${${(%):-%x}:A:h} # :A follows ~/.zshrc symlink
# shellcheck disable=SC1091
. "${_dotfiles_dir}/aliases.sh"
# shellcheck disable=SC1091
. "${_dotfiles_dir}/gh-failover.sh"
unset _dotfiles_dir

# Rank files by net lines added. --no-project: stdlib script, no cwd project sync/lock.
glines() {
  local repo=${${functions_source[glines]}:A:h:h}
  env -u UV_FROZEN -u UV_NO_SYNC uv run --no-project "${repo}/scripts/git_line_rank.py" "$@"
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
