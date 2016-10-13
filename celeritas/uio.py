#!/usr/bin/python -uB

"""
	Window manager for Celeritas. Initializes an OpenGL-capable window,
	without exposing the underlying API.
	The most important thing we need the window to expose is the OpenGL context
	
	
	We could use the inspect module to avoid many of the inheritance boilerplate
	but speed is important here
"""
import ctypes
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


# map of property names -> SDL modifier flags
KMOD_FLAGS = {

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


# map of property names -> SDL modifier flags
MBUTTON_FLAGS = {
	# this must be custom functionality we do not support yet
	#SDL_BUTTON(X)       (1 << ((X)-1))
	"butt_l": SDL_BUTTON_LEFT,
	"butt_m": SDL_BUTTON_MIDDLE,
	"butt_r": SDL_BUTTON_RIGHT,
	"butt_x1": SDL_BUTTON_X1,
	"butt_x2": SDL_BUTTON_X2
}



window_count = 0



# event queue, maintained as an ever increasing counter
# each member actually contains a tuple: (raw_SDL_event, our_object_representation)
polled_sdl_events = {}
# current event counter
# this may overflow on 32 bit machines if the application keeps running
# long enough
event_counter = 0

# window_id -> [event_ids] list to accelerate lookups
windows_events = {}







class SDLException(Exception): pass

class Event(object):
	"""
		Generic User I/O Event
	"""
	def __init__(self,
		event_type,
		timestamp
	):
		"""
			Arguments:
				event_type:				SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEMOTION and so on...
				timestamp:				process-relative event timestamp as supplied by SDL
		"""
		self.sdl_type = event_type;
		self.ts = timestamp;

class WindowScopeEvent(Event):
	"""
		Any event that could happen within the scope of a window
	"""
	def __init__(self,
		event_type,
		timestamp,
		window_id
	):
		"""
			Extension arguments:
				window_id:				the window ID the event occurred on
		"""
		super(WindowScopeEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp
		)
		self.winid = window_id


class WindowEvent(WindowScopeEvent):
	"""
		Events affecting the window itself
	"""
	def __init__(self,
		event_type,
		timestamp,
		window_id,
		window_event_type
	):
		"""
			Extension arguments:
				window_event_type:				specific sub type of the window event (SDL_WINDOWEVENT_*)
		"""
		super(WindowEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp,
			window_id = window_id
		)
		self.we_type = window_event_type


class WindowFocusOnEvent(WindowEvent):	"""Window focus event. Has no properties of its own"""; pass;
class WindowFocusOffEvent(WindowEvent):	"""Window un-focus event. Has no properties of its own"""; pass;
class WindowMinimizeEvent(WindowEvent):	"""Window minimization event. Has no properties of its own"""; pass;
class WindowRestoreEvent(WindowEvent):	"""Window size restoration event. Has no properties of its own"""; pass;
class WindowMaximizeEvent(WindowEvent):	"""Window maximization event. Has no properties of its own"""; pass;
class WindowCloseEvent(WindowEvent):	"""Window close event. Has no properties of its own"""; pass;





class KeyInputEvent(WindowScopeEvent):
	"""
		Key press/release/whatever event.
		
		Modifiers are represented as individual properties
	"""
	def __init__(self,
		event_type,
		timestamp,
		window_id,
		key_code,
		unicode_cp = None,
		scan_code = None,
		modifiers = KMOD_NONE,
		is_repeat = False
	):
		"""
			Right now this is taken straight out of SDL: https://wiki.libsdl.org/SDL_KeyboardEvent and
			https://wiki.libsdl.org/SDL_Keysym. In fact, modifiers are internally stored as the native SDL bitmask

			Arguments:
				key_code:				see https://wiki.libsdl.org/SDL_Keysym
				unicode_cp:				unicode Code Point. For some reason not documented by SDL but returned by pySDL
				scan_code:				see https://wiki.libsdl.org/SDL_Keysym
				modifiers:				see https://wiki.libsdl.org/SDL_Keysym
				is_repeat:				https://wiki.libsdl.org/SDL_KeyboardEvent

		"""
		super(KeyInputEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp,
			window_id = window_id
		)
		# single assignment is good
		(self.down,                   self.up,                     self.kc,  self.uc,    self.sc,    self._modifiers, self.rep) = \
		((event_type == SDL_KEYDOWN), (event_type == SDL_KEYUP),   key_code, unicode_cp, scan_code,  modifiers,       is_repeat)



	def __getattr__(self, attribute):
		"""
			Instead of materializing the modifiers in a tuple/list
			at event generation (expensive) we resolve them on-demand
			from the bitmask
		"""
		try:
			return bool(self._modifiers & KMOD_FLAGS[attribute]);
		except:
			raise AttributeError("No such attribute: %s" % attribute);
			return None;



class MouseInputEvent(WindowScopeEvent):
	"""
		Generic mouse action event. Base class that is meant to be
		extended by various mouse event types
	"""
	def __init__(self,
		event_type,
		timestamp,
		window_id,
		mouse_id,
		buttons_mask,
		x,
		y,
	):
		"""
			These are all the attributes shared by:
				https://wiki.libsdl.org/SDL_MouseMotionEvent
				https://wiki.libsdl.org/SDL_MouseButtonEvent
				https://wiki.libsdl.org/SDL_MouseWheelEvent

			mouse_id:		the mouse device id, as supplied by SDL. Could be SDL_TOUCH_MOUSEID, which requires special handling
			button_mask:	what buttons were pressed at the time of the event
			x:				absolute x mouse position at  the time of the event, SDL coordinate system
			y:				see x_abs and guess...
			
		"""
		super(MouseInputEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp,
			window_id = window_id
		)

		(self.md_id, self._buttons_mask, self.x_abs, self.y_abs) = \
		(mouse_id,   buttons_mask,       x,          y)

	def __getattr__(self, attribute):
		"""
			Much like for keyboard events, it is preferable not to materialize
			the list of buttons at class initialization; the flag mask is compared on
			demand instead
		"""
		try:
			return bool(self._buttons_mask & MBUTTON_FLAGS[attribute]);
		except:
			raise AttributeError("No such attribute: %s" % attribute);
			return None;


class MouseMotionEvent(MouseInputEvent):
	"""
		Mouse move. Implemented as its own class as it has specific properties
	"""
	def __init__(self,
		event_type,
		timestamp,
		window_id,
		mouse_id,
		buttons_mask,
		x,
		y,
		xrel,
		yrel
	):
		"""
			Right now this is taken straight out of SDL: https://wiki.libsdl.org/SDL_MouseMotionEvent

			Additional arguments to parent[s]:
				xrel:		relative motion x
				yrel:		relative motion y
		"""
		super(MouseMotionEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp,
			window_id = window_id,
			mouse_id = mouse_id,
			buttons_mask = buttons_mask,
			x = x,
			y = y
		)
		
		(self.x_rel, self.y_rel) = (xrel, yrel)


class MouseButtonEvent(MouseInputEvent):
	def __init__(self,
		event_type,
		timestamp,
		window_id,
		mouse_id,
		buttons_mask,
		x,
		y,
		clicks
	):
		"""
			Right now this is taken straight out of SDL: https://wiki.libsdl.org/SDL_MouseButtonEvent

			Additional arguments to parent[s]:
				clicks:		number of consecutive clicks
		"""

		super(MouseMotionEvent, self).__init__(
			event_type = event_type,
			timestamp = timestamp,
			window_id = window_id,
			mouse_id = mouse_id,
			buttons_mask = buttons_mask,
			x = x,
			y = y
		)
		self.click_count = clicks;

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
		self.sdl_winid = None
		self.gl_context = None;

		global window_count
		
		if (window_count == 0):
			logger.debug("This is the first window. Initializing SDL")
			if (SDL_Init(SDL_INIT_VIDEO) != 0):
				raise SDLException("SDL Initialization failed: `%s`" % (SDL_GetError()))

			for (att_name, att_value) in UIO_SDL_SETTINGS.items():
				if (SDL_GL_SetAttribute(sdl2.__dict__[att_name], att_value) != 0):
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
			self.sdl_winid = SDL_GetWindowID(self.sdl_window)
			logger.debug("Window count increased to %d", (window_count))
		else:
			raise SDLException("Unable to create SDL window with title `%s`: %s" % (title, SDL_GetError()))


		self.gl_context = SDL_GL_CreateContext(self.sdl_window)
		if (self.gl_context is None):
			SDL_DestroyWindow(self.sdl_window);
			self.sdl_winid = None
			window_count -= 1;
			raise SDLException("Unable to create an OpenGL context for window `%s`: %s" % (self.sdl_window, SDL_GetError()));
	
			
		if (SDL_GL_MakeCurrent(self.sdl_window, self.gl_context) != 0):
			SDL_GL_DeleteContext(self.gl_context)
			SDL_DestroyWindow(self.sdl_window);
			self.sdl_winid = None
			window_count -= 1;
			raise SDLException("Unable to set OpenGL context #%d as the current one for window `%s`: %s" % (self.gl_context, self.sdl_window, SDL_GetError()));


		if (SDL_GL_SetSwapInterval(1)):
			SDL_GL_DeleteContext(self.gl_context)
			SDL_DestroyWindow(self.sdl_window);
			self.sdl_winid = None
			raise SDLException("Unable to set GL swap interval: %s" % (SDL_GetError()))


	def __del__(self):
		"""
			Some cleanup whenever possible
		"""
		global window_count
		global windows_events;

		try:
			del(windows_events[self.sdl_winid])
		except:
			pass
		SDL_GL_DeleteContext(self.gl_context)
		SDL_DestroyWindow(self.sdl_window)
		window_count -= 1

		logger.debug("Window count decreased to %d", (window_count))


	def pop_events(self, limit = 0, retain = False):
		"""
			Returns up to `limit` events from the object internal queue.
			Deletes the retrieved objects unless `retain` evaluates to True
		"""
		# we need to scroll to get events selectively
		global polled_sdl_events;
		global event_counter;
		global windows_events;

		poll_events()

		pop_out = [];
		# there MUST be a more efficient and idiomatic way to do this,
		# but I'd rather not return a generator
		if self.sdl_winid in windows_events:
			for eid in list(windows_events[self.sdl_winid][:(limit if (limit > 0) else len(windows_events[self.sdl_winid]))]):
				pop_out.append(polled_sdl_events[eid][1])
				if (not retain):
					windows_events[self.sdl_winid].remove(eid)
					del(polled_sdl_events[eid])
		
		return pop_out

	@property
	def polled_events(self):
		"""
			Simply show the whole event list as a property.
			Sidesteps the popping mechanism and is therefore much faster
		"""
		try:
			return [polled_sdl_events[eid][1] for eid in windows_events[self.sdl_winid]]
		except KeyError:
			return [];
			

	def get_queued_events(limit = None, pop = True):
		"""
			Retrieves the queue of events from the windowing system.
			Arguments:
				limit:		maximum number of events to retrieve
				pop:		whether or not the retrieved events should be removed from the queue
			
			Return:
				a mixed list of event objects in queue order
		"""

		event = SDL_Event()
		# output buffers
		SDL_GetWindowSize(main_window.sdl_window, w_x, w_y); # move this to "on resize" events and the like
		rel_x = 0.0; rel_y = 0.0


		# we now scroll the queue in an oderly fashion and cherry pick the events for this window


		# now we start scrolling the queue

		# we peek ahead not to collect events belonging to other windows. Unfortunately this is inefficient
		while (SDL_PollEvent(ctypes.byref(event))):
			if (event.type == SDL_QUIT):
				out_list.append(WindowCloseEvent())
			#elif (event.type in (SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED, SDL_WINDOWEVENT_MOVED)):
				#w_x = ctypes.c_int(); w_y = ctypes.c_int()
				#print("Resized")
				#SDL_GetWindowSize(main_window.sdl_window, w_x, w_y)
			elif (event.type == SDL_MOUSEMOTION):
				m_x = ctypes.c_int(); m_y = ctypes.c_int()
				
				buttons = SDL_GetMouseState(m_x, m_y)
				rel_x = (-0.5 + (float(m_x.value) / float(w_x.value))) * 2.0
				rel_y = (-0.5 + (float(m_y.value) / float(w_y.value))) * -2.0
			elif (event.type in (SDL_KEYDOWN, SDL_KEYUP)):
				key_event = uio.KeyInputEvent(
					event_type = event.type,
					timestamp = event.key.timestamp,
					window_id = event.key.windowID,
					key_code = event.key.keysym.sym,
					unicode_cp = event.key.keysym.unicode,
					scan_code = event.key.keysym.scancode,
					modifiers = event.key.keysym.mod,
					is_repeat = bool(event.key.repeat)
				)


	def frame_swap(self):
		"""
			Framebuffer swap
		"""
		SDL_GL_SwapWindow(self.sdl_window)



def poll_events():
	"""
		Pops events from the subsystem's queue and puts them into our
		internal one. Decodes them immediately
	"""
	
	global polled_sdl_events;
	global event_counter;
	global windows_events;

	# we pump events into our internal queue first
	event = SDL_Event()
	while (SDL_PollEvent(ctypes.byref(event))):
		e_obj = None
		# resolution can be flaky. So far it is assumed that all events have a vaild .winid

		if (event.type == SDL_WINDOWEVENT):
			
			# windows have event subtypes. We resolve the relevant ones
			eo_type = None
			if (event.window.event == SDL_WINDOWEVENT_CLOSE): eo_type = WindowCloseEvent
			
			if (eo_type is not None):
				e_obj = eo_type(
					event_type = event.type,
					timestamp = event.window.timestamp,
					window_id = event.window.windowID,
					window_event_type = event.window.event
				)
		#elif (event.type in (SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED, SDL_WINDOWEVENT_MOVED)):
			#w_x = ctypes.c_int(); w_y = ctypes.c_int()
			#print("Resized")
			#SDL_GetWindowSize(main_window.sdl_window, w_x, w_y)
		elif (event.type == SDL_MOUSEMOTION):
			e_obj = MouseMotionEvent(
				event_type = event.type,
				timestamp = event.motion.timestamp,
				window_id = event.motion.windowID,
				mouse_id = event.motion.which,
				buttons_mask = event.motion.state,
				x = event.motion.x,
				y = event.motion.y,
				xrel = event.motion.xrel,
				yrel = event.motion.yrel
			)
		elif (event.type in (SDL_KEYDOWN, SDL_KEYUP)):
			e_obj = KeyInputEvent(
				event_type = event.type,
				timestamp = event.key.timestamp,
				window_id = event.key.windowID,
				key_code = event.key.keysym.sym,
				unicode_cp = event.key.keysym.unicode,
				scan_code = event.key.keysym.scancode,
				modifiers = event.key.keysym.mod,
				is_repeat = bool(event.key.repeat)
			)



		if (e_obj is not None):
			polled_sdl_events[event_counter] = (event, e_obj)
			if e_obj.winid not in windows_events:
				windows_events[e_obj.winid] = [event_counter]
			else:
				windows_events[e_obj.winid].append(event_counter)
		else:
			logger.info("SDL Event of type %d:%d has no handler class" % (event.type, (event.window.event if (event.type == SDL_WINDOWEVENT) else 0)))

		event_counter += 1
