# Deduplicate PATH: each entry below is prepended once per interactive shell.
typeset -U PATH path

# === Options ===
setopt autocd prompt_subst

# Start Apple Terminal in ~/dev without overriding an explicitly inherited directory.
if [[ $TERM_PROGRAM == Apple_Terminal && $PWD == $HOME && -d $HOME/dev ]]; then
  cd "$HOME/dev"
fi

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
unsetopt flowcontrol
setopt complete_in_word always_to_end
zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' matcher-list 'm:{[:lower:][:upper:]}={[:upper:][:lower:]}' 'r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' special-dirs true
zstyle ':completion:*' use-cache yes
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME:-$HOME/.cache}/zsh/completions"
zstyle ':completion:*:cd:*' tag-order local-directories directory-stack path-directories
# On fpath before compinit. configure_macos chmods /opt/homebrew/share (compinit insecure-dir warn).
[[ -d /opt/homebrew/share/zsh-completions ]] && fpath=(/opt/homebrew/share/zsh-completions $fpath)
autoload -Uz compinit && compinit

# === Environment ===
# Shared py314 venv. Check -x on python: brew upgrades can leave a dangling symlink.
if [[ -x ~/.venv/py314/bin/python ]]; then
  export VIRTUAL_ENV="$HOME/.venv/py314"
  export PATH="$VIRTUAL_ENV/bin:$PATH"
fi
export PATH="$HOME/.cargo/bin:$PATH"
# No lock files in repos: uv refuses lock writes and skips .venv sync on `uv run`;
# pnpm writes none, overriding repo config.
export UV_FROZEN=1
export UV_NO_SYNC=1
export PNPM_CONFIG_LOCKFILE=false
[[ -f "$HOME"/.local/bin/env ]] && . "$HOME"/.local/bin/env
[[ -r "$HOME/.vite-plus/env" ]] && . "$HOME/.vite-plus/env" # https://viteplus.dev

# === Plugins (syntax-highlighting last) ===
HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1
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
bindkey '^U' backward-kill-line # delete to start of line
if (( $+functions[history-substring-search-up] )); then
  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down
  [[ -n $terminfo[kcuu1] ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
  [[ -n $terminfo[kcud1] ]] && bindkey "$terminfo[kcud1]" history-substring-search-down
fi

# === Shared aliases / gh account selection ===
_dotfiles_dir=${${(%):-%x}:A:h} # :A follows ~/.zshrc symlink
. "${_dotfiles_dir}/aliases.sh"
. "${_dotfiles_dir}/gh-account.sh"
unset _dotfiles_dir

# Rank files by net lines added. --no-project: stdlib script, no cwd project sync/lock.
gdiff() {
  local repo=${${functions_source[gdiff]}:A:h:h}
  env -u UV_FROZEN -u UV_NO_SYNC uv run --no-project "${repo}/scripts/gdiff.py" "$@"
}

# Delete gone-upstream, GitHub-merged and pr/* branches (with their clean worktrees) and non-origin remotes.
grcl() {
  local branch head remote
  local -a gh_merged remotes

  git fetch --prune

  _grcl_delete gone ${(f)"$(git for-each-ref --format='%(refname:short)%09%(upstream:track)' refs/heads |
    awk -F'\t' '$2 == "[gone]" {print $1}')"}

  for branch in ${(f)"$(git for-each-ref --format='%(refname:short)' refs/heads)"}; do
    [[ $branch == (main|master) ]] && continue
    head=$(gh pr list --state merged --head "$branch" --json headRefOid -q '.[0].headRefOid' 2>/dev/null)
    [[ -z $head ]] && continue
    # Squash merges leave the PR head off main, so compare the branch tip with it instead.
    if git cat-file -e "$head^{commit}" 2>/dev/null && git merge-base --is-ancestor "refs/heads/$branch" "$head"; then
      gh_merged+=("$branch")
    else
      echo "Kept $branch: its tip is not part of its merged PR's head ${head:0:9}"
    fi
  done
  _grcl_delete GitHub-merged $gh_merged

  _grcl_delete PR ${(f)"$(git for-each-ref --format='%(refname:short)' 'refs/heads/pr/*')"}

  remotes=(${(f)"$(git remote | grep -vx origin)"})
  for remote in $remotes; do git remote remove "$remote"; done
  (( $#remotes )) || echo "No remotes to remove"
}

# Usage: _grcl_delete <label> <branch>... `git worktree remove` refuses dirty worktrees and the
# primary checkout, so branches checked out there are kept. It does delete ignored files (.env,
# tmp/, ...), so those are listed first.
_grcl_delete() {
  local label=$1 branch ignored worktree here=${$(git rev-parse --show-toplevel):A}
  shift
  (( $# )) || { echo "No $label branches to delete"; return; }
  for branch; do
    worktree=$(git worktree list --porcelain |
      awk -v ref="branch refs/heads/$branch" '/^worktree /{path = substr($0, 10)} $0 == ref {print path}')
    if [[ -n $worktree && ${worktree:A} != $here ]]; then
      ignored=$(git -C "$worktree" ls-files --others --ignored --exclude-standard --directory)
      [[ -n $ignored ]] && print -rl -- "Ignored files in $worktree:" ${${(f)ignored}/#/  }
    fi
    # Never remove the worktree grcl runs in: every later git call would fail.
    if [[ -n $worktree ]] && { [[ ${worktree:A} == $here ]] || ! git worktree remove "$worktree"; }; then
      echo "Kept $branch: checked out in $worktree"
      continue
    fi
    git branch -D -- "$branch"
  done
}
