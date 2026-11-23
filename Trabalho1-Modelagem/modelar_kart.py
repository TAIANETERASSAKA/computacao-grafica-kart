"""
Trabalho 1 - Computação Gráfica - Modelagem 3D de um Kart
==========================================================

Script de modelagem para o Blender (testado no Blender 4.5 LTS).

O modelo é construído a partir de primitivas (cubo, cilindro, esfera,
toro, texto e curva) que são transformadas (translação, rotação e escala)
e refinadas com modificadores não destrutivos:

  * Bevel ............ arredonda as arestas (carenagem, banco, pneus...)
  * Mirror ........... modela só um lado das laterais e espelha o outro
  * Array ............ repete as aletas de refrigeração do motor
  * Subdivision ...... suaviza o tronco do piloto (box modeling)
  * Boolean .......... recorta a viseira do capacete (interseção)

As peças são organizadas numa hierarquia (pai/filho). O objeto vazio
"Kart" é a raiz; cada roda tem seu próprio pivô no centro do eixo, o que
permite girá-las (rolagem e esterço) individualmente no jogo do Trabalho 2.

Como executar:
    blender --background --python modelar_kart.py

Saídas (na mesma pasta do script):
    kart.blend   - arquivo do Blender com o modelo, materiais, luzes e câmera
    kart.glb     - modelo exportado em glTF binário (usado no Godot)
    renders/     - imagens renderizadas (Cycles) para o relatório
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_RENDERS = os.path.join(PASTA, "renders")
SO_MODELO = "--so-modelo" in sys.argv  # pula os renders (mais rápido)

# Convenção de eixos (Blender): X = direita do kart, Y = frente, Z = cima.
# O chão está em Z = 0. Unidades em metros.


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def limpar_cena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def nova_colecao(nome):
    col = bpy.data.collections.new(nome)
    bpy.context.scene.collection.children.link(col)
    return col


def ativar(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def material(nome, cor, metal=0.0, rugosidade=0.5, verniz=0.0, emissao=0.0):
    """Cria um material PBR (Principled BSDF)."""
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rugosidade
    if verniz:
        bsdf.inputs["Coat Weight"].default_value = verniz
        bsdf.inputs["Coat Roughness"].default_value = 0.05
    if emissao:
        bsdf.inputs["Emission Color"].default_value = (*cor, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emissao
    mat.diffuse_color = (*cor, 1.0)  # cor no modo "Solid" da viewport
    mat.metallic = metal
    mat.roughness = rugosidade
    return mat


def finalizar(obj, nome, mat, pai, colecao, suave=True, angulo=35):
    """Nomeia, aplica material, suaviza e coloca o objeto na hierarquia."""
    obj.name = nome
    if obj.data is not None and hasattr(obj.data, "name"):
        obj.data.name = nome
    if mat is not None:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    if obj.type == "MESH" and suave:
        ativar(obj)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angulo))
    # move para a coleção desejada
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    colecao.objects.link(obj)
    if pai is not None:
        bpy.context.view_layer.update()
        mundo = obj.matrix_world.copy()
        obj.parent = pai
        obj.matrix_world = mundo
    return obj


def bevel(obj, largura=0.012, segmentos=3, angulo=40):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = largura
    mod.segments = segmentos
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angulo)
    mod.harden_normals = True
    return mod


def caixa(nome, centro, tamanho, mat, pai, col, chanfro=0.012, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centro, rotation=rot)
    obj = bpy.context.active_object
    obj.scale = tamanho
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if chanfro:
        bevel(obj, chanfro)
    return finalizar(obj, nome, mat, pai, col)


def cilindro(nome, centro, raio, prof, mat, pai, col, eixo="Z", vertices=32, rot=None):
    rotacoes = {"X": (0, math.radians(90), 0), "Y": (math.radians(90), 0, 0), "Z": (0, 0, 0)}
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=raio, depth=prof, location=centro,
        rotation=rot if rot is not None else rotacoes[eixo])
    return finalizar(bpy.context.active_object, nome, mat, pai, col)


def cilindro_entre(nome, p1, p2, raio, mat, pai, col, vertices=16):
    """Cilindro cujas bases ficam nos pontos p1 e p2 (útil para tubos e membros)."""
    p1, p2 = Vector(p1), Vector(p2)
    direcao = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=raio, depth=direcao.length,
                                        location=(p1 + p2) / 2)
    obj = bpy.context.active_object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direcao.normalized())
    obj.rotation_mode = "XYZ"
    return finalizar(obj, nome, mat, pai, col)


def esfera(nome, centro, raio, mat, pai, col, escala=(1, 1, 1), segmentos=32, aneis=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=aneis, radius=raio,
                                         location=centro)
    obj = bpy.context.active_object
    obj.scale = escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finalizar(obj, nome, mat, pai, col, angulo=180)


def loft(nome, secoes, mat, pai, col, chanfro=0.015):
    """Cria um sólido ligando seções transversais de 4 vértices (técnica de 'loft').

    Cada seção é uma lista de 4 pontos na ordem:
    inferior-esquerdo, inferior-direito, superior-direito, superior-esquerdo.
    """
    malha = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in secao] for secao in secoes]
    bm.faces.new(vs[0])                         # tampa de trás
    bm.faces.new(list(reversed(vs[-1])))        # tampa da frente
    for a, b in zip(vs[:-1], vs[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malha)
    bm.free()
    obj = bpy.data.objects.new(nome, malha)
    bpy.context.scene.collection.objects.link(obj)
    if chanfro:
        bevel(obj, chanfro)
    return finalizar(obj, nome, mat, pai, col)


def vazio(nome, local, pai, col, tamanho=0.15):
    obj = bpy.data.objects.new(nome, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = tamanho
    obj.location = local
    col.objects.link(obj)
    if pai is not None:
        obj.parent = pai
        obj.location = Vector(local) - pai.matrix_world.translation
    return obj


# ---------------------------------------------------------------------------
# Materiais
# ---------------------------------------------------------------------------

def criar_materiais():
    return {
        "carenagem": material("Carenagem_Vermelha", (0.75, 0.015, 0.01), rugosidade=0.30, verniz=0.5),
        "faixa": material("Faixa_Amarela", (1.0, 0.60, 0.0), rugosidade=0.35),
        "branco": material("Placa_Branca", (0.90, 0.90, 0.88), rugosidade=0.40),
        "preto": material("Numero_Preto", (0.01, 0.01, 0.01), rugosidade=0.45),
        "pneu": material("Borracha_Pneu", (0.015, 0.015, 0.015), rugosidade=0.85),
        "aro": material("Aro_Metal", (0.80, 0.80, 0.82), metal=1.0, rugosidade=0.25),
        "cubo": material("Cubo_Roda", (0.10, 0.10, 0.12), metal=0.8, rugosidade=0.35),
        "chassi": material("Chassi_Metal", (0.08, 0.09, 0.10), metal=0.7, rugosidade=0.40),
        "banco": material("Banco_Preto", (0.03, 0.03, 0.035), rugosidade=0.55),
        "motor": material("Motor_Aluminio", (0.62, 0.63, 0.65), metal=1.0, rugosidade=0.38),
        "cromo": material("Escapamento_Cromado", (0.90, 0.90, 0.92), metal=1.0, rugosidade=0.12),
        "macacao": material("Macacao_Azul", (0.02, 0.12, 0.65), rugosidade=0.60),
        "capacete": material("Capacete_Amarelo", (1.0, 0.55, 0.0), rugosidade=0.25, verniz=0.4),
        "viseira": material("Viseira_Fume", (0.02, 0.02, 0.03), metal=0.3, rugosidade=0.05),
        "luva": material("Luva_Preta", (0.02, 0.02, 0.02), rugosidade=0.70),
    }


# ---------------------------------------------------------------------------
# Peças do kart
# ---------------------------------------------------------------------------

def criar_roda(nome, centro, raio, largura, lado, M, pai, col):
    """Roda = pivô (vazio no centro do eixo) + pneu + aro + cubo."""
    pivo = vazio(nome, centro, pai, col)
    x, y, z = centro

    pneu = cilindro(nome + "_Pneu", centro, raio, largura, M["pneu"], pivo, col, eixo="X", vertices=40)
    bevel(pneu, largura=raio * 0.25, segmentos=4, angulo=30)

    aro = cilindro(nome + "_Aro", centro, raio * 0.62, largura + 0.006, M["aro"], pivo, col,
                   eixo="X", vertices=32)
    bevel(aro, largura=0.006, segmentos=2)

    # cubo central, ligeiramente para fora do lado externo da roda
    cx = x + lado * (largura / 2 + 0.004)
    cilindro(nome + "_Cubo", (cx, y, z), raio * 0.2, 0.02, M["cubo"], pivo, col, eixo="X", vertices=16)

    # 5 porcas distribuídas em círculo (coordenadas polares)
    for i in range(5):
        a = 2 * math.pi * i / 5
        py = y + math.cos(a) * raio * 0.36
        pz = z + math.sin(a) * raio * 0.36
        cilindro(f"{nome}_Porca{i + 1}", (cx, py, pz), raio * 0.045, 0.016, M["cromo"], pivo, col,
                 eixo="X", vertices=6)
    return pivo


def criar_volante(M, pai, col):
    """Volante: toro + raios + cubo, montado na origem e depois posicionado."""
    centro = Vector((0.0, 0.20, 0.44))
    base_coluna = Vector((0.0, 0.52, 0.12))
    eixo = (centro - base_coluna).normalized()

    cilindro_entre("Coluna_Direcao", base_coluna, centro - eixo * 0.02, 0.014, M["chassi"], pai, col)

    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.016,
                                     major_segments=48, minor_segments=12, location=(0, 0, 0))
    aro = bpy.context.active_object
    pecas = [aro]
    for ang in (0, 120, 240):  # três raios
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        raio = bpy.context.active_object
        raio.scale = (0.12, 0.022, 0.01)
        raio.location = (math.cos(math.radians(ang - 90)) * 0.06, math.sin(math.radians(ang - 90)) * 0.06, 0)
        raio.rotation_euler = (0, 0, math.radians(ang - 90))
        pecas.append(raio)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.035, depth=0.03, location=(0, 0, 0))
    pecas.append(bpy.context.active_object)

    # junta as peças num único objeto (operação "Join")
    bpy.ops.object.select_all(action="DESELECT")
    for p in pecas:
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.objects.active = aro
    bpy.ops.object.join()
    volante = bpy.context.active_object

    # orienta o eixo Z local do volante ao longo da coluna de direção
    volante.rotation_mode = "QUATERNION"
    volante.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(eixo)
    volante.rotation_mode = "XYZ"
    volante.location = centro
    return finalizar(volante, "Volante", M["preto"], pai, col, angulo=50), centro


def criar_piloto(M, pai, col, aux, centro_volante):
    piloto = vazio("Piloto", (0, -0.20, 0.10), pai, col)

    # Tronco: box modeling + Subdivision Surface
    tronco = caixa("Piloto_Tronco", (0, -0.24, 0.40), (0.38, 0.26, 0.48), M["macacao"], piloto, col,
                   chanfro=0, rot=(math.radians(12), 0, 0))
    sub = tronco.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 3

    cilindro_entre("Piloto_Pescoco", (0, -0.27, 0.58), (0, -0.26, 0.68), 0.05, M["macacao"], piloto, col)

    centro_cabeca = (0, -0.25, 0.77)
    esfera("Piloto_Capacete", centro_cabeca, 0.13, M["capacete"], piloto, col)

    # Viseira: esfera um pouco maior + Boolean (interseção) com uma caixa auxiliar
    viseira = esfera("Piloto_Viseira", centro_cabeca, 0.134, M["viseira"], piloto, col)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.13, 0.785))
    cortador = bpy.context.active_object
    cortador.scale = (0.30, 0.20, 0.075)
    cortador.name = "Aux_Cortador_Viseira"
    for c in list(cortador.users_collection):
        c.objects.unlink(cortador)
    aux.objects.link(cortador)
    cortador.display_type = "WIRE"
    cortador.hide_render = True
    bpy.context.view_layer.update()
    mundo = cortador.matrix_world.copy()
    cortador.parent = piloto          # acompanha o piloto (e o kart) nas transformações
    cortador.matrix_world = mundo
    booleano = viseira.modifiers.new("Boolean", "BOOLEAN")
    booleano.operation = "INTERSECT"
    booleano.object = cortador
    booleano.solver = "EXACT"

    # Braços (ombro -> cotovelo -> mão no volante)
    cv = Vector(centro_volante)
    for lado, sufixo in ((1, "D"), (-1, "E")):
        ombro = Vector((lado * 0.17, -0.25, 0.55))
        cotovelo = Vector((lado * 0.23, -0.03, 0.42))
        mao = cv + Vector((lado * 0.125, 0.0, 0.0))
        esfera(f"Piloto_Ombro_{sufixo}", ombro, 0.055, M["macacao"], piloto, col)
        cilindro_entre(f"Piloto_Braco_{sufixo}", ombro, cotovelo, 0.045, M["macacao"], piloto, col)
        esfera(f"Piloto_Cotovelo_{sufixo}", cotovelo, 0.045, M["macacao"], piloto, col)
        cilindro_entre(f"Piloto_Antebraco_{sufixo}", cotovelo, mao, 0.04, M["macacao"], piloto, col)
        esfera(f"Piloto_Luva_{sufixo}", mao, 0.042, M["luva"], piloto, col)

        # Pernas (quadril -> joelho -> pé)
        quadril = Vector((lado * 0.09, -0.16, 0.16))
        joelho = Vector((lado * 0.11, 0.16, 0.25))
        pe = Vector((lado * 0.11, 0.46, 0.13))
        cilindro_entre(f"Piloto_Coxa_{sufixo}", quadril, joelho, 0.06, M["macacao"], piloto, col)
        esfera(f"Piloto_Joelho_{sufixo}", joelho, 0.06, M["macacao"], piloto, col)
        cilindro_entre(f"Piloto_Canela_{sufixo}", joelho, pe, 0.05, M["macacao"], piloto, col)
        caixa(f"Piloto_Sapato_{sufixo}", pe + Vector((0, 0.03, -0.01)), (0.09, 0.14, 0.08), M["luva"],
              piloto, col, chanfro=0.02)
    return piloto


def criar_motor(M, pai, col):
    caixa("Motor_Bloco", (0.30, -0.36, 0.20), (0.15, 0.20, 0.20), M["motor"], pai, col, chanfro=0.015)

    # Aletas de refrigeração: uma peça + modificador Array
    aleta = caixa("Motor_Aletas", (0.30, -0.36, 0.315), (0.13, 0.18, 0.012), M["motor"], pai, col,
                  chanfro=0.003)
    arr = aleta.modifiers.new("Array", "ARRAY")
    arr.count = 5
    arr.use_relative_offset = True
    arr.relative_offset_displace = (0, 0, 2.4)

    cilindro("Motor_Filtro_Ar", (0.43, -0.40, 0.24), 0.055, 0.07, M["preto"], pai, col, eixo="X")
    cilindro("Motor_Coroa", (0.21, -0.50, 0.16), 0.09, 0.012, M["motor"], pai, col, eixo="X", vertices=36)

    # Escapamento: curva Bézier com perfil circular (bevel) convertida em malha
    curva = bpy.data.curves.new("Escapamento", type="CURVE")
    curva.dimensions = "3D"
    curva.bevel_depth = 0.022
    curva.bevel_resolution = 4
    curva.resolution_u = 16
    spline = curva.splines.new("BEZIER")
    pontos = [(0.33, -0.44, 0.24), (0.38, -0.60, 0.28), (0.30, -0.70, 0.32)]
    spline.bezier_points.add(len(pontos) - 1)
    for bp, p in zip(spline.bezier_points, pontos):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new("Escapamento", curva)
    bpy.context.scene.collection.objects.link(obj)
    ativar(obj)
    bpy.ops.object.convert(target="MESH")
    finalizar(obj, "Escapamento", M["cromo"], pai, col, angulo=60)

    ponta = cilindro("Escapamento_Silenciador", (0.20, -0.71, 0.33), 0.045, 0.20, M["cromo"], pai, col,
                     eixo="X")
    bevel(ponta, largura=0.01, segmentos=3)


def criar_kart(col, aux):
    M = criar_materiais()
    kart = vazio("Kart", (0, 0, 0), None, col, tamanho=0.5)

    # --- Chassi -----------------------------------------------------------
    caixa("Chassi_Assoalho", (0, 0.0, 0.055), (0.64, 1.25, 0.03), M["chassi"], kart, col, chanfro=0.01)
    cilindro_entre("Chassi_Eixo_Traseiro", (-0.50, -0.50, 0.16), (0.50, -0.50, 0.16), 0.022, M["chassi"],
                   kart, col)
    for lado in (-1, 1):
        cilindro_entre(f"Chassi_Tubo_Lateral_{'D' if lado > 0 else 'E'}", (lado * 0.30, -0.60, 0.09),
                       (lado * 0.30, 0.62, 0.09), 0.016, M["chassi"], kart, col)
        cilindro_entre(f"Chassi_Manga_{'D' if lado > 0 else 'E'}", (lado * 0.30, 0.56, 0.11),
                       (lado * 0.46, 0.56, 0.14), 0.018, M["chassi"], kart, col)
        cilindro_entre(f"Chassi_Suporte_Eixo_{'D' if lado > 0 else 'E'}", (lado * 0.30, -0.45, 0.09),
                       (lado * 0.30, -0.50, 0.16), 0.02, M["chassi"], kart, col)

    # --- Carenagem frontal (loft de 3 seções) --------------------------------
    loft("Carenagem_Frontal", [
        [(-0.27, 0.40, 0.07), (0.27, 0.40, 0.07), (0.25, 0.40, 0.25), (-0.25, 0.40, 0.25)],
        [(-0.42, 0.74, 0.06), (0.42, 0.74, 0.06), (0.40, 0.74, 0.20), (-0.40, 0.74, 0.20)],
        [(-0.48, 1.00, 0.05), (0.48, 1.00, 0.05), (0.46, 0.98, 0.12), (-0.46, 0.98, 0.12)],
    ], M["carenagem"], kart, col, chanfro=0.02)
    caixa("Carenagem_Faixa", (0, 0.86, 0.16), (0.12, 0.24, 0.03), M["faixa"], kart, col, chanfro=0.008,
          rot=(math.radians(-18), 0, 0))

    # --- Laterais: modela o lado direito e espelha com Mirror ----------------
    lateral = loft("Laterais", [
        [(0.34, -0.30, 0.07), (0.45, -0.30, 0.07), (0.45, -0.30, 0.17), (0.34, -0.30, 0.17)],
        [(0.33, -0.18, 0.06), (0.52, -0.18, 0.06), (0.52, -0.18, 0.22), (0.33, -0.18, 0.22)],
        [(0.33, 0.18, 0.06), (0.52, 0.18, 0.06), (0.52, 0.18, 0.22), (0.33, 0.18, 0.22)],
        [(0.34, 0.34, 0.07), (0.46, 0.34, 0.07), (0.46, 0.34, 0.15), (0.34, 0.34, 0.15)],
    ], M["carenagem"], kart, col, chanfro=0)
    espelho = lateral.modifiers.new("Mirror", "MIRROR")  # Mirror antes do Bevel
    espelho.use_axis = (True, False, False)
    espelho.mirror_object = kart
    bevel(lateral, 0.02)

    faixa = caixa("Laterais_Faixa", (0.43, 0.0, 0.225), (0.14, 0.34, 0.012), M["faixa"], kart, col,
                  chanfro=0.004)
    m2 = faixa.modifiers.new("Mirror", "MIRROR")
    m2.use_axis = (True, False, False)
    m2.mirror_object = kart

    # --- Para-choque traseiro -------------------------------------------------
    caixa("Para_Choque_Traseiro", (0, -0.76, 0.16), (1.10, 0.08, 0.14), M["chassi"], kart, col, chanfro=0.025)
    for lado in (-1, 1):
        cilindro_entre(f"Para_Choque_Suporte_{'D' if lado > 0 else 'E'}", (lado * 0.25, -0.60, 0.10),
                       (lado * 0.25, -0.72, 0.15), 0.018, M["chassi"], kart, col)

    # --- Placa de número (com texto convertido em malha) -----------------------
    caixa("Placa_Numero", (0, 0.47, 0.31), (0.30, 0.012, 0.16), M["branco"], kart, col, chanfro=0.006,
          rot=(math.radians(25), 0, 0))
    bpy.ops.object.text_add(location=(0, 0.4775, 0.3135), rotation=(math.radians(65), 0, math.radians(180)))
    texto = bpy.context.active_object
    texto.data.body = "7"
    texto.data.size = 0.14
    texto.data.extrude = 0.004
    texto.data.align_x = "CENTER"
    texto.data.align_y = "CENTER"
    bpy.ops.object.convert(target="MESH")
    finalizar(texto, "Placa_Numero_Texto", M["preto"], kart, col, suave=False)

    # --- Banco ------------------------------------------------------------
    caixa("Banco_Assento", (0, -0.20, 0.11), (0.38, 0.30, 0.08), M["banco"], kart, col, chanfro=0.03)
    caixa("Banco_Encosto", (0, -0.36, 0.33), (0.40, 0.06, 0.42), M["banco"], kart, col, chanfro=0.025,
          rot=(math.radians(14), 0, 0))

    # --- Motor e escapamento ---------------------------------------------------
    criar_motor(M, kart, col)

    # --- Direção ------------------------------------------------------------
    _, centro_volante = criar_volante(M, kart, col)

    # --- Rodas (cada uma com pivô próprio) -------------------------------------
    criar_roda("Roda_DE", (-0.53, 0.56, 0.14), 0.14, 0.13, -1, M, kart, col)  # dianteira esquerda
    criar_roda("Roda_DD", (0.53, 0.56, 0.14), 0.14, 0.13, 1, M, kart, col)    # dianteira direita
    criar_roda("Roda_TE", (-0.58, -0.50, 0.16), 0.16, 0.20, -1, M, kart, col)  # traseira esquerda
    criar_roda("Roda_TD", (0.58, -0.50, 0.16), 0.16, 0.20, 1, M, kart, col)    # traseira direita

    # --- Piloto -------------------------------------------------------------
    criar_piloto(M, kart, col, aux, centro_volante)
    return kart


# ---------------------------------------------------------------------------
# Estúdio (fundo infinito, luzes e câmera) - não é exportado para o jogo
# ---------------------------------------------------------------------------

def criar_estudio(col):
    # Fundo infinito ("ciclorama"): perfil em L com canto arredondado, extrudado em X
    perfil = [(-6.0, 0.0)]
    raio, y0 = 2.5, 3.5
    for i in range(17):
        a = math.radians(90) * i / 16
        perfil.append((y0 + raio * math.sin(a), raio - raio * math.cos(a)))
    perfil.append((y0 + raio, 8.0))
    verts, faces = [], []
    for x in (-12.0, 12.0):
        for (y, z) in perfil:
            verts.append((x, y, z))
    n = len(perfil)
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))
    malha = bpy.data.meshes.new("Fundo_Estudio")
    malha.from_pydata(verts, [], faces)
    fundo = bpy.data.objects.new("Fundo_Estudio", malha)
    col.objects.link(fundo)
    for p in malha.polygons:
        p.use_smooth = True
    fundo.data.materials.append(material("Fundo_Cinza", (0.62, 0.64, 0.68), rugosidade=0.7))

    def luz(nome, local, energia, tamanho, cor=(1, 1, 1)):
        dados = bpy.data.lights.new(nome, type="AREA")
        dados.energy = energia
        dados.size = tamanho
        dados.color = cor
        obj = bpy.data.objects.new(nome, dados)
        obj.location = local
        col.objects.link(obj)
        rastrear = obj.constraints.new("TRACK_TO")
        rastrear.target = alvo
        rastrear.track_axis = "TRACK_NEGATIVE_Z"
        rastrear.up_axis = "UP_Y"
        return obj

    alvo = bpy.data.objects.new("Alvo_Camera", None)
    alvo.location = (0, 0.1, 0.35)
    col.objects.link(alvo)

    luz("Luz_Principal", (-3.0, -3.0, 4.0), 900, 3.0, (1.0, 0.96, 0.9))
    luz("Luz_Preenchimento", (4.0, -2.5, 2.0), 300, 4.0, (0.85, 0.9, 1.0))
    luz("Luz_Recorte", (0.5, 3.0, 3.5), 600, 2.0)

    cam_dados = bpy.data.cameras.new("Camera")
    cam_dados.lens = 60
    cam = bpy.data.objects.new("Camera", cam_dados)
    cam.location = (0, -5.4, 1.75)
    col.objects.link(cam)
    t = cam.constraints.new("TRACK_TO")
    t.target = alvo
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    bpy.context.scene.camera = cam

    mundo = bpy.data.worlds.new("Mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.7, 1)
    mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    bpy.context.scene.world = mundo
    return fundo, cam, alvo


# ---------------------------------------------------------------------------
# Renderização
# ---------------------------------------------------------------------------

def configurar_render():
    cena = bpy.context.scene
    cena.render.engine = "CYCLES"
    cena.cycles.device = "CPU"
    cena.cycles.samples = 48
    cena.cycles.use_denoising = True
    cena.render.resolution_x = 1600
    cena.render.resolution_y = 1000
    cena.render.film_transparent = False
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.exposure = -0.6
    try:
        cena.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass


def material_wireframe():
    mat = bpy.data.materials.new("Override_Wireframe")
    mat.use_nodes = True
    nos = mat.node_tree.nodes
    links = mat.node_tree.links
    nos.clear()
    saida = nos.new("ShaderNodeOutputMaterial")
    fio = nos.new("ShaderNodeWireframe")
    fio.use_pixel_size = True
    fio.inputs["Size"].default_value = 1.2
    branco = nos.new("ShaderNodeBsdfDiffuse")
    branco.inputs["Color"].default_value = (0.85, 0.87, 0.9, 1)
    linha = nos.new("ShaderNodeEmission")
    linha.inputs["Color"].default_value = (0.02, 0.15, 0.55, 1)
    mistura = nos.new("ShaderNodeMixShader")
    links.new(fio.outputs["Fac"], mistura.inputs["Fac"])
    links.new(branco.outputs["BSDF"], mistura.inputs[1])
    links.new(linha.outputs["Emission"], mistura.inputs[2])
    links.new(mistura.outputs["Shader"], saida.inputs["Surface"])
    return mat


def renderizar(kart, fundo, cam, alvo):
    os.makedirs(PASTA_RENDERS, exist_ok=True)
    cena = bpy.context.scene

    def render(nome, rot_graus, cam_local=(0, -5.4, 1.75), lente=60):
        kart.rotation_euler = (0, 0, math.radians(rot_graus))
        cam.location = cam_local
        cam.data.lens = lente
        cena.render.filepath = os.path.join(PASTA_RENDERS, nome)
        bpy.ops.render.render(write_still=True)
        print("Render salvo:", nome)

    render("01_perspectiva_frontal.png", 215)
    render("02_perspectiva_traseira.png", 35)
    render("03_vista_lateral.png", 270, (0, -6.5, 0.6), 60)
    render("04_vista_frontal.png", 180, (0, -6.5, 0.6), 60)
    render("05_vista_superior.png", 180, (0, -0.4, 6.5), 50)

    # Wireframe (topologia da malha) usando um material de substituição
    cena.view_layers[0].material_override = material_wireframe()
    fundo.hide_render = True
    cena.world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    cena.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 2.0
    render("06_wireframe.png", 215)

    # restaura a cena
    cena.view_layers[0].material_override = None
    fundo.hide_render = False
    cena.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.7, 1)
    cena.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    kart.rotation_euler = (0, 0, math.radians(215))
    cam.location = (0, -5.4, 1.75)
    cam.data.lens = 60


# ---------------------------------------------------------------------------
# Estatísticas e exportação
# ---------------------------------------------------------------------------

def pecas_do_kart(kart):
    """Raiz + descendentes, exceto objetos auxiliares (ex.: cortador do Boolean)."""
    return [o for o in [kart] + list(kart.children_recursive) if not o.name.startswith("Aux_")]


def estatisticas(kart):
    deps = bpy.context.evaluated_depsgraph_get()
    objs = pecas_do_kart(kart)
    malhas = [o for o in objs if o.type == "MESH"]
    vertices = faces = triangulos = 0
    for o in malhas:
        avaliado = o.evaluated_get(deps)
        m = avaliado.to_mesh()
        vertices += len(m.vertices)
        faces += len(m.polygons)
        triangulos += sum(len(p.vertices) - 2 for p in m.polygons)
        avaliado.to_mesh_clear()
    modificadores = sorted({m.type for o in malhas for m in o.modifiers})
    return {
        "objetos_total": len(objs),
        "objetos_malha": len(malhas),
        "vertices": vertices,
        "faces": faces,
        "triangulos": triangulos,
        "materiais": len({s.material.name for o in malhas for s in o.material_slots if s.material}),
        "modificadores_usados": modificadores,
    }


def exportar_glb(kart, caminho):
    kart.rotation_euler = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    for o in pecas_do_kart(kart):
        o.select_set(True)
    bpy.context.view_layer.objects.active = kart
    bpy.ops.export_scene.gltf(
        filepath=caminho,
        export_format="GLB",
        use_selection=True,
        export_apply=True,      # aplica os modificadores na exportação
        export_yup=True,        # Godot usa Y para cima
        export_cameras=False,
        export_lights=False,
    )


def main():
    limpar_cena()
    col_kart = nova_colecao("Kart")
    col_aux = nova_colecao("Auxiliares")
    col_estudio = nova_colecao("Estudio")

    kart = criar_kart(col_kart, col_aux)
    fundo, cam, alvo = criar_estudio(col_estudio)
    configurar_render()

    exportar_glb(kart, os.path.join(PASTA, "kart.glb"))
    stats = estatisticas(kart)
    with open(os.path.join(PASTA, "estatisticas.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print("Estatísticas:", stats)

    if not SO_MODELO:
        renderizar(kart, fundo, cam, alvo)
    else:
        kart.rotation_euler = (0, 0, math.radians(215))

    # Deixa a viewport em modo de visualização de material ao abrir o .blend
    for tela in bpy.data.screens:
        for area in tela.areas:
            if area.type == "VIEW_3D":
                for espaco in area.spaces:
                    if espaco.type == "VIEW_3D":
                        espaco.shading.type = "MATERIAL"

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PASTA, "kart.blend"), compress=True)
    print("Concluído.")


if __name__ == "__main__":
    main()
