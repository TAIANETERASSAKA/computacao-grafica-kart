extends Camera3D
## Câmera em terceira pessoa.
##
## A posição desejada é calculada a partir do kart (atrás e acima dele) e a
## câmera se aproxima dela com suavização exponencial: pos += (alvo - pos) * k,
## onde k = 1 - e^(-suavidade * dt). Isso independe da taxa de quadros.
## O campo de visão (FOV) aumenta com a velocidade para dar sensação de rapidez.

enum Modo { VITRINE, PERSEGUICAO, AEREA }

@export var alvo: Node3D
@export var distancia := 5.5
@export var altura := 2.2
@export var suavidade := 9.0
@export var fov_base := 70.0
@export var fov_extra := 12.0

var modo := Modo.VITRINE
var tremor := 0.0
var angulo_vitrine := 0.6
var direcao_suave := Vector3.BACK
var deslocamento_vitrine := 0.0   ## desloca o kart para o lado na tela (menu)
var altura_olhar_vitrine := 0.45


func _physics_process(delta: float) -> void:
	if alvo == null:
		return
	var pos_alvo := alvo.global_position
	var desejada: Vector3
	var olhar: Vector3
	var k := 1.0 - exp(-suavidade * delta)

	match modo:
		Modo.VITRINE:
			# gira lentamente ao redor do kart (menu e fim de jogo)
			angulo_vitrine += delta * 0.3
			desejada = pos_alvo + Vector3(sin(angulo_vitrine) * 4.0, 1.4, cos(angulo_vitrine) * 4.0)
			olhar = pos_alvo + Vector3(0.0, altura_olhar_vitrine, 0.0)
		Modo.PERSEGUICAO:
			var tras := alvo.global_basis.z
			tras.y = 0.0
			tras = tras.normalized()
			direcao_suave = direcao_suave.lerp(tras, 1.0 - exp(-4.0 * delta)).normalized()
			desejada = pos_alvo + direcao_suave * distancia + Vector3.UP * altura
			olhar = pos_alvo + Vector3.UP * 0.8 - direcao_suave * 3.0
		Modo.AEREA:
			desejada = pos_alvo + Vector3(0.0, 17.0, 10.0)
			olhar = pos_alvo

	global_position = global_position.lerp(desejada, k)
	look_at(olhar)

	# deslocamento lateral no menu + tremor da câmera após batidas
	var base_h := deslocamento_vitrine if modo == Modo.VITRINE else 0.0
	h_offset = lerpf(h_offset, base_h, k)
	v_offset = 0.0
	if tremor > 0.0:
		tremor = maxf(tremor - delta * 2.5, 0.0)
		h_offset += randf_range(-1.0, 1.0) * tremor * 0.2
		v_offset = randf_range(-1.0, 1.0) * tremor * 0.2

	var razao := 0.0
	if modo == Modo.PERSEGUICAO and alvo.has_method("razao_velocidade"):
		razao = alvo.razao_velocidade()
	fov = lerpf(fov, fov_base + fov_extra * razao, 3.0 * delta)


func alternar_modo() -> void:
	modo = Modo.AEREA if modo == Modo.PERSEGUICAO else Modo.PERSEGUICAO


func seguir() -> void:
	modo = Modo.PERSEGUICAO
	if alvo:
		direcao_suave = alvo.global_basis.z


func vitrine(deslocamento := 0.0, altura_olhar := 0.45) -> void:
	modo = Modo.VITRINE
	deslocamento_vitrine = deslocamento
	altura_olhar_vitrine = altura_olhar


func tremer(intensidade: float) -> void:
	tremor = clampf(intensidade / 10.0, 0.2, 1.0)
