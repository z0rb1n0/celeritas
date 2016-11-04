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
#from OpenGL.AGL import *
#from OpenGL.GLE import *
#from OpenGL.GLU import *
#from OpenGL.GLUT import *
from OpenGL.arrays import GLbyteArray
import numpy

from OpenGL.GL import shaders


logger = logging.getLogger(__name__)


# this translates GL_* constant types to pyOpenGL's types
TYPES_MAPS = {
	GL_BYTE: GLbyte,
	GL_UNSIGNED_BYTE: GLubyte,
	GL_SHORT: GLshort,
	GL_UNSIGNED_SHORT: GLushort,
	GL_INT: GLint,
	GL_UNSIGNED_INT: GLushort,
	GL_FLOAT: GLfloat,
	GL_DOUBLE: GLdouble
}



# in order to quickly translate numerical uniform type
# identifiers returned by OpenGL calls into their pyOpenGL constants,
# we map them out indexing them by value.
UNIFORM_TYPE_MAPS = {ut.real: ut for ut in (
	GL_FLOAT, GL_FLOAT_VEC2, GL_FLOAT_VEC3, GL_FLOAT_VEC4,
	GL_DOUBLE, GL_DOUBLE_VEC2, GL_DOUBLE_VEC3, GL_DOUBLE_VEC4,
	GL_INT, GL_INT_VEC2, GL_INT_VEC3, GL_INT_VEC4,
	GL_UNSIGNED_INT, GL_UNSIGNED_INT_VEC2, GL_UNSIGNED_INT_VEC3, GL_UNSIGNED_INT_VEC4,
	GL_BOOL, GL_BOOL_VEC2, GL_BOOL_VEC3, GL_BOOL_VEC4,
	GL_FLOAT_MAT2, GL_FLOAT_MAT3, GL_FLOAT_MAT4, GL_FLOAT_MAT2x3, GL_FLOAT_MAT2x4,
	GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3, GL_DOUBLE_MAT2,
	GL_DOUBLE_MAT3, GL_DOUBLE_MAT4, GL_DOUBLE_MAT2x3, GL_DOUBLE_MAT2x4, GL_DOUBLE_MAT3x2,
	GL_DOUBLE_MAT3x4, GL_DOUBLE_MAT4x2, GL_DOUBLE_MAT4x3, GL_SAMPLER_1D, GL_SAMPLER_2D,
	GL_SAMPLER_3D, GL_SAMPLER_CUBE, GL_SAMPLER_1D_SHADOW, GL_SAMPLER_2D_SHADOW,
	GL_SAMPLER_1D_ARRAY, GL_SAMPLER_2D_ARRAY, GL_SAMPLER_1D_ARRAY_SHADOW,
	GL_SAMPLER_2D_ARRAY_SHADOW, GL_SAMPLER_2D_MULTISAMPLE, GL_SAMPLER_2D_MULTISAMPLE_ARRAY,
	GL_SAMPLER_CUBE_SHADOW, GL_SAMPLER_BUFFER, GL_SAMPLER_2D_RECT, GL_SAMPLER_2D_RECT_SHADOW,
	GL_INT_SAMPLER_1D, GL_INT_SAMPLER_2D, GL_INT_SAMPLER_3D, GL_INT_SAMPLER_CUBE,
	GL_INT_SAMPLER_1D_ARRAY, GL_INT_SAMPLER_2D_ARRAY, GL_INT_SAMPLER_2D_MULTISAMPLE,
	GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY, GL_INT_SAMPLER_BUFFER, GL_INT_SAMPLER_2D_RECT,
	GL_UNSIGNED_INT_SAMPLER_1D, GL_UNSIGNED_INT_SAMPLER_2D, GL_UNSIGNED_INT_SAMPLER_3D,
	GL_UNSIGNED_INT_SAMPLER_CUBE, GL_UNSIGNED_INT_SAMPLER_1D_ARRAY,
	GL_UNSIGNED_INT_SAMPLER_2D_ARRAY, GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE,
	GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY, GL_UNSIGNED_INT_SAMPLER_BUFFER,
	GL_UNSIGNED_INT_SAMPLER_2D_RECT, GL_IMAGE_1D, GL_IMAGE_2D, GL_IMAGE_3D, GL_IMAGE_2D_RECT,
	GL_IMAGE_CUBE, GL_IMAGE_BUFFER, GL_IMAGE_1D_ARRAY, GL_IMAGE_2D_ARRAY, GL_IMAGE_2D_MULTISAMPLE,
	GL_IMAGE_2D_MULTISAMPLE_ARRAY, GL_INT_IMAGE_1D, GL_INT_IMAGE_2D, GL_INT_IMAGE_3D,
	GL_INT_IMAGE_2D_RECT, GL_INT_IMAGE_CUBE, GL_INT_IMAGE_BUFFER, GL_INT_IMAGE_1D_ARRAY,
	GL_INT_IMAGE_2D_ARRAY, GL_INT_IMAGE_2D_MULTISAMPLE, GL_INT_IMAGE_2D_MULTISAMPLE_ARRAY,
	GL_UNSIGNED_INT_IMAGE_1D, GL_UNSIGNED_INT_IMAGE_2D, GL_UNSIGNED_INT_IMAGE_3D,
	GL_UNSIGNED_INT_IMAGE_2D_RECT, GL_UNSIGNED_INT_IMAGE_CUBE, GL_UNSIGNED_INT_IMAGE_BUFFER,
	GL_UNSIGNED_INT_IMAGE_1D_ARRAY, GL_UNSIGNED_INT_IMAGE_2D_ARRAY,
	GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE, GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE_ARRAY,
	GL_UNSIGNED_INT_ATOMIC_COUNTER
)}



