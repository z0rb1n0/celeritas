#include <config.h>
#include <stdio.h>
#include <unistd.h>
#include <iostream>
#include <SDL2/SDL.h>
#include "celeritas.h"
#include <OGRE/Ogre.h>


int app_setup() {

const char *run_dirs[] = {APP_DIR, CONFIG_DIR, LOG_DIR};
unsigned int i;
char *h;
char *next_path;

	for (i = 0; i < (sizeof(run_dirs) / sizeof(run_dirs[0])); i++) {

		h = getenv("HOME");
		next_path = ((char*) calloc(strlen(h) + strlen(run_dirs[i]) + 1, sizeof(char)));
		strcpy(next_path, h);
		strcat(next_path, "/");
		strcat(next_path, run_dirs[i]);
		
		if (mkdir(next_path, 0777)) {
			if (errno == EEXIST) {
				//fprintf(stderr, "Directory already exists: `%s`\n", next_path);
			} else {
				fprintf(stderr, "Unable to create directory: `%s`\n", next_path);
			}
		}

	}
	//free(next_path);
	return 0;

}



int main(int argc, char *argv[]) {

std::string plugin_cfg;

	app_setup();

	
	Ogre::Root *oRoot = new Ogre::Root(
		((std::string) getenv("HOME") + "/" + OGRE_PLUGINS_FILE),
		(getenv("HOME") + ((std::string) "/" + OGRE_CONFIG_FILE)),
		(getenv("HOME") + ((std::string) "/" + OGRE_LOG_FILE))
	);
	oRoot->restoreConfig();
	oRoot->showConfigDialog();
	Ogre::ResourceGroupManager::getSingleton().initialiseAllResourceGroups();

	

	
	Ogre::String windowTitle = "Celeritas Test Window";
	
	
	/* explicit window creation
	Ogre::uint resX = 800;
	Ogre::uint resY = 600;
	bool fullScreen = false;

	Ogre::NameValuePairList wOpts;
	wOpts["title"] = "Celeritas Test Window";
	wOpts["colourDepth"] = "32";
	wOpts["vsync"] = "true";

	oRoot->initialise(false);
	Ogre::RenderWindow *rwMain = oRoot->createRenderWindow(windowTitle, resX, resY, fullScreen, &wOpts);
	*/

	// automatic window initialisation
	Ogre::RenderWindow *rwMain = oRoot->initialise(true, windowTitle);
	Ogre::SceneManager *osMainScene = oRoot->createSceneManager("OctreeSceneManager", "primary");
	Ogre::Camera *camMain = osMainScene->createCamera(CELERITAS_MAIN_CAMERA);
	
	camMain->setPosition(0, 0, 0);
	camMain->lookAt(0, 0, -300);
	camMain->setNearClipDistance(5);
	
	Ogre::Viewport *vpMain = rwMain->addViewport(camMain);
	vpMain->setBackgroundColour(Ogre::ColourValue(0.5, 0.5, 0.5));



	return 0;
	//oRoot->initialise(false, "Celeritas");

	//Ogre::SceneManager *osMainScene = oRoot->createSceneManager(Ogre::ST_GENERIC, "primary");
	//osMainScene->setAmbientLight(Ogre::ColourValue(0.5, 0.5, 0.5));
	//mgr->setAmbientLight(Ogre::ColourValue(0.5, 0.5, 0.5));
	//mgr->setAmbientLight(Ogre::ColourValue(0.5, 0.5, 0.5));
	/*
	if (SDL_Init(SDL_INIT_VIDEO) != 0) {
		std::cout << "SDL_Init Error: " << SDL_GetError() << std::endl;
		return 1;
	} else {
		std::cout << "Initialization successful\n";
	}
	SDL_Window *win = SDL_CreateWindow("Hello World!", 100, 100, 640, 480, SDL_WINDOW_SHOWN);
	SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
	if (ren == 0) {
		SDL_DestroyWindow(win);
		std::cout << "SDL_CreateRenderer Error: " << SDL_GetError() << std::endl;
		SDL_Quit();
		return 1;
	}
	sleep(2);
	SDL_Quit();
	*/
	//return 0;
}
