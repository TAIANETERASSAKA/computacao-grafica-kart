"""Gera o relatório dos Trabalhos 1 e 2 de Computação Gráfica em PDF.

1. Preencha os dados da capa logo abaixo (DADOS).
2. Rode:  python3 gerar_relatorio.py
   O HTML é convertido em PDF pelo Google Chrome (modo headless). O script faz
   duas passagens: na primeira descobre em que página cai cada seção e, na
   segunda, escreve esses números no sumário.
"""
import html
import os
import re
import shutil
import subprocess
import tempfile

DADOS = {
    "instituicao": "Universidade de São Paulo",
    "curso": "Ciência da Computação",
    "disciplina": "Computação Gráfica",
    "autores": "Taiane\nCaio",   # um nome por linha (\n)
    "professor": "",              # deixe vazio para omitir a linha
    "cidade": "",                 # deixe vazio para mostrar só o ano
    "ano": "2026",
}

PASTA = os.path.dirname(os.path.abspath(__file__))
SAIDA_PDF = os.path.join(PASTA, "Relatorio_CG_Trabalhos_1_e_2.pdf")
SAIDA_HTML = os.path.join(PASTA, "relatorio.html")

# (id, número, título, nível) — usados no sumário
SECOES = [
    ("intro", "1", "INTRODUÇÃO", 1),
    ("t1", "2", "TRABALHO 1 — MODELAGEM 3D DO KART", 1),
    ("t1-concepcao", "2.1", "Concepção do modelo", 2),
    ("t1-metodo", "2.2", "Metodologia", 2),
    ("t1-tecnicas", "2.3", "Técnicas de modelagem", 2),
    ("t1-hierarquia", "2.4", "Hierarquia do modelo", 2),
    ("t1-materiais", "2.5", "Materiais", 2),
    ("t1-render", "2.6", "Iluminação e renderização", 2),
    ("t1-export", "2.7", "Exportação em glTF e conversão de eixos", 2),
    ("t1-result", "2.8", "Resultados", 2),
    ("t2", "3", "TRABALHO 2 — JOGO “KART DAS MOEDAS”", 1),
    ("t2-visao", "3.1", "Visão geral e regras", 2),
    ("t2-arq", "3.2", "Arquitetura do projeto", 2),
    ("t2-modelo", "3.3", "Uso do modelo do Trabalho 1", 2),
    ("t2-fisica", "3.4", "Modelo físico do kart", 2),
    ("t2-camera", "3.5", "Câmera virtual", 2),
    ("t2-luz", "3.6", "Iluminação e ambiente", 2),
    ("t2-shaders", "3.7", "Shaders", 2),
    ("t2-extras", "3.8", "Partículas, áudio e interface", 2),
    ("t2-testes", "3.9", "Testes", 2),
    ("t2-result", "3.10", "Resultados", 2),
    ("conclusao", "4", "CONCLUSÃO", 1),
    ("refs", "", "REFERÊNCIAS", 1),
    ("apendice", "", "APÊNDICE A — COMO EXECUTAR", 1),
]

contador_figuras = [0]
contador_tabelas = [0]


def h(ident):
    num, titulo, nivel = next((n, t, l) for i, n, t, l in SECOES if i == ident)
    tag = "h1" if nivel == 1 else "h2"
    rotulo = f"{num} {titulo}" if num else titulo
    return f'<{tag} id="{ident}">{html.escape(rotulo)}</{tag}>'


def figura(arquivo, legenda, largura="100%", fonte="Elaborado pelo autor (2026)."):
    contador_figuras[0] += 1
    n = contador_figuras[0]
    return (f'<figure><figcaption>Figura {n} – {legenda}</figcaption>'
            f'<img src="imagens/{arquivo}" style="width:{largura}">'
            f'<div class="fonte">Fonte: {fonte}</div></figure>')


def grade(itens, colunas=2):
    """Várias imagens numa figura só (subfiguras a, b, c...)."""
    contador_figuras[0] += 1
    n = contador_figuras[0]
    legenda, imagens = itens
    celulas = "".join(
        f'<div class="sub"><img src="imagens/{a}"><div class="subleg">({chr(97 + i)}) {html.escape(l)}</div></div>'
        for i, (a, l) in enumerate(imagens))
    return (f'<figure><figcaption>Figura {n} – {legenda}</figcaption>'
            f'<div class="grade c{colunas}">{celulas}</div>'
            f'<div class="fonte">Fonte: Elaborado pelo autor (2026).</div></figure>')


def tabela(legenda, cabecalho, linhas, classe=""):
    contador_tabelas[0] += 1
    n = contador_tabelas[0]
    th = "".join(f"<th>{c}</th>" for c in cabecalho)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return (f'<div class="tabela {classe}"><div class="cap">Tabela {n} – {legenda}</div>'
            f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'
            f'<div class="fonte">Fonte: Elaborado pelo autor (2026).</div></div>')


def srgb(r, g, b):
    def c(x):
        x = max(0.0, min(1.0, x))
        return round(255 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055))
    return f"rgb({c(r)},{c(g)},{c(b)})"


def amostra(cor):
    return f'<span class="amostra" style="background:{srgb(*cor)}"></span>'


def sumario(paginas):
    linhas = []
    for ident, num, titulo, nivel in SECOES:
        pag = paginas.get(ident, "")
        classe = "s1" if nivel == 1 else "s2"
        linhas.append(f'<div class="{classe}"><span class="num">{num}</span>'
                      f'<span class="tit">{html.escape(titulo)}</span><span class="pontos"></span>'
                      f'<span class="pag">{pag}</span></div>')
    return "\n".join(linhas)


