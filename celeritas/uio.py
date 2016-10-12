#!/usr/bin/python -uB

"""
	Window manager for Celeritas. Initializes an OpenGL-capable window,
	without exposing the underlying API.
	The most important thing we need the window to expose is the OpenGL context
"""
import logging
import sdl2
from sdl2 import *


import info;


logger = logging.getLogger(__name__)


WINDOW_WINDOWED = 0
WINDOW_FULL_SCREEN = 1
WINDOW_FAKE_FULL_SCREEN = 2


EVENT_KEY_DOWN = 64
EVENT_KEY_UP = 65

EVENT_MOUSE_DOWN = 128
EVENT_MOUSE_UP = 129
EVENT_MOUSE_CLICK = 130



UIO_SDL_SETTINGS = {
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

class Event(object):
	"""
		Generic User I/O Event
	"""
	pass;

class EventWindowFocusOn(Event):	"""Window focus event. Has no properties"""; pass;
class EventWindowFocusOff(Event):	"""Window un-focus event. Has no properties"""; pass;
class EventWindowMinimize(Event):	"""Window minimization event. Has no properties"""; pass;
class EventWindowRestore(Event):	"""Window size restoration event. Has no properties"""; pass;
class EventWindowMaximize(Event):	"""Window maximization event. Has no properties"""; pass;
class EventWindowClose(Event):	"""Window close event. Has no properties"""; pass;

# map of property names -> SDL modifier flags
KMOD_PROPERTIES = {

	"ctrl": KMOD_CTRL,
	"ctrl_l": KMOD_LCTRL,
	"ctrl_r": KMOD_RCTRL,

	"alt": KMOD_ALT,
	"alt_l": KMOD_LALT,
	"alt_r": KMOD_RALT,
	"alt_gr": KMOD_MODE,

	"shift": KMOD_SHIFT,
	"shift_l": KMOD_LSHIFT,
	"shift_r": KMOD_RSHIFT,

	"num_lock": KMOD_NUM,
	"caps_lock": KMOD_CAPS,
	
	"win": KMOD_GUI,
	"win_l": KMOD_LGUI,
	"win_r": KMOD_RGUI,

}


class EventKeyChange(Event):
	"""
		Key press/release/whatever event.
		
		Modifiers are represented as individual properties
	"""
	def __init__(self,
		change_type,
		key_code,
		unicode_cp = None,
		scan_code = None,
		modifiers = KMOD_NONE,
		timestamp = None,
		window_id = None
	):
		"""
			Right now this is taken straight out of SDL: https://wiki.libsdl.org/SDL_KeyboardEvent and
			https://wiki.libsdl.org/SDL_Keysym. In fact, modifiers are internally stored as the native SDL bitmask

			Arguments:
				change_type:			SDL_KEYDOWN | SDL_KEYUP
				key_code:				see https://wiki.libsdl.org/SDL_Keysym
				unicode_cp:				unicode Code Point. For some reason not documented by SDL but returned by pySDL
				scan_code:				see https://wiki.libsdl.org/SDL_Keysym
				modifiers:				see https://wiki.libsdl.org/SDL_Keysym
				timestamp:				see https://wiki.libsdl.org/SDL_KeyboardEvent
				window_id:				see https://wiki.libsdl.org/SDL_KeyboardEvent

		"""
		# called from a subclass, we don't care about what is passed in change_type
		self.down = (change_type == SDL_KEYDOWN)
		self.kc = key_code
		self.uc = unicode_cp
		self.sc = scan_code
		self._modifiers = modifiers
		self.ts = timestamp
		self.wid = window_id



	def __getattr__(self, attribute):
		"""
			As opposed to materializing the modifiers at event generation
			we resolve them from the bitmask
		"""
		try:
			return bool(self._modifiers & KMOD_PROPERTIES[attribute]);
		except:
			raise AttributeError("No such attribute: %s" % attribute);
			return None;


class EventKeyDown(EventKeyChange):
	"""
		Key press. Same as KeyChange but with the firsta argument passed as SDL_KEYDOWN.
		If change_type is passed as a keyword argument it is ignored
		Has one more member on top of the KeyChange indicating keyboard repeat.
	"""
	def __init__(self, *args, **kwargs):
		"""
			Additional arguments:
				is_repeat:				see https://wiki.libsdl.org/SDL_KeyboardEvent
		"""
		self.rep = (bool(kwargs["is_repeat"]) if "is_repeat" in kwargs else False)
		kwargs.pop("change_type", None)
		kwargs.pop("is_repeat", None)
		super(EventKeyDown, self).__init__(*(( SDL_KEYDOWN, ) + args), **kwargs)

class EventKeyUp(EventKeyChange):
	"""
		Key release. Same semantics as EventKeyDown, minus is_repeat
	"""
	def __init__(self, *args, **kwargs):
		kwargs.pop("change_type", None)
		super(EventKeyUp, self).__init__(*(( SDL_KEYUP	, ) + args), **kwargs)

		

class AppWindow():

	"""
		Application window class. An I/O subsystem-agnostic window.
		Window subsystems are initialized/shut down based on a reference count
	"""

	def __init__(self,
		mode = WINDOW_WINDOWED,
		w = 320,
		h = 200,
		title = "New SDL/OpenGL Window",
		visible = True
	):
		"""
			Initializes a window. If necessary initializes a the SDL context.
			
			ArgumentsL
			
			mode:		one of the WINDOW_ modes.
			w:			width
			h:			height
			title:		title
			visiblle:	whether or not the window should be visible on initializtion
		"""

		self.sdl_window = None
		self.gl_context = None;

		global window_count
		
		if (window_count == 0):
			logger.debug("This is the first window. Initializing SDL")
			if (SDL_Init(SDL_INIT_VIDEO) != 0):
				raise SDLException("SDL Initialization failed: `%s`" % (SDL_GetError()))

			for (att_name, att_value) in UIO_SDL_SETTINGS.items():
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
		"""
			Some cleanup whenever possible
		"""
		global window_count

		SDL_GL_DeleteContext(self.gl_context)
		SDL_DestroyWindow(self.sdl_window)
		window_count -= 1

		logger.debug("Window count decreased to %d", (window_count))
		if (window_count <= 0):
			logger.debug("No more windows left. Shutting down SDL")
			SDL_Quit()
			

	def get_event_queue(retain = False):
		"""
			Retrieves the queue of events from the windowing system.
		"""
