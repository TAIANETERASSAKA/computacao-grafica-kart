// Listras diagonais vermelhas e brancas calculadas a partir da posição no
// mundo (não precisa de textura nem de coordenadas UV).
shader_type spatial;

uniform vec3 cor_a : source_color = vec3(0.85, 0.08, 0.06);
uniform vec3 cor_b : source_color = vec3(0.95, 0.95, 0.95);
uniform float largura = 1.0;

varying vec3 pos_mundo;

void vertex() {
	pos_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float s = (pos_mundo.x + pos_mundo.z + pos_mundo.y) / (2.0 * largura);
	float listra = step(0.5, fract(s));
	ALBEDO = mix(cor_a, cor_b, listra);
	ROUGHNESS = 0.55;
}
