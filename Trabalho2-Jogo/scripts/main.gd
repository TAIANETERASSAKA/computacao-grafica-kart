extends Node3D
## Controla o fluxo do jogo: VITRINE (menu) -> CONTAGEM -> JOGANDO -> FIM.
##
## Também cria as moedas e os relógios em posições livres da arena,
## conta os pontos e o tempo e guarda o recorde em disco (user://).

const DURACAO := 60.0
const QTD_MOEDAS := 12
const LIMITE_ARENA := 31.0
const BONUS_RELOGIO := 5.0
const ARQUIVO_RECORDE := "user://recorde.cfg"

enum Estado { MENU, CONTAGEM, JOGANDO, FIM }

var estado := Estado.MENU
var pontos := 0
var tempo_restante := DURACAO
var recorde := 0
var contagem := 0.0
var espera_relogio := 0.0
var relogio_atual: Node3D = null
var transformacao_largada: Transform3D

var cena_moeda: PackedScene = preload("res://cenas/moeda.tscn")
var cena_relogio: PackedScene = preload("res://cenas/relogio.tscn")

@onready var kart = $Kart  # script kart.gd
@onready var camera = $Camera  # script camera_seguidora.gd
@onready var hud = $HUD  # script hud.gd
@onready var coletaveis: Node3D = $Coletaveis
@onready var som_moeda: AudioStreamPlayer = $Sons/Moeda
@onready var som_relogio: AudioStreamPlayer = $Sons/Relogio
@onready var som_turbo: AudioStreamPlayer = $Sons/Turbo
@onready var som_batida: AudioStreamPlayer = $Sons/Batida
@onready var som_bip: AudioStreamPlayer = $Sons/Bip
@onready var som_largada: AudioStreamPlayer = $Sons/Largada
@onready var som_fim: AudioStreamPlayer = $Sons/Fim


func _ready() -> void:
	transformacao_largada = kart.global_transform
	_carregar_recorde()
	kart.bateu.connect(_ao_bater)
	for faixa in get_tree().get_nodes_in_group("turbo"):
		faixa.acionado.connect(_ao_turbo)
	for cone in get_tree().get_nodes_in_group("cone"):
		cone.set_meta("transformacao_inicial", cone.global_transform)
	_ir_para_menu()


func _unhandled_input(evento: InputEvent) -> void:
	if evento.is_action_pressed("pausar") and estado in [Estado.CONTAGEM, Estado.JOGANDO]:
		_alternar_pausa()
	elif get_tree().paused:
		if evento.is_action_pressed("voltar_menu"):
			_alternar_pausa()
			_ir_para_menu()
	elif evento.is_action_pressed("confirmar") and estado in [Estado.MENU, Estado.FIM]:
		_iniciar_corrida()
	elif evento.is_action_pressed("camera") and estado in [Estado.CONTAGEM, Estado.JOGANDO]:
		camera.alternar_modo()
	elif evento.is_action_pressed("reposicionar") and estado == Estado.JOGANDO:
		kart.reiniciar(transformacao_largada)


func _process(delta: float) -> void:
	if get_tree().paused:
		return
	match estado:
		Estado.CONTAGEM:
			var antes := ceili(contagem)
			contagem -= delta
			var agora := ceili(contagem)
			if agora != antes and agora > 0:
				hud.mensagem(str(agora), 0.9)
				som_bip.play()
			if contagem <= 0.0:
				estado = Estado.JOGANDO
				kart.controle_ativo = true
				hud.mensagem("VAI!", 0.8, Color(0.4, 1.0, 0.4))
				som_largada.play()
		Estado.JOGANDO:
			tempo_restante -= delta
			if not is_instance_valid(relogio_atual):
				espera_relogio -= delta
				if espera_relogio <= 0.0:
					_criar_relogio()
			if tempo_restante <= 0.0:
				tempo_restante = 0.0
				_fim_de_jogo()
	hud.atualizar(pontos, tempo_restante, kart.velocidade_kmh())


# --- Estados ---------------------------------------------------------------

func _ir_para_menu() -> void:
	estado = Estado.MENU
	kart.controle_ativo = false
	kart.reiniciar(transformacao_largada)
	_limpar_coletaveis()
	camera.vitrine(-1.1)          # kart aparece à direita do painel do menu
	hud.mostrar_menu(recorde)


