// Bandeira quadriculada: o vertex shader desloca os vértices com uma onda
// senoidal (animação procedural); o fragment shader desenha o xadrez.
shader_type spatial;
render_mode cull_disabled;

uniform float amplitude = 0.25;
uniform float frequencia = 2.5;
uniform float velocidade = 4.0;
uniform float casas = 6.0;

void vertex() {
	// UV.x = 0 no mastro (fixo) e 1 na ponta (balança mais)
	float onda = sin(UV.x * frequencia * TAU - TIME * velocidade);
	VERTEX.y += onda * amplitude * UV.x;
	// normal aproximada pela derivada da onda, para a iluminação acompanhar
	float derivada = cos(UV.x * frequencia * TAU - TIME * velocidade) * amplitude * UV.x * frequencia;
	NORMAL = normalize(vec3(-derivada, 1.0, 0.0));
}

void fragment() {
	vec2 q = floor(UV * vec2(casas, casas * 0.66));
	float xadrez = mod(q.x + q.y, 2.0);
	ALBEDO = mix(vec3(0.03), vec3(0.95), xadrez);
	ROUGHNESS = 0.8;
}
