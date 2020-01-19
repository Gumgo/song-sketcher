#vs

#version 330

void main()
{
    gl_Position = vec4(0.0);
}

#gs

#version 330

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

uniform mat4 mvp_matrix;

uniform vec2 xy1;
uniform vec2 xy2;

out vec2 xy;

void main()
{
    xy = xy1;
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = vec2(xy2.x, xy1.y);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = vec2(xy1.x, xy2.y);
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();
    xy = xy2;
    gl_Position = mvp_matrix * vec4(xy, 0.0, 1.0);
    EmitVertex();

    EndPrimitive();
}

#fs

#version 130

uniform sampler1D waveform_texture;

uniform vec4 background_rgba;
uniform vec4 waveform_rgba;
uniform vec4 border_rgba;
uniform float border_thickness;

uniform vec2 xy1;
uniform vec2 xy2;

in vec2 xy;

// Blends smoothly across a 1-pixel wide region around edge_distance, where < 0.5 indicates distance < edge_distance
float smooth_edge(float distance, float edge_distance) {
    // Find the distance change per-pixel - fwidth is the sum of abs(dFdx) and abs(dFdy)
    // Is max(abs(dFdx(xy.x)), abs(dFdy(xy.y))) more correct?
    float distance_change_per_pixel = fwidth(distance);

    // Blend between edge_distance - 0.5 and edge_distance + 0.5
    return clamp((distance - edge_distance) / distance_change_per_pixel + 0.5, 0.0, 1.0);
}

void main()
{
    vec2 xy_min = min(xy1, xy2);
    vec2 xy_max = max(xy1, xy2);

    vec2 min_outer_dist = xy - xy_min;
    float left_outer_edge = smooth_edge(min_outer_dist[0], 0.0);
    float bottom_outer_edge = smooth_edge(min_outer_dist[1], 0.0);

    vec2 max_outer_dist = xy_max - xy;
    float right_outer_edge = smooth_edge(max_outer_dist[0], 0.0);
    float top_outer_edge = smooth_edge(max_outer_dist[1], 0.0);

    float outer_edge = left_outer_edge * bottom_outer_edge * right_outer_edge * top_outer_edge;

    float left_inner_edge = smooth_edge(min_outer_dist[0], border_thickness);
    float bottom_inner_edge = smooth_edge(min_outer_dist[1], border_thickness);

    float right_inner_edge = smooth_edge(max_outer_dist[0], border_thickness);
    float top_inner_edge = smooth_edge(max_outer_dist[1], border_thickness);

    float inner_edge = left_inner_edge * bottom_inner_edge * right_inner_edge * top_inner_edge;

    vec2 uv = (xy - xy_min + vec2(border_thickness)) / (xy_max - xy_min - 2.0 * vec2(border_thickness));
    float waveform_y = texture(waveform_texture, uv.x).r;

    float fragment_y = uv.y * 2.0 - 1.0;
    float waveform_edge = 1.0 - smooth_edge(fragment_y, waveform_y); // 0 if background, 1 if waveform
    bool is_waveform_positive = waveform_y >= 0.0;
    bool is_fragment_positive = fragment_y >= 0.0;
    bool is_side_correct = is_waveform_positive == is_fragment_positive;
    waveform_edge = is_waveform_positive ? waveform_edge : 1.0 - waveform_edge;
    waveform_edge *= float(is_side_correct);

    vec4 inner_color = mix(background_rgba, waveform_rgba, waveform_edge);
    vec4 color = mix(border_rgba, inner_color, inner_edge);
    color.a = mix(0.0, color.a, outer_edge);
	gl_FragColor = color;
}
