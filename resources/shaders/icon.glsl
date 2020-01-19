#vs

#version 130

void main()
{
    gl_Position = vec4(0.0);
}

#gs

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

uniform mat4 mvp_matrix;

uniform vec2 xy1;
uniform vec2 xy2;

out vec2 uv;

void main()
{
    vec2 xy = xy1;
    uv = vec2(0.0, 0.0);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = vec2(xy2.x, xy1.y);
    uv = vec2(1.0, 0.0);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = vec2(xy1.x, xy2.y);
    uv = vec2(0.0, 1.0);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = xy2;
    uv = vec2(1.0, 1.0);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();

    EndPrimitive();
}

#fs

#version 130

uniform vec4 rgba;
uniform sampler2D icon_texture;
uniform float pxrange;

in vec2 uv;

float median(float r, float g, float b) {
    return max(min(r, g), min(max(r, g), b));
}

void main()
{
    vec4 sample = texture(icon_texture, uv);
    float signed_distance = median(sample.r, sample.g, sample.b) - 0.5;

    vec2 msdf_unit = pxrange / vec2(textureSize(icon_texture, 0));
    signed_distance *= dot(msdf_unit, 0.5 / fwidth(uv));
    float alpha = clamp(signed_distance + 0.5, 0.0, 1.0);

	gl_FragColor = rgba * vec4(vec3(1.0), alpha);
}
