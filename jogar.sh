#!/usr/bin/env bash
# Abre o jogo do Trabalho 2 (Kart das Moedas)
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/ferramentas/Godot_v4.7.2-stable_linux.x86_64" --path "$DIR/Trabalho2-Jogo"
