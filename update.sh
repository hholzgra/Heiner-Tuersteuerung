#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

git fetch --all
git reset --hard origin/main
chmod +x "$SCRIPT_DIR"/update.sh
