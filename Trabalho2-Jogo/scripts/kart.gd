extends CharacterBody3D
## Kart controlado pelo jogador, com física "arcade".
##
## Guardamos uma velocidade escalar ao longo da frente do kart (-Z local) e
## giramos o corpo em torno do eixo Y conforme o volante. A "aderência"
## define com que rapidez a velocidade real se alinha à frente do kart:
## com o freio de mão ela diminui e o kart derrapa (drift).
##
## O modelo 3D vem do Trabalho 1 (modelos/kart.glb). As rodas e o volante
## são nós separados na hierarquia do modelo, então podemos girá-los aqui.

signal bateu(intensidade: float)

@export_group("Motor")
@export var aceleracao := 12.0          ## m/s²
@export var velocidade_maxima := 20.0   ## m/s (72 km/h)
@export var velocidade_re := 7.0        ## m/s
@export var freio := 30.0               ## m/s²
@export var atrito := 5.0               ## desaceleração sem acelerar (m/s²)

@export_group("Direção")
@export var giro_maximo := 2.4          ## velocidade angular máxima (rad/s)
@export var aderencia := 9.0
@export var aderencia_drift := 1.8
@export var angulo_esterco := 0.45      ## ângulo máximo das rodas dianteiras (rad)

@export_group("Turbo")
@export var multiplicador_turbo := 1.55
@export var gravidade := 28.0

const RAIO_RODA_DIANTEIRA := 0.14
const RAIO_RODA_TRASEIRA := 0.16

var velocidade := 0.0          ## velocidade escalar ao longo da frente (m/s)
var controle_ativo := false
var tempo_turbo := 0.0
var esterco := 0.0             ## -1 (direita) .. 1 (esquerda), suavizado
var distancia_percorrida := 0.0
var velocidade_anterior := 0.0

@onready var modelo: Node3D = $Modelo
@onready var som_motor: AudioStreamPlayer = $SomMotor

var rodas := {}                ## nome -> [nó, base original]
var volante: Node3D
var base_volante: Basis
var fumaca: Array[CPUParticles3D] = []
var chama_turbo: CPUParticles3D


func _ready() -> void:
	add_to_group("jogador")
	for nome in ["Roda_DE", "Roda_DD", "Roda_TE", "Roda_TD"]:
		var no := modelo.find_child(nome, true, false) as Node3D
		if no:
			rodas[nome] = [no, no.transform.basis]
	volante = modelo.find_child("Volante", true, false) as Node3D
	if volante:
		base_volante = volante.transform.basis

	# Partículas: fumaça nas rodas traseiras (drift) e chama no escapamento (turbo)
	fumaca.append(_criar_fumaca(Vector3(-0.58, 0.08, 0.5)))
	fumaca.append(_criar_fumaca(Vector3(0.58, 0.08, 0.5)))
	chama_turbo = _criar_chama(Vector3(0.2, 0.33, 0.82))


