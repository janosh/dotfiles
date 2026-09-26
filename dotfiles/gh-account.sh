# shellcheck shell=bash

# HTTPS github.com push/pull authenticate as the active gh account, which may lack access.
# Try each logged-in account, advancing only on auth errors so other failures fail fast.
_gh_git() {
  local subcommand=$1
  shift
  # not `status`: zsh reserves it as a read-only alias for $?
  local logins='' login token log exit_code=0
  case "$(command git remote get-url origin 2>/dev/null)" in
    # SSH and non-GitHub remotes never use gh tokens. Active account first.
    https://github.com/*) logins=$(command gh auth status --json hosts --jq \
      '.hosts."github.com" // [] | sort_by(.active | not) | .[].login' 2>/dev/null) ;;
  esac
  if [ -z "$logins" ]; then
    command git "$subcommand" "$@"
    return
  fi
  log=$(mktemp)
  while IFS= read -r login; do
    token=$(command gh auth token --user "$login" 2>/dev/null) || continue
    GH_TOKEN=$token command git "$subcommand" "$@" 2>&1 | tee "$log"
    # zsh pipestatus is 1-based and unset in bash, which falls back to 0-based PIPESTATUS
    exit_code=${pipestatus[1]-${PIPESTATUS[0]}}
    [ "$exit_code" -eq 0 ] && break
    # GitHub hides inaccessible private repositories behind a 404.
    grep -qE 'denied to|403|Authentication failed|Repository not found' "$log" || break
    printf 'git %s failed as %s, retrying as the next account\n' "$subcommand" "$login" >&2
  done <<EOF
$logins
EOF
  rm -f "$log"
  return "$exit_code"
}

gp() { _gh_git push "$@"; }
gl() { _gh_git pull "$@"; }

gh() {
  local account remote_url token
  if [ "$1" = pr ] && [ "$2" = create ]; then
    # `|| remote_url=`: no origin must not abort a `set -e` caller.
    remote_url=$(git remote get-url origin 2>/dev/null) || remote_url=
    case "$remote_url" in
      git@github-janosh:*) account=janosh ;;
      git@github-janosh-per:*) account=janosh_per ;;
      # No SSH alias to read the account from: use gh's active account.
      *) command gh "$@"; return ;;
    esac
    token=$(command gh auth token --user "$account") || return
    GH_TOKEN=$token command gh "$@"
    return
  fi
  command gh "$@"
}
