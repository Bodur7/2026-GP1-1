#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print 'Set up .venv as described in README_PIPELINE.md first.'
  exit 1
fi
exec ./.venv/bin/python ./manual_testing/pipeline_app.py "$@"
