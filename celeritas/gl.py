#!/usr/bin/python -uB

"""
	Window manager for Celeritas. Initializes an OpenGL-capable window,
	without exposing the underlying API.
	The most important thing we need the window to expose is the OpenGL context
"""
import logging
import Open
from sdl2 import *


import info;


logger = logging.getLogger(__name__)


UIO_WINDOWED = 0
UIO_FULL_SCREEN = 1
UIO_FAKE_FULL_SCREEN = 2


UIO_SDL_ATTRIBUTES = {
	"SDL_GL_CONTEXT_MAJOR_VERSION": 4,
	"SDL_GL_CONTEXT_MINOR_VERSION": 5,
	"SDL_GL_RED_SIZE": 8,
	"SDL_GL_GREEN_SIZE": 8,
	"SDL_GL_BLUE_SIZE": 8,
	"SDL_GL_DEPTH_SIZE": 24,
	"SDL_GL_DOUBLEBUFFER": 1,
	"SDL_GL_CONTEXT_PROFILE_MASK": SDL_GL_CONTEXT_PROFILE_CORE
}




window_count = 0;


class SDLException(Exception): pass


		

class AppWindow():

	"""
		Application window class. An I/O subsystem-agnostic window
	"""

	def __init__(self,
		mode = UIO_WINDOWED,
		w = 320,
		h = 200,
		title = "New SDL/OpenGL Window",
		visible = True
	):

		self.sdl_window = None
		self.gl_context = None;

		global window_count
		
		if (window_count == 0):
			logger.debug("This is the first window. Initializing SDL")
			if (SDL_Init(SDL_INIT_VIDEO) != 0):
				raise SDLException("SDL Initialization failed: `%s`" % (SDL_GetError()))

			for (att_name, att_value) in UIO_SDL_ATTRIBUTES.items():
				if (SDL_GL_SetAttribute(sdl2.__dict__[att_name], att_value) != 0):
					SDL_Quit()
					raise SDLException("Error setting SDL attribute `%s` to %d: %s" % (att_name, att_value, SDL_GetError()))



		self.sdl_window = SDL_CreateWindow(
			title,
			SDL_WINDOWPOS_CENTERED,
			SDL_WINDOWPOS_CENTERED,
			w, h,
			(SDL_WINDOW_SHOWN if visible else SDL_WINDOW_HIDDEN) | SDL_WINDOW_OPENGL
		)

		if (self.sdl_window):
			window_count += 1;
			logger.debug("Window count increased to %d", (window_count))
		else:
			raise SDLException("Unable to create SDL window with title `%s`: %s" % (title, SDL_GetError()))


		self.gl_context = SDL_GL_CreateContext(self.sdl_window)
		if (self.gl_context is None):
			SDL_DestroyWindow(self.sdl_window);
			window_count -= 1;
			raise SDLException("Unable to create an OpenGL context for window `%s`: %s" % (self.sdl_window, SDL_GetError()));
	
			
		if (SDL_GL_MakeCurrent(self.sdl_window, self.gl_context) != 0):
			SDL_GL_DeleteContext(self.gl_context)
			SDL_DestroyWindow(self.sdl_window);
			window_count -= 1;
			raise SDLException("Unable to set OpenGL context #%d as the current one for window `%s`: %s" % (self.gl_context, self.sdl_window, SDL_GetError()));


		if (SDL_GL_SetSwapInterval(1)):
			SDL_GL_DeleteContext(self.gl_context)
			SDL_DestroyWindow(self.sdl_window);
			SDL_Quit()
			raise SDLException("Unable to set GL swap interval: %s" % (SDL_GetError()))


	def __del__(self):
		global window_count

		SDL_GL_DeleteContext(self.gl_context)
		SDL_DestroyWindow(self.sdl_window)
		window_count -= 1

		logger.debug("Window count decreased to %d", (window_count))
		if (window_count <= 0):
			logger.debug("No more windows left. Shutting down SDL")
			SDL_Quit()
			



