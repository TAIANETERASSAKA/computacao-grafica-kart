extends SceneTree
## Cria as ações de entrada (Input Map) e salva no project.godot.
## Uso: godot --headless --path <projeto> --script ferramentas_dev/configurar_entradas.gd

func _tecla(codigo: Key) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.device = -1  # qualquer dispositivo
	ev.physical_keycode = codigo
	return ev

func _botao(b: JoyButton) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.device = -1
	ev.button_index = b
	return ev

func _eixo(e: JoyAxis, valor: float) -> InputEventJoypadMotion:
	var ev := InputEventJoypadMotion.new()
	ev.device = -1
	ev.axis = e
	ev.axis_value = valor
	return ev

func _init() -> void:
	var acoes := {
		"acelerar": [_tecla(KEY_W), _tecla(KEY_UP), _eixo(JOY_AXIS_TRIGGER_RIGHT, 1.0)],
		"re": [_tecla(KEY_S), _tecla(KEY_DOWN), _eixo(JOY_AXIS_TRIGGER_LEFT, 1.0)],
		"esquerda": [_tecla(KEY_A), _tecla(KEY_LEFT), _eixo(JOY_AXIS_LEFT_X, -1.0)],
		"direita": [_tecla(KEY_D), _tecla(KEY_RIGHT), _eixo(JOY_AXIS_LEFT_X, 1.0)],
		"freio_mao": [_tecla(KEY_SPACE), _botao(JOY_BUTTON_X)],
		"camera": [_tecla(KEY_C), _botao(JOY_BUTTON_Y)],
		"reposicionar": [_tecla(KEY_R), _botao(JOY_BUTTON_BACK)],
		"pausar": [_tecla(KEY_ESCAPE), _tecla(KEY_P), _botao(JOY_BUTTON_START)],
		"confirmar": [_tecla(KEY_ENTER), _tecla(KEY_KP_ENTER), _botao(JOY_BUTTON_A)],
		"voltar_menu": [_tecla(KEY_Q), _botao(JOY_BUTTON_B)],
	}
	for nome in acoes:
		ProjectSettings.set_setting("input/" + nome, {"deadzone": 0.2, "events": acoes[nome]})
	var erro := ProjectSettings.save()
	print("Entradas salvas: ", error_string(erro))
	quit()
