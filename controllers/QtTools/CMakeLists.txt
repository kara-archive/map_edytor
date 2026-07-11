cmake_minimum_required(VERSION 3.10)
project(QtTools)

find_package(Qt5 COMPONENTS Core Gui Widgets REQUIRED)

add_library(QtTools MODULE image_tools.cpp python_bindings.cpp)
target_link_libraries(QtTools PRIVATE Qt5::Core Qt5::Gui Qt5::Widgets)
