# Waypoint with metadata
string name
geometry_msgs/PoseStamped pose
int8 type           # 0=patrol, 1=trash_pickup, 2=trash_bin, 3=charging
bool visited
float64 last_visit_time
string comment      # arbitrary note