def diagrama_estados():
    caixa = lambda x, y, t, w=150: (
        f'<rect x="{x}" y="{y}" width="{w}" height="46" rx="10" fill="#eef2fb" stroke="#1d3f8f" stroke-width="2"/>'
        f'<text x="{x + w / 2}" y="{y + 29}" text-anchor="middle" font-size="16" font-weight="bold" fill="#1d3f8f">{t}</text>')
    seta = lambda d, txt, tx, ty: (
        f'<path d="{d}" fill="none" stroke="#333" stroke-width="1.6" marker-end="url(#ponta)"/>'
        f'<text x="{tx}" y="{ty}" text-anchor="middle" font-size="12.5" fill="#333">{txt}</text>')
    return f'''<svg viewBox="0 0 760 285" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="Liberation Sans, Arial">
<defs><marker id="ponta" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#333"/></marker></defs>
{caixa(10, 75, "MENU")}{caixa(205, 75, "CONTAGEM")}{caixa(400, 75, "JOGANDO")}{caixa(610, 75, "FIM", 140)}
{caixa(400, 215, "PAUSA")}
{seta("M160,98 L201,98", "Enter", 180, 66)}
{seta("M355,98 L396,98", "3 s", 375, 66)}
{seta("M550,98 L606,98", "tempo = 0", 578, 66)}
{seta("M680,75 C680,22 280,22 280,71", "Enter (jogar de novo)", 480, 26)}
{seta("M460,121 L460,211", "Esc", 444, 170)}
{seta("M490,215 L490,125", "Esc", 507, 170)}
{seta("M400,238 C200,238 85,205 85,125", "Q (voltar ao menu)", 215, 262)}
</svg>'''