func _physics_process(delta: float) -> void:
	var acelerador := 0.0
	var direcao := 0.0
	var freio_mao := false
	if controle_ativo:
		acelerador = Input.get_axis("re", "acelerar")
		direcao = Input.get_axis("direita", "esquerda")
		freio_mao = Input.is_action_pressed("freio_mao")

	esterco = move_toward(esterco, direcao, 5.0 * delta)
	tempo_turbo = maxf(tempo_turbo - delta, 0.0)
	var em_turbo := tempo_turbo > 0.0
	var vmax := velocidade_maxima * (multiplicador_turbo if em_turbo else 1.0)

	# --- Velocidade longitudinal --------------------------------------------
	if em_turbo:
		velocidade = move_toward(velocidade, vmax, aceleracao * 3.0 * delta)
	elif acelerador > 0.0:
		if velocidade < 0.0:
			velocidade = move_toward(velocidade, 0.0, freio * delta)
		else:
			var alvo := vmax * acelerador
			var taxa := aceleracao if velocidade < alvo else atrito
			velocidade = move_toward(velocidade, alvo, taxa * delta)
	elif acelerador < 0.0:
		if velocidade > 0.5:
			velocidade = move_toward(velocidade, 0.0, freio * delta)
		else:
			velocidade = move_toward(velocidade, -velocidade_re * -acelerador, aceleracao * 0.7 * delta)
	else:
		velocidade = move_toward(velocidade, 0.0, atrito * delta)
	if freio_mao:
		velocidade = move_toward(velocidade, 0.0, atrito * 0.8 * delta)

	# --- Direção: rotação em torno de Y proporcional à velocidade ------------
	var fator := clampf(absf(velocidade) / 5.0, 0.0, 1.0) * signf(velocidade)
	# encostado em algo (quase parado) e acelerando: permite girar devagar
	if absf(velocidade) < 1.5 and acelerador != 0.0:
		fator = 0.4 * signf(acelerador)
	var estabilidade := lerpf(1.0, 0.65, clampf(absf(velocidade) / velocidade_maxima, 0.0, 1.0))
	var giro := esterco * giro_maximo * fator * estabilidade
	if freio_mao and absf(velocidade) > 4.0:
		giro *= 1.6
	rotate_y(giro * delta)

	# --- Velocidade no mundo: alinha gradualmente à frente do kart ------------
	var frente := -global_basis.z
	var horizontal := Vector3(velocity.x, 0.0, velocity.z)
	var grip := aderencia_drift if freio_mao else aderencia
	horizontal = horizontal.lerp(frente * velocidade, 1.0 - exp(-grip * delta))
	velocity.x = horizontal.x
	velocity.z = horizontal.z
	if is_on_floor():
		velocity.y = 0.0
	else:
		velocity.y -= gravidade * delta

	move_and_slide()
	_tratar_colisoes(frente, horizontal)

	# derrapagem = componente lateral grande da velocidade
	var lateral := absf(velocity.dot(global_basis.x))
	var derrapando := is_on_floor() and (lateral > 2.5 or (freio_mao and absf(velocidade) > 6.0))
	for f in fumaca:
		f.emitting = derrapando
	chama_turbo.emitting = em_turbo

	_animar_modelo(delta)
	_atualizar_som()


func _tratar_colisoes(frente: Vector3, horizontal_antes: Vector3) -> void:
	var bateu_parede := false
	var impacto := 0.0
	for i in get_slide_collision_count():
		var colisao := get_slide_collision(i)
		var normal := colisao.get_normal()
		var corpo := colisao.get_collider()
		if corpo is RigidBody3D:
			# empurra objetos soltos (cones)
			var forca := -normal * maxf(absf(velocidade), 3.0) * 0.9 + Vector3.UP * absf(velocidade) * 0.25
			(corpo as RigidBody3D).apply_central_impulse(forca)
			velocidade *= 0.97
		elif absf(normal.y) < 0.5:
			bateu_parede = true
			impacto = maxf(impacto, -horizontal_antes.dot(normal))
	if bateu_parede:
		# a velocidade passa a ser a que sobrou depois de deslizar na parede
		var restante := Vector3(velocity.x, 0.0, velocity.z).dot(frente)
		velocidade = clampf(restante, -absf(velocidade), absf(velocidade))
		if impacto > 4.0:
			# batida forte de frente: o kart quica para trás
			if absf(restante) < 2.0:
				velocidade = -signf(horizontal_antes.dot(frente)) * minf(impacto * 0.3, 6.0)
			bateu.emit(impacto)


func _animar_modelo(delta: float) -> void:
	distancia_percorrida += velocidade * delta

	# Rodas: rolagem (eixo X) + esterço das dianteiras (eixo Y).
	# A ordem de Euler padrão do Godot (YXZ) aplica o esterço antes da rolagem.
	var esterco_rodas := esterco * angulo_esterco
	for nome in rodas:
		var no: Node3D = rodas[nome][0]
		var base: Basis = rodas[nome][1]
		var dianteira: bool = nome.begins_with("Roda_D")
		var raio := RAIO_RODA_DIANTEIRA if dianteira else RAIO_RODA_TRASEIRA
		var rolagem := -distancia_percorrida / raio
		var rot := Vector3(rolagem, esterco_rodas if dianteira else 0.0, 0.0)
		no.transform.basis = base * Basis.from_euler(rot)

	if volante:
		volante.transform.basis = base_volante * Basis(Vector3.UP, esterco * 1.6)

	# Inclinação da carroceria: rola para fora na curva e "empina" ao acelerar
	var razao := clampf(absf(velocidade) / velocidade_maxima, 0.0, 1.0)
	var rolagem_alvo := -esterco * razao * 0.08
	var aceleracao_atual := (velocidade - velocidade_anterior) / maxf(delta, 0.0001)
	var arfagem_alvo := clampf(aceleracao_atual / 300.0, -0.05, 0.05)
	velocidade_anterior = velocidade
	modelo.rotation.z = lerpf(modelo.rotation.z, rolagem_alvo, 6.0 * delta)
	modelo.rotation.x = lerpf(modelo.rotation.x, arfagem_alvo, 6.0 * delta)


