#!/bin/bash

if [ "$IS_DEVCONTAINER" = "True" ]; then
    echo "-- Correcting permission to 1000:1000 for .venv .python .uv_cache folders"
    sudo chown 1000:1000 .venv
    sudo chown 1000:1000 .python
    sudo chown 1000:1000 .uv_cache
fi

echo "-- Installing Python"
uv python install

echo "-- Loading pip"
uv sync

if [ "$IS_DEVCONTAINER" = "True" ]; then
    echo "-- Installing CLI"
    uv run $PROJECT_NAME --install-completion
fi