def conteudo(paginas):
    D = {k: html.escape(v).replace("\n", "<br>") for k, v in DADOS.items()}
    D["local_ano"] = f'{D["cidade"]}<br>{D["ano"]}' if D["cidade"] else D["ano"]
    D["linha_professor"] = f'<br><br>Professor(a): {D["professor"]}' if D["professor"] else ""
    contador_figuras[0] = 0
    contador_tabelas[0] = 0
    p = []
    add = p.append

    # ---------------- Capa, folha de rosto, resumo e sumário ----------------
    add(f'''<section class="capa">
<div class="topo">{D["instituicao"]}<br>{D["curso"]}</div>
<div class="autor">{D["autores"]}</div>
<div class="titulo">MODELAGEM 3D DE UM KART E DESENVOLVIMENTO DO JOGO “KART DAS MOEDAS” NO GODOT</div>
<div class="subtitulo">Relatório dos Trabalhos 1 e 2 da disciplina de {D["disciplina"]}</div>
<div class="rodape">{D["local_ano"]}</div>
</section>''')

    add(f'''<section class="capa rosto">
<div class="autor">{D["autores"]}</div>
<div class="titulo">MODELAGEM 3D DE UM KART E DESENVOLVIMENTO DO JOGO “KART DAS MOEDAS” NO GODOT</div>
<div class="natureza">Relatório apresentado à disciplina de {D["disciplina"]} do curso de {D["curso"]}
da {D["instituicao"]}, como requisito parcial para avaliação dos Trabalhos 1 (Modelagem) e 2 (Jogo 3D).{D["linha_professor"]}</div>
<div class="rodape">{D["local_ano"]}</div>
</section>''')

    add('''<section class="pre"><h1 class="semnum">RESUMO</h1>
<p>Este relatório descreve o desenvolvimento de dois trabalhos encadeados da disciplina de Computação Gráfica.
No Trabalho 1 foi modelado, no Blender 4.5 LTS, um kart de corrida com piloto, composto por 81 malhas
(cerca de 22 mil triângulos) e 15 materiais PBR. A modelagem foi feita de forma procedural por meio da API
Python do Blender e empregou primitivas, transformações geométricas, <i>loft</i> de seções transversais e os
modificadores Bevel, Mirror, Array, Subdivision Surface e Boolean; o modelo foi organizado em hierarquia,
renderizado com o Cycles e exportado em glTF 2.0. No Trabalho 2 esse modelo foi utilizado como personagem
principal do jogo 3D “Kart das Moedas”, desenvolvido no Godot 4.7, no qual o jogador deve coletar o maior
número de moedas em 60 segundos. O jogo explora transformações hierárquicas (rodas que giram e esterçam),
física de veículo do tipo <i>arcade</i>, câmera virtual com suavização exponencial, iluminação com sombras,
<i>shaders</i> procedurais escritos em linguagem de <i>shading</i> do Godot, sistemas de partículas e interface
2D sobreposta à cena 3D. O resultado é um jogo completo, testado de forma automatizada e exportado como
executável para Linux e Windows.</p>
<p class="chave"><b>Palavras-chave:</b> computação gráfica; modelagem 3D; Blender; Godot; shaders; jogos digitais.</p>
</section>''')

    add(f'<section class="pre"><h1 class="semnum">SUMÁRIO</h1><div class="sumario">{sumario(paginas)}</div></section>')

    # ---------------- 1 Introdução ----------------
    add('<section class="corpo">')
    add(h("intro"))
    add('''<p>A Computação Gráfica estuda a representação, a manipulação e a síntese de imagens de objetos
por computador. Dois de seus pilares são a <b>modelagem geométrica</b>, que descreve a forma e a aparência
dos objetos, e a <b>síntese de imagens em tempo real</b>, que transforma esses modelos em quadros
interativos — base dos jogos digitais (HUGHES <i>et al.</i>, 2013; MARSCHNER; SHIRLEY, 2021).</p>
<p>Os dois trabalhos descritos aqui percorrem esse caminho completo. No <b>Trabalho 1</b>, um kart com
piloto foi modelado no Blender. No <b>Trabalho 2</b>, o mesmo modelo foi importado no motor de jogos Godot
e transformado no personagem controlado pelo jogador em um jogo 3D de coleta de moedas.</p>
<p>As ferramentas utilizadas foram o <b>Blender 4.5 LTS</b> (modelagem, materiais e renderização), a
linguagem <b>Python</b> (automação da modelagem e geração de sons), o <b>Godot Engine 4.7</b> com a
linguagem <b>GDScript</b> (jogo) e a linguagem de <i>shading</i> do Godot, derivada do GLSL (efeitos
visuais). Todas são livres e de código aberto.</p>''')

    # ---------------- 2 Trabalho 1 ----------------
    add(h("t1"))
    add(h("t1-concepcao"))
    add('''<p>O objeto escolhido foi um <b>kart de competição</b>: um veículo pequeno, de estrutura aparente,
que reúne formas variadas — superfícies planas com arestas arredondadas (carenagem), sólidos de revolução
(rodas, tubos e escapamento), peças repetidas (aletas do motor, porcas das rodas) e formas orgânicas
(piloto). Isso permite exercitar diferentes técnicas de modelagem em um único modelo.</p>
<p>As dimensões seguem as de um kart real, em metros: aproximadamente 1,8 m de comprimento, 1,3 m de
largura e 0,9 m de altura até o topo do capacete. Adotou-se a convenção de eixos do Blender: <i>X</i> aponta
para a direita do kart, <i>Y</i> para a frente e <i>Z</i> para cima, com o chão no plano <i>Z</i> = 0. A Figura 1 mostra o
resultado final.</p>''')
    add(figura("modelo_01_perspectiva_frontal.jpg", "Kart modelado, renderizado em perspectiva (Cycles)", "92%"))
    add(h("t1-metodo"))
    add('''<p>Em vez de posicionar cada vértice manualmente na interface, o modelo foi construído por um
<b>script Python</b> (<code>modelar_kart.py</code>) que usa a API <code>bpy</code> do Blender. O script
chama os mesmos operadores disponíveis na interface (adicionar primitiva, aplicar escala, adicionar
modificador, unir objetos etc.), de modo que o resultado é um arquivo <code>.blend</code> comum, totalmente
editável. Essa abordagem tem três vantagens: (i) o modelo é <b>reprodutível</b> — basta executar o script
para recriá-lo; (ii) as medidas são <b>precisas</b>; e (iii) o próprio código documenta cada etapa da
modelagem.</p>
<p>O script também monta um estúdio fotográfico virtual, renderiza as imagens de apresentação e exporta o
modelo para o jogo, como descrito nas seções seguintes.</p>''')
    add(h("t1-tecnicas"))
    add('<p>A Tabela 1 relaciona as técnicas empregadas às peças em que foram usadas.</p>')
    add(tabela("Técnicas de modelagem utilizadas", ["Técnica", "Aplicação no modelo"], [
        ["Primitivas geométricas (cubo, cilindro, esfera UV, toro)", "Base de quase todas as peças"],
        ["Transformações geométricas (translação, rotação, escala)", "Posicionamento e orientação das peças; cilindros orientados por quatérnio entre dois pontos (braços, pernas e tubos)"],
        ["<i>Loft</i> de seções transversais (malha criada vértice a vértice com <code>bmesh</code>)", "Carenagem frontal (3 seções) e laterais (4 seções)"],
        ["Modificador <b>Bevel</b> com <i>harden normals</i>", "Arredondamento das arestas da carenagem, do banco, dos pneus e do para-choque"],
        ["Modificador <b>Mirror</b>", "Laterais modeladas só do lado direito e espelhadas no eixo X"],
        ["Modificador <b>Array</b>", "Aletas de refrigeração do motor (1 peça repetida 5 vezes)"],
        ["Modificador <b>Subdivision Surface</b>", "Tronco do piloto (<i>box modeling</i>)"],
        ["Modificador <b>Boolean</b> (interseção)", "Viseira do capacete (esfera ∩ caixa auxiliar)"],
        ["Curva de Bézier com perfil circular", "Tubo do escapamento, convertido em malha"],
        ["Texto 3D", "Número “7” da placa, convertido em malha"],
        ["União de malhas (<i>Join</i>)", "Volante: aro (toro) + 3 raios + cubo"],
        ["Coordenadas polares", "Distribuição das 5 porcas de cada roda em círculo"],
        ["Suavização por ângulo", "Superfícies curvas suaves com arestas vivas preservadas"],
    ]))
    add('''<p>Os <b>modificadores</b> são operações não destrutivas: ficam empilhados sobre a malha original e
podem ser ajustados a qualquer momento. O Mirror, por exemplo, garante simetria perfeita entre as laterais,
e o Boolean permitiu obter a viseira curva do capacete como a interseção de uma esfera ligeiramente maior que
o capacete com uma caixa que delimita a faixa frontal. Na exportação, todos os modificadores são aplicados
e convertidos em geometria final.</p>''')
    add(h("t1-hierarquia"))
    add('''<p>As peças foram organizadas em uma <b>hierarquia pai-filho</b> (grafo de cena), mostrada no
Quadro 1. A raiz é um objeto vazio (<i>empty</i>) chamado <code>Kart</code>. Cada roda possui um vazio
próprio posicionado exatamente no centro do eixo, que funciona como <b>pivô</b>: girar esse nó gira todas as
partes da roda (pneu, aro, cubo e porcas) em torno do eixo correto. Essa decisão de modelagem foi pensada
para o Trabalho 2, em que as rodas são animadas.</p>
<div class="quadro"><div class="cap">Quadro 1 – Hierarquia do modelo</div><pre>
Kart (vazio, raiz)
├── Chassi_*, Carenagem_*, Laterais, Para_Choque_*, Placa_*, Banco_*
├── Motor_*, Escapamento, Escapamento_Silenciador
├── Coluna_Direcao, Volante
├── Roda_DE / Roda_DD / Roda_TE / Roda_TD   (vazios no centro de cada eixo)
│   └── _Pneu, _Aro, _Cubo, _Porca1 … _Porca5
└── Piloto (vazio)
    └── Tronco, Pescoço, Capacete, Viseira, Braços, Luvas, Pernas, Sapatos
</pre><div class="fonte">Fonte: Elaborado pelo autor (2026).</div></div>''')
    add(h("t1-materiais"))
    add('''<p>Foram criados 15 materiais baseados no modelo físico <b>PBR</b> (<i>Physically Based
Rendering</i>) por meio do nó Principled BSDF, parametrizados por cor base, metalicidade e rugosidade
(Tabela 2). Na carenagem e no capacete foi acrescentada uma camada de verniz (<i>coat</i>), que produz o
reflexo brilhante característico de plástico pintado.</p>''')
    mats = [
        ("Carenagem vermelha", (0.75, 0.015, 0.01), "0,0", "0,30", "Verniz 0,5"),
        ("Faixa amarela", (1.0, 0.60, 0.0), "0,0", "0,35", ""),
        ("Placa branca", (0.90, 0.90, 0.88), "0,0", "0,40", ""),
        ("Número / volante", (0.01, 0.01, 0.01), "0,0", "0,45", ""),
        ("Borracha do pneu", (0.015, 0.015, 0.015), "0,0", "0,85", ""),
        ("Aro metálico", (0.80, 0.80, 0.82), "1,0", "0,25", ""),
        ("Cubo da roda", (0.10, 0.10, 0.12), "0,8", "0,35", ""),
        ("Chassi metálico", (0.08, 0.09, 0.10), "0,7", "0,40", ""),
        ("Banco", (0.03, 0.03, 0.035), "0,0", "0,55", ""),
        ("Alumínio do motor", (0.62, 0.63, 0.65), "1,0", "0,38", ""),
        ("Escapamento cromado", (0.90, 0.90, 0.92), "1,0", "0,12", ""),
        ("Macacão azul", (0.02, 0.12, 0.65), "0,0", "0,60", ""),
        ("Capacete amarelo", (1.0, 0.55, 0.0), "0,0", "0,25", "Verniz 0,4"),
        ("Viseira fumê", (0.02, 0.02, 0.03), "0,3", "0,05", ""),
        ("Luvas e sapatos", (0.02, 0.02, 0.02), "0,0", "0,70", ""),
    ]
    add(tabela("Materiais PBR do modelo", ["", "Material", "Metalicidade", "Rugosidade", "Obs."],
               [[amostra(c), n, m, r, o] for n, c, m, r, o in mats], "compacta"))
    add(h("t1-render"))
    add('''<p>As imagens de apresentação foram geradas com o <b>Cycles</b>, o renderizador de traçado de
caminhos (<i>path tracing</i>) do Blender, com 48 amostras por pixel e remoção de ruído (<i>denoising</i>).
A cena de estúdio, também criada pelo script, é composta por:</p>
<ul>
<li>um <b>fundo infinito</b> (ciclorama): um perfil em “L” com o canto arredondado por um quarto de
circunferência, extrudado ao longo do eixo X, que elimina a linha do horizonte;</li>
<li><b>iluminação de três pontos</b> com luzes de área: principal (900 W, quente), preenchimento (300 W, fria)
e recorte (600 W, por trás), todas apontadas para o kart por uma restrição <i>Track To</i>;</li>
<li>câmera com lente de 60 mm e mapeamento de cores AgX.</li>
</ul>
<p>Para as vistas, em vez de mover a câmera, o kart é girado em torno do eixo Z. A imagem de
<i>wireframe</i> foi obtida com um material de substituição que usa o nó <i>Wireframe</i> para desenhar as
arestas da malha triangulada sobre uma superfície clara, evidenciando a topologia.</p>''')
    add(h("t1-export"))
    add('''<p>O modelo foi exportado no formato <b>glTF 2.0</b> binário (<code>kart.glb</code>), padrão aberto
do Khronos Group para transmissão de cenas 3D (KHRONOS GROUP, 2021), com os modificadores aplicados. Como o
Blender usa <i>Z</i> para cima e o glTF usa <i>Y</i> para cima, o exportador aplica a mudança de base</p>
<div class="eq"><math display="block"><mrow><mo>(</mo><msub><mi>x</mi><mi>g</mi></msub><mo>,</mo><msub><mi>y</mi><mi>g</mi></msub><mo>,</mo><msub><mi>z</mi><mi>g</mi></msub><mo>)</mo><mo>=</mo><mo>(</mo><msub><mi>x</mi><mi>b</mi></msub><mo>,</mo><msub><mi>z</mi><mi>b</mi></msub><mo>,</mo><mo>−</mo><msub><mi>y</mi><mi>b</mi></msub><mo>)</mo></mrow></math><span class="eqn">(1)</span></div>
<p>tanto aos vértices quanto às transformações de cada nó. Assim, a frente do kart, modelada apontando para
+<i>Y</i> no Blender, passa a apontar para −<i>Z</i> no Godot — exatamente a direção “para frente” de um nó 3D
nesse motor. Isso evitou qualquer rotação corretiva no jogo.</p>''')
    add(h("t1-result"))
    add(tabela("Estatísticas do modelo final", ["Item", "Valor"], [
        ["Objetos (total / malhas)", "87 / 81"], ["Vértices", "11.229"], ["Faces", "10.699"],
        ["Triângulos", "22.054"], ["Materiais", "15"],
        ["Modificadores usados", "Array, Bevel, Boolean, Mirror, Subdivision Surface"],
        ["Tamanho do arquivo .glb", "660 KB"]], "estreita"))
    add('<p>As Figuras 2 e 3 apresentam outras vistas do modelo e a topologia de sua malha.</p>')
    add(grade(("Vistas do modelo", [
        ("modelo_02_perspectiva_traseira.jpg", "perspectiva traseira"),
        ("modelo_03_vista_lateral.jpg", "vista lateral direita"),
        ("modelo_04_vista_frontal.jpg", "vista frontal"),
        ("modelo_05_vista_superior.jpg", "vista superior")])))
    add(figura("modelo_06_wireframe.jpg", "Topologia da malha (wireframe)", "80%"))

    # ---------------- 3 Trabalho 2 ----------------
    add(h("t2"))
    add(h("t2-visao"))
    add('''<p>“Kart das Moedas” é um jogo 3D em que o jogador pilota o kart do Trabalho 1 em uma arena
fechada e precisa <b>coletar o maior número de moedas em 60 segundos</b>. Há sempre 12 moedas na arena;
cada moeda coletada vale um ponto e é substituída por outra em posição aleatória livre de obstáculos.
Periodicamente surge um <b>relógio</b> azul que acrescenta 5 segundos ao cronômetro. Quatro <b>faixas de
turbo</b> no chão dão um impulso de velocidade, e a arena contém cones que podem ser derrubados, pilhas de
pneus e uma ilha central com uma bandeira quadriculada. O recorde é salvo em disco. Os controles estão na
Tabela 4.</p>''')
    add(tabela("Controles do jogo", ["Tecla", "Ação"], [
        ["W / ↑", "acelerar"], ["S / ↓", "frear e dar ré"], ["A, D / ←, →", "virar"],
        ["Espaço", "freio de mão (derrapagem)"], ["C", "alternar câmera (perseguição / aérea)"],
        ["R", "voltar à largada"], ["Esc ou P", "pausar (Q volta ao menu)"], ["Enter", "começar / jogar de novo"]],
        "estreita"))
    add(h("t2-arq"))
    add('''<p>No Godot, um jogo é composto por <b>cenas</b> — árvores de nós reutilizáveis — e por
<b>scripts</b> associados aos nós. A Tabela 5 resume os principais arquivos do projeto.</p>''')
    add(tabela("Cenas e scripts do projeto", ["Arquivo", "Responsabilidade"], [
        ["<code>main.tscn</code> / <code>main.gd</code>", "Arena, iluminação, ambiente e máquina de estados do jogo; criação de moedas e relógios; pontuação, tempo e recorde"],
        ["<code>kart.tscn</code> / <code>kart.gd</code>", "Corpo físico (<code>CharacterBody3D</code>) com o modelo glTF; controle, física, animação das rodas, partículas e som do motor"],
        ["<code>camera_seguidora.gd</code>", "Câmera de perseguição, aérea e de vitrine (menu)"],
        ["<code>moeda.tscn</code>, <code>relogio.tscn</code> / <code>coletavel.gd</code>", "Itens coletáveis com animação e detecção por <code>Area3D</code>"],
        ["<code>turbo.tscn</code> / <code>turbo.gd</code>", "Faixa de turbo"],
        ["<code>cone.tscn</code>, <code>pneus.tscn</code>", "Obstáculos (cone com corpo rígido; pneus estáticos)"],
        ["<code>hud.tscn</code> / <code>hud.gd</code>", "Interface 2D: placar, tempo, velocímetro e telas de menu, pausa e fim"],
        ["<code>decoracao.gd</code>", "Geração procedural das árvores ao redor da arena"],
        ["<code>shaders/*.gdshader</code>", "Asfalto, grama, listras, turbo e bandeira"],
    ]))
    add('''<p>O fluxo do jogo é controlado por uma <b>máquina de estados finitos</b> (Figura 4). Durante a pausa,
a árvore de cena é suspensa (<code>get_tree().paused</code>), o que congela física, animações e áudio, enquanto
a interface continua respondendo porque seu modo de processamento é <i>Always</i>.</p>''')
    contador_figuras[0] += 1
    add(f'<figure><figcaption>Figura {contador_figuras[0]} – Máquina de estados do jogo</figcaption>'
        f'{diagrama_estados()}<div class="fonte">Fonte: Elaborado pelo autor (2026).</div></figure>')
    add(h("t2-modelo"))
    add('''<p>A cena do kart instancia <code>kart.glb</code> como filho de um <code>CharacterBody3D</code>. Graças
à hierarquia criada no Trabalho 1, o script localiza os nós <code>Roda_DE</code>, <code>Roda_DD</code>,
<code>Roda_TE</code>, <code>Roda_TD</code> e <code>Volante</code> e os anima a cada passo de física.</p>
<p><b>Rolagem das rodas.</b> Para uma roda que rola sem deslizar, o ângulo girado é a distância percorrida
dividida pelo raio:</p>
<div class="eq"><math display="block"><mrow><mi>θ</mi><mo>=</mo><mo>−</mo><mfrac><mi>d</mi><mi>r</mi></mfrac></mrow></math><span class="eqn">(2)</span></div>
<p>onde <i>d</i> é a distância acumulada e <i>r</i> é 0,14 m nas rodas dianteiras e 0,16 m nas traseiras. O
sinal negativo vem da regra da mão direita: para o kart andar em −<i>Z</i>, o topo da roda deve se mover
para −<i>Z</i>, o que corresponde a uma rotação negativa em torno de +<i>X</i>.</p>
<p><b>Esterço.</b> As rodas dianteiras combinam a rolagem (eixo <i>X</i>) com o esterço φ (eixo <i>Y</i>). A
orientação de cada roda é obtida por composição de matrizes de rotação a partir da orientação original
<i>B</i><sub>0</sub>:</p>
<div class="eq"><math display="block"><mrow><mi>B</mi><mo>=</mo><msub><mi>B</mi><mn>0</mn></msub><mo>·</mo><msub><mi>R</mi><mi>y</mi></msub><mo>(</mo><mi>φ</mi><mo>)</mo><mo>·</mo><msub><mi>R</mi><mi>x</mi></msub><mo>(</mo><mi>θ</mi><mo>)</mo></mrow></math><span class="eqn">(3)</span></div>
<p>que é exatamente a ordem de Euler YXZ usada pelo Godot: primeiro a roda esterça e, no referencial já
esterçado, ela rola. Se a ordem fosse invertida, a roda giraria em torno de um eixo inclinado. O volante gira
em torno do eixo da coluna de direção, e a carroceria (nó <code>Modelo</code>) inclina para fora nas curvas e
“empina” levemente ao acelerar.</p>''')
    add(figura("jogo_09_esterco.jpg", "Rodas dianteiras e volante esterçados para a esquerda (kart parado)", "85%"))
    add(h("t2-fisica"))
    add('''<p>Foi adotado um modelo físico do tipo <i>arcade</i>, mais previsível e divertido que uma simulação
de pneus. O kart guarda uma velocidade escalar <i>v</i> ao longo de sua frente, atualizada com aceleração,
frenagem e atrito constantes (velocidade máxima de 20 m/s, ou 72 km/h). A rotação em torno do eixo vertical
é proporcional ao comando de direção <i>s</i> ∈ [−1, 1] e cresce com a velocidade, de modo que o kart parado
não gira:</p>
<div class="eq"><math display="block"><mrow><mi>ω</mi><mo>=</mo><mi>s</mi><mo>·</mo><msub><mi>ω</mi><mi>máx</mi></msub><mo>·</mo><mtext>clamp</mtext><mo>(</mo><mfrac><mrow><mo>|</mo><mi>v</mi><mo>|</mo></mrow><mn>5</mn></mfrac><mo>,</mo><mn>0</mn><mo>,</mo><mn>1</mn><mo>)</mo><mo>·</mo><mtext>sinal</mtext><mo>(</mo><mi>v</mi><mo>)</mo></mrow></math><span class="eqn">(4)</span></div>
<p>A velocidade real no plano, <b>u</b>, não muda instantaneamente para a direção da frente <b>f</b>; ela é
interpolada com uma taxa de <b>aderência</b> <i>a</i>:</p>
<div class="eq"><math display="block"><mrow><msub><mi mathvariant="bold">u</mi><mrow><mi>t</mi><mo>+</mo><mi>Δ</mi><mi>t</mi></mrow></msub><mo>=</mo><mtext>lerp</mtext><mo>(</mo><msub><mi mathvariant="bold">u</mi><mi>t</mi></msub><mo>,</mo><mspace width="0.2em"/><mi mathvariant="bold">f</mi><mi>v</mi><mo>,</mo><mspace width="0.2em"/><mn>1</mn><mo>−</mo><msup><mi>e</mi><mrow><mo>−</mo><mi>a</mi><mi>Δ</mi><mi>t</mi></mrow></msup><mo>)</mo></mrow></math><span class="eqn">(5)</span></div>
<p>Com <i>a</i> = 9 o kart “gruda” no chão; ao puxar o freio de mão, <i>a</i> cai para 1,8 e a velocidade
passa a ter uma componente lateral — a <b>derrapagem</b> (<i>drift</i>), que dispara as partículas de fumaça.
O termo 1 − <i>e</i><sup>−<i>a</i>Δ<i>t</i></sup> torna o comportamento independente da taxa de quadros. A
colisão com o cenário é resolvida por <code>move_and_slide</code>: o kart desliza ao longo das paredes,
quica para trás em batidas frontais fortes e aplica impulsos nos cones, que são corpos rígidos simulados pelo
motor de física Jolt.</p>''')
    add(h("t2-camera"))
    add('''<p>A câmera virtual usa projeção perspectiva e possui três modos: <b>vitrine</b> (órbita lenta ao
redor do kart no menu e no fim de jogo), <b>perseguição</b> (atrás e acima do kart) e <b>aérea</b>. Em todos,
a posição desejada <b>p</b>* é calculada a partir do kart e a câmera se aproxima dela com suavização
exponencial:</p>
<div class="eq"><math display="block"><mrow><msub><mi mathvariant="bold">p</mi><mrow><mi>t</mi><mo>+</mo><mi>Δ</mi><mi>t</mi></mrow></msub><mo>=</mo><msub><mi mathvariant="bold">p</mi><mi>t</mi></msub><mo>+</mo><mo>(</mo><msup><mi mathvariant="bold">p</mi><mo>*</mo></msup><mo>−</mo><msub><mi mathvariant="bold">p</mi><mi>t</mi></msub><mo>)</mo><mo>(</mo><mn>1</mn><mo>−</mo><msup><mi>e</mi><mrow><mo>−</mo><mi>k</mi><mi>Δ</mi><mi>t</mi></mrow></msup><mo>)</mo></mrow></math><span class="eqn">(6)</span></div>
<p>A orientação é definida por <code>look_at</code>, que constrói a base da câmera a partir do vetor que
aponta para o alvo e do vetor “para cima”. O <b>campo de visão</b> aumenta de 70° até 82° com a velocidade,
reforçando a sensação de rapidez, e um tremor aleatório de curta duração é aplicado após batidas. Com a
interpolação de física ativada no projeto, o movimento fica suave mesmo em monitores acima de 60 Hz.</p>''')
    add(h("t2-luz"))
    add('''<ul>
<li><b>Luz direcional</b> (sol) com <b>mapas de sombra</b> até 70 m de distância;</li>
<li><b>céu procedural</b>, que também fornece a luz ambiente e os reflexos;</li>
<li><b>luzes pontuais</b> (<code>OmniLight3D</code>) dentro das moedas e dos relógios, que iluminam o asfalto
ao redor;</li>
<li>pós-processamento: mapeamento de tons Filmic, <i>glow</i> (<i>bloom</i>) nos materiais emissivos,
oclusão de ambiente em espaço de tela (SSAO) e neblina exponencial leve;</li>
<li>materiais PBR vindos do glTF e materiais emissivos para moedas, relógios e turbo.</li>
</ul>''')
    add(h("t2-shaders"))
    add('''<p>Cinco <i>shaders</i> foram escritos na linguagem de <i>shading</i> do Godot. Nenhum usa textura de
imagem: tudo é calculado no processador gráfico (GPU) a cada pixel ou vértice.</p>
<ul>
<li><b>Asfalto</b> (<i>fragment</i>): ruído de valor (<i>value noise</i>) em duas escalas, com interpolação
suavizada <i>f</i>² (3 − 2<i>f</i>), gera a textura do asfalto; a linha branca da borda e a faixa
quadriculada da largada são obtidas pelas coordenadas de mundo do pixel.</li>
<li><b>Grama</b> (<i>fragment</i>): três oitavas de ruído misturam dois tons de verde.</li>
<li><b>Listras</b> (<i>fragment</i>): <code>step(0.5, fract((x + y + z) / 2L))</code> produz as listras diagonais
vermelhas e brancas dos muros e da zebra, contínuas entre objetos diferentes por usarem a posição no mundo.</li>
<li><b>Turbo</b> (<i>fragment</i>): setas em “V” definidas por <code>fract(v·n − |u − 0,5|·1,4 + t·vel)</code>,
que deslizam com o tempo e emitem luz.</li>
<li><b>Bandeira</b> (<i>vertex</i> + <i>fragment</i>): os vértices de um plano subdividido são deslocados por uma
onda senoidal cuja amplitude cresce do mastro para a ponta; a normal é recalculada pela derivada da onda
para que a iluminação acompanhe as dobras (Quadro 2).</li>
</ul>
<div class="quadro"><div class="cap">Quadro 2 – <i>Vertex shader</i> da bandeira</div><pre class="codigo">void vertex() {
    // UV.x = 0 no mastro (fixo) e 1 na ponta (balança mais)
    float onda = sin(UV.x * frequencia * TAU - TIME * velocidade);
    VERTEX.y += onda * amplitude * UV.x;
    // normal aproximada pela derivada da onda
    float derivada = cos(UV.x * frequencia * TAU - TIME * velocidade)
                     * amplitude * UV.x * frequencia;
    NORMAL = normalize(vec3(-derivada, 1.0, 0.0));
}</pre><div class="fonte">Fonte: Elaborado pelo autor (2026).</div></div>''')
    add(h("t2-extras"))
    add('''<p><b>Partículas.</b> Três sistemas (<code>CPUParticles3D</code>) foram criados por código: fumaça nas
rodas traseiras durante a derrapagem, chama no escapamento durante o turbo (mistura aditiva) e uma explosão
de partículas ao coletar itens. As partículas usam <i>billboards</i> — quadriláteros sempre voltados para a
câmera — com uma textura de gradiente radial gerada em tempo de execução e cor que se apaga ao longo da vida
da partícula.</p>
<p><b>Instanciação.</b> As árvores ao redor da arena são geradas proceduralmente com semente fixa: todas
compartilham as mesmas malhas (tronco, copa cônica ou esférica) e variam apenas a transformação (posição,
rotação e escala).</p>
<p><b>Áudio.</b> Os efeitos sonoros (moeda, relógio, turbo, batida, contagem regressiva, fim de jogo e motor)
foram sintetizados em Python a partir de senoides, harmônicos e ruído filtrado. O som do motor é um laço
contínuo cuja frequência (<i>pitch</i>) acompanha a velocidade do kart.</p>
<p><b>Interface.</b> O HUD (moedas, cronômetro, recorde e velocímetro) e as telas de menu, pausa e fim são
nós 2D desenhados sobre a cena 3D em uma <code>CanvasLayer</code>. As placas da arena usam texto 3D
(<code>Label3D</code>) com a fonte livre Russo One.</p>''')
    add(h("t2-testes"))
    add('''<p>Além dos testes manuais, foram escritos <b>roteiros de teste automatizados</b> em GDScript que
carregam a cena principal, simulam as entradas do jogador (iniciar, acelerar, virar, derrapar, trocar de
câmera, pausar) e registram o estado do jogo a cada segundo. Os roteiros foram executados em modo
<i>headless</i> (sem janela), para checar a lógica, e com janela, para capturar as telas deste relatório.
Os testes revelaram e permitiram corrigir, por exemplo:</p>
<ul>
<li>o kart ficava <b>preso</b> após bater de frente num obstáculo: a colisão zerava a velocidade e, sem
velocidade, ele não conseguia virar. Foram adicionados o quique para trás em batidas fortes e um giro lento
quando o jogador acelera encostado em algo;</li>
<li>a câmera ficava distante demais em alta velocidade, o que foi corrigido com o ajuste da constante de
suavização <i>k</i>;</li>
<li>detalhes de interface, como a concordância “1 moeda” / “2 moedas”.</li>
</ul>
<p>O projeto também foi testado a partir de uma cópia limpa (sem cache), simulando a entrega, e exportado
como executável para Linux e Windows.</p>''')
    add(h("t2-result"))
    add('<p>As Figuras 6 a 8 mostram o jogo em funcionamento.</p>')
    add(figura("jogo_01_menu.jpg", "Menu principal, com a câmera orbitando o kart"))
    add(grade(("Partida em andamento", [
        ("jogo_03_corrida.jpg", "largada com câmera de perseguição"),
        ("jogo_04_drift.jpg", "derrapagem com fumaça"),
        ("jogo_05_turbo.jpg", "faixa de turbo e chama do escapamento"),
        ("jogo_06_aerea.jpg", "câmera aérea")])))
    add(grade(("Telas de pausa e de fim de jogo", [
        ("jogo_07_pausa.jpg", "pausa"), ("jogo_08_fim.jpg", "fim de jogo")])))

    # ---------------- 4 Conclusão ----------------
    add(h("conclusao"))
    add('''<p>Os dois trabalhos formaram um ciclo completo de produção gráfica: da construção geométrica de um
objeto à sua exibição interativa em tempo real. No Trabalho 1, a combinação de primitivas, transformações e
modificadores não destrutivos resultou em um modelo detalhado e leve (cerca de 22 mil triângulos), adequado a
um jogo. A decisão de organizar o modelo em hierarquia, com pivôs no centro das rodas, mostrou-se essencial
no Trabalho 2, em que rodas e volante são animados por composição de rotações.</p>
<p>No Trabalho 2 foram aplicados, em um produto jogável, conceitos centrais da disciplina: transformações
geométricas e mudança de base, grafo de cena, câmera virtual, iluminação e sombras, materiais PBR,
<i>shaders</i> de vértice e de fragmento, ruído procedural, sistemas de partículas e interfaces sobrepostas.
Como trabalhos futuros, sugerem-se uma pista com voltas cronometradas, adversários controlados por
inteligência artificial e o alinhamento do kart à inclinação do terreno, permitindo rampas.</p>''')

    # ---------------- Referências ----------------
    add(h("refs"))
    add('''<div class="refs">
<p>BLENDER FOUNDATION. <b>Blender 4.5 LTS Reference Manual</b>. Amsterdam, 2025. Disponível em:
https://docs.blender.org/manual/en/4.5/. Acesso em: 21 nov. 2026.</p>
<p>GODOT ENGINE. <b>Godot Engine documentation</b>. [S. l.], 2026. Disponível em:
https://docs.godotengine.org/en/stable/. Acesso em: 21 nov. 2026.</p>
<p>HUGHES, J. F. <i>et al.</i> <b>Computer graphics</b>: principles and practice. 3. ed. Upper Saddle River:
Addison-Wesley, 2013.</p>
<p>KHRONOS GROUP. <b>glTF 2.0 specification</b>. Beaverton, 2021. Disponível em:
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html. Acesso em: 21 nov. 2026.</p>
<p>LEMONAD, J. <b>Russo One</b>. [S. l.]: Google Fonts, 2012. Fonte tipográfica sob licença SIL Open Font
License 1.1. Disponível em: https://fonts.google.com/specimen/Russo+One. Acesso em: 21 nov. 2026.</p>
<p>MARSCHNER, S.; SHIRLEY, P. <b>Fundamentals of computer graphics</b>. 5. ed. Boca Raton: CRC Press, 2021.</p>
</div>''')

    # ---------------- Apêndice ----------------
    add(h("apendice"))
    add('''<p>Os arquivos estão organizados como mostra o Quadro 3.</p>
<div class="quadro"><div class="cap">Quadro 3 – Organização dos arquivos entregues</div><pre>
Trabalho1-Modelagem/
    kart.blend          modelo, materiais, luzes e câmera (Blender 4.5 ou superior)
    kart.glb            modelo exportado (glTF 2.0)
    modelar_kart.py     script que constrói o modelo e gera os renders
    renders/            imagens renderizadas
Trabalho2-Jogo/         projeto do Godot (abrir project.godot no Godot 4.4 ou superior)
executaveis/
    KartDasMoedas-Windows.exe
    KartDasMoedas-Linux.x86_64
</pre><div class="fonte">Fonte: Elaborado pelo autor (2026).</div></div>
<p><b>Para jogar sem instalar nada:</b> execute <code>KartDasMoedas-Windows.exe</code> (Windows) ou
<code>KartDasMoedas-Linux.x86_64</code> (Linux).</p>
<p><b>Para abrir o projeto:</b> no Godot, escolha <i>Importar</i>, selecione o arquivo
<code>Trabalho2-Jogo/project.godot</code> e pressione F5.</p>
<p><b>Para recriar o modelo:</b> <code>blender --background --python modelar_kart.py</code>.</p>''')
    add('</section>')
    return "\n".join(p)


