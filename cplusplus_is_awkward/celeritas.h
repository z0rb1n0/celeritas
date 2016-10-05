
// keep these paths shorter than 128
#define APP_DIR						".celeritas"
#define CONFIG_DIR					APP_DIR "/" "config"
#define LOG_DIR						APP_DIR "/" "log"


#define OGRE_CONFIG_FILE			CONFIG_DIR "/" "ogre.cfg"
#define OGRE_PLUGINS_FILE			CONFIG_DIR "/" "ogre_plugins.cfg"
#define OGRE_LOG_FILE				LOG_DIR "/" "ogre.log"




#define CELERITAS_MAIN_CAMERA		"main_camera"


int app_setup();



int main(int argc, char *argv[]);