# possible usage patterns for buffers
BUFFER_USAGE_PATTERNS = (
	GL_STREAM_DRAW,
	GL_STREAM_READ,
	GL_STREAM_COPY,
	GL_STATIC_DRAW,
	GL_STATIC_READ,
	GL_STATIC_COPY,
	GL_DYNAMIC_DRAW,
	GL_DYNAMIC_READ,
	GL_DYNAMIC_COPY
)

# possible targets for buffers
BUFFER_BIND_TARGETS = (
	GL_ARRAY_BUFFER,
	GL_ATOMIC_COUNTER_BUFFER,
	GL_COPY_READ_BUFFER,
	GL_COPY_WRITE_BUFFER,
	GL_DISPATCH_INDIRECT_BUFFER,
	GL_DRAW_INDIRECT_BUFFER,
	GL_ELEMENT_ARRAY_BUFFER,
	GL_PIXEL_PACK_BUFFER,
	GL_PIXEL_UNPACK_BUFFER,
	GL_QUERY_BUFFER,
	GL_SHADER_STORAGE_BUFFER,
	GL_TEXTURE_BUFFER,
	GL_TRANSFORM_FEEDBACK_BUFFER,
	GL_UNIFORM_BUFFER
)



# UNIFORM_FUNCTION_MAPS for each uniform type, determines what function is called.
# Parameters are passed as-is and not validated
UNIFORM_FUNCTION_MAPS = {
	GL_INT:                                           glProgramUniform1i,
	GL_UNSIGNED_INT:                                  glProgramUniform1ui,
	GL_FLOAT:                                         glProgramUniform1f,
	GL_DOUBLE:                                        glProgramUniform1f,
	GL_IMAGE_1D:                                      glProgramUniform1i,
	GL_IMAGE_2D:                                      glProgramUniform1i,
	GL_IMAGE_3D:                                      glProgramUniform1i,
	GL_IMAGE_2D_RECT:                                 glProgramUniform1i,
	GL_IMAGE_CUBE:                                    glProgramUniform1i,
	GL_IMAGE_BUFFER:                                  glProgramUniform1i,
	GL_IMAGE_1D_ARRAY:                                glProgramUniform1i,
	GL_IMAGE_2D_ARRAY:                                glProgramUniform1i,
	GL_IMAGE_2D_MULTISAMPLE:                          glProgramUniform1i,
	GL_IMAGE_2D_MULTISAMPLE_ARRAY:                    glProgramUniform1i,
	GL_INT_IMAGE_1D:                                  glProgramUniform1i,
	GL_INT_IMAGE_2D:                                  glProgramUniform1i,
	GL_INT_IMAGE_3D:                                  glProgramUniform1i,
	GL_INT_IMAGE_2D_RECT:                             glProgramUniform1i,
	GL_INT_IMAGE_CUBE:                                glProgramUniform1i,
	GL_INT_IMAGE_BUFFER:                              glProgramUniform1i,
	GL_INT_IMAGE_1D_ARRAY:                            glProgramUniform1i,
	GL_INT_IMAGE_2D_ARRAY:                            glProgramUniform1i,
	GL_INT_IMAGE_2D_MULTISAMPLE:                      glProgramUniform1i,
	GL_INT_IMAGE_2D_MULTISAMPLE_ARRAY:                glProgramUniform1i,
	GL_UNSIGNED_INT_IMAGE_1D:                         glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_2D:                         glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_3D:                         glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_2D_RECT:                    glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_CUBE:                       glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_BUFFER:                     glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_1D_ARRAY:                   glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_2D_ARRAY:                   glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE:             glProgramUniform1ui,
	GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE_ARRAY:       glProgramUniform1ui,
	GL_UNSIGNED_INT_ATOMIC_COUNTER:                   glProgramUniform1ui,
	GL_SAMPLER_2D_MULTISAMPLE:                        glProgramUniform2i,
	GL_INT_SAMPLER_2D_MULTISAMPLE:                    glProgramUniform1i,
	GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE:           glProgramUniform1ui,
	GL_SAMPLER_2D_MULTISAMPLE_ARRAY:                  glProgramUniform2i,
	GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY:              glProgramUniform1i,
	GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY:     glProgramUniform1ui,
	GL_DOUBLE_MAT2:                                   glProgramUniformMatrix2fv,
	GL_DOUBLE_MAT3:                                   glProgramUniformMatrix3fv,
	GL_DOUBLE_MAT4:                                   glProgramUniformMatrix4fv,
	GL_DOUBLE_MAT2x3:                                 glProgramUniformMatrix2x3fv,
	GL_DOUBLE_MAT2x4:                                 glProgramUniformMatrix2x4fv,
	GL_DOUBLE_MAT3x2:                                 glProgramUniformMatrix3x2fv,
	GL_DOUBLE_MAT3x4:                                 glProgramUniformMatrix3x4fv,
	GL_DOUBLE_MAT4x2:                                 glProgramUniformMatrix4x2fv,
	GL_DOUBLE_MAT4x3:                                 glProgramUniformMatrix4x3fv,
	GL_FLOAT_VEC2:                                    glProgramUniform2f,
	GL_FLOAT_VEC3:                                    glProgramUniform3f,
	GL_FLOAT_VEC4:                                    glProgramUniform4f,
	GL_INT_VEC2:                                      glProgramUniform2i,
	GL_INT_VEC3:                                      glProgramUniform3i,
	GL_INT_VEC4:                                      glProgramUniform4i,
	GL_BOOL:                                          glProgramUniform1ui,
	GL_BOOL_VEC2:                                     glProgramUniform2ui,
	GL_BOOL_VEC3:                                     glProgramUniform3ui,
	GL_BOOL_VEC4:                                     glProgramUniform4ui,
	GL_FLOAT_MAT2:                                    glProgramUniformMatrix2fv,
	GL_FLOAT_MAT3:                                    glProgramUniformMatrix3fv,
	GL_FLOAT_MAT4:                                    glProgramUniformMatrix4fv,
	GL_SAMPLER_1D:                                    glProgramUniform1i,
	GL_SAMPLER_2D:                                    glProgramUniform2i,
	GL_SAMPLER_3D:                                    glProgramUniform3i,
	GL_SAMPLER_CUBE:                                  glProgramUniform1i,
	GL_SAMPLER_1D_SHADOW:                             glProgramUniform1i,
	GL_SAMPLER_2D_SHADOW:                             glProgramUniform2i,
	GL_SAMPLER_2D_RECT:                               glProgramUniform2i,
	GL_SAMPLER_2D_RECT_SHADOW:                        glProgramUniform2i,
	GL_FLOAT_MAT2x3:                                  glProgramUniformMatrix2x3fv,
	GL_FLOAT_MAT2x4:                                  glProgramUniformMatrix2x4fv,
	GL_FLOAT_MAT3x2:                                  glProgramUniformMatrix3x2fv,
	GL_FLOAT_MAT3x4:                                  glProgramUniformMatrix3x4fv,
	GL_FLOAT_MAT4x2:                                  glProgramUniformMatrix4x2fv,
	GL_FLOAT_MAT4x3:                                  glProgramUniformMatrix4x3fv,
	GL_SAMPLER_1D_ARRAY:                              glProgramUniform1i,
	GL_SAMPLER_2D_ARRAY:                              glProgramUniform2i,
	GL_SAMPLER_BUFFER:                                glProgramUniform1i,
	GL_SAMPLER_1D_ARRAY_SHADOW:                       glProgramUniform1i,
	GL_SAMPLER_2D_ARRAY_SHADOW:                       glProgramUniform2i,
	GL_SAMPLER_CUBE_SHADOW:                           glProgramUniform1i,
	GL_UNSIGNED_INT_VEC2:                             glProgramUniform2ui,
	GL_UNSIGNED_INT_VEC3:                             glProgramUniform3ui,
	GL_UNSIGNED_INT_VEC4:                             glProgramUniform4ui,
	GL_INT_SAMPLER_1D:                                glProgramUniform1i,
	GL_INT_SAMPLER_2D:                                glProgramUniform1i,
	GL_INT_SAMPLER_3D:                                glProgramUniform1i,
	GL_INT_SAMPLER_CUBE:                              glProgramUniform1i,
	GL_INT_SAMPLER_2D_RECT:                           glProgramUniform1i,
	GL_INT_SAMPLER_1D_ARRAY:                          glProgramUniform1i,
	GL_INT_SAMPLER_2D_ARRAY:                          glProgramUniform1i,
	GL_INT_SAMPLER_BUFFER:                            glProgramUniform1i,
	GL_UNSIGNED_INT_SAMPLER_1D:                       glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_2D:                       glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_3D:                       glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_CUBE:                     glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_2D_RECT:                  glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_1D_ARRAY:                 glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_2D_ARRAY:                 glProgramUniform1ui,
	GL_UNSIGNED_INT_SAMPLER_BUFFER:                   glProgramUniform1ui,
	GL_DOUBLE_VEC2:                                   glProgramUniform2f,
	GL_DOUBLE_VEC3:                                   glProgramUniform3f,
	GL_DOUBLE_VEC4:                                   glProgramUniform4f
}




