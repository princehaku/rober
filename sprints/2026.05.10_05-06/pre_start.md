# Sprint 2026.05.10 05-06 Pre-start

状态：active

目标：推进 Objective 3 route learning closure，让学习阶段可以从一个 launch 同时启动 SLAM、waypoint 学习和 fixed-route CSV/keyframe 采集。

Owner：Autonomy Algorithm Engineer 主责，Robot Platform Engineer 负责 launch 集成验证。

验收口径：`learn.launch.py` 显式提供 route recorder 开关和参数；默认不启动 recorder；启用后将参数传给 `route_data_recorder`；工作流文档给出一键学习采集命令；目标测试和 smoke 护栏通过。

风险：本轮只做 launch/文档/静态契约验证，不声明真实 `/odom`、`/camera/image_raw`、Nav2 或硬件路线采集已经完成。
