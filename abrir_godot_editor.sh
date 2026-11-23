#!/usr/bin/env bash
# Abre o projeto do Trabalho 2 no editor do Godot
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/ferramentas/Godot_v4.7.2-stable_linux.x86_64" --editor --path "$DIR/Trabalho2-Jogo"