# Uniforms we care about. They're directly mapped as properties in  the uniform objects
UNIFORM_PROPS = (
	GL_NAME_LENGTH, GL_TYPE, GL_ARRAY_SIZE, GL_OFFSET, GL_BLOCK_INDEX, GL_ARRAY_STRIDE,
	GL_MATRIX_STRIDE, GL_IS_ROW_MAJOR, GL_ATOMIC_COUNTER_BUFFER_INDEX, GL_REFERENCED_BY_VERTEX_SHADER,
	GL_REFERENCED_BY_TESS_CONTROL_SHADER, GL_REFERENCED_BY_TESS_EVALUATION_SHADER,
	GL_REFERENCED_BY_GEOMETRY_SHADER, GL_REFERENCED_BY_FRAGMENT_SHADER,
	GL_REFERENCED_BY_COMPUTE_SHADER, GL_LOCATION
)



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
class OpenGLOperationException(OpenGLException):
	""" Some generic operation went toes up """
	pass



class IndexableObject(object):
	"""
		All objects you can define in opengl that have an identifier (shaders, buffers and so on)
		are subclasses of this one.
	"""
	def __init__(self):
		self.id = None

	def __long__(self):
		return self.id

	def __str__(self):
		return str(type(self))

	def __repr__(self):
		"""
			The representation of indexable objects is always the text wrapped
			into lt/gt symbols
		"""
		return "<" + self.__str__() + ">"


