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


# blatantly aliasing OpenGL's own qualifiers not to clash
# with other instances
ST_VERTEX = GL_VERTEX_SHADER
ST_FRAGMENT = GL_FRAGMENT_SHADER



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





# glUniform1f(GL_FLOAT);
# glUniform2f(GL_FLOAT_VEC2);
# glUniform3f(GL_FLOAT_VEC3);
# glUniform4f(GL_FLOAT_VEC4);
# glUniform1i(GL_INT);
# glUniform2i(GL_INT_VEC2);
# glUniform3i(GL_INT_VEC3);
# glUniform4i(GL_INT_VEC4);
# glUniform1ui(GL_UNSIGNED_INT);
# glUniform2ui(GL_UNSIGNED_INT_VEC2);
# glUniform3ui(GL_UNSIGNED_INT_VEC3);
# glUniform4ui(GL_UNSIGNED_INT_VEC4);

# glUniform1fv( GLint location, GLsizei count, const GLfloat *value);
# glUniform2fv( GLint location, GLsizei count, const GLfloat *value);
# glUniform3fv( GLint location, GLsizei count, const GLfloat *value);
# glUniform4fv( GLint location, GLsizei count, const GLfloat *value);
# glUniform1iv( GLint location, GLsizei count, const GLint *value);
# glUniform2iv( GLint location, GLsizei count, const GLint *value);
# glUniform3iv( GLint location, GLsizei count, const GLint *value);
# glUniform4iv( GLint location, GLsizei count, const GLint *value);
# glUniform1uiv( GLint location, GLsizei count, const GLuint *value);
# glUniform2uiv( GLint location, GLsizei count, const GLuint *value);
# glUniform3uiv( GLint location, GLsizei count, const GLuint *value);
# glUniform4uiv( GLint location, GLsizei count, const GLuint *value);
# glUniformMatrix2fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix3fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix4fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix2x3fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix3x2fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix2x4fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix4x2fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix3x4fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
# glUniformMatrix4x3fv( GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);


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



class IndexableObject(object):
	"""
		All objects you can define in opengl that have an identifier (shaders, buffers and so on)
		are subclasses of this one.
	"""
	def __init__(self):
		self.id = None

	def __long__(self):
		return self.id

class ObjectCatalog(dict):
	"""
		Base type for all OpenGL catalogs that is useful to index by object ID
		(shaders, buffers, programs...)
		Although it is a sublclassed dictionary, the keys are always
		set to those of the passed object IDs (EG: supplied keys are ignored for updates).
		In fact, the constructor/adder only accepts scalars, lists and dictionaries
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
				raise TypeError("Insufficient number of members to construct a shader")
			if (settee[0] not in (ST_VERTEX, ST_FRAGMENT)):
				raise TypeError("Invalid shader type: %d" % (settee[0]))

			# I hate rewriting arguments, and yet here I am rewriting an array into an object
			settee = (FragmentShader if (settee[0] == ST_FRAGMENT) else VertexShader)(settee[1])

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
		self.type = UNIFORM_TYPE_MAPS[uniform_properties[GL_TYPE]].name


	def __str__(self):
		return ("OpenGL program uniform `%s(%s)` at location #%d" % (
			self.id,
			self.type,
			self.location
		))

	def __repr__(self):
		return "<" + self.__str__() + ">"
			

class UniformCatalog(ObjectCatalog):
	"""
		This subclass prevents non-uniforms from entering the catalog.

		Similarly to ShaderCatalog, it also allows one to instantiate it by
		passing a list/tuple of arguments that can be passed to the Uniform
		constructor as-is, or a list thereof.


		A uniform object does not know what program it belongs to:
		do not mix uniforms from different programs in the same catalog or there
		will be collisions

	"""
	def __setitem__(self, key, settee):
		
		if (isinstance(settee, (tuple, list))):
			if (len(settee) < 2):
				raise TypeError("Insufficient number of members for a Uniform constructor")

			# here I am rewriting arguments again...
			settee = Uniform(*settee)

		if (not isinstance(settee, Uniform)):
			raise TypeError("Not a Uniform or constructor arguments for it: %s" % settee)
		return super(UniformCatalog, self).__setitem__(key, settee)


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
		
	def __repr__(self):
		return "<" + self.__str__() + ">"


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


	def uniform_set(self, uniform, new_value):
		"""
			Simply attempts to change the value of a uniform to w/e is passed.
			Expected to croak if a value of the wrong type/dimensions is passed.
			
			Can accept both a uniform name or an object as the first argument
		"""
		if (isinstance(uniform, str)):
			# we resolve it off our uniforms "cache"
			try:
				uniform = self._uniforms[uniform]
			except:
				raise KeyError("Uniform '%s' not defined for program #d", (uniform, self.id))

		# now, what we need to do is resolve the uniform type into the correct
		# type-specific OpenGL function
		


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





