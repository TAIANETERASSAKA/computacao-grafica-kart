"""Gera cenas/hud.tscn e cenas/main.tscn (layout da arena calculado aqui).

Depois de gerado, tudo pode ser editado normalmente no editor do Godot;
este script só foi usado para posicionar os obstáculos com precisão.
Uso: python3 gerar_cenas.py <pasta_do_projeto>
"""
import math
import os
import sys

PROJ = sys.argv[1] if len(sys.argv) > 1 else "."


def v3(x, y, z):
    return f"Vector3({x:g}, {y:g}, {z:g})"


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

def rotulo(nome, pai, texto, ajustes, estilo, alinh_h=0, alinh_v=0, extra=""):
    linhas = [f'[node name="{nome}" type="Label" parent="{pai}"]']
    linhas += ajustes
    linhas.append(f'text = "{texto}"')
    linhas.append(f'label_settings = SubResource("{estilo}")')
    if alinh_h:
        linhas.append(f"horizontal_alignment = {alinh_h}")
    if alinh_v:
        linhas.append(f"vertical_alignment = {alinh_v}")
    if extra:
        linhas.append(extra)
    return "\n".join(linhas) + "\n"


TELA_CHEIA = [
    "layout_mode = 3", "anchors_preset = 15", "anchor_right = 1.0", "anchor_bottom = 1.0",
    "grow_horizontal = 2", "grow_vertical = 2", "mouse_filter = 2",
]


def faixa_central(topo, base):
    """Rótulo que ocupa a largura toda, numa faixa vertical relativa ao centro da tela."""
    return ["layout_mode = 1", "anchors_preset = -1", "anchor_top = 0.5", "anchor_right = 1.0",
            "anchor_bottom = 0.5", f"offset_top = {topo:g}", f"offset_bottom = {base:g}",
            "grow_horizontal = 2", "grow_vertical = 2"]


