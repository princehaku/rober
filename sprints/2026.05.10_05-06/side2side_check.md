# Sprint 2026.05.10 05-06 Side-to-side Check

## 对照验收

- 需求：学习 launch 能一键带上 route/keyframe 采集。状态：已实现 `route_recorder:=true` 条件启动 `route_data_recorder`。
- 需求：默认学习流程不强依赖相机。状态：已保留 `route_recorder:=false` 默认值。
- 需求：工作流文档给出普通启动命令和参数边界。状态：已更新 `docs/navigation/fixed_route_workflow.md`。

## 未完成验收

- 未在 ROS2/Humble runtime 中实际启动 `learn.launch.py route_recorder:=true`。
- 未用真实 `/odom` 与 `/camera/image_raw` 产出 route CSV/keyframes。
- 未完成 Docker/Humble colcon build：当前 WSL 2 distro 未启用 Docker Desktop integration。
