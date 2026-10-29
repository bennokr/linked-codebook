#!/bin/sh
# Rewrites the expected output of every conformance case with the TypeScript command line.
# Review the diff before committing: the files are the specification by example.
set -e
for dir in conformance/*/*/; do
  command=$(basename "$(dirname "$dir")")
  files=$(cd "$dir" && ls in* | sort)
  code=0
  (cd "$dir" && node ../../../packages/ts/src/bin.ts "$command" $files) > "$dir/out" || code=$?
  rm -f "$dir/code"
  [ "$code" = 0 ] || echo "$code" > "$dir/code"
done
