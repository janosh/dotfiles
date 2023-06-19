#!/bin/bash

cleanup_error_log() {
  sed -i '' -E '/^Password: /d;/#.*%/d;/\* \[new/d;/Cloning into/d;/Execute post install script?/d' "${ERROR_LOG}"
}

final_message() {
  echo "All automated scripts have finished. 'stderr' has been logged to '${ERROR_LOG}'."
  echo "Remaining manual step: Run './system-settings.sh'."
}
