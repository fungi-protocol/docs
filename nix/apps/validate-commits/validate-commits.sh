#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: validate-commits <revision-range>"
}

if [[ ${1:-} == --help ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

repo_root=$(git rev-parse --show-toplevel)
revision_range=$1
commits=$(git rev-list --reverse "$revision_range")

if [[ -z $commits ]]; then
  echo "No commits in range."
  exit 0
fi

while read -r commit; do
  echo "Validating $commit"
  nix flake check --no-update-lock-file --print-build-logs \
    "git+file://$repo_root?rev=$commit&shallow=1"
done <<<"$commits"