CSS = r"""
@page { size: A4; margin: 3cm 2cm 2cm 3cm;
  @top-right { content: counter(page); font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 10pt; } }
@page semnumero { @top-right { content: none; } }
html { font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 12pt; color: #000; }
body { margin: 0; }
section { break-before: page; }
section:first-child { break-before: auto; }
.capa, .pre { page: semnumero; }
.capa { height: 24.5cm; display: flex; flex-direction: column; justify-content: space-between; text-align: center;
  font-weight: bold; text-transform: uppercase; line-height: 1.5; }
.capa .titulo { font-size: 14pt; margin: 0 1cm; }
.capa .subtitulo { text-transform: none; font-weight: normal; }
.capa.rosto .natureza { text-transform: none; font-weight: normal; text-align: justify; margin-left: 8cm;
  font-size: 11pt; line-height: 1.2; }
.capa .autor, .capa .topo { font-size: 12pt; }
h1 { font-size: 12pt; font-weight: bold; text-transform: uppercase; margin: 0 0 1.2em; break-after: avoid; }
h1.semnum { text-align: center; }
.corpo h1 { break-before: page; }
.corpo h1:first-child { break-before: auto; }
.corpo h1#t1-concepcao { break-before: auto; }
h2 { font-size: 12pt; font-weight: bold; margin: 1.4em 0 0.6em; break-after: avoid; }
p { text-align: justify; line-height: 1.5; margin: 0 0 0.5em; text-indent: 1.25cm; orphans: 3; widows: 3; }
.refs p { text-indent: 0; line-height: 1.0; margin-bottom: 1em; text-align: left; }
p.chave { text-indent: 0; margin-top: 1em; }
ul { line-height: 1.5; margin: 0.3em 0 0.6em; padding-left: 1.6cm; text-align: justify; }
li { margin-bottom: 0.15em; }
code { font-family: 'Liberation Mono', 'DejaVu Sans Mono', monospace; font-size: 10pt; }
figure { margin: 0.8em 0 1em; text-align: center; break-inside: avoid; }
figure img { display: block; margin: 0 auto; border: 0.5pt solid #bbb; }
figcaption, .cap { font-size: 10pt; text-align: center; margin-bottom: 0.4em; line-height: 1.2; }
.fonte { font-size: 10pt; text-align: center; margin-top: 0.3em; }
.grade { display: grid; gap: 0.35cm; }
.grade.c2 { grid-template-columns: 1fr 1fr; }
.grade img { width: 100%; }
.subleg { font-size: 9.5pt; margin-top: 0.15em; }
.tabela, .quadro { margin: 0.8em 0 1em; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 10pt; line-height: 1.25; }
thead th { border-top: 1pt solid #000; border-bottom: 0.75pt solid #000; padding: 4px 6px; text-align: left; }
tbody td { padding: 3.5px 6px; vertical-align: top; }
tbody tr:last-child td { border-bottom: 1pt solid #000; }
.tabela.estreita table { width: 75%; margin: 0 auto; }
.tabela.compacta table { width: 85%; margin: 0 auto; }
.tabela.compacta td:first-child { width: 18px; }
.amostra { display: inline-block; width: 14px; height: 14px; border: 0.5pt solid #555; vertical-align: middle; }
.quadro pre { border: 0.75pt solid #000; padding: 8px 12px; font-family: 'DejaVu Sans Mono', monospace;
  font-size: 8.8pt; line-height: 1.35; margin: 0; white-space: pre; text-align: left; }
.eq { display: flex; align-items: center; justify-content: center; position: relative; margin: 0.5em 0 0.7em; }
.eq math { font-size: 12.5pt; }
.eqn { position: absolute; right: 0; }
.sumario { line-height: 1.5; }
.sumario > div { display: flex; align-items: baseline; }
.sumario .num { width: 1.2cm; flex: none; }
.sumario .s1 { font-weight: bold; text-transform: uppercase; margin-top: 0.25em; }
.sumario .pontos { flex: 1; border-bottom: 1px dotted #000; margin: 0 4px; transform: translateY(-4px); }
.sumario .pag { flex: none; min-width: 0.6cm; text-align: right; }
"""


