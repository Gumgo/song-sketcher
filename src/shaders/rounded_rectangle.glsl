#vs

#version 130

varying vec2 xy;

void main()
{
    xy = gl_Vertex.xy;
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}

#fs

#version 130

uniform vec4 rgba;
uniform vec4 border_rgba;
uniform float border_thickness;
uniform float radius;

uniform vec2 xy1;
uniform vec2 xy2;

varying vec2 xy;

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
    vec2 size = xy_max - xy_min;

    float outer_radius = min(radius, min(size.x * 0.5, size.y * 0.5));
    float border_radius = outer_radius - border_thickness;
    xy_min += vec2(outer_radius, outer_radius);
    xy_max -= vec2(outer_radius, outer_radius);
    vec2 clamped_xy = clamp(xy, xy_min, xy_max);
    float dist = length(xy - clamped_xy);
    float border_ratio = smooth_edge(dist, border_radius);
    float outer_ratio = smooth_edge(dist, outer_radius);
    vec4 color = mix(rgba, border_rgba, border_ratio);
    color.a = mix(color.a, 0.0, outer_ratio);
	gl_FragColor = color;
}
