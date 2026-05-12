cmake_minimum_required(VERSION 3.8)
project(ros2_trashbot_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TrashStatus.msg"
  "msg/Waypoint.msg"
  "msg/WaypointList.msg"
  "msg/TaskResult.msg"
  "srv/RecordWaypoint.srv"
  "srv/SetTrashBin.srv"
  "action/TrashCollection.action"
  "action/Patrol.action"
  DEPENDENCIES std_msgs geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
