noinst_HEADERS = celeritas.h

bin_PROGRAMS = celeritas
celeritas_CPPFLAGS = -I$(top_srcdir) -Wall -pedantic
celeritas_SOURCES = celeritas.cpp
celeritas_CXXFLAGS = $(OGRE_CFLAGS) $(SDL2_LIBS)
celeritas_LDADD = $(OGRE_LIBS) $(SDL2_LIBS) -lboost_system

check_PROGRAMS = celeritas

EXTRA_DIST = bootstrap
AUTOMAKE_OPTIONS = foreign