def montar_html(paginas):
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            f'<title>Relatório – Computação Gráfica – Trabalhos 1 e 2</title><style>{CSS}</style></head>'
            f'<body>{conteudo(paginas)}</body></html>')


def chrome_pdf(html_path, pdf_path):
    perfil = tempfile.mkdtemp(prefix="chrome-relatorio-")
    try:
        subprocess.run([
            "google-chrome", "--headless=new", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={perfil}", "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}", "file://" + html_path,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    finally:
        shutil.rmtree(perfil, ignore_errors=True)


def localizar_paginas(pdf_path):
    """Descobre a página (numeração física) em que cada título de seção aparece."""
    total = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", pdf_path], capture_output=True, text=True).stdout).group(1))
    textos = []
    for i in range(1, total + 1):
        t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf_path, "-"],
                           capture_output=True, text=True).stdout
        textos.append(re.sub(r"\s+", " ", t))
    inicio = next(i for i, t in enumerate(textos) if "SUMÁRIO" in t) + 1
    paginas = {}
    for ident, num, titulo, nivel in SECOES:
        alvo = re.sub(r"\s+", " ", f"{num} {titulo}" if num else titulo)
        for i in range(inicio, total):
            if alvo in textos[i]:
                paginas[ident] = i + 1
                inicio = i
                break
    return paginas, total


def main():
    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(montar_html({}))
    chrome_pdf(SAIDA_HTML, SAIDA_PDF)
    paginas, total = localizar_paginas(SAIDA_PDF)
    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(montar_html(paginas))
    chrome_pdf(SAIDA_HTML, SAIDA_PDF)
    faltando = [i for i, *_ in SECOES if i not in paginas]
    print(f"PDF gerado: {SAIDA_PDF} ({total} páginas)")
    if faltando:
        print("Seções não localizadas no sumário:", faltando)


if __name__ == "__main__":
    main()