def gerar_hud():
    s = ['[gd_scene format=3]\n',
         '[ext_resource type="Script" path="res://scripts/hud.gd" id="1_script"]\n']

    estilos = {
        "LS_titulo": dict(font_size=58, font_color="Color(1, 0.8, 0.12, 1)", outline_size=14,
                          outline_color="Color(0.12, 0.05, 0, 1)"),
        "LS_grande": dict(font_size=96, outline_size=18, outline_color="Color(0, 0, 0, 1)"),
        "LS_tempo": dict(font_size=54, outline_size=12, outline_color="Color(0, 0, 0, 1)"),
        "LS_medio": dict(font_size=34, outline_size=10, outline_color="Color(0, 0, 0, 1)"),
        "LS_pequeno": dict(font_size=19, outline_size=6, outline_color="Color(0, 0, 0, 0.9)"),
        "LS_texto": dict(font_size=19, font_color="Color(0.9, 0.93, 1, 1)", line_spacing=4.0),
        "LS_tecla": dict(font_size=19, font_color="Color(1, 0.8, 0.12, 1)"),
        "LS_recorde": dict(font_size=26, font_color="Color(1, 0.8, 0.12, 1)"),
    }
    for nome, props in estilos.items():
        s.append(f'[sub_resource type="LabelSettings" id="{nome}"]')
        for k, v in props.items():
            s.append(f"{k} = {v}")
        s.append("")
    s.append('''[sub_resource type="StyleBoxFlat" id="Estilo_painel"]
content_margin_left = 34.0
content_margin_top = 28.0
content_margin_right = 34.0
content_margin_bottom = 28.0
bg_color = Color(0.03, 0.06, 0.15, 0.86)
border_width_left = 3
border_width_top = 3
border_width_right = 3
border_width_bottom = 3
border_color = Color(1, 0.75, 0.1, 0.85)
corner_radius_top_left = 22
corner_radius_top_right = 22
corner_radius_bottom_right = 22
corner_radius_bottom_left = 22
''')

    s.append('[node name="HUD" type="CanvasLayer"]\nprocess_mode = 3\nscript = ExtResource("1_script")\n')

    # --- Durante o jogo ---------------------------------------------------
    s.append('[node name="Jogo" type="Control" parent="."]\n' + "\n".join(TELA_CHEIA) + "\n")
    s.append(rotulo("Moedas", "Jogo", "MOEDAS  0",
                    ["layout_mode = 0", "offset_left = 32.0", "offset_top = 22.0",
                     "offset_right = 420.0", "offset_bottom = 70.0"], "LS_medio"))
    s.append(rotulo("Tempo", "Jogo", "1:00",
                    ["layout_mode = 1", "anchors_preset = 5", "anchor_left = 0.5", "anchor_right = 0.5",
                     "offset_left = -160.0", "offset_top = 12.0", "offset_right = 160.0",
                     "offset_bottom = 82.0", "grow_horizontal = 2"], "LS_tempo", 1))
    s.append(rotulo("Recorde", "Jogo", "RECORDE 0",
                    ["layout_mode = 1", "anchors_preset = 1", "anchor_left = 1.0", "anchor_right = 1.0",
                     "offset_left = -420.0", "offset_top = 32.0", "offset_right = -32.0",
                     "offset_bottom = 62.0", "grow_horizontal = 0"], "LS_pequeno", 2))
    s.append(rotulo("Velocidade", "Jogo", "0 km/h",
                    ["layout_mode = 1", "anchors_preset = 3", "anchor_left = 1.0", "anchor_top = 1.0",
                     "anchor_right = 1.0", "anchor_bottom = 1.0", "offset_left = -380.0",
                     "offset_top = -84.0", "offset_right = -32.0", "offset_bottom = -26.0",
                     "grow_horizontal = 0", "grow_vertical = 0"], "LS_medio", 2))
    s.append(rotulo("Dicas", "Jogo",
                    "ESPAÇO drift   ·   C câmera   ·   R voltar à largada   ·   ESC pausa",
                    ["layout_mode = 1", "anchors_preset = 2", "anchor_top = 1.0", "anchor_bottom = 1.0",
                     "offset_left = 32.0", "offset_top = -58.0", "offset_right = 900.0",
                     "offset_bottom = -28.0", "grow_vertical = 0"], "LS_pequeno"))
    s.append(rotulo("Mensagem", "Jogo", "", faixa_central(-200.0, -60.0), "LS_grande", 1, 1))

    # --- Menu ------------------------------------------------------------
    s.append('[node name="Menu" type="Control" parent="."]\n' + "\n".join(TELA_CHEIA) + "\n")
    s.append('''[node name="Painel" type="PanelContainer" parent="Menu"]
layout_mode = 1
anchors_preset = 9
anchor_bottom = 1.0
offset_left = 40.0
offset_top = 36.0
offset_right = 560.0
offset_bottom = -36.0
grow_vertical = 2
theme_override_styles/panel = SubResource("Estilo_painel")
''')
    s.append('''[node name="Coluna" type="VBoxContainer" parent="Menu/Painel"]
layout_mode = 2
theme_override_constants/separation = 10
''')
    pai = "Menu/Painel/Coluna"
    s.append(rotulo("Titulo", pai, "KART DAS MOEDAS", ["layout_mode = 2"], "LS_titulo", 1,
                    extra="autowrap_mode = 2"))
    s.append(rotulo("Subtitulo", pai, "Trabalho 2  ·  Computação Gráfica", ["layout_mode = 2"],
                    "LS_texto", 1))
    s.append(f'[node name="Separador1" type="HSeparator" parent="{pai}"]\nlayout_mode = 2\n')
    s.append(rotulo("Objetivo", pai,
                    "Colete o máximo de moedas em 60 segundos! Relógios azuis dão +5 s e as "
                    "faixas com setas dão turbo. Derrube os cones à vontade.",
                    ["layout_mode = 2"], "LS_texto", extra="autowrap_mode = 3"))
    s.append(f'''[node name="Controles" type="GridContainer" parent="{pai}"]
layout_mode = 2
theme_override_constants/h_separation = 22
theme_override_constants/v_separation = 4
columns = 2
''')
    controles = [
        ("W  /  SETA CIMA", "acelerar"),
        ("S  /  SETA BAIXO", "frear e dar ré"),
        ("A D  /  SETAS", "virar"),
        ("ESPAÇO", "freio de mão (drift)"),
        ("C", "trocar câmera"),
        ("R", "voltar à largada"),
        ("ESC", "pausar"),
    ]
    for i, (tecla, acao) in enumerate(controles):
        s.append(rotulo(f"Tecla{i}", f"{pai}/Controles", tecla, ["layout_mode = 2"], "LS_tecla"))
        s.append(rotulo(f"Acao{i}", f"{pai}/Controles", acao, ["layout_mode = 2"], "LS_texto"))
    s.append(f'[node name="Separador2" type="HSeparator" parent="{pai}"]\nlayout_mode = 2\n')
    s.append(rotulo("Recorde", pai, "Recorde: 0 moedas", ["layout_mode = 2"], "LS_recorde", 1))
    s.append(f'[node name="Espaco" type="Control" parent="{pai}"]\nlayout_mode = 2\nsize_flags_vertical = 3\n')
    s.append(rotulo("Iniciar", pai, "ENTER para começar", ["layout_mode = 2"], "LS_medio", 1))

    # --- Pausa -------------------------------------------------------------
    s.append('[node name="Pausa" type="Control" parent="."]\n' + "\n".join(TELA_CHEIA) + "\n")
    s.append('[node name="Fundo" type="ColorRect" parent="Pausa"]\n' + "\n".join(TELA_CHEIA[:-1]) +
             "\nmouse_filter = 2\ncolor = Color(0, 0, 0, 0.55)\n")
    s.append(rotulo("Titulo", "Pausa", "PAUSADO", faixa_central(-120.0, 0.0), "LS_grande", 1, 1))
    s.append(rotulo("Opcoes", "Pausa", "ESC continuar   ·   Q voltar ao menu", faixa_central(10.0, 60.0),
                    "LS_medio", 1, 1))

    # --- Fim de jogo ---------------------------------------------------------
    s.append('[node name="Fim" type="Control" parent="."]\n' + "\n".join(TELA_CHEIA) + "\n")
    s.append('[node name="Fundo" type="ColorRect" parent="Fim"]\n' + "\n".join(TELA_CHEIA[:-1]) +
             "\nmouse_filter = 2\ncolor = Color(0, 0, 0, 0.4)\n")
    s.append(rotulo("Titulo", "Fim", "FIM DE JOGO!", faixa_central(-230.0, -110.0), "LS_grande", 1, 1))
    s.append(rotulo("Pontos", "Fim", "0 moedas", faixa_central(-100.0, -20.0), "LS_titulo", 1, 1))
    s.append(rotulo("Recorde", "Fim", "Recorde: 0 moedas", faixa_central(-10.0, 40.0), "LS_medio", 1, 1))
    s.append(rotulo("JogarNovamente", "Fim", "ENTER para jogar de novo", faixa_central(90.0, 140.0),
                    "LS_medio", 1, 1))

    with open(os.path.join(PROJ, "cenas", "hud.tscn"), "w", encoding="utf-8") as f:
        f.write("\n".join(s))


