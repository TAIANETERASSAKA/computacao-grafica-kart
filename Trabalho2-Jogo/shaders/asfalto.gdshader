// Piso da arena: asfalto procedural (ruído de valor), linhas brancas
// perto da borda e faixa quadriculada de largada.
shader_type spatial;

uniform vec3 cor_asfalto : source_color = vec3(0.15, 0.145, 0.14);
uniform float meia_largura = 35.0;
uniform float z_largada = 26.5;

varying vec3 pos_mundo;

void vertex() {
	pos_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float ruido(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
	           mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void fragment() {
	vec2 p = pos_mundo.xz;
	float n = ruido(p * 6.0) * 0.35 + ruido(p * 0.7) * 0.65;
	vec3 cor = cor_asfalto * (0.8 + 0.45 * n);

	// linha branca a 2 m da borda
	float d = meia_largura - max(abs(p.x), abs(p.y));
	float linha = step(1.8, d) * step(d, 2.1);
	cor = mix(cor, vec3(0.92), linha);

	// faixa quadriculada da largada
	if (abs(p.y - z_largada) < 0.75 && abs(p.x) < 6.0) {
		vec2 q = floor(p / 0.5);
		float xadrez = mod(q.x + q.y, 2.0);
		cor = mix(vec3(0.05), vec3(0.95), xadrez);
	}

	ALBEDO = cor;
	ROUGHNESS = 0.85 - 0.2 * linha;
}
