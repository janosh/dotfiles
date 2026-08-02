# shellcheck shell=bash
# Retry git/gh across gh auth accounts on permission errors.
# GitHub masks 403 as 404 on private repos, so "not found" counts as a denial.

_gh_run() { # tee stdout+stderr into $1; return cmd exit (not tee's)
  local errf=$1 ret; shift
  # Capture pipestatus/PIPESTATUS on the next line; any command in between clears it.
  if [ -n "${ZSH_VERSION:-}" ]; then
    setopt local_options no_multios
    "$@" 2>&1 | tee "$errf" >&2
    # shellcheck disable=SC2154 # zsh pipeline statuses
    ret=${pipestatus[1]}
  else
    "$@" 2>&1 | tee "$errf" >&2
    ret=${PIPESTATUS[0]}
  fi
  return "$ret"
}

_gh_failover() {
  local tmp ret auth active acct
  tmp=$(mktemp) || { "$@"; return $?; }
  local perm_re='permission|403|denied|authentication failed|repository not found'

  _gh_run "$tmp" "$@"
  ret=$?
  if [ "$ret" -ne 0 ] && grep -qiE "$perm_re" "$tmp"; then
    auth=$(command gh auth status 2>/dev/null) || true
    active=$(printf '%s\n' "$auth" | awk '/account /{u=$0;sub(/.*account /,"",u);sub(/ .*/,"",u)} /Active account: true/{print u; exit}')
    for acct in $(printf '%s\n' "$auth" | sed -nE 's/.*account ([^ ]+).*/\1/p'); do
      [ -z "$acct" ] || [ "$acct" = "$active" ] && continue
      printf "🔑 gh: '%s' denied; retrying as '%s'…\n" "${active:-?}" "$acct" >&2
      command gh auth switch --user "$acct" >/dev/null 2>&1 || continue
      _gh_run "$tmp" "$@"
      ret=$?
      [ "$ret" -eq 0 ] && break
      grep -qiE "$perm_re" "$tmp" || break
    done
  fi
  rm -f "$tmp"
  return "$ret"
}

gp() { _gh_failover git push "$@"; }
gh() {
  if [ "$1" = pr ] && [ "$2" = create ]; then
    _gh_failover command gh "$@"
  else
    command gh "$@"
  fi
}
