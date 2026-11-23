extends Area3D
## Item coletável (moeda ou relógio).
##
## O nó "Visual" gira em torno de Y e flutua com uma senoide. Quando o kart
## entra na área de colisão, o item emite o sinal "coletado", solta uma
## explosão de partículas e se remove da cena.

signal coletado(item: Area3D)

@export_enum("moeda", "relogio") var tipo := "moeda"
@export var velocidade_giro := 2.5
@export var cor_particulas := Color(1.0, 0.8, 0.2)

var tempo := 0.0
var altura_base := 0.0
var ja_coletado := false

@onready var visual: Node3D = $Visual


func _ready() -> void:
	altura_base = visual.position.y
	tempo = randf() * TAU
	body_entered.connect(_ao_entrar)


func _physics_process(delta: float) -> void:
	tempo += delta
	visual.rotation.y += velocidade_giro * delta
	visual.position.y = altura_base + sin(tempo * 3.0) * 0.12


func _ao_entrar(corpo: Node3D) -> void:
	if ja_coletado or not corpo.is_in_group("jogador"):
		return
	ja_coletado = true
	coletado.emit(self)
	_soltar_particulas()
	queue_free()


func _soltar_particulas() -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.explosiveness = 1.0
	p.amount = 28
	p.lifetime = 0.7
	p.direction = Vector3.UP
	p.spread = 180.0
	p.initial_velocity_min = 2.5
	p.initial_velocity_max = 5.5
	p.gravity = Vector3(0, -9.8, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = cor_particulas
	mat.emission_enabled = true
	mat.emission = cor_particulas
	mat.emission_energy_multiplier = 3.0
	var malha := BoxMesh.new()
	malha.size = Vector3(0.12, 0.12, 0.12)
	malha.material = mat
	p.mesh = malha
	get_parent().add_child(p)
	p.global_position = visual.global_position
	p.emitting = true
	p.finished.connect(p.queue_free)
