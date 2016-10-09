#!/usr/bin/python -u



import sys;
import ctypes;
import struct;
import time;
import logging;
from sdl2 import *;
#import sdl2.ext;


import OpenGL;
OpenGL.USE_ACCELERATE = True
OpenGL.ERROR_CHECKING = True
OpenGL.ERROR_LOGGING = True;
#OpenGL.FULL_LOGGING = True;

from OpenGL.GL import *;
from OpenGL.AGL import *;
from OpenGL.GLE import *;
from OpenGL.GLU import *;
from OpenGL.GLUT import *;
from OpenGL.arrays import vbo;
import numpy;

from OpenGL.GL import shaders;


APP_TITLE = b"Celeritas 0.0.0";

USE_GLUT = False;

WINDOW_WIDTH = 800;
WINDOW_HEIGHT = 600;


def main():

	if (USE_GLUT):
		print("Initializing GLUT");
		glutInit(sys.argv);
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA);
		print("Initializing GLUT window");
		glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT);
		main_window = glutCreateWindow(APP_TITLE + " (GLUT)");
		#InitGL(WINDOW_WIDTH, WINDOW_HEIGHT);
	else:

		print("Initializing SDL");
		if (SDL_Init(SDL_INIT_VIDEO) != 0):
			print("SDL Initialization failed");
			exit(5);
		

		SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4);
		SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 5);

		SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8);
		SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
		SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8);
		SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

		SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);

		SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);


		print("Initializing SDL window");
		main_window = SDL_CreateWindow(
			APP_TITLE + " (SDL)",
			SDL_WINDOWPOS_CENTERED,
			SDL_WINDOWPOS_CENTERED,
			WINDOW_WIDTH, WINDOW_HEIGHT,
			SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL
		);

		if (not main_window):
			print("Initializing SDL window");
			print(SDL_GetError());
			return 3;


		print("Creating OpenGL context");
		main_context = SDL_GL_CreateContext(main_window);
		if (SDL_GL_MakeCurrent(main_window, main_context)):
			print("Failed to make OpenGL context current");
			exit(5);

		SDL_GL_SetSwapInterval(1);


	print("Vendor:          %s" % (glGetString(GL_VENDOR)));
	print("Opengl version:  %s" % (glGetString(GL_VERSION)));
	print("GLSL Version:    %s" % (glGetString(GL_SHADING_LANGUAGE_VERSION)));
	print("Renderer:        %s" % (glGetString(GL_RENDERER)));

	#glMatrixMode(GL_PROJECTION);
	#glLoadIdentity();


	print("Creating OpenGL viewport");
	glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT);

	#glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	#glEnable(GL_DEPTH_TEST);
	#glEnable(GL_CULL_FACE);
	#glEnable(GL_BLEND);


	print("Creating vertex shader");
	shader_v_main = glCreateShader(GL_VERTEX_SHADER);
	print("Preparing vertex shader source");
	glShaderSource(
		shader_v_main,
		"""
			#version 450 core
			layout (location = 0) in vec3 position;

			void main() {
				gl_Position = vec4(position.x, position.y, position.z, 1.0);
			};
		"""
	);
	print("Compiling vertex shader");
	glCompileShader(shader_v_main);
	if (not glGetShaderiv(shader_v_main, GL_COMPILE_STATUS)):
		print("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(shader_v_main));
		return 5;


	print("Creating fragment shader");
	shader_f_main = glCreateShader(GL_FRAGMENT_SHADER);
	print("Preparing fragment shader source");
	glShaderSource(
		shader_f_main,
		"""
			#version 450 core

			out vec4 color;

			void main()	{
				color = vec4(1.0f, 0.5f, 0.2f, 1.0f);
			}
		"""
	);
	print("Compiling fragment shader");
	glCompileShader(shader_f_main);
	if (not glGetShaderiv(shader_f_main, GL_COMPILE_STATUS)):
		print("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(shader_f_main));
		return 5;


	print("Creating shader program");
	shprog_main = glCreateProgram();
	print("Attaching shaders to program");
	glAttachShader(shprog_main, shader_v_main);
	glAttachShader(shprog_main, shader_f_main);
	print("Linking program");
	glLinkProgram(shprog_main);
	if (not glGetProgramiv(shprog_main, GL_LINK_STATUS)):
		print("Program linking failed. Error: `%s`" % glGetProgramInfoLog(shprog_main));
		return 5;

	print("Deleting shader objects");
	map(glDeleteShader, (shader_f_main, shader_v_main));

	vertices = [
		-0.5, -0.5,  0.0,		# bottom left
		 0.5, -0.5,  0.0,		# bottom right
		-0.5,  0.5,  0.0,		# top left
		 0.5,  0.5,  0.0,		# top right
	];
	vertices_s = (GLfloat * len(vertices))(*vertices);

	indices = [
		0, 1, 3,
		3, 2, 0
	];
	indices_s = (GLuint * len(indices))(*indices);



	print("Generating Vertex Array Object");
	vao_main = glGenVertexArrays(1);
	print("Binding Vertex Array Object");
	glBindVertexArray(vao_main);

	print("Generating vertex buffer");
	vbo_main = glGenBuffers(1);
	print("Binding vertex buffer");
	glBindBuffer(GL_ARRAY_BUFFER, vbo_main);
	print("Storing data in the vertex buffer");
	glBufferData(
		GL_ARRAY_BUFFER,
		ArrayDatatype.arrayByteCount(vertices_s),	# calculate size
		vertices_s,   								# this is how the array of GLfloats is built: sort a dynamic type. Ask Mike
		GL_STATIC_DRAW
	);


	print("Generating element buffer");
	ebo_main = glGenBuffers(1);
	print("Binding element buffer");
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_main);
	print("Storing data in the element buffer");
	glBufferData(
		GL_ELEMENT_ARRAY_BUFFER,
		ArrayDatatype.arrayByteCount(indices_s),	# calculate size
		indices_s,   								# this is how the array of GLfloats is built: sort a dynamic type. Ask Mike
		GL_STATIC_DRAW
	);


	print("Preparing vertex attribute definition for position");
	glVertexAttribPointer(
		0,								# location 0 is position according to the layout in our vertex shader
		3,								# we supply 3 variables per vertex
		GL_FLOAT,						# they're floats
		False,							# not sure why the author specifies "false" here. The data in fact IS normalized
		ctypes.sizeof(GLfloat) * 3,		# stride is same as length as the array has no gaps
		None							# we start at the first byte. This is a null pointer
	);
	print("Activating vertex attribute definition for position");
	glEnableVertexAttribArray(0);


	print("Unbinding Vertex Buffer Object");
	glBindBuffer(GL_ARRAY_BUFFER, 0);
	print("Unbinding Vertex Array Object");
	glBindVertexArray(0);


	loop_active = True;

	if (USE_GLUT):
		pass;
	else:
		event = SDL_Event();

	while loop_active:
		if (USE_GLUT):
			pass;
		else:
			if (SDL_PollEvent(ctypes.byref(event)) and (event.type == SDL_QUIT)):
				loop_active = False;
				break;

		glClear(GL_COLOR_BUFFER_BIT);
		#glClearColor(0, 0.2, 0.2, 0);

		#print("Activating program");
		glUseProgram(shprog_main);
		
		glBindVertexArray(vao_main);

		#glDrawArrays(GL_TRIANGLES, 0, 3);
		glDrawElements(GL_TRIANGLES, len(indices_s), GL_UNSIGNED_INT, None);

		glUseProgram(0);
		glBindVertexArray(0);

		if (USE_GLUT):
			glutSwapBuffers();
		else:
			SDL_GL_SwapWindow(main_window);

		time.sleep(0.001);


	glDeleteVertexArrays(1, [vao_main]);
	glDeleteBuffers(1, [vbo_main]);

	SDL_GL_DeleteContext(main_context);
	SDL_DestroyWindow(main_window);
	SDL_Quit();
	#windowsurface = sfSDL_SetVideoMode(2560, 1440, 24, SDL_OPENGL);
	print("Terminating");


	return 0;






#     GL.glOrtho(-400, 400, 300, -300, 0, 1);

#     x = 0.0;
#     y = 30.0;

#     event = sdl2.SDL_Event();
#     running = True
#     while running:
#         while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
#             if event.type == sdl2.SDL_QUIT:
#                 running = False

#         GL.glClearColor(0, 0, 0, 1)
#         GL.glClear(GL.GL_COLOR_BUFFER_BIT)
#         GL.glRotatef(10.0, 0.0, 0.0, 1.0)
#         GL.glBegin(GL.GL_TRIANGLES)
#         GL.glColor3f(1.0, 0.0, 0.0)
#         GL.glVertex2f(x, y + 90.0)
#         GL.glColor3f(0.0, 1.0, 0.0)
#         GL.glVertex2f(x + 90.0, y - 90.0)
#         GL.glColor3f(0.0, 0.0, 1.0)
#         GL.glVertex2f(x - 90.0, y - 90.0)
#         GL.glEnd()

#         sdl2.SDL_GL_SwapWindow(window)
#         sdl2.SDL_Delay(10)
#     sdl2.SDL_GL_DeleteContext(context)
#     sdl2.SDL_DestroyWindow(window)
#     sdl2.SDL_Quit()












# 	windowsurface = SDL_GetWindowSurface(window)

# 	image = SDL_LoadBMP(b"exampleimage.bmp")
# 	SDL_BlitSurface(image, None, windowsurface, None)

# 	SDL_UpdateWindowSurface(window)
# 	SDL_FreeSurface(image)

# 	running = True
# 	event = SDL_Event()
# 	while running:
# 		while SDL_PollEvent(ctypes.byref(event)) != 0:
# 			if event.type == SDL_QUIT:
# 				running = False
# 				break

# 	SDL_DestroyWindow(window)

# 	SDL_Quit();


# 	return 0;

# 	main_window = sdl2.ext.Window("Celeritas 0.0.0", size=(2560, 1440));
# 	main_window.show();

# 	#processor = sdl2.ext.TestEventProcessor();

# 	main_renderer = sdl2.ext.SoftwareSpriteRenderSystem(main_window);
# 	sdl2.ext.fill(main_renderer.surface, sdl2.ext.Color(0, 0, 0));


# 	loop_active = True;
# 	while loop_active:
# 		events = sdl2.ext.get_events();
# 		for event in events:
# 			print(event.type);
# 			if event.type == sdl2.SDL_QUIT:
# 				loop_active = False;
# 				break;
# 			

# 		time.sleep(0.001);
# 		main_window.refresh();

# 	return 0;



exit(main());
