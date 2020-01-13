#vs

#version 130

varying vec4 uv;

void main()
{
    uv = gl_MultiTexCoord0;
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}

#fs

#version 130

uniform vec4 rgba;
uniform sampler2D icon_texture;
uniform float pxrange;

varying vec4 uv;

float median(float r, float g, float b) {
    return max(min(r, g), min(max(r, g), b));
}

void main()
{
    vec4 sample = texture(icon_texture, uv.xy);
    float signed_distance = median(sample.r, sample.g, sample.b) - 0.5;

    vec2 msdf_unit = pxrange / vec2(textureSize(icon_texture, 0));
    signed_distance *= dot(msdf_unit, 0.5 / fwidth(uv.xy));
    float alpha = clamp(signed_distance + 0.5, 0.0, 1.0);

	gl_FragColor = rgba * vec4(vec3(1.0), alpha);
}
