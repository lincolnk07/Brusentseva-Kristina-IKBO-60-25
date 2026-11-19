#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <practice-base-commit> <end-commit>" >&2
    exit 2
fi

base_commit=$1
end_commit=$2
git rev-parse --verify "$base_commit^{commit}" >/dev/null
git rev-parse --verify "$end_commit^{commit}" >/dev/null

if ! git merge-base --is-ancestor "$base_commit" "$end_commit"; then
    echo "The practice base must be an ancestor of the end commit." >&2
    exit 2
fi

failures=0
while IFS= read -r subject; do
    if ! printf '%s\n' "$subject" | awk '
        /^(feat|fix|docs|test|refactor|chore|style|build|ci|perf)\([a-z0-9][a-z0-9._-]*\): .+/ {
            valid = 1
        }
        END { exit !valid }
    '; then
        echo "Invalid scoped commit: $subject" >&2
        failures=1
    fi
done <<EOF_MESSAGES
$(git log --format=%s --reverse "$base_commit..$end_commit")
EOF_MESSAGES

if [ "$failures" -ne 0 ]; then
    exit 1
fi

echo "All commits after $base_commit follow Scoped Conventional Commits."
