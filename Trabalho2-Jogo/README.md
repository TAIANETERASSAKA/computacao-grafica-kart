# Trabalho 2 — Jogo 3D: Kart das Moedas

Jogo 3D feito no **Godot 4.7** (GDScript) usando o **kart modelado no Trabalho 1**.

## O jogo

Você pilota o kart numa arena e precisa **coletar o máximo de moedas em 60 segundos**.

- **Moedas douradas**: +1 ponto. Sempre há 12 na arena; quando você pega uma, outra aparece em outro lugar.
- **Relógios azuis**: +5 segundos. Aparecem de tempos em tempos.
- **Faixas de turbo** (setas azuis no chão): dão um impulso de velocidade.
- **Cones**: têm física e podem ser derrubados. **Pilhas de pneus**, a **ilha central** e os **muros** são obstáculos fixos.
- O **recorde** fica salvo entre uma partida e outra.

### Controles

| Tecla | Ação |
|---|---|
| W / ↑ | acelerar |
| S / ↓ | frear e dar ré |
| A D / ← → | virar |
| Espaço | freio de mão (drift) |
| C | alternar câmera (perseguição / aérea) |
| R | voltar à largada |
| Esc ou P | pausar (no menu de pausa, Q volta ao menu) |
| Enter | começar / jogar de novo |

Também funciona com controle (gatilhos aceleram e freiam, analógico esquerdo vira).

## Como executar

**Sem instalar nada:** use os executáveis exportados, `KartDasMoedas-Windows.exe` (Windows) ou
`KartDasMoedas-Linux.x86_64` (Linux).

**Pelo editor:**

1. Abra o Godot 4.7 (ou mais novo) e clique em **Importar**.
2. Selecione o arquivo `project.godot` desta pasta.
3. Pressione **F5** para jogar.

Pelo terminal:

```bash
godot --path .            # joga
godot --editor --path .   # abre o editor
```

## Estrutura do projeto

```
cenas/      main.tscn (arena e fluxo do jogo), kart.tscn, moeda.tscn, relogio.tscn,
            turbo.tscn, cone.tscn, pneus.tscn, hud.tscn
scripts/    kart.gd, camera_seguidora.gd, main.gd, hud.gd, coletavel.gd, turbo.gd, decoracao.gd
shaders/    asfalto, grama, listras, turbo e bandeira (.gdshader)
modelos/    kart.glb  ← modelo exportado do Trabalho 1
sons/       efeitos sonoros (.wav)
fontes/     Russo One (licença SIL OFL)
ferramentas_dev/  scripts auxiliares (ignorados pelo Godot)
```

## Como o modelo do Trabalho 1 é usado

`kart.tscn` instancia `modelos/kart.glb` dentro de um `CharacterBody3D`. Como o modelo foi feito com
hierarquia, o script `kart.gd` encontra os nós `Roda_DE`, `Roda_DD`, `Roda_TE`, `Roda_TD` e `Volante` e:

- **gira as rodas** de acordo com a distância percorrida (ângulo = distância ÷ raio da roda);
- **esterça as rodas dianteiras** e **gira o volante** quando o jogador vira;
- **inclina a carroceria** para fora nas curvas e para trás ao acelerar.

## Conceitos de Computação Gráfica aplicados

| Conceito | Onde |
|---|---|
| **Transformações geométricas** (translação, rotação, escala; `Basis`/matrizes; ângulos de Euler na ordem YXZ) | `kart.gd`: rotação do kart em Y, rolagem + esterço das rodas, inclinação da carroceria; `decoracao.gd`: árvores com transformações aleatórias |
| **Hierarquia de cena / grafo de cena** | Rodas e volante animados como nós filhos do modelo |
| **Câmera virtual** (projeção perspectiva, `look_at`, campo de visão) | `camera_seguidora.gd`: câmera de perseguição com suavização exponencial `k = 1 − e^(−s·Δt)`, FOV que aumenta com a velocidade, câmera aérea, órbita no menu, tremor nas batidas |
| **Iluminação** | Luz direcional (sol) com **sombras**, luz ambiente do céu procedural, **luzes pontuais** nas moedas e relógios, *tonemapping* Filmic, *glow* (bloom) e SSAO |
| **Shaders (GLSL do Godot)** | *Vertex shader*: bandeira ondulando com uma onda senoidal e normal recalculada pela derivada. *Fragment shaders*: asfalto com ruído procedural (*value noise*), listras calculadas pelas coordenadas de mundo, setas do turbo animadas no tempo |
| **Modelos de material PBR** | Materiais do glTF (metalicidade/rugosidade) e `StandardMaterial3D` com emissão |
| **Sistemas de partículas** | Fumaça das rodas no drift, chama do escapamento no turbo, explosão ao coletar moedas (texturas radiais geradas por código) |
| **Física e detecção de colisão** | `CharacterBody3D` com `move_and_slide`, `Area3D` para coletáveis e turbo, `RigidBody3D` para cones empurrados por impulso |
| **Instanciação de geometria** | Moedas, cones, pneus e árvores reaproveitam a mesma malha |
| **Interface 2D sobre 3D** | HUD em `CanvasLayer`; textos 3D (`Label3D`) nas placas da arena |
| **Interpolação de física** | Movimento suave mesmo com monitores acima de 60 Hz |

## Física do kart (resumo)

O kart guarda uma **velocidade escalar** ao longo da frente (−Z local). O volante gira o corpo em Y com
velocidade angular proporcional à velocidade. A velocidade real se alinha à frente do kart conforme a
**aderência**: `v = lerp(v, frente·velocidade, 1 − e^(−aderência·Δt))`. Com o freio de mão, a aderência cai
e o kart derrapa. Ao bater de frente numa parede, o kart quica para trás.

## Créditos

- Modelo 3D, código, shaders e sons: feitos para este trabalho (os sons foram sintetizados em Python
  com `ferramentas_dev/gerar_sons.py`).
- Fonte **Russo One**, de Jovanny Lemonad, sob a licença SIL Open Font License (`fontes/OFL.txt`).

## Ferramentas de desenvolvimento (`ferramentas_dev/`)

- `gerar_sons.py`: sintetiza os efeitos sonoros (o som do motor inclui pontos de loop no arquivo WAV).
- `gerar_cenas.py`: gerou `main.tscn` e `hud.tscn`, calculando a posição dos obstáculos. **Atenção:** rodar
  de novo sobrescreve essas duas cenas. Se você editar a arena no editor, não rode este script.
- `configurar_entradas.gd`: cria as ações de teclado e controle no `project.godot`.

As predefinições de exportação (Windows e Linux) estão em `export_presets.cfg` (menu **Projeto → Exportar**).
