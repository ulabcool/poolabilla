cmake_minimum_required(VERSION 3.7)
project(streamnect)

set(CMAKE_CXX_STANDARD 11)

find_package(freenect2 REQUIRED)

INCLUDE_DIRECTORIES(
        ${freenect2_INCLUDE_DIR}
)

include_directories("/usr/include/libusb-1.0/")
link_libraries(${FREENECT2_LIBRARIES})

set(SOURCE_FILES main.cpp)
add_executable(streamnect ${SOURCE_FILES})
target_link_libraries(streamnect ${freenect2_LIBRARIES})
