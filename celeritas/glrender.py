#!/usr/bin/python -uB

"""
	Window manager for Celeritas. Initializes an OpenGL-capable window,
	without exposing the underlying API.
	The most important thing we need the window to expose is the OpenGL context
"""
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


logger = logging.getLogger(__name__)


# blatantly aliasing OpenGL's own qualifiers not to clash
# with other instances
ST_VERTEX = GL_VERTEX_SHADER
ST_FRAGMENT = GL_FRAGMENT_SHADER


class Context(object):
	"""
		An OpenGL Context. Very few applications need more than one.
		A context is always passed from the windowing system.
	"""
	def __init__(self, context_id):
		"""
			Simple initialization based on a context number
		"""
		self.id = context_id
		self.shaders = {}
		self.programs = {}
		self.buffers = {}
		#glViewport(0, 0, guc["video"]["resolution_x"], guc["video"]["resolution_y"])

	def __int__(self):
		return int(self.id)
		
	def __str__(self):
		""" Serialized, hierarchical representation of the whole context """
		return ("OpenGL context #%d, shaders: %s, programs: %s, buffers %s" % (
			self.id,
			str(map(str, self.shaders.values())),
			str(map(str, self.programs.values())),
			str(map(str, self.buffers.values()))
		))

	def add_program(self, *args, **kwargs):
		"""
			Program factory.
			If passed a full-on program
			
			In the first case simply 
		"""
		
	def add_shader(self, shader):
		"""
			Appends a shader to the list of shaders
		"""

class Shader(object):
	"""
		A generic shader object. Compiled on initialization
	"""
	def __init__(self,
		shader_source,
		shader_type
	):
		"""
			The shader is built by __init__
		"""
		self.id = glCreateShader(shader_type)
		glShaderSource(
			shader_source,
			self.id
		)
		glCompileShader(self._id)
		if (not glGetShaderiv(self._id, GL_COMPILE_STATUS)):
			print("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(self._id))
			self.id = None

		self.type = shader_type
		self.source = shader_source


	def __str__(self):
		return ("OpenGL shader #%d, type: %d, source_length: %d", (
			self.id,
			self.shader_type,
			len(self.source)
		))

class Program(object):
	"""
		OpenGL program. Basically an array of shaders
	"""
	def __init__(self, p_shaders = []):
		"""
			Initialization is rather simple: each shaders in the argument list
			is added to the list of attached shaders (the index is extracted
		"""
		self.id = glCreateProgram()
		if (not isinstance(long, self.id)):
			raise Exception("Cannot create shader program")
			self.id = None
		self.shaders = {}
		
		self.attach_shaders(p_shaders)

	def __del__(self):
		""" Progam is unlinked and deleted"""
		glDeleteProgram(self.id)

	def __long__(self):
		return self.id

	def attach_shaders(self, shaders):
		"""
			As the name implies, the passed shader[s] is/are attached to the program.
			A basic check is performed to prevent wrong IDs from being passed
			Arguments:
				shaders:	the list of shaders to attach. Can be a tuple or a 
				
			Return value:
				a list with all the appended shader IDs
		"""
		out_list = []
		for attachee in ([shaders] if not isinstance(shaders, (tuple, list)) else shaders):
			if (not isinstance(attachee, Shader)):
				raise TypeError("Not a Shader object: %s" % (attachee))
				return None

			self.shaders[attachee.id] = attachee
			
			# need to find a way to test the success of glAttachShader()
			glAttachShader(self.id, attachee.id)

			out_list.append(attachee.id)

		return out_list

	def detach_shaders(self, shader_ids):
		"""
			When passed a list of shader IDs detaches them from the program
		"""
		for detachee_id in ([shader_ids] if not isinstance(shader_ids, (tuple, list)) else shader_ids):
			glDetachShader(self.id, detachee_id)
			try:
				del(self.shaders[detachee_id])
			except:
				raise KeyError("Shader #%d is not attached to program #%d", (detachee_id, self.id))
		return None

class Buffer(object):
	"""
		A generic OpenGL buffer. Automatically chooses the data type based on the number of
		elements
	"""
	def __init__(self,
		
	):
		pass

class VertexBuffer(object):
	"""
		Vertex Buffer Object representation
	"""
	def __init__(self
	):
		pass





