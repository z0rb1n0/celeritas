#!/usr/bin/python -u



import sys
import logging
import time
import logging




import OpenGL
OpenGL.USE_ACCELERATE = True
#OpenGL.ERROR_CHECKING = True
#OpenGL.ERROR_LOGGING = True
#OpenGL.FULL_LOGGING = True

from OpenGL.GL import *
from OpenGL.AGL import *
from OpenGL.GLE import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
import numpy

from OpenGL.GL import shaders


import celeritas.config
import celeritas.info
from celeritas.config import guc

from celeritas.uio import AppWindow





APP_TITLE = b"Celeritas 0.0.0"



logger = logging.getLogger(__name__)


def main():

	celeritas.config.load()


	main_window = AppWindow(
		w = guc["video"]["resolution_x"],
		h = guc["video"]["resolution_y"],
		title = ("%s %d.%d.%d" % (
			celeritas.info.APP_TITLE,
			celeritas.info.APP_MAJOR,
			celeritas.info.APP_MINOR,
			celeritas.info.APP_REVISION
		))
	)

	print("Vendor:          %s" % (glGetString(GL_VENDOR)))
	print("Opengl version:  %s" % (glGetString(GL_VERSION)))
	print("GLSL Version:    %s" % (glGetString(GL_SHADING_LANGUAGE_VERSION)))
	print("Renderer:        %s" % (glGetString(GL_RENDERER)))

	#glMatrixMode(GL_PROJECTION)
	#glLoadIdentity()


	print("Creating OpenGL viewport")
	glViewport(0, 0, guc["video"]["resolution_x"], guc["video"]["resolution_y"])

	#glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	#glEnable(GL_DEPTH_TEST)
	#glEnable(GL_CULL_FACE)
	#glEnable(GL_BLEND)


	print("Creating vertex shader")
	shader_v_main = glCreateShader(GL_VERTEX_SHADER)
	print("Preparing vertex shader source")
	glShaderSource(
		shader_v_main,
		"""
			#version 450 core
			layout (location = 0) in vec3 vertex_offset;

			uniform vec2 crosshair_position;


			void main() {
				gl_Position = vec4(
					crosshair_position.x + vertex_offset.x,
					crosshair_position.y + vertex_offset.y,
					vertex_offset.z,
					1.0
				);
			}
		"""
	)
	print("Compiling vertex shader")
	glCompileShader(shader_v_main)
	if (not glGetShaderiv(shader_v_main, GL_COMPILE_STATUS)):
		print("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(shader_v_main))
		return 5


	print("Creating fragment shader")
	shader_f_main = glCreateShader(GL_FRAGMENT_SHADER)
	print("Preparing fragment shader source")
	glShaderSource(
		shader_f_main,
		"""
			#version 450 core

			out vec4 color;

			void main()	{
				color = vec4(1.0f, 0.5f, 0.2f, 1.0f);
			}
		"""
	)
	print("Compiling fragment shader")
	glCompileShader(shader_f_main)
	if (not glGetShaderiv(shader_f_main, GL_COMPILE_STATUS)):
		print("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(shader_f_main))
		return 5


	print("Creating shader program")
	shprog_main = glCreateProgram()
	print("Attaching shaders to program")
	glAttachShader(shprog_main, shader_v_main)
	glAttachShader(shprog_main, shader_f_main)
	print("Linking program")
	glLinkProgram(shprog_main)
	if (not glGetProgramiv(shprog_main, GL_LINK_STATUS)):
		print("Program linking failed. Error: `%s`" % glGetProgramInfoLog(shprog_main))
		return 5


	print("Deleting shader objects")
	map(glDeleteShader, (shader_f_main, shader_v_main))

	crosshair_uniform = glGetUniformLocation(shprog_main, "crosshair_position")


	vertices = [
		-0.2, -0.2,  0.0,		# bottom left
		 0.2, -0.2,  0.0,		# bottom right
		-0.2,  0.2,  0.0,		# top left
		 0.2,  0.2,  0.0,		# top right
	]
	vertices_s = (GLfloat * len(vertices))(*vertices)

	indices = [
		0, 1, 3,
		3, 2, 0
	]
	indices_s = (GLuint * len(indices))(*indices)


	print("Generating Vertex Array Object")
	vao_main = glGenVertexArrays(1)
	print("Binding Vertex Array Object")
	glBindVertexArray(vao_main)

	print("Generating vertex buffer")
	vbo_main = glGenBuffers(1)
	print("Binding vertex buffer")
	glBindBuffer(GL_ARRAY_BUFFER, vbo_main)
	print("Storing data in the vertex buffer")
	glBufferData(
		GL_ARRAY_BUFFER,
		ArrayDatatype.arrayByteCount(vertices_s),	# calculate size
		vertices_s,   								# this is how the array of GLfloats is built: sort a dynamic type. Ask Mike
		GL_STATIC_DRAW
	)


	print("Generating element buffer")
	ebo_main = glGenBuffers(1)
	print("Binding element buffer")
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_main)
	print("Storing data in the element buffer")
	glBufferData(
		GL_ELEMENT_ARRAY_BUFFER,
		ArrayDatatype.arrayByteCount(indices_s),	# calculate size
		indices_s,   								# this is how the array of GLfloats is built: sort a dynamic type. Ask Mike
		GL_STATIC_DRAW
	)


	print("Preparing vertex attribute definition for position")
	glVertexAttribPointer(
		0,								# location 0 is position according to the layout in our vertex shader
		3,								# we supply 3 variables per vertex
		GL_FLOAT,						# they're floats
		False,							# not sure why the author specifies "false" here. The data in fact IS normalized
		ctypes.sizeof(GLfloat) * 3,		# stride is same as length as the array has no gaps
		None							# we start at the first byte. This is a null pointer
	)
	print("Activating vertex attribute definition for position")
	glEnableVertexAttribArray(0)


	print("Unbinding Vertex Buffer Object")
	glBindBuffer(GL_ARRAY_BUFFER, 0)
	print("Unbinding Vertex Array Object")
	glBindVertexArray(0)



	# this is temporary as we need to abstract away the events
	from sdl2 import *

	loop_active = True
	event = SDL_Event()
	w_x = ctypes.c_int(); w_y = ctypes.c_int()
	SDL_GetWindowSize(main_window.sdl_window, w_x, w_y); # move this to "on resize" events and the like
	rel_x = 0.0; rel_y = 0.0

	while loop_active:

		while (SDL_PollEvent(ctypes.byref(event))):
			if (event.type == SDL_QUIT):
				loop_active = False
				break
			#elif (event.type in (SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED, SDL_WINDOWEVENT_MOVED)):
				#print("Resized")
				#SDL_GetWindowSize(main_window.sdl_window, w_x, w_y)
			elif (event.type == SDL_MOUSEMOTION):
				m_x = ctypes.c_int(); m_y = ctypes.c_int()
				SDL_GetMouseState(m_x, m_y)
				rel_x = (-0.5 + (float(m_x.value) / float(w_x.value))) * 2.0
				rel_y = (-0.5 + (float(m_y.value) / float(w_y.value))) * -2.0

			

		glClear(GL_COLOR_BUFFER_BIT)
		glClearColor(0, 0.2, 0.2, 0)

		#print("Activating program")
		glUseProgram(shprog_main)
		glUniform2f(crosshair_uniform, rel_x, rel_y)


		glBindVertexArray(vao_main)

		#glDrawArrays(GL_TRIANGLES, 0, 3)
		glDrawElements(GL_TRIANGLES, len(indices_s), GL_UNSIGNED_INT, None)

		glUseProgram(0)
		glBindVertexArray(0)

		SDL_GL_SwapWindow(main_window.sdl_window)

		time.sleep(0.001)


	glDeleteVertexArrays(1, [vao_main])
	glDeleteBuffers(1, [vbo_main])

	SDL_GL_DeleteContext(main_context)
	SDL_DestroyWindow(main_window)
	SDL_Quit()
	celeritas.config.save();
	#windowsurface = sfSDL_SetVideoMode(2560, 1440, 24, SDL_OPENGL)
	logger.info("Terminating");


	return 0





exit(main())
