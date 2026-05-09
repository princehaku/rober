# Sprint 2026.05.10 06-07 Pre-start

状态：active

目标：继续推进 OKR 完成度偏低的 Objective 3，让 fixed-route 在真实运动前能一次性暴露全路线关键帧覆盖问题，而不是跑到某个 checkpoint 才发现缺图或坏图。

Owner：Autonomy Algorithm Engineer 主责；Robot Platform Engineer 负责 smoke 护栏和 sprint 留档。

验收口径：`fixed_route_autonomy` 的 debug status 包含 route-wide keyframe preflight 摘要；dry-run/diagnostics 可以看到总 checkpoint、已加载关键帧、缺失/无效关键帧和视觉门控是否具备路线级准备度；目标测试和 smoke 护栏通过。

风险：本轮仍不声明真实 Nav2、真实摄像头、WAVE ROVER HIL 或 Docker/Humble colcon build 已完成。
