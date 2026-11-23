extends Area3D
## Faixa de turbo: dá um impulso de velocidade a quem passar por cima.

signal acionado

@export var duracao := 1.3

var espera := 0.0


func _ready() -> void:
	add_to_group("turbo")
	body_entered.connect(_ao_entrar)


func _process(delta: float) -> void:
	espera = maxf(espera - delta, 0.0)


func _ao_entrar(corpo: Node3D) -> void:
	if espera > 0.0 or not corpo.has_method("ativar_turbo"):
		return
	corpo.ativar_turbo(duracao)
	espera = 0.5
	acionado.emit()
