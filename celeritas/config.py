#!/usr/bin/python -uB

"""
	Configuration manager for the "Celeritas" engine.
	It's a silly JSON
"""
import os
import json
import logging
import logging.config

import info


logger = logging.getLogger(__name__)

CONFIG_DIR_RELATIVE = "." + info.APP_NAME

# Grand Unified Configuration, Postgres style

guc = {
	"system": {
		"config_dir": None,
		"guc_file": "celeritas_guc.json",
		"application_name": info.APP_NAME,
		"version_string": ("%d.%d.%d" % (info.APP_MAJOR, info.APP_MINOR, info.APP_REVISION))
	},
	"video": {
		"full_screen": False,
		"resolution_x": 640,
		"resolution_y": 480
	}
}


def init_log():
	logging.config.dictConfig({
		"version": 1,
		"disable_existing_loggers": False,
		"formatters": {
			"standard": {
				"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
			},
		},
		"handlers": {
			"default": {
				"level": "INFO",
				"formatter": "standard",
				"class": "logging.StreamHandler",
			},
		},
		"loggers": {
			"": {
				"handlers": [ "default" ],
				"level": "INFO",
				"propagate": True
			},
		}
	})
	return True



def load():
	if (not init_log()):
		print("Failed to initialize the logger")
		exit(3)

	if ("HOME" not in os.environ):
		logger.error("There is no HOME environment variable. Cannot continue")
		exit(3)

	logger.info("Loading configuration")


	guc["system"]["config_dir"] = os.environ["HOME"] + "/" + CONFIG_DIR_RELATIVE

	if (not os.path.isdir(guc["system"]["config_dir"])):
		try:
			os.mkdir(guc["system"]["config_dir"])
		except OSError:
			logger.error("Unable to create configuration directory `%s`", (guc["system"]["config_dir"]))
			exit(3)

	config_file = guc["system"]["config_dir"] + "/" + guc["system"]["guc_file"]

	try:
		guc_fp = open(config_file, "r")
	except IOError:
		logger.info("Missing configuration file `%s`. Running off hard coded defaults", (config_file))
		return False


	file_guc = None
	try:
		file_guc = json.load(guc_fp, encoding = "UTF-8")
	except:
		logger.info("Unable to load JSON from file `%s`. Running off hard coded defaults", (config_file))


	guc_fp.close()

	if (file_guc is None):
		return False


	# we now only update the guc's already existing settings and raise warnings for the other ones
	def import_guc_settings(file_guc, process_guc, base_key_path = ""):
		for (guc_key, guc_value) in file_guc.items():
			full_key_path = base_key_path + '\t' + guc_key
			
			# some settings we don't import from the file
			if (full_key_path not in (
				"\tsystem\tapplication_name",
				"\tsystem\tversion_string"
			)):
				if (guc_key in process_guc):
					if (type(guc_value) is dict):
						import_guc_settings(guc_value, process_guc[guc_key], full_key_path)
					else:
						# we use python's reference system to replace the guc settings
						process_guc[guc_key] = guc_value
				else:
					logger.warning("Unsupported/deprecated configuration option `%s`. Will not be saved in the configuration", (full_key_path.replace("\t", "/")))

	import_guc_settings(file_guc, guc)


	return True




def save():

	logger.info("Saving configuration")
	config_file = guc["system"]["config_dir"] + "/" + guc["system"]["guc_file"]
	config_file_tmp = config_file + ".tmp"

	guc_fp = None
	try:
		guc_fp = open(config_file_tmp, "w")
	except IOError:
		logger.error("Unable to open temporary file `%s`. Configuration will not be saved", (config_file_tmp))
		return False
	
	if (guc_fp is not None):
		saved_in_full = False
		try:
			# some keys must not be saved
			# this is how we filter them :(
			s_guc = dict(guc)
			s_guc["system"] = {s_key: s_val for (s_key, s_val) in guc["system"].items() if (s_key not in ("config_dir", "guc_file"))}
			json.dump(s_guc, guc_fp, encoding = "UTF-8", indent = 4, separators = None)
			saved_in_full = True
		except IOError:
			logger.error("Cannot write to temporary file `%s`. Configuration will not be saved", (config_file_tmp))

		guc_fp.close()


	if ((guc_fp is not None) and saved_in_full):
		# this guarantees atomic operations
		try:
			os.rename(config_file_tmp, config_file)
			return True
		except:
			logger.error("Cannot rename temporary file `%s` into `%s`. Configuration will not be saved", (config_file_tmp, config_file))
			return False

			
	