class ObjectCatalog(dict):
	"""
		Base type for all OpenGL catalogs that is useful to index by object ID
		(shaders, buffers, programs...)
		Although it is a sublclassed dictionary, the keys are always
		set to those of the passed object IDs (EG: supplied keys are ignored for updates).
		In fact, the constructor/adder only accepts scalars, lists and dictionaries.
		
		A validation mechanism allows to restrict subclasses to a specific
		set of objects: if self.item_class is not None, only
		instances of that class are accepted. Moreover, when item_class is set,
		the constructor of that class is used to initialize the objects for easy
		mass-instantiation via
		
		my_catalog = WhateverSubclassOfObjectCatalog([
			[constructor_arg_1, constructor_arg-2],
			[constructor_arg_1, constructor_arg-2],
			...
		])
		
		
		This technique is overridden by some exceptional subclasses such as shaders,
		as there are many subtypes with common behavior that can live in the same
		list
		
	"""
	item_class = None

	def __init__(self, objects = None):
		"""
			Initializes the catalog with the supplied shaders.
			Does it inefficiently but we don't expect frequent calls.
			
		"""		
		# We're not defaulting to an empty list in "objects" as that makes it
		# confusing at run-time, but then we've got to test for this
		if (not (objects is None)):
			self.add(objects)

	def __setitem__(self, key, settee):
		""" Some validation """

		# we do validate only against either test
		if (self.item_class is not None):

			# we can accept 3 possible type of values: Objects, and all kinds of
			# iterable/dictionaries for the constructor
			
			# here we are rewriting arguments again...
			if (settee is None):
				# special case for dumb constructors
				settee = self.item_class()
			if (isinstance(settee, (tuple, list))):
				# positional-based constructor
				settee = self.item_class(*settee)
			elif (isinstance(settee, (dict))):
				# keyword-based constructor
				settee = self.item_class(**settee)
			else:
				# any scalar is treated as an object. Nothing happens apart
				# from some basic validation
				if (not isinstance(settee, self.item_class)):
					raise TypeError("%s only accepts %s-type items. An object of type %s was passed instead" %
						(self.__class__.__name__, self.item_class.__name__, settee.__class__.__name__)
					)
					return None
		else:
			# unfiltered case
			if (not isinstance(settee, IndexableObject)):
				raise TypeError("Not an OpenGL indexable object : %s" % settee)
			
		super(ObjectCatalog, self).__setitem__(settee.id, settee)
		return settee

	def add(self, addees = None):
		"""
			Adds one or multiple indexable objects to this catalog.
			Note that if multiple objects in the list have the same ID,
			the last one is taken. This is in fact an update

			Returns the list of of added objects
			

			Can be called without parameters to add a "vanilla"
			instance of whatever subclass

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
			shader_type = GL_VERTEX_SHADER
		elif (isinstance(self, FragmentShader)):
			shader_type = GL_FRAGMENT_SHADER
		else:
			raise TypeError("Unsupported shader subclass: %s" % (self.__class__.__name__))

		super(Shader, self).__init__()


		self.id = glCreateShader(shader_type)
		if (not isinstance(self.id, long)):
			raise OpenGLCreationException("Shader creation failed for %s" % self.__class__.__name__)


		# we now simply set our own attribute to trigger compilation
		self.source = shader_source
		

	@property
	def info_log(self):
		""" Program's info log """
		l_length = GLint()
		glGetShaderiv(self.id, GL_INFO_LOG_LENGTH, l_length)

		r_length = GLsizei()
		r_buf = (GLchar * l_length.value)()
		
		# unfortunately the pyOpenGL wrapper is not implemented like for like to the API here
		#glGetProgramInfoLog(self.id, l_length.value, r_length, r_buf)
		r_buf.value = glGetShaderInfoLog(self.id)
		return r_buf.value

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
			raise OpenGLBuildException("Shader compilation failed. Error: `%s`" % self.info_log)


	def __del__(self):
		""" We just try to get rid of it """
		glDeleteShader(self.id)

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



