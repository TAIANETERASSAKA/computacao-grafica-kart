extends Node3D
## Espalha árvores low-poly ao redor da arena.
##
## As malhas são criadas por código (cilindros, cones e esferas) e
## reaproveitadas por todas as árvores; cada árvore só muda a transformação
## (posição, rotação e escala aleatórias) — instanciação de geometria.

@export var quantidade := 90
@export var raio_minimo := 42.0
@export var raio_maximo := 110.0
@export var semente := 2026


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = semente

	var mat_tronco := _material(Color(0.36, 0.22, 0.12))
	var mat_pinheiro := _material(Color(0.10, 0.35, 0.16))
	var mat_copa := _material(Color(0.22, 0.52, 0.18))

	var tronco := CylinderMesh.new()
	tronco.top_radius = 0.18
	tronco.bottom_radius = 0.25
	tronco.height = 1.6
	tronco.radial_segments = 8
	tronco.material = mat_tronco

	var pinheiro := CylinderMesh.new()
	pinheiro.top_radius = 0.0
	pinheiro.bottom_radius = 1.6
	pinheiro.height = 4.0
	pinheiro.radial_segments = 8
	pinheiro.material = mat_pinheiro

	var copa := SphereMesh.new()
	copa.radius = 1.6
	copa.height = 3.0
	copa.radial_segments = 10
	copa.rings = 6
	copa.material = mat_copa

	for i in quantidade:
		var angulo := rng.randf() * TAU
		var raio := rng.randf_range(raio_minimo, raio_maximo)
		var arvore := Node3D.new()
		arvore.position = Vector3(cos(angulo) * raio, 0.0, sin(angulo) * raio)
		arvore.rotation.y = rng.randf() * TAU
		var escala := rng.randf_range(0.8, 1.6)
		arvore.scale = Vector3.ONE * escala
		add_child(arvore)

		var t := MeshInstance3D.new()
		t.mesh = tronco
		t.position.y = 0.8
		arvore.add_child(t)

		var folhas := MeshInstance3D.new()
		if rng.randf() < 0.55:
			folhas.mesh = pinheiro
			folhas.position.y = 3.4
		else:
			folhas.mesh = copa
			folhas.position.y = 2.8
		arvore.add_child(folhas)


func _material(cor: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = cor
	m.roughness = 0.9
	return m
