# Sprint 2026.05.10 07-08 Pre-start

状态：active

目标：继续推进完成度偏低的 Objective 4，把学习阶段 route keyframe 从“只有图片/CSV”升级为可被远程诊断读取的视觉样本证据。

Owner：Autonomy Algorithm Engineer 主责；User Touchpoint Full-Stack Engineer 复查 diagnostics contract；Robot Platform Engineer 负责 smoke 护栏和提交。

验收口径：`route_data_recorder` 在成功写入 keyframe 图片时同步写入 companion JSON，并追加 `trashbot.vision_samples.v1` manifest；`learn.launch.py` 能透传 route/sample manifest 参数；operator diagnostics 的现有 manifest summary 能读取 route keyframe 样本。

风险：本轮不声明真实摄像头采集、Nav2 实跑、WAVE ROVER HIL 或 Docker/Humble colcon build 已完成。