func _atualizar_som() -> void:
	var razao := absf(velocidade) / velocidade_maxima
	som_motor.pitch_scale = 0.7 + razao * 1.2
	som_motor.volume_db = lerpf(-18.0, -9.0, clampf(razao, 0.0, 1.0))


## Chamado pelas faixas de turbo.
func ativar_turbo(duracao := 1.3) -> void:
	tempo_turbo = duracao
	velocidade = maxf(velocidade, velocidade_maxima * 1.2)


## Velocidade em km/h para o painel.
func velocidade_kmh() -> float:
	return absf(velocidade) * 3.6


## Razão entre 0 e ~1.5 usada pela câmera (campo de visão).
func razao_velocidade() -> float:
	return absf(velocidade) / velocidade_maxima


func reiniciar(t: Transform3D) -> void:
	global_transform = t
	velocity = Vector3.ZERO
	velocidade = 0.0
	velocidade_anterior = 0.0
	tempo_turbo = 0.0
	esterco = 0.0
	modelo.rotation = Vector3.ZERO
	reset_physics_interpolation()


# --- Criação das partículas -------------------------------------------------

func _criar_fumaca(posicao: Vector3) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.position = posicao
	p.emitting = false
	p.amount = 32
	p.lifetime = 0.7
	p.local_coords = false
	p.direction = Vector3(0, 1, 0.4)
	p.spread = 25.0
	p.gravity = Vector3(0, 0.8, 0)
	p.initial_velocity_min = 0.5
	p.initial_velocity_max = 1.4
	p.scale_amount_min = 0.6
	p.scale_amount_max = 1.2
	var curva := Curve.new()
	curva.add_point(Vector2(0, 0.35))
	curva.add_point(Vector2(1, 1))
	p.scale_amount_curve = curva
	var gradiente := Gradient.new()
	gradiente.set_color(0, Color(0.9, 0.9, 0.9, 0.55))
	gradiente.set_color(1, Color(0.9, 0.9, 0.9, 0.0))
	p.color_ramp = gradiente
	p.mesh = _quad_particula(0.45, false)
	add_child(p)
	return p


func _criar_chama(posicao: Vector3) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.position = posicao
	p.emitting = false
	p.amount = 30
	p.lifetime = 0.25
	p.local_coords = false
	p.direction = Vector3(0, 0.2, 1)
	p.spread = 12.0
	p.gravity = Vector3.ZERO
	p.initial_velocity_min = 3.0
	p.initial_velocity_max = 5.0
	p.scale_amount_min = 0.5
	p.scale_amount_max = 0.9
	var gradiente := Gradient.new()
	gradiente.set_color(0, Color(1.0, 0.9, 0.4, 1.0))
	gradiente.set_color(1, Color(1.0, 0.2, 0.0, 0.0))
	p.color_ramp = gradiente
	p.mesh = _quad_particula(0.35, true)
	add_child(p)
	return p


func _quad_particula(tamanho: float, brilhante: bool) -> QuadMesh:
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.billboard_keep_scale = true
	if brilhante:
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	# textura circular suave gerada por código (gradiente radial)
	var grad := Gradient.new()
	grad.set_color(0, Color(1, 1, 1, 1))
	grad.set_color(1, Color(1, 1, 1, 0))
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(0.5, 0.0)
	tex.width = 64
	tex.height = 64
	mat.albedo_texture = tex
	var quad := QuadMesh.new()
	quad.size = Vector2(tamanho, tamanho)
	quad.material = mat
	return quad
