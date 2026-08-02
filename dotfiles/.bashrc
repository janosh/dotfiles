#!/bin/bash
# Cluster/HPC shell. Not linked by macOS setup; copy with aliases.sh + gh-failover.sh.

# === Options ===
shopt -s autocd # https://gnu.org/software/bash/manual/html_node/The-Shopt-Builtin
set show-all-if-ambiguous on # https://coderwall.com/p/oqtj8w/the-single-most-useful-thing-in-bash
set completion-ignore-case on
export LANG=C # https://stackoverflow.com/a/2510548

# === Prompt ===
parse_git_branch() {
  git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ \1/'
}
# \[\033[32m\] green, \[\033[33m\] yellow, \[\033[34m\] blue, \[\033[00m\] reset
export PS1="\[\033[34m\]\h \[\033[32m\]\w\[\033[33m\]\$(parse_git_branch)\[\033[00m\]$ "

# === History ===
shopt -s histappend # write history immediately; survives ssh drops. https://askubuntu.com/a/67306
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"

# === Key bindings ===
if [[ $- == *i* ]]; then # https://superuser.com/a/686293
  bind '"\e[A": history-search-backward' # https://unix.stackexchange.com/a/20830
  bind '"\e[B": history-search-forward'
  bind '"\eOA": history-search-backward'
  bind '"\eOB": history-search-forward'
  bind '"\e\e[D": backward-word'
  bind '"\e\e[C": forward-word'
fi

# === Shared aliases / gp failover (realpath follows symlinks) ===
_dotfiles_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
# shellcheck disable=SC1091
. "${_dotfiles_dir}/aliases.sh"
# shellcheck disable=SC1091
. "${_dotfiles_dir}/gh-failover.sh"
unset _dotfiles_dir

# === SLURM ===
alias sq="squeue --me --format '%18i %10P %28j %8T %8M %9l %6D'" # https://slurm.schedmd.com/squeue.html
alias sacctx="sacct --allocations --format jobid,JobName%25,elapsed,state,reqmem"
