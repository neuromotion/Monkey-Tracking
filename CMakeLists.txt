PROJECT(MonkeyTracking)
cmake_minimum_required(VERSION 2.8)
# list of source files
set(project_files Source.cpp)

include_directories("./")
include_directories($ENV{OPENCV_INCDIR})

# define the executable
if(WIN32)
  add_executable(MonkeyTracking WIN32 ${project_files})
else()
  add_executable(MonkeyTracking ${project_files})
endif()

target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_video300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_video300d.lib)
target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_videoio300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_videoio300d.lib)
target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_core300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_core300d.lib)
target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_highgui300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_highgui300d.lib)
target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_imgproc300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_imgproc300d.lib)
target_link_libraries(MonkeyTracking $ENV{OPENCV_LIBDIR}/opencv_imgcodecs300.lib)
target_link_libraries(MonkeyTracking debug $ENV{OPENCV_LIBDIR}/opencv_imgcodecs300d.lib)
# in Windows + Visual Studio we need this to make it a console application
if(WIN32)
   if(MSVC)
     set_target_properties(MonkeyTracking PROPERTIES LINK_FLAGS "/SUBSYSTEM:CONSOLE")
   endif(MSVC)
endif(WIN32)

# install application
set(BIN_DIR ${CMAKE_INSTALL_PREFIX}/bin)
install(TARGETS MonkeyTracking DESTINATION ${BIN_DIR})
