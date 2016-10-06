import sys;
import ctypes;
import time;
from sdl2 import *;
#import sdl2.ext;
from OpenGL import GL;



def main():

	SDL_Init(SDL_INIT_VIDEO);

	main_window = SDL_CreateWindow(
		b"Celeritas 0.0.0",
		SDL_WINDOWPOS_CENTERED,
		SDL_WINDOWPOS_CENTERED,
		2560, 1440,
		SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL
	);


	if (not main_window):
		print(SDL_GetError());
		return 3;


	# This is only for non-GL content
	#main_surface = SDL_GetWindowSurface(main_window);

	main_context = SDL_GL_CreateContext(main_window);

	GL.glMatrixMode(GL.GL_PROJECTION | GL.GL_MODELVIEW);
	GL.glLoadIdentity();
	GL.glOrtho(-400, 400, 300, -300, 0, 1);


	loop_active = True;
	event = SDL_Event();
	SDL_UpdateWindowSurface(main_window);

	GL.glClearColor(0, 0, 0, 1);
	GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_ACCUM_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT);
	SDL_GL_SwapWindow(main_window);

	while loop_active:
		if (SDL_PollEvent(ctypes.byref(event)) and (event.type == SDL_QUIT)):
			loop_active = False;
			break;

		time.sleep(0.001);

	SDL_GL_DeleteContext(main_context);
	SDL_DestroyWindow(main_window);
	SDL_Quit();
	#windowsurface = sfSDL_SetVideoMode(2560, 1440, 24, SDL_OPENGL);
	print("Terminating");



	return 0;






#     GL.glMatrixMode(GL.GL_PROJECTION | GL.GL_MODELVIEW);
#     GL.glLoadIdentity();
#     GL.glOrtho(-400, 400, 300, -300, 0, 1);

#     x = 0.0;
#     y = 30.0;

#     event = sdl2.SDL_Event();
#     running = True
#     while running:
#         while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
#             if event.type == sdl2.SDL_QUIT:
#                 running = False

#         GL.glClearColor(0, 0, 0, 1)
#         GL.glClear(GL.GL_COLOR_BUFFER_BIT)
#         GL.glRotatef(10.0, 0.0, 0.0, 1.0)
#         GL.glBegin(GL.GL_TRIANGLES)
#         GL.glColor3f(1.0, 0.0, 0.0)
#         GL.glVertex2f(x, y + 90.0)
#         GL.glColor3f(0.0, 1.0, 0.0)
#         GL.glVertex2f(x + 90.0, y - 90.0)
#         GL.glColor3f(0.0, 0.0, 1.0)
#         GL.glVertex2f(x - 90.0, y - 90.0)
#         GL.glEnd()

#         sdl2.SDL_GL_SwapWindow(window)
#         sdl2.SDL_Delay(10)
#     sdl2.SDL_GL_DeleteContext(context)
#     sdl2.SDL_DestroyWindow(window)
#     sdl2.SDL_Quit()












# 	windowsurface = SDL_GetWindowSurface(window)

# 	image = SDL_LoadBMP(b"exampleimage.bmp")
# 	SDL_BlitSurface(image, None, windowsurface, None)

# 	SDL_UpdateWindowSurface(window)
# 	SDL_FreeSurface(image)

# 	running = True
# 	event = SDL_Event()
# 	while running:
# 		while SDL_PollEvent(ctypes.byref(event)) != 0:
# 			if event.type == SDL_QUIT:
# 				running = False
# 				break

# 	SDL_DestroyWindow(window)

# 	SDL_Quit();


# 	return 0;

# 	main_window = sdl2.ext.Window("Celeritas 0.0.0", size=(2560, 1440));
# 	main_window.show();

# 	#processor = sdl2.ext.TestEventProcessor();

# 	main_renderer = sdl2.ext.SoftwareSpriteRenderSystem(main_window);
# 	sdl2.ext.fill(main_renderer.surface, sdl2.ext.Color(0, 0, 0));


# 	loop_active = True;
# 	while loop_active:
# 		events = sdl2.ext.get_events();
# 		for event in events:
# 			print(event.type);
# 			if event.type == sdl2.SDL_QUIT:
# 				loop_active = False;
# 				break;
# 			

# 		time.sleep(0.001);
# 		main_window.refresh();

# 	return 0;



exit(main());
