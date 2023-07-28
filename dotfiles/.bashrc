#!/bin/bash

# NERSC bash config

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

# ls options: -l: long format
# -h: human-readable file size
# -A: show hidden files but not ..
alias l='ls -lhA'
# list queued SLURM jobs (docs at https://slurm.schedmd.com/squeue.html)
alias sq="squeue --me --format '%18i %10P %28j %8T %8M %9l %6D'"
# multiple stats about running and passed SLURM jobs in table form
# (includes jobs since midnight today by default, use -S MMDD to specify other dates)
# --allocations: only show statistics relevant to the job itself, not taking steps into consideration.
alias sacctx="sacct --allocations --format jobid,JobName%25,elapsed,state,reqmem"
# show remaining computation budget
alias path='printf "%s\n" ${PATH//:/ }'

# if no command specified and shell input is name of a directory, assume cd
# https://gnu.org/software/bash/manual/html_node/The-Shopt-Builtin
shopt -s autocd
# https://coderwall.com/p/oqtj8w/the-single-most-useful-thing-in-bash
set show-all-if-ambiguous on
set completion-ignore-case on

# activate virtualenv
# shellcheck disable=SC1090
module load python/3.11 > /dev/null 2>&1
. ~/.venv/py311/bin/activate

# shell prompt (PS1 = prompt string 1)
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ \1/'
}
# color codes affect the text following them
# \[\033[32m\] = green
# \[\033[33m\] = yellow
# \[\033[34m\] = blue
# \[\033[00m\] = white
export PS1="\[\033[34m\]\h \[\033[32m\]\w\[\033[33m\]\$(parse_git_branch)\[\033[00m\]$ "
export LANG=C  # https://stackoverflow.com/a/2510548

# add commands to history immediately, not when shell closes https://askubuntu.com/a/67306
# shell may crash or ssh drops out, leading to lost commands
shopt -s histappend
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"

# VASP config see https://gist.github.com/janosh/a484f3842b600b60cd575440e99455c0#benchmarking
export OMP_NUM_THREADS="1"

# atomate2 config
export ATOMATE2_CONFIG_FILE=/global/homes/j/janosh/matpes/config/atomate2.yaml
export JOBFLOW_CONFIG_FILE=/global/homes/j/janosh/matpes/config/jobflow.yaml
export FW_CONFIG_FILE=/global/homes/j/janosh/matpes/fireworks_config/gpu/FW_config.yaml
# add bader executable to path
export PATH=$PATH:/global/homes/j/janosh/matpes

# https://superuser.com/a/686293 (see link in 2nd comment)
if [[ $- == *i* ]]; then  # check if running in interactive shell that supports line editing

    # For interactive shells, enable key bindings for up/down arrow search through history
    # from https://unix.stackexchange.com/a/20830
    bind '"\e[A": history-search-backward'
    bind '"\e[B": history-search-forward'
    bind '"\eOA": history-search-backward'
    bind '"\eOB": history-search-forward'

    # enable alt + right/left arrow to move one word
    bind '"\e\e[D": backward-word'
    bind '"\e\e[C": forward-word'
fi

qlaunch_rf() {
    pushd /global/cfs/projectdirs/matgen/janosh/ > /dev/null || exit
    qlaunch rapidfire "$@"
    popd > /dev/null || exit
}