class VertexShader(Shader):
	"""Just a shorthand wrapper around Shader to avoid specifying more args"""
	pass

class FragmentShader(Shader):
	"""Just a shorthand wrapper around Shader to avoid specifying more args"""
	pass


class ShaderCatalog(ObjectCatalog):
	"""
		This subclass prevents non-shaders from entering the catalog.
		The tuple format is (shader_class, source), which is an exception
		for object catalogs
	"""
	item_class = Shader

	def __setitem__(self, key, settee):
		"""
			Shaders handle "constructors argument lists" specially as
			one of the arguments, the shader class, must be specified
			in the list. We just call the constructor here
		"""
		if (isinstance(settee, (tuple, list))):
			if (len(settee) < 2):
				raise TypeError("Insufficient number of members. Must supply shader class and constructor arguments")
			if ((settee[0] is not VertexShader) and (settee[0] is not FragmentShader)):
				raise TypeError("Invalid shader type: %d" % (settee[0]))

			# I hate rewriting arguments, and yet here I am rewriting an array into an object
			settee = settee[0](settee[1])

		if (not isinstance(settee, Shader)):
			raise TypeError("Not an OpenGL shader or shader definition: %s" % settee)
		return super(ShaderCatalog, self).__setitem__(key, settee)


class Uniform(IndexableObject):
	"""
		As the name implies, this is an OpenGL uniform class to
		automate retrieval/validation+injection of uniform data.
		Its main purpose is to hold addressing/type information about
		discovered uniforms.

		In order to maintain a consistent behavior with the other classes,
		no discovery is done from within the initialization itself.
		
		Resource-type properties are stored in the gl_properties member

		"uniform_name" is a string cannot be reported as a numeric property.
		It is therefore passed

		Given how often uniforms are accessed and how expensive,
		it is to infer uniform information from OpenGL, it is highly
		advisable to cache uniforms as long as their scope is valid
		(Much like the Program class does)
	

		A caller has no reason to instantiate uniforms: the main consumer of this
		constructor is the "Program" class
	"""
	def __init__(self,
		uniform_name,
		uniform_properties
	):
		"""
			Arguments:
			name: 					uniform name, should be unique per program
			uniform_properties:		is a dictionary indexed by the GLenums that
									glGetProgramResourceiv accepts as property identifiers
		"""
		super(Uniform, self).__init__()
		self.id = uniform_name

		self.gl_properties = uniform_properties
		
		# some members are assumed to be there as the uniform cannot exist without them
		self.location = uniform_properties[GL_LOCATION]
		self.type = UNIFORM_TYPE_MAPS[uniform_properties[GL_TYPE]]


	def __str__(self):
		return ("OpenGL program uniform `%s(%s)` at location #%d" % (
			self.id,
			self.type,
			self.location
		))

			

