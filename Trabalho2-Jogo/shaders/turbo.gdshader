// Faixa de turbo: setas (chevrons) que deslizam para a frente (-Z) com o tempo.
shader_type spatial;

uniform vec3 cor : source_color = vec3(0.1, 0.85, 1.0);
uniform float velocidade = 1.6;
uniform float repeticoes = 3.0;

void fragment() {
	float x = abs(UV.x - 0.5);
	// UV.y cresce de -Z para +Z; somar o tempo faz as setas andarem para -Z
	float v = fract(UV.y * repeticoes - x * 1.4 + TIME * velocidade);
	float seta = step(0.5, v) * step(v, 0.8) * step(x, 0.38);
	float borda = step(0.44, x);
	float intensidade = max(seta, borda);
	ALBEDO = mix(vec3(0.03, 0.05, 0.08), cor, intensidade);
	EMISSION = cor * intensidade * 2.0;
	ROUGHNESS = 0.4;
}