# ---------------------------------------------------------------------------
# Cena principal
# ---------------------------------------------------------------------------

def gerar_main():
    ext = [
        ("Script", "res://scripts/main.gd", "1_main"),
        ("PackedScene", "res://cenas/kart.tscn", "2_kart"),
        ("Script", "res://scripts/camera_seguidora.gd", "3_camera"),
        ("PackedScene", "res://cenas/hud.tscn", "4_hud"),
        ("Shader", "res://shaders/asfalto.gdshader", "5_asfalto"),
        ("Shader", "res://shaders/grama.gdshader", "6_grama"),
        ("Shader", "res://shaders/listras.gdshader", "7_listras"),
        ("Shader", "res://shaders/bandeira.gdshader", "8_bandeira"),
        ("PackedScene", "res://cenas/cone.tscn", "9_cone"),
        ("PackedScene", "res://cenas/pneus.tscn", "10_pneus"),
        ("PackedScene", "res://cenas/turbo.tscn", "11_turbo"),
        ("Script", "res://scripts/decoracao.gd", "12_decoracao"),
        ("FontFile", "res://fontes/RussoOne-Regular.ttf", "13_fonte"),
    ]
    sons = ["moeda", "relogio", "turbo", "batida", "bip", "largada", "fim"]
    for i, nome in enumerate(sons):
        ext.append(("AudioStream", f"res://sons/{nome}.wav", f"{20 + i}_{nome}"))

    s = ["[gd_scene format=3]\n"]
    for tipo, caminho, ident in ext:
        s.append(f'[ext_resource type="{tipo}" path="{caminho}" id="{ident}"]')
    s.append("")

    s.append('''[sub_resource type="ProceduralSkyMaterial" id="Mat_ceu"]
sky_top_color = Color(0.2, 0.42, 0.82, 1)
sky_horizon_color = Color(0.66, 0.76, 0.9, 1)
ground_bottom_color = Color(0.16, 0.2, 0.14, 1)
ground_horizon_color = Color(0.66, 0.76, 0.9, 1)

[sub_resource type="Sky" id="Ceu"]
sky_material = SubResource("Mat_ceu")

[sub_resource type="Environment" id="Ambiente"]
background_mode = 2
sky = SubResource("Ceu")
ambient_light_source = 3
reflected_light_source = 2
tonemap_mode = 2
tonemap_white = 6.0
ssao_enabled = true
glow_enabled = true
glow_intensity = 0.5
glow_bloom = 0.05
fog_enabled = true
fog_light_color = Color(0.68, 0.77, 0.9, 1)
fog_density = 0.0015
fog_sky_affect = 0.0

[sub_resource type="ShaderMaterial" id="Mat_asfalto"]
render_priority = 0
shader = ExtResource("5_asfalto")

[sub_resource type="PlaneMesh" id="Malha_pista"]
material = SubResource("Mat_asfalto")
size = Vector2(70, 70)

[sub_resource type="WorldBoundaryShape3D" id="Forma_chao"]

[sub_resource type="ShaderMaterial" id="Mat_grama"]
render_priority = 0
shader = ExtResource("6_grama")

[sub_resource type="PlaneMesh" id="Malha_grama"]
material = SubResource("Mat_grama")
size = Vector2(400, 400)

[sub_resource type="ShaderMaterial" id="Mat_listras"]
render_priority = 0
shader = ExtResource("7_listras")

[sub_resource type="BoxMesh" id="Malha_muro_x"]
material = SubResource("Mat_listras")
size = Vector3(72, 1.2, 1)

[sub_resource type="BoxMesh" id="Malha_muro_z"]
material = SubResource("Mat_listras")
size = Vector3(1, 1.2, 70)

[sub_resource type="BoxShape3D" id="Forma_muro_x"]
size = Vector3(72, 3, 1)

[sub_resource type="BoxShape3D" id="Forma_muro_z"]
size = Vector3(1, 3, 70)

[sub_resource type="CylinderMesh" id="Malha_ilha"]
material = SubResource("Mat_grama")
top_radius = 6.0
bottom_radius = 6.0
height = 0.4
radial_segments = 48
rings = 1

[sub_resource type="CylinderMesh" id="Malha_zebra"]
material = SubResource("Mat_listras")
top_radius = 6.4
bottom_radius = 6.4
height = 0.25
radial_segments = 48
rings = 1

[sub_resource type="CylinderShape3D" id="Forma_ilha"]
height = 2.0
radius = 6.4

[sub_resource type="StandardMaterial3D" id="Mat_metal"]
albedo_color = Color(0.9, 0.9, 0.92, 1)
metallic = 0.8
roughness = 0.3

[sub_resource type="CylinderMesh" id="Malha_mastro"]
material = SubResource("Mat_metal")
top_radius = 0.06
bottom_radius = 0.08
height = 6.0
radial_segments = 12
rings = 1

[sub_resource type="ShaderMaterial" id="Mat_bandeira"]
render_priority = 0
shader = ExtResource("8_bandeira")

[sub_resource type="PlaneMesh" id="Malha_bandeira"]
material = SubResource("Mat_bandeira")
size = Vector2(2.4, 1.6)
subdivide_width = 24
subdivide_depth = 8

[sub_resource type="StandardMaterial3D" id="Mat_placa"]
albedo_color = Color(0.05, 0.12, 0.35, 1)
roughness = 0.6

[sub_resource type="BoxMesh" id="Malha_placa"]
material = SubResource("Mat_placa")
size = Vector3(18, 3, 0.3)

[sub_resource type="CylinderMesh" id="Malha_poste"]
material = SubResource("Mat_metal")
top_radius = 0.15
bottom_radius = 0.15
height = 5.0
radial_segments = 10
rings = 1
''')

    s.append('[node name="Main" type="Node3D"]\nprocess_mode = 3\nscript = ExtResource("1_main")\n')
    s.append('[node name="Ambiente" type="WorldEnvironment" parent="."]\nenvironment = SubResource("Ambiente")\n')
    s.append(f'''[node name="Sol" type="DirectionalLight3D" parent="."]
rotation = Vector3(-0.87, 0.55, 0)
light_energy = 1.1
shadow_enabled = true
directional_shadow_max_distance = 70.0
''')

    # Arena -------------------------------------------------------------------
    s.append('[node name="Arena" type="Node3D" parent="."]\nprocess_mode = 1\n')
    s.append('''[node name="Grama" type="MeshInstance3D" parent="Arena"]
position = Vector3(0, -0.02, 0)
cast_shadow = 0
mesh = SubResource("Malha_grama")

[node name="Pista" type="StaticBody3D" parent="Arena"]

[node name="Malha" type="MeshInstance3D" parent="Arena/Pista"]
cast_shadow = 0
mesh = SubResource("Malha_pista")

[node name="Colisao" type="CollisionShape3D" parent="Arena/Pista"]
shape = SubResource("Forma_chao")
''')
    muros = [("Norte", (0, 0.6, -35.5), "x"), ("Sul", (0, 0.6, 35.5), "x"),
             ("Oeste", (-35.5, 0.6, 0), "z"), ("Leste", (35.5, 0.6, 0), "z")]
    s.append('[node name="Muros" type="Node3D" parent="Arena"]\n')
    for nome, pos, eixo in muros:
        s.append(f'''[node name="{nome}" type="StaticBody3D" parent="Arena/Muros"]
position = {v3(*pos)}

[node name="Malha" type="MeshInstance3D" parent="Arena/Muros/{nome}"]
mesh = SubResource("Malha_muro_{eixo}")

[node name="Colisao" type="CollisionShape3D" parent="Arena/Muros/{nome}"]
position = Vector3(0, 0.9, 0)
shape = SubResource("Forma_muro_{eixo}")
''')

    # Ilha central com mastro e bandeira animada
    s.append('''[node name="Ilha" type="StaticBody3D" parent="Arena" groups=["obstaculo"]]
metadata/raio_livre = 9.0

[node name="Zebra" type="MeshInstance3D" parent="Arena/Ilha"]
position = Vector3(0, 0.125, 0)
mesh = SubResource("Malha_zebra")

[node name="Gramado" type="MeshInstance3D" parent="Arena/Ilha"]
position = Vector3(0, 0.2, 0)
mesh = SubResource("Malha_ilha")

[node name="Colisao" type="CollisionShape3D" parent="Arena/Ilha"]
position = Vector3(0, 1, 0)
shape = SubResource("Forma_ilha")

[node name="Mastro" type="MeshInstance3D" parent="Arena/Ilha"]
position = Vector3(0, 3.2, 0)
mesh = SubResource("Malha_mastro")

[node name="Bandeira" type="MeshInstance3D" parent="Arena/Ilha"]
position = Vector3(1.25, 5.3, 0)
rotation = Vector3(1.5708, 0, 0)
cast_shadow = 0
mesh = SubResource("Malha_bandeira")
''')

    # Placas com texto 3D (Label3D) atrás dos muros norte e sul
    for nome, z, rot, texto in (("PlacaNorte", -39.0, 0.0, "KART DAS MOEDAS"),
                                ("PlacaSul", 39.0, math.pi, "COMPUTAÇÃO GRÁFICA")):
        s.append(f'''[node name="{nome}" type="Node3D" parent="Arena"]
position = Vector3(0, 0, {z:g})
rotation = Vector3(0, {rot:.5f}, 0)

[node name="Painel" type="MeshInstance3D" parent="Arena/{nome}"]
position = Vector3(0, 4.5, 0)
mesh = SubResource("Malha_placa")

[node name="PosteE" type="MeshInstance3D" parent="Arena/{nome}"]
position = Vector3(-7, 2.5, -0.3)
mesh = SubResource("Malha_poste")

[node name="PosteD" type="MeshInstance3D" parent="Arena/{nome}"]
position = Vector3(7, 2.5, -0.3)
mesh = SubResource("Malha_poste")

[node name="Texto" type="Label3D" parent="Arena/{nome}"]
position = Vector3(0, 4.5, 0.17)
pixel_size = 0.012
text = "{texto}"
font = ExtResource("13_fonte")
font_size = 160
outline_size = 24
modulate = Color(1, 0.8, 0.12, 1)
outline_modulate = Color(0.1, 0.04, 0, 1)
''')

    # Obstáculos ------------------------------------------------------------
    s.append('[node name="Obstaculos" type="Node3D" parent="Arena"]\n')
    n = 0
    cones = []
    for x in range(-16, 17, 4):          # slalom ao norte
        cones.append((x, -27))
    for z in range(-16, 17, 4):          # slalom a oeste
        cones.append((-27, z))
    for k in range(6):                   # anel ao redor da ilha
        a = math.radians(30 + 60 * k)
        cones.append((round(11 * math.cos(a), 2), round(11 * math.sin(a), 2)))
    for x, z in cones:
        n += 1
        s.append(f'[node name="Cone{n}" parent="Arena/Obstaculos" instance=ExtResource("9_cone")]\n'
                 f'position = {v3(x, 0, z)}\n')
    pilhas = [(29, 29), (-29, 29), (29, -29), (-29, -29), (14, 14), (-14, 14), (14, -14), (-14, -14)]
    for i, (x, z) in enumerate(pilhas, 1):
        s.append(f'[node name="Pneus{i}" parent="Arena/Obstaculos" instance=ExtResource("10_pneus")]\n'
                 f'position = {v3(x, 0, z)}\n')
    turbos = [((21, 0), 0.0), ((0, -21), math.pi / 2), ((-21, 0), math.pi), ((12, 24), -math.pi / 2)]
    for i, ((x, z), rot) in enumerate(turbos, 1):
        s.append(f'[node name="Turbo{i}" parent="Arena/Obstaculos" instance=ExtResource("11_turbo")]\n'
                 f'position = {v3(x, 0, z)}\nrotation = Vector3(0, {rot:.5f}, 0)\n')

    s.append('[node name="Decoracao" type="Node3D" parent="Arena"]\nscript = ExtResource("12_decoracao")\n')

    # Jogador, câmera, coletáveis, HUD e sons ------------------------------------
    s.append('''[node name="Kart" parent="." instance=ExtResource("2_kart")]
process_mode = 1
position = Vector3(0, 0, 29)

[node name="Camera" type="Camera3D" parent="." node_paths=PackedStringArray("alvo")]
process_mode = 1
position = Vector3(4, 2, 33)
current = true
fov = 70.0
script = ExtResource("3_camera")
alvo = NodePath("../Kart")

[node name="Coletaveis" type="Node3D" parent="."]
process_mode = 1

[node name="HUD" parent="." instance=ExtResource("4_hud")]

[node name="Sons" type="Node" parent="."]
process_mode = 1
''')
    volumes = {"moeda": -6, "relogio": -4, "turbo": -6, "batida": -6, "bip": -6, "largada": -6, "fim": -4}
    for i, nome in enumerate(sons):
        s.append(f'[node name="{nome.capitalize()}" type="AudioStreamPlayer" parent="Sons"]\n'
                 f'stream = ExtResource("{20 + i}_{nome}")\nvolume_db = {volumes[nome]:.1f}\n')

    with open(os.path.join(PROJ, "cenas", "main.tscn"), "w", encoding="utf-8") as f:
        f.write("\n".join(s))


if __name__ == "__main__":
    gerar_hud()
    gerar_main()
    print("Cenas geradas.")
