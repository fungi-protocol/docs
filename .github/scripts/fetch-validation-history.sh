#!/usr/bin/env bash

set -euo pipefail

base=${1:?Usage: fetch-validation-history.sh <base-sha>}
head=$(git rev-parse HEAD)

if ! git cat-file -e "$base^{commit}" 2>/dev/null; then
  git fetch --no-tags --depth=1 origin "$base"
fi

base=$(git rev-parse "$base^{commit}")
shallow_file=$(git rev-parse --git-path shallow)

# Deepening is needed until no range commit can reach $base through unfetched history.
range_needs_deepening() {
  [[ -s $shallow_file ]] || return 1

  local roots joins join
  roots=$(git rev-list --max-parents=0 "$base..$head") || exit "$?"
  [[ -z $roots ]] || return 0

  joins=$(git rev-list --boundary "$base..$head" | sed -n 's/^-//p') || exit "$?"
  for join in $joins; do
    roots=$(git rev-list --max-parents=0 "$base" --not "$join") || exit "$?"
    [[ -z $roots ]] || return 0
  done
  return 1
}

deepen=8
while range_needs_deepening; do
  git fetch --no-tags --deepen="$deepen" origin "$head" "$base"
  deepen=$((deepen * 2))
done
