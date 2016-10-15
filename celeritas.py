#!/usr/bin/python -uB



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

import celeritas.uio as uio
import celeritas.glrender as glrender





APP_TITLE = b"Celeritas 0.0.0"



logger = logging.getLogger(__name__)


# this is temporary as we need to abstract away the events

def main():

	celeritas.config.load()


	main_window = uio.AppWindow(
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



	
	shader_src_vertex_0 = """
			#version 450 core
			layout (location = 0) in vec3 vertex_offset;

			uniform vec2 crosshair_position;

			void main() {
				gl_Position = vec4(
					crosshair_position.x + (vertex_offset.x * (1.0 - abs(crosshair_position.x))),
					crosshair_position.y + (vertex_offset.y * (1.0 - abs(crosshair_position.y))),
					vertex_offset.z,
					1.0
				);
			}
		"""

	shader_src_fragment_0 = """
			#version 450 core

			uniform vec4 obj_rgba;
			uniform vec2 crosshair_position;

			out vec4 color;

			float distance;

			void main()	{
				distance = pow(pow(abs(crosshair_position.x), 2.0) + pow(abs(crosshair_position.y), 2.0), 0.5) / 1.414213562;
				//distance = (abs.crosshair_position.x ** 2);
				//color = obj_rgba;
				color = vec4(1.0, 1.0, 1.0, 1.0);
				color = vec4((1 - distance), distance, 0.0, obj_rgba.w);
				//color = vec4((1 - abs(crosshair_position.x)), (1 - abs(crosshair_position.x)), abs(crosshair_position.x), 1.0);
			}
		"""

	main_context = glrender.Context(main_window.gl_context)
	(gprog_main,) = main_context.programs.add()
	(shader_v_main, shader_f_main) = gprog_main.shaders.add([
			(glrender.ST_VERTEX, shader_src_vertex_0),
			(glrender.ST_FRAGMENT, shader_src_fragment_0)
		
	])

	gprog_main.build()

	crosshair_uniform = glGetUniformLocation(gprog_main, "crosshair_position")
	rgba_uniform = glGetUniformLocation(gprog_main, "obj_rgba")

	vertices = [
		-0.2, -0.2,  0.0,		# bottom left
		 0.2, -0.2,  0.0,		# bottom right
		-0.2,  0.2,  0.0,		# top left
		 0.2,  0.2,  0.0,		# top right
	]

	indices = [
		1, 2, 0,
		1, 3, 2
	]


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
		ctypes.sizeof(GLfloat) * len(vertices),	# calculate size
		(GLfloat * len(vertices))(*vertices),
		GL_STATIC_DRAW
	)


	print("Generating element buffer")
	ebo_main = glGenBuffers(1)
	print("Binding element buffer")
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_main)
	print("Storing data in the element buffer")
	glBufferData(
		GL_ELEMENT_ARRAY_BUFFER,
		ctypes.sizeof(GLuint) * len(indices),	# calculate size
		(GLuint * len(indices))(*indices),
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




	w_x = ctypes.c_int(); w_y = ctypes.c_int()
	#SDL_GetWindowSize(main_window.sdl_window, w_x, w_y); # move this to "on resize" events and the like
	rel_x = 0.0; rel_y = 0.0

	while (uio.window_count > 0):

		for event in main_window.pop_events():
			#print(isinstance(event, uio.WindowCloseEvent))
			if (isinstance(event, uio.WindowCloseEvent)):
				main_window = None
				break
			#elif (event.type in (SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED, SDL_WINDOWEVENT_MOVED)):
				#print("Resized")
				#SDL_GetWindowSize(main_window.sdl_window, w_x, w_y)
			if (isinstance(event, uio.MouseMotionEvent)):
 				rel_x = (-0.5 + (float(event.x_abs) / float(guc["video"]["resolution_x"]))) * 2.0
 				rel_y = (-0.5 + (float(event.y_abs) / float(guc["video"]["resolution_y"]))) * -2.0
# 				rel_y = (-0.5 + (float(m_y.value) / float(w_y.value))) * -2.0
# 			elif (event.type in (SDL_KEYDOWN, SDL_KEYUP)):
# 				key_event = uio.KeyInputEvent(
# 					event_type = event.type,
# 					timestamp = event.key.timestamp,
# 					window_id = event.key.windowID,
# 					key_code = event.key.keysym.sym,
# 					unicode_cp = event.key.keysym.unicode,
# 					scan_code = event.key.keysym.scancode,
# 					modifiers = event.key.keysym.mod,
# 					is_repeat = bool(event.key.repeat)
# 				)
# 			

		# did we delete the window
		if (main_window is None):
			break;

		glClear(GL_COLOR_BUFFER_BIT)
		glClearColor(0, 0.2, 0.2, 0)

		#print("Activating program")
		glUseProgram(gprog_main)
		glUniform2f(crosshair_uniform, rel_x, rel_y)

		glUniform4f(rgba_uniform, 0.0, 0.0, 0.0, 1.0)


		glBindVertexArray(vao_main)

		#glDrawArrays(GL_TRIANGLES, 0, 3)
		glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

		glUseProgram(0)
		glBindVertexArray(0)

		main_window.frame_swap()

		time.sleep(0.001)


	del(main_context)

	logger.info("The last window was closed. Shutting down")

	glDeleteVertexArrays(1, [vao_main])
	glDeleteBuffers(1, [vbo_main])


	del(main_window);


	celeritas.config.save()
	#windowsurface = sfSDL_SetVideoMode(2560, 1440, 24, SDL_OPENGL)
	logger.info("Terminating")






exit(main())
