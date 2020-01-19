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

#version 330

uniform vec4 inner_rgba;
uniform vec4 outer_rgba;
uniform vec4 outer_background_rgba;

uniform float inner_radius;
uniform float outer_radius;
uniform float meter_a;
uniform float meter_b;
uniform float meter_c;

uniform vec2 xy_center;

in vec2 xy;

// Blends smoothly across a 1-pixel wide region around edge_distance, where < 0.5 indicates distance < edge_distance
float smooth_edge(float distance, float edge_distance) {
    // Find the distance change per-pixel - fwidth is the sum of abs(dFdx) and abs(dFdy)
    // Is max(abs(dFdx(xy.x)), abs(dFdy(xy.y))) more correct?
    float distance_change_per_pixel = fwidth(distance);

    // Blend between edge_distance - 0.5 and edge_distance + 0.5
    return clamp((distance - edge_distance) / distance_change_per_pixel + 0.5, 0.0, 1.0);
}

float float_and(float a, float b) {
    return a * b;
}

float float_or(float a, float b) {
    return 1.0 - (1.0 - a) * (1.0 - b);
}

const float k_pi = 3.14159265358979;

void main()
{
    vec2 relative_xy = xy - xy_center;
    float distance = length(relative_xy);

    // Rotate 90 degrees CW so that 0 is +y
    float angle = atan(-relative_xy.x, relative_xy.y);
    // Ratio starts at the bottom and goes from 0 to 1 CCW
    float meter_ratio = 0.5 - angle * (0.5 / k_pi);
    float a_edge = smooth_edge(meter_ratio, meter_a);
    float b_edge = smooth_edge(meter_ratio, meter_b);
    float c_edge = smooth_edge(meter_ratio, meter_c);
    float pre_a_edge = smooth_edge(meter_ratio, meter_a - 0.05);
    float post_c_edge = smooth_edge(meter_ratio, meter_c + 0.05);

    // Fix the edge at the bottom
    float is_valid_multiplier = float(meter_ratio > 0.05 && meter_ratio < 0.95);
    a_edge *= is_valid_multiplier;
    b_edge *= is_valid_multiplier;
    c_edge *= is_valid_multiplier;
    pre_a_edge *= is_valid_multiplier;
    post_c_edge *= is_valid_multiplier;

    float inner_ratio = 1.0 - smooth_edge(distance, inner_radius);
    float outer_ratio = 1.0 - smooth_edge(distance, outer_radius);
    float meter_alpha = float_and(a_edge, 1.0 - c_edge);
    float outer_alpha = float_and(meter_alpha, outer_ratio);
    float alpha = float_or(outer_alpha, inner_ratio);

    // Fix AA on the bottom edge by making it the inner color
    float expanded_meter_ratio = float_and(pre_a_edge, 1.0 - post_c_edge);
    float inner_color_ratio = float_or(inner_ratio, 1.0 - expanded_meter_ratio);
    float meter_color_ratio = float_and(a_edge, 1.0 - b_edge);

    vec4 outer_color = mix(outer_background_rgba, outer_rgba, meter_color_ratio);
    vec4 color = mix(outer_color, inner_rgba, inner_color_ratio);
    color.a = mix(0.0, color.a, alpha);
	gl_FragColor = color;
}
