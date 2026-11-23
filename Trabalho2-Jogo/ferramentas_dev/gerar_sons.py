"""Gera os efeitos sonoros do jogo por síntese (numpy) e salva em WAV 16 bits.

O som do motor recebe um bloco 'smpl' com pontos de loop; o Godot lê esse
bloco e toca o arquivo em repetição contínua.
Uso: python3 gerar_sons.py <pasta_de_saida>
"""
import os
import struct
import sys

import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def salvar(nome, sinal, pasta, loop=False):
    sinal = np.clip(sinal, -1, 1)
    dados = (sinal * 32000).astype("<i2").tobytes()
    fmt = struct.pack("<HHIIHH", 1, 1, SR, SR * 2, 2, 16)
    blocos = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    blocos += b"data" + struct.pack("<I", len(dados)) + dados
    if loop:
        n = len(sinal)
        smpl = struct.pack("<9I", 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<6I", 0, 0, 0, n - 1, 0, 0)
        blocos += b"smpl" + struct.pack("<I", len(smpl)) + smpl
    with open(os.path.join(pasta, nome), "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 4 + len(blocos)) + b"WAVE" + blocos)


def t(dur):
    return np.arange(int(SR * dur)) / SR


def envelope(n, ataque=0.005, decaimento=8.0):
    x = np.arange(n) / SR
    env = np.exp(-x * decaimento)
    a = int(SR * ataque)
    env[:a] *= np.linspace(0, 1, a)
    return env


def nota(freq, dur, decaimento=8.0, harm=(1.0, 0.3, 0.12)):
    x = t(dur)
    s = sum(a * np.sin(2 * np.pi * freq * (i + 1) * x) for i, a in enumerate(harm))
    return s * envelope(len(x), decaimento=decaimento)


def passa_baixa(s, k):
    return np.convolve(s, np.ones(k) / k, mode="same")


def main(pasta):
    os.makedirs(pasta, exist_ok=True)

    # Moeda: duas notas rápidas (B5 -> E6)
    s = np.concatenate([nota(988, 0.07, 20), nota(1319, 0.35, 9)])
    salvar("moeda.wav", s * 0.5, pasta)

    # Relógio: arpejo ascendente
    s = np.concatenate([nota(f, 0.08, 14) for f in (1047, 1319, 1568)] + [nota(2093, 0.4, 7)])
    salvar("relogio.wav", s * 0.45, pasta)

    # Turbo: ruído + varredura de frequência ascendente
    x = t(0.8)
    freq = np.linspace(180, 900, len(x))
    fase = 2 * np.pi * np.cumsum(freq) / SR
    s = 0.5 * np.sin(fase) * (0.6 + 0.4 * np.sin(fase * 0.5))
    s += passa_baixa(rng.uniform(-1, 1, len(x)), 6) * 0.6
    s *= np.sin(np.pi * x / x[-1]) ** 0.7
    salvar("turbo.wav", s * 0.5, pasta)

    # Batida: baque grave + ruído curto
    x = t(0.35)
    s = np.sin(2 * np.pi * 70 * x) * np.exp(-x * 14)
    s += passa_baixa(rng.uniform(-1, 1, len(x)), 12) * np.exp(-x * 30) * 1.5
    salvar("batida.wav", s * 0.7, pasta)

    # Contagem regressiva e largada
    salvar("bip.wav", nota(660, 0.18, 12, (1.0, 0.0, 0.25)) * 0.5, pasta)
    salvar("largada.wav", nota(1320, 0.6, 4, (1.0, 0.0, 0.25)) * 0.5, pasta)

    # Fim de jogo: fanfarra C5-E5-G5-C6
    s = np.concatenate([nota(f, d, dec) for f, d, dec in
                        ((523, 0.14, 10), (659, 0.14, 10), (784, 0.14, 10), (1047, 0.9, 3))])
    salvar("fim.wav", s * 0.5, pasta)

    # Motor (loop de 1 s): harmônicos de 50 Hz modulados + um pouco de ruído
    x = t(1.0)
    f0 = 50
    s = sum((1 / k ** 0.9) * np.sin(2 * np.pi * f0 * k * x + k) for k in range(1, 14))
    s *= 0.75 + 0.25 * np.sin(2 * np.pi * 25 * x)
    s += passa_baixa(rng.uniform(-1, 1, len(x)), 20) * 0.5
    s = passa_baixa(s, 4)
    s /= np.max(np.abs(s))
    salvar("motor.wav", s * 0.55, pasta, loop=True)
    print("Sons gerados em", pasta)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sons")
