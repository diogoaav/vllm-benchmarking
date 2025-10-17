#!/bin/bash

# Update package lists
sudo apt-get update

# Step 1 install docker
curl -fsSL https://get.docker.com | sudo sh


# Install necessary packages
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git

sudo apt install unzip

# Set up Python environment
curl https://pyenv.run | bash

# Append pyenv config to ~/.bashrc if not already present
if ! grep -q 'pyenv init' ~/.bashrc; then
  {
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"'
    echo 'eval "$(pyenv init --path)"'
    echo 'eval "$(pyenv init -)"'
    echo 'eval "$(pyenv virtualenv-init -)"'
  } >> ~/.bashrc
fi
