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




class OpenGLException(Exception):
	""" Base/Generic OpenenGL exception """
	pass
class OpenGLCreationException(OpenGLException):
	""" When some object creation fails """
	pass
class OpenGLBuildException(OpenGLException):
	""" When building shaders goes awry """
	pass


class OpenGLStateException(OpenGLException):
	""" When your objects are not ready to do what you want to """
	pass



class IndexableObject(object):
	"""
		All objects you can define in opengl that have a numeric ID (shaders, buffers and so on)
		are subclasses of this one.
	"""
	def __init__(self, *args, **kwargs):
		self.id = None

	def __long__(self):
		return self.id

class ObjectCatalog(dict):
	"""
		Base type for all OpenGL catalogs that is useful to index by object ID
		(shaders, buffers, programs...)
		Although it is a sublclassed dictionary, the keys are always
		set to those of the passed object IDs (EG: supplied keys are ignored for updates).
		In fact, the constructor/adder only accepts lists and dictionaries
	"""
	def __init__(self, objects = {}):
		"""
			Initializes the catalog with the supplied shaders.
			Does it inefficiently but we don't expect frequent calls
		"""
		self.add(objects)

	def __setitem__(self, key, settee):
		""" Some validation """
		if (not isinstance(settee, IndexableObject)):
			raise TypeError("Not an OpenGL indexable object : %s" % settee)
		super(ObjectCatalog, self).__setitem__(settee.id, settee)
		return settee

	def add(self, addees = None):
		"""
			Adds one or multiple indexable objects to this catalog.
			Note that if multiple objects in the list have the same ID
			the last one is taken. This is in fact an update

			Returns the list of of added objects
			
			Can be called without parameters to add an "all defaults"
			instance of whatever subclass, but this mode will fail for
			classes whose constructor has mandatory arguments
		"""
		# no matter what they give us, we need something to loop over
		ret_list = [];
		for addee in (
			addees if isinstance(addees, (tuple, list)) else (
				addees.values() if isinstance(addees, dict) else ( addees, )
			)
		):
			ret_list += [ self.__setitem__(None, addee) ]

		return ret_list
			

	def update(self, updaters):
		"""
			On update, the keys are ignored and the object IDs are used instead
		"""
		self.add(updaters.values())

	def __str__(self):
		"""
			It is always preferable to see the string representation of the internal objects if available
		"""
		return str({id: str(st) for (id, st) in self.items()})



class Shader(IndexableObject):
	"""
		A abstract base class for shaders. Compiled on initialization, or when the source is changed.
		Does not allow instantiation directly
	"""
	def __new__(cls, *args, **kwargs):
		if (cls is Shader):
			raise TypeError("Class %s cannot be instantiated directly" % (cls.__name__))
		return object.__new__(cls, *args, **kwargs)

	def __init__(self, shader_source):
		"""
			The shader is initialized and built by __init__,
		"""
		if (isinstance(self, VertexShader)):
			shader_type = ST_VERTEX
		elif (isinstance(self, FragmentShader)):
			shader_type = ST_FRAGMENT
		else:
			raise TypeError("Unsupported shader subclass: %s" % (self.__class__.__name__))

		super(Shader, self).__init__()


		self.id = glCreateShader(shader_type)
		if (not isinstance(self.id, long)):
			raise OpenGLCreationException("Shader creation failed for %s" % self.__class__.__name__)


		# we now simply set our own attribute to trigger compilation
		self.source = shader_source
		


	@property
	def source(self):
		return self._source
	
	@source.setter
	def source(self, new_source):
		""" Change the source and build it """
		self._source = new_source
		glShaderSource(
			self.id,
			self._source
		)
		glCompileShader(self.id)
		if (glGetShaderiv(self.id, GL_COMPILE_STATUS)):
			self.compiled = True
		else:
			raise OpenGLBuildException("Shader compilation failed. Error: `%s`" % glGetShaderInfoLog(self.id))


	def __int__(self):
		""" This cast is unsafe but handy """
		return self.id

	def __long__(self):
		return self.id

	def __str__(self):
		return ("OpenGL shader #%d, type: %s, source_length: %d" % (
			self.id,
			self.__class__.__name__,
			len(self.source)
		))

	def __repr__(self):
		return "<" + self.__str__() + ">"


class VertexShader(Shader):
	"""Just a shorthand wrapper around Shader to avoid specifying more args"""
	pass
#super(VertexShader, self).__init__(shader_source = shader_source, shader_type = ST_VERTEX)

class FragmentShader(Shader):
	"""Just a shorthand wrapper around Shader to avoid specifying more args"""
	pass
#super(FragmentShader, self).__init__(shader_source = shader_source, shader_type = ST_FRAGMENT)


