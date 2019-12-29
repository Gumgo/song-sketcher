#vs

#version 130

void main()
{
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}

#fs

#version 130

uniform vec4 rgba;

void main()
{
	gl_FragColor = rgba;
}
