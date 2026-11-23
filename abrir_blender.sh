#!/usr/bin/env bash
# Abre o modelo do Trabalho 1 no Blender
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/ferramentas/blender-4.5.16-linux-x64/blender" "$DIR/Trabalho1-Modelagem/kart.blend"