class ShaderCatalog(ObjectCatalog):
	"""
		This subclass prevents non-shaders from entering the catalog.

		It also automagically turns 2 member tuples/lists comprised of (ST_*, source) into
		shader objects by calling the appropriate constructor
	"""
	def __setitem__(self, key, settee):
		
		if (isinstance(settee, (tuple, list))):
			if (len(settee) < 2):
				raise TypeError("Insufficient number of members in shader catalog entry")
			if (settee[0] not in (ST_VERTEX, ST_FRAGMENT)):
				raise TypeError("Invalid shader type: %d" % (settee[0]))

			# I hate rewriting arguments, and yet here I am rewriting an array into an object
			settee = (FragmentShader if (settee[0] == ST_FRAGMENT) else VertexShader)(settee[1])

		if (not isinstance(settee, Shader)):
			raise TypeError("Not an OpenGL shader or shader definition: %s" % settee)
		return super(ShaderCatalog, self).__setitem__(key, settee)
		



class Program(IndexableObject):
	"""
		OpenGL program.
		A little more than a wrapper for an catalog of shaders
		(I was really tempted to implement it by extending ShaderCatalog)
		Any change to the list of shaders or any of the shaders themselves causes
		the "current" to be unset.

		Bear in mind that shaders are not attached until the build() method is called,
		and they're immediately detached afterwards. This allows us to follow the reccomendations
		about not leaving shaders attached to the program at all times

	"""
	def __init__(self, shaders = {}, build = False, activate = False):
		"""
			Just a collection of shaders.
			"build" indicates whether or not the build() method should be called at init.
			Note that if "build" is passed without a valid shader list an exception will be thrown
		"""
		self.id = glCreateProgram()
		if (not isinstance(self.id, long)):
			raise OpenGLCreationException("Unable to create Program")

		self.linked = False

		self.shaders = ShaderCatalog(shaders)

		if (build):
			self.build()
			
		if (activate):
			self.activate()

	def __del__(self):
		""" Progam is unlinked and deleted"""
		glDeleteProgram(self.id)

	def __int__(self):
		""" This cast is unsafe but handy """
		return self.id

	def __long__(self):
		return self.id

	def __str__(self):
		return("OpenGL Program #%d, %d shaders: %s" % (self.id, len(self.shaders), self.shaders))
		
	def __repr__(self):
		return "<" + self.__str__() + ">"

	def build(self, activate = False):
		"""
			Attaches all the shaders to the program, links the program and detaches the shaders
			Can't find proper error checking for pyOpenGL
		"""
		if (not len(self.shaders)):
			raise OpenGLStateException("No shaders to link")
		for shader_id in self.shaders:
			# we really hope this does not fail silently fail
			glAttachShader(self.id, shader_id)

		self.linked = False
		glLinkProgram(self.id)
		# we raise the exception after detaching the shaders,
		# however we collect the state now
		build_ok = bool(glGetProgramiv(self.id, GL_LINK_STATUS))

		for shader_id in self.shaders:
			glDetachShader(self.id, shader_id)


		if (build_ok):
			self.linked = True
		else:
			raise OpenGLBuildException("Program linking failed. Error: `%s`" % glGetProgramInfoLog(self.id))


		
	def activate(self):
		"""
			Makes this program the active one.
			Can't find proper error checking for pyOpenGL
		"""
		# we really hope this does not fail silently fail
		if (not self.linked):
			raise OpenGLStateException("Program is not linked")
		glUseProgram(self.id)
		return 0;



		return True


class ProgramCatalog(ObjectCatalog):
	"""
		This subclass simply calls the right constructor no matter what,
		as no parameters are needed for programs
	"""
	def __setitem__(self, key, settee):
		if (not isinstance(settee, Program)):
			settee = Program()
			#raise TypeError("Not an OpenGL program: %s" % settee)

		return super(ProgramCatalog, self).__setitem__(key, settee)



class Context(object):
	"""
		An OpenGL Context. Very few applications need more than one.
		A context is generally passed from the windowing system as a number
	"""
	def __init__(self, context_id, programs = []):
		"""
			Simple initialization based on a context number
		"""
		self.id = context_id
		self.shaders = ShaderCatalog()
		self.programs = ProgramCatalog()
		self.buffers = {}
		#glViewport(0, 0, guc["video"]["resolution_x"], guc["video"]["resolution_y"])

	def __int__(self):
		return int(self.id)


	def __str__(self):
		""" Serialized, hierarchical representation of the whole context """
		return ("OpenGL context #%d, shaders: %s, programs: %s, buffers %s" % (
			self.id,
			self.shaders,
			self.programs,
			self.buffers
		))

	def __repr__(self):
		return "<" + self.__str() + ">"

class Buffer(object):
	"""
		A generic OpenGL buffer. Automatically chooses the data type based on the number of
		elements
	"""
	def __init__(self,
		
	):
		pass

class VertexBuffer(Buffer):
	"""
		Vertex Buffer Object representation
	"""
	def __init__(self
	):
		pass





