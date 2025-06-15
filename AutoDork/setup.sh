#!/bin/bash
# setup.sh: One-click dev setup for AutoDork

set -e

# Check for pyenv
if ! command -v pyenv &>/dev/null; then
  echo "pyenv not found! Install from https://github.com/pyenv/pyenv#installation"
  exit 1
fi

# Install Python 3.12.3 if missing
if ! pyenv versions | grep -q 3.12.3; then
  echo "Installing Python 3.12.3 via pyenv..."
  pyenv install 3.12.3
fi

echo "Setting local Python version to 3.12.3"
pyenv local 3.12.3

echo "Creating virtual environment (.venv)..."
python -m venv .venv
source .venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Done. To activate: source .venv/bin/activate"
