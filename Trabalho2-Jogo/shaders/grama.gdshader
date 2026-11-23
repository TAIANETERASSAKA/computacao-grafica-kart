// Grama ao redor da arena: duas tonalidades de verde misturadas por ruído.
shader_type spatial;

uniform vec3 verde_claro : source_color = vec3(0.30, 0.55, 0.16);
uniform vec3 verde_escuro : source_color = vec3(0.14, 0.36, 0.10);

varying vec3 pos_mundo;

void vertex() {
	pos_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(269.5, 183.3))) * 43758.5453);
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
	float n = ruido(p * 0.15) * 0.6 + ruido(p * 1.3) * 0.3 + ruido(p * 9.0) * 0.1;
	ALBEDO = mix(verde_escuro, verde_claro, n);
	ROUGHNESS = 0.95;
}