func _iniciar_corrida() -> void:
	pontos = 0
	tempo_restante = DURACAO
	kart.reiniciar(transformacao_largada)
	kart.controle_ativo = false
	_resetar_cones()
	_limpar_coletaveis()
	for _i in QTD_MOEDAS:
		_criar_moeda()
	espera_relogio = 6.0
	camera.seguir()
	hud.mostrar_jogo(recorde)
	estado = Estado.CONTAGEM
	contagem = 3.0
	hud.mensagem("3", 0.9)
	som_bip.play()


func _fim_de_jogo() -> void:
	estado = Estado.FIM
	kart.controle_ativo = false
	var novo_recorde := pontos > recorde
	if novo_recorde:
		recorde = pontos
		_salvar_recorde()
	som_fim.play()
	camera.vitrine(0.0, 1.3)      # kart mais abaixo, sob o placar
	hud.mostrar_fim(pontos, recorde, novo_recorde)


func _alternar_pausa() -> void:
	get_tree().paused = not get_tree().paused
	hud.mostrar_pausa(get_tree().paused)


# --- Coletáveis ---------------------------------------------------------------

func _criar_moeda() -> void:
	var moeda := cena_moeda.instantiate()
	coletaveis.add_child(moeda)
	moeda.global_position = _posicao_livre()
	moeda.coletado.connect(_ao_coletar_moeda)


func _criar_relogio() -> void:
	relogio_atual = cena_relogio.instantiate()
	coletaveis.add_child(relogio_atual)
	relogio_atual.global_position = _posicao_livre()
	relogio_atual.coletado.connect(_ao_coletar_relogio)


func _ao_coletar_moeda(_item: Area3D) -> void:
	if estado != Estado.JOGANDO:
		return
	pontos += 1
	som_moeda.pitch_scale = randf_range(0.95, 1.08)
	som_moeda.play()
	hud.pulsar_moedas()
	_criar_moeda.call_deferred()


func _ao_coletar_relogio(_item: Area3D) -> void:
	if estado != Estado.JOGANDO:
		return
	tempo_restante += BONUS_RELOGIO
	som_relogio.play()
	hud.mensagem("+%d s" % int(BONUS_RELOGIO), 0.8, Color(0.4, 0.85, 1.0))
	relogio_atual = null
	espera_relogio = randf_range(6.0, 10.0)


func _posicao_livre() -> Vector3:
	var obstaculos := get_tree().get_nodes_in_group("obstaculo")
	for _tentativa in 60:
		var p := Vector3(randf_range(-LIMITE_ARENA, LIMITE_ARENA), 0.0,
				randf_range(-LIMITE_ARENA, LIMITE_ARENA))
		if Vector2(p.x, p.z).length() < 9.0:          # ilha central
			continue
		if p.distance_to(kart.global_position) < 6.0:  # muito perto do kart
			continue
		var livre := true
		for o in obstaculos:
			var raio: float = o.get_meta("raio_livre", 2.0)
			if Vector2(o.global_position.x - p.x, o.global_position.z - p.z).length() < raio:
				livre = false
				break
		if livre:
			for c in coletaveis.get_children():
				if c is Area3D and c.global_position.distance_to(p) < 3.0:
					livre = false
					break
		if livre:
			return p
	return Vector3(randf_range(-20, 20), 0.0, 20.0)


func _limpar_coletaveis() -> void:
	for c in coletaveis.get_children():
		c.queue_free()
	relogio_atual = null


func _resetar_cones() -> void:
	for cone in get_tree().get_nodes_in_group("cone"):
		var rb := cone as RigidBody3D
		rb.global_transform = cone.get_meta("transformacao_inicial")
		rb.linear_velocity = Vector3.ZERO
		rb.angular_velocity = Vector3.ZERO
		rb.reset_physics_interpolation()


# --- Eventos -------------------------------------------------------------------

func _ao_bater(intensidade: float) -> void:
	camera.tremer(intensidade)
	som_batida.volume_db = lerpf(-14.0, -2.0, clampf(intensidade / 15.0, 0.0, 1.0))
	som_batida.play()


func _ao_turbo() -> void:
	som_turbo.play()
	if estado == Estado.JOGANDO:
		hud.mensagem("TURBO!", 0.6, Color(0.3, 0.9, 1.0))


# --- Recorde ---------------------------------------------------------------------

func _carregar_recorde() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(ARQUIVO_RECORDE) == OK:
		recorde = int(cfg.get_value("jogo", "recorde", 0))


func _salvar_recorde() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("jogo", "recorde", recorde)
	cfg.save(ARQUIVO_RECORDE)
