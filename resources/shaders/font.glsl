#vs

#version 330

layout(location = 0) in vec2 position;
layout(location = 1) in vec2 tex_coord;

uniform mat4 mvp_matrix;

varying vec2 uv;

void main()
{
    uv = tex_coord;
	gl_Position = mvp_matrix * vec4(position, 0.0, 1.0);
}

#fs

#version 330

uniform vec4 rgba;
uniform sampler2D font_texture;
uniform float pxrange;

varying vec2 uv;

float median(float r, float g, float b) {
    return max(min(r, g), min(max(r, g), b));
}

void main()
{
    vec4 sample = texture(font_texture, uv);
    float signed_distance = median(sample.r, sample.g, sample.b) - 0.5;

    vec2 msdf_unit = pxrange / vec2(textureSize(font_texture, 0));
    signed_distance *= dot(msdf_unit, 0.5 / fwidth(uv));
    float alpha = clamp(signed_distance + 0.5, 0.0, 1.0);

	gl_FragColor = rgba * vec4(vec3(1.0), alpha);
}
