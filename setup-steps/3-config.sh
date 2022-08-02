#!/bin/bash

configure_zsh() {
  # Link .zshrc from dotfiles to home directory.
  # -f: Overwrite config if already exists.
  ln -f dotfiles/.zshrc ~

  # Install Oh My Zsh.
  sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
}

configure_git() {
  # Hard-link global gitignore file into default location.
  mkdir -p ~/.config/git
  ln -f dotfiles/git/global-ignore ~/.config/git/ignore
  ln -f dotfiles/git/global-attributes ~/.config/git/attributes

  # Hard-link git config into home directory.
  ln -f dotfiles/git/config ~/.gitconfig
}

configure_ssh() {
  mkdir -p ~/.ssh
  ln -f dotfiles/ssh_config ~/.ssh/config
}