class UniformCatalog(ObjectCatalog):
	"""
		This subclass prevents non-uniforms from entering the catalog.

		See the parent class for usage

		A uniform object does not know what program it belongs to:
		do not mix uniforms from different programs in the same catalog or there
		will be collisions

	"""
	item_class = Uniform


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
	def __init__(self, shaders = None, build = False, activate = False):
		"""
			Just a collection of shaders.
			"build" indicates whether or not the build() method should be called at init.
			Note that if "build" is passed without a valid shader list an exception will be thrown
		"""
		self.id = glCreateProgram()
		if (not isinstance(self.id, long)):
			raise OpenGLCreationException("Unable to create Program")

		self.shaders = ShaderCatalog(shaders)
		
		# uniform cache to quickly resolve them.
		# gets reset at every build/binary upload
		self._uniforms = UniformCatalog()


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
		


	@property
	def linked(self):
		""" Linked status of the program """
		status = GLint()
		glGetProgramiv(self.id, GL_LINK_STATUS, status)
		return bool(status.value)
		
	@property
	def uniforms(self):
		""" Shows the "uniform cache" as a read-only property"""
		return self._uniforms

	@property
	def info_log(self):
		""" Program's info log """
		l_length = GLint()
		glGetProgramiv(self.id, GL_INFO_LOG_LENGTH, l_length)

		r_length = GLsizei()
		r_buf = (GLchar * l_length.value)()
		
		# unfortunately the pyOpenGL wrapper is not implemented like for like to the API here
		#glGetProgramInfoLog(self.id, l_length.value, r_length, r_buf)
		r_buf.value = glGetProgramInfoLog(self.id)

		return r_buf.value


	@property
	def binary(self):
		"""
			This property represents the program's binary, as a tuple.
			First member is the binary format, the second the program image.
		"""
		if (not self.linked):
			raise OpenGLStateException("Program is not linked")
			return None

		p_size = GLint()
		glGetProgramiv(self.id, GL_PROGRAM_BINARY_LENGTH, p_size)
		r_size = GLsizei()
		r_format = GLenum()
		r_buf = (GLchar * p_size.value)()

		glGetProgramBinary(self.id, p_size.value, r_size, r_format, r_buf)
		return (r_format.value, r_buf.raw)


	@binary.setter
	def binary(self, b_prog):
		"""
			Please note that replacing the binary has no bearing on the object's own
			representation.
		"""
		if ((not isinstance(b_prog, (list, tuple))) or (len(b_prog) != 2)):
			raise TypeError("Binaries must be supplied as lists/tuples such as (bin_fmt, image)")

		bbuf = (GLchar * len(b_prog[1]))()
		bbuf.raw = b_prog[1]

		glProgramBinary(self.id, GLenum(b_prog[0]), bbuf, len(b_prog[1]))

		# it is important that this happens before any exception is raised
		self.reload_uniforms()

		if (self.linked):
			return True
		else:
			raise OpenGLBuildException("Uploading of program failed: %s", self.info_log)


			

	def build(self, activate = False):
		"""
			Attaches all the shaders to the program, links the program and detaches the shaders
			Can't find proper error checking for pyOpenGL
		"""
		if (not len(self.shaders)):
			raise OpenGLStateException("No shaders to link")
			return None
		for shader_id in self.shaders:
			# we really hope this does not fail silently fail
			glAttachShader(self.id, shader_id)

		glLinkProgram(self.id)
		# we raise the exception after detaching the shaders,
		# however we collect the state now
		build_ok = bool(glGetProgramiv(self.id, GL_LINK_STATUS))

		for shader_id in self.shaders:
			glDetachShader(self.id, shader_id)

		if (not build_ok):
			raise OpenGLBuildException("Program linking failed. Error: `%s`" % self.info_log)
			return None

		self.reload_uniforms()

		if (activate):
			self.activate()


	def reload_uniforms(self):
		"""
			Finds uniforms in the built program and	loads our uniform "cache".
			It is important that this method is called every time
			linking/reloading happens/fails

			If the program is not linked the uniforms are simply wiped
			
			Returns the number of uniforms that were loaded
		"""

		# we always start by blasting what we knew
		self._uniforms = UniformCatalog()

		if (not self.linked):
			# no linked program. boo boo
			logger.debug("Program is not linked, uniform list emptied")
			return 0

		# how many uniforms?
		u_count = GLint()
		glGetProgramInterfaceiv(self.id, GL_UNIFORM, GL_ACTIVE_RESOURCES, u_count);


		# some buffers
		r_size = GLsizei()
		p_buf = (GLint * len(UNIFORM_PROPS))()
		r_name_buf = (GLchar * 256)()

		uni_list = []

		for uniform_id in range(0, u_count.value):
			glGetProgramResourceiv(
				self.id,
				GL_UNIFORM,
				uniform_id,
				len(UNIFORM_PROPS),
				UNIFORM_PROPS,
				ctypes.sizeof(p_buf),
				r_size,
				p_buf
			)
			
			# r_size is discarded as we know exactly how many we're retrieving

			# we now explode that buffer into an array.
			# If it turns out this loop is a performance bottleneck it can be made into a more static assignment
			uniform_properties = {UNIFORM_PROPS[prop_n]: p_buf[prop_n] for prop_n in range(0, len(UNIFORM_PROPS))}
			
			# name is needed for the Uniform constructor
			# a loop could be used to get uniform names longer than 256, but screw them
			# this time we DO use r_size
			glGetProgramResourceName(self.id, GL_UNIFORM, uniform_id, ctypes.sizeof(r_name_buf), r_size, r_name_buf)


			# we got everything. Build the constructors list
			uni_list.append((r_name_buf.value, uniform_properties))


		self._uniforms.add(uni_list)
		
		
		return len(self._uniforms)


	def uniform_set(self, uniform, *new_data):
		"""
			Simply attempts to change the value of a uniform to w/e is passed.
			Expected to croak if a value of the wrong type/dimensions is passed.

			Can accept both a uniform name or an object as the first argument.
			
			The passed parameters are passed directly to glProgramUniform(program, uniform, *your_args).
			
			No checks are performed ATM, and given how complex some of them could be that could affect performance
		"""
		if (isinstance(uniform, str)):
			# we resolve it off our uniforms "cache"
			try:
				uniform = self._uniforms[uniform]
			except:
				raise KeyError("Uniform '%s' not defined for program #d", (uniform, self.id))

		# now, what we need to do is resolve the uniform type into the correct
		# type-specific OpenGL function
		UNIFORM_FUNCTION_MAPS[uniform.type](self.id, uniform.location, *new_data)
		


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
		as no constructor arguments are needed for programs

		See the parent class for usage
	"""
	item_class = Program


class Context(object):
	"""
		An OpenGL Context. Very few applications need more than one.
		A context is generally passed from the windowing system as a number
	"""
	def __init__(self, context_id, programs = None):
		"""
			Simple initialization based on a context number
		"""

		self.vendor = glGetString(GL_VENDOR)
		self.gl_version = glGetString(GL_VERSION)
		self.glsl_version = glGetString(GL_SHADING_LANGUAGE_VERSION)
		self.renderer = glGetString(GL_RENDERER)

		self.id = context_id
		self.shaders = ShaderCatalog()
		self.programs = ProgramCatalog(programs)
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



class BufferMemberDef(IndexableObject):
	"""
		Buffers are made of records(structures), and records are made of
		members. A member identifier is its offset in the record stride,
		and the name is merely an indication.
	"""
	def __init__(self,
		mem_offset = 0,
		mem_type = GL_UNSIGNED_BYTE,
		mem_name = None
	):
		"""
			Arguments:
			mem_offset:			the offset of the member in the record stride.
								Does not make much sense outside the context of
								a record structure
			mem_type:			a GL_* type constant
			mem_name: 			just a label. Can be None and in that case it
								defaults to a string representation of the ID
		"""
		super(BufferMemberDef, self).__init__()
		self.id = mem_offset
		self.type = mem_type
		try:
			self.c_type = TYPES_MAPS[mem_type]
		except KeyError:
			raise TypeError("Unsupported buffer attribute type: `%s`" % (str(mem_type)[0:64]))
		self.size = ctypes.sizeof(self.c_type)
		self.name = (str(mem_name) if (mem_name is not None) else str(mem_offset))


	def __str__(self):
		return ("OpenGL %s at offset %d, name: `%s` type: %s(%s, length: %d)" % (
			self.__class__.__name__,
			self.id,
			self.name,
			self.type.name,
			self.c_type.__name__,
			self.size
		))


class BufferRecordDef(ObjectCatalog):
	"""

		A collection of BufferMemberDefs in a specific order.
		(What a C programmer would call a struct definition)


		As it is usual for this kind of catalog objects,
		a buffer attribute object does not know what buffer it belongs to:
		do not mix attributes from different buffers in the same catalog as
		they'd have overlapping offset ranges.

		The IDs of the passed BufferMemberDefs (or their constructors)
		are ignored: the offset within the record decides what ID they get
	
		Offers a pack() method to efficiently build binary records

	"""
	item_class = BufferMemberDef

	def __init__(self, *args, **kwargs):
		""" We need to keep track of the stride so that we can maintain proper offsets """
		self.stride = 0
		
		# we index attributes by name, also to prevent dupes
		self.indexed_members = {}
		super(BufferRecordDef, self).__init__(*args, **kwargs)

		# this is a tuple of ctypes instances referring to the relevant offsets
		# in the packed representation, which is stored in .
		# It gets destroyed every time attributes change and rebuilt on first use
		self._packer = None
		self._last_packed = None

	def __setitem__(self, key, settee):
		"""
			Unfortunately, we need to replicate some functionality from the parent class.
			The current stride is used to set the ID for the next item, but since
			we need to accept constructor arguments too if need be, and not just objects,
			the settee may not be an IndexableObject yet. This forces us to do call the
			constructor from here and pass it the current stride
		"""
		if (settee is None):
			# special case for dumb constructors
			settee = self.item_class()
		if (isinstance(settee, (tuple, list))):
			# positional-based constructor. We replace the first argument
			# (the id/offset) with the current stride
			settee = self.item_class(*([self.stride] + list(settee[1:])))
		elif (isinstance(settee, (dict))):
			# keyword-based constructor. We replace that keyword
			settee.update({"mem_offset": self.stride})
			settee = self.item_class(**settee)
		elif (isinstance(settee, (OpenGL.constant.IntConstant))):
			# they passed the IntConstant
			settee = self.item_class(mem_offset = self.stride, mem_type = settee)
		elif (isinstance(settee, (self.item_class))):
			# they passed the object itself. We force the internal ID
			settee.id = self.stride
		else:
			raise TypeError("Invalid object type: `%s`. Must be `%s`" %
				(settee.__class__.__name__, self.item_class.__name__)
			)
			return None

		if (settee.name in self.indexed_members):
			raise ValueError("Duplicate name for %s: %s" % (
				settee.__class__.__name,
				settee.name
			))
			return None

		self.indexed_members[settee.name] = settee
		super(BufferRecordDef, self).__setitem__(settee.id, settee)
		self.stride += settee.size
		# we reset the packer class to force pack() into rebuilding it
		self._packer = None
		self._last_packed = None

		return settee

	def pack(self, member_data):
		"""
			Can be used to efficiently encode a sequence of numbericals of the
			into the internal record binary format.
			All it expects is a tuple of numerical values in the same amount
			as the attributes

			Returns a GLchar[] that can be directly used as a buffer
			
			TODO: 	Consider implementing support for packing multple records
					to improve performance
		"""
		
		if (not self.stride):
			raise OpenGLStateException("No record structure is defined")

		if (len(member_data) != len(self)):
			raise OpenGLStateException("Wrong number of members. Must match number of attributes (%d)" % (len(self), ))

		if (self._packer is None):
			# we rebuild the packer if need be
			self._last_packed = (GLchar * self.stride)()
			self._packer = tuple(att.c_type.from_buffer(self._last_packed, att_off) for att_off, att in sorted(self.items()))

		# unfortunately I could not find a way to to this without a loop at all
		# indirect attribute addressing methods (eg: setattr) fail with ctypes
		# TODO: for a real performance boost, either use itertools or try with ctypes.pointers
		for aid in range(len(self._packer)):
			self._packer[aid].value = member_data[aid]

		return self._last_packed;

	def __str__(self):
		return "OpenGL %s of stride %d. Members: %s" % (
			self.__class__.__name__,
			self.stride,
			super(BufferRecordDef, self).__str__()
		)

class Buffer(IndexableObject):
	"""
		A generic OpenGL buffer. Internally it is just an array of GLchar
		of a given size, but to facilitate interaction from subclasses
		(eg VertexBuffer) it can be constructed by passing a record definition,
		as an N-long sequence of GL_* types.

		The corresponding data array lenght must obviously be a multiple of
		the record members


		Has a "bind()" convenience method, however at this stage that is not
		very useful as PyOpenGL does not support glNamedBufferData(),
		therefore the buffer must be bound when it is initialized. 

		OpenGL buffers are treated as immutable at this stage,
		so this object is too

		TODO: optimize buffer creation by packing/batching
	"""
	# this chooses what class defines our record type
	_record_def_processor = BufferRecordDef
	def __init__(self,
		data_types,
		buffer_data,
		usage = GL_READ_WRITE,
		bind_target = GL_ARRAY_BUFFER,
		retain_data = False
	):
		"""
			Simply initializes the buffer and eventually binds it if required
			
			Arguments:
				data_types: 		the desired types for the record members.
									Passed as-is to BufferRecordDef()
				buffer_data:		the buffer string. Can be an sequence of
									numerical byte values (unsigned).
									Can be any ctypes-compatible array type too,
									but bear in mind that the internal representation
									is always a GLubyte[]
				usage:				the expected usage pattern for this buffer
				bind_target:		the bind target
				retain_data:		whether or not the buffer data should be
									kept around by the object after it's been
									sent to the renderer's memory. When false,
									(the default) the member is set to None
									after glBufferData() is called
		"""
		super(Buffer, self).__init__()

		self.data = None
		self.last_bound_to = None

		if ((buffer_data is None) or (len(buffer_data) == 0)):
			raise ValueError("Buffers cannot be initialized as empty")

		self.record_def = self._record_def_processor(data_types)

		# some convenience vars
		i_m = len(self.record_def.indexed_members)
		r_s = self.record_def.stride

		if (not self.record_def.stride):
			raise TypeError("Unable to define a buffer without a valid record definition")

		# unfortunately we need to use different checks for different input types (str or sequence)
		if (isinstance(buffer_data, (bytes, str)) and (len(buffer_data) % r_s)):
			raise ValueError("Buffer data size is not a multpile of record stride")

		if (isinstance(buffer_data, (tuple, list)) and (len(buffer_data) % i_m)):
			raise ValueError("Buffer array length is not a multpile of numbers of member count")



		self.total_records = len(buffer_data) / i_m

		# no matter what, we now allocate a buffer of the right lenght
		self.data = (GLchar * (r_s * self.total_records))()

		if (isinstance(buffer_data, (bytes, str))):
			# they passed a string, directly. We just check the lenght
			if isinstance(buffer_data, (str)):
				self.data.value = buffer_data
			else:
				self.data.raw = buffer_data
		elif (isinstance(buffer_data, (tuple, list))):
			# sequence of number
			member_shift = 0
			for r_off in range(0, len(self.data), r_s):
				self.data[r_off:r_off + r_s] = self.record_def.pack(buffer_data[member_shift:member_shift + i_m])
				member_shift += i_m
		else:
			# it is assumed that these are convertable to ctypes
			self.data[0:len(self.data)] = buffer_data


		self.size = ctypes.sizeof(self.data)

		bid = GLuint()
		glGenBuffers(1, bid)
		if (bid is not None):
			self.id = bid.value
		else:
			raise OpenGLCreationException("Buffer generation failed")


		# sigh
		self.bind(bind_target)
		try:
			glBufferData(
				bind_target,
				len(buffer_data),
				self.data,
				usage
			)
		except(Exception) as e:
			raise OpenGLCreationException("Unable to initialize data store for buffer #%d", (self.id,))

		if (not retain_data):
			self.data = None

	def bind(self, target = GL_ARRAY_BUFFER):
		""" Attempts to bind the specified buffer """
		try:
			glBindBuffer(target, self.id)
			self.last_bound_to = target
		except:
			raise OpenGLOperationException("Bind of buffer #%d failed", (self.id,))


	def __del__(self):
		""" Clean up """
		glDeleteBuffers(1, (self.id,))

	def __str__(self):
		bind_str = (("Last bound to %s" % self.last_bound_to.name) if (self.last_bound_to is not None) else "Never bound")
		return("OpenGL %s #%d(%d bytes). %s. Record format: %s" % (self.__class__.__name__, self.id, self.size, bind_str, self.record_def))


class VertexAttributeDef(BufferMemberDef):
	"""
		A vertex attribute definition is just a member in a buffer record.
	"""
	pass



class VertexRecordDef(BufferRecordDef):
	"""
		An in-memory vertex definition is basically a glorified buffer record.
		Just it accepts only VertexAttributeDef as members

	"""
	item_class = VertexAttributeDef


class VertexBuffer(Buffer):
	"""
		Vertex buffer abstraction. It's just a buffer that uses its own
		record definition processor
	"""
	_record_def_processor = VertexRecordDef

