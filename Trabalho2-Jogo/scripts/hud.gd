extends CanvasLayer
## Interface 2D sobreposta ao jogo (HUD) e telas de menu, pausa e fim.
## Este nó processa mesmo com o jogo pausado (process_mode = Always).

@onready var painel_jogo: Control = $Jogo
@onready var lbl_moedas: Label = $Jogo/Moedas
@onready var lbl_tempo: Label = $Jogo/Tempo
@onready var lbl_velocidade: Label = $Jogo/Velocidade
@onready var lbl_recorde_jogo: Label = $Jogo/Recorde
@onready var lbl_mensagem: Label = $Jogo/Mensagem
@onready var painel_menu: Control = $Menu
@onready var lbl_recorde_menu: Label = $Menu/Painel/Coluna/Recorde
@onready var lbl_iniciar: Label = $Menu/Painel/Coluna/Iniciar
@onready var painel_pausa: Control = $Pausa
@onready var painel_fim: Control = $Fim
@onready var lbl_fim_pontos: Label = $Fim/Pontos
@onready var lbl_fim_recorde: Label = $Fim/Recorde
@onready var lbl_fim_jogar: Label = $Fim/JogarNovamente

var relogio := 0.0
var tween_mensagem: Tween
var tween_moedas: Tween


func _ready() -> void:
	lbl_mensagem.text = ""
	painel_pausa.hide()
	painel_fim.hide()


func _process(delta: float) -> void:
	relogio += delta
	# texto "pressione ENTER" piscando suavemente
	var alfa := 0.55 + 0.45 * sin(relogio * 4.0)
	lbl_iniciar.modulate.a = alfa
	lbl_fim_jogar.modulate.a = alfa


func mostrar_menu(recorde: int) -> void:
	painel_menu.show()
	painel_jogo.hide()
	painel_fim.hide()
	painel_pausa.hide()
	lbl_recorde_menu.text = "Recorde: " + _moedas(recorde)


func mostrar_jogo(recorde: int) -> void:
	painel_menu.hide()
	painel_fim.hide()
	painel_jogo.show()
	lbl_recorde_jogo.text = "RECORDE %d" % recorde


func mostrar_pausa(pausado: bool) -> void:
	painel_pausa.visible = pausado


func mostrar_fim(pontos: int, recorde: int, novo_recorde: bool) -> void:
	painel_jogo.hide()
	painel_fim.show()
	lbl_fim_pontos.text = _moedas(pontos)
	if novo_recorde:
		lbl_fim_recorde.text = "NOVO RECORDE!"
		lbl_fim_recorde.modulate = Color(1.0, 0.85, 0.2)
	else:
		lbl_fim_recorde.text = "Recorde: " + _moedas(recorde)
		lbl_fim_recorde.modulate = Color.WHITE


## "1 moeda", "2 moedas"...
func _moedas(n: int) -> String:
	return "%d moeda%s" % [n, "" if n == 1 else "s"]


func atualizar(pontos: int, tempo: float, kmh: float) -> void:
	lbl_moedas.text = "MOEDAS  %d" % pontos
	var segundos := ceili(tempo)
	lbl_tempo.text = "%d:%02d" % [floori(segundos / 60.0), segundos % 60]
	lbl_tempo.modulate = Color(1.0, 0.35, 0.3) if tempo <= 10.0 else Color.WHITE
	lbl_velocidade.text = "%d km/h" % roundi(kmh)


func mensagem(texto: String, duracao := 1.0, cor := Color.WHITE) -> void:
	lbl_mensagem.text = texto
	lbl_mensagem.modulate = cor
	lbl_mensagem.pivot_offset = lbl_mensagem.size / 2.0
	if tween_mensagem:
		tween_mensagem.kill()
	tween_mensagem = create_tween()
	lbl_mensagem.scale = Vector2(1.8, 1.8)
	tween_mensagem.tween_property(lbl_mensagem, "scale", Vector2.ONE, 0.25) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween_mensagem.tween_interval(duracao)
	tween_mensagem.tween_property(lbl_mensagem, "modulate:a", 0.0, 0.3)


func pulsar_moedas() -> void:
	lbl_moedas.pivot_offset = Vector2(0.0, lbl_moedas.size.y / 2.0)
	if tween_moedas:
		tween_moedas.kill()
	tween_moedas = create_tween()
	lbl_moedas.scale = Vector2(1.3, 1.3)
	lbl_moedas.modulate = Color(1.0, 0.85, 0.2)
	tween_moedas.tween_property(lbl_moedas, "scale", Vector2.ONE, 0.25)
	tween_moedas.parallel().tween_property(lbl_moedas, "modulate", Color.WHITE, 0.4)
