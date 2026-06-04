# PRD: O9 Fresh Scan Proof Runtime

## 用户价值

普通手机用户不关心 ROS2、SSH 或雷达 topic；他们关心小车是否能可靠知道自己周围环境，并最终沿固定路线把垃圾送到垃圾站。fresh `/scan` proof 是建图、定位、固定路线和 PC/operator 可信状态的前置材料：没有它，PC 上的 refresh 按钮、状态面板和 operator report 都只能证明接口存在，不能证明机器人具备导航材料。

## 产品北极星

北极星保持不变：用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站，必要时请求人工协助，并在异常时安全停止、留下可复盘证据。本 sprint 只推进这条闭环里的雷达 runtime 前置证据。

## 需求范围

- 必须证明或收窄 live upper ROS2/LiDAR runtime 是否能发布 `/scan`。
- 必须复测 `POST /api/radar/scan-proof/refresh` 与 `GET /api/radar/scan-proof/latest`。
- 必须记录 `ros2_command_unavailable`、`upper_api_scan_not_proven`、missing `/scan` topics 的真实状态。
- 必须引用 LiDAR vendor 来源：`docs/vendor/VENDOR_INDEX.md` 和 `docs/vendor/lidar_pkg_ros2-main/`。
- 不做底盘运动，不发 `/cmd_vel`，不做 HIL，不扩大 PC UI。

## 验收口径

验收成功可以是两类之一：

1. `robot_runtime_material`：live 8787 refresh 返回 HTTP 2xx，latest artifact 显示 fresh `/scan` once/hz 可观测，`/lidar/raw_packet` 或缺失原因明确，TF 状态明确，collector log 和 timestamp 可追溯，`safe_to_control=false` 保持。
2. `blocked_with_root_cause`：如果仍失败，必须把 blocker 收窄到具体原因，例如 LiDAR driver 未安装、serial device 缺失、udev `/dev/lidar` 不存在、frame mismatch、launch 未运行、topic 名称不匹配或 ROS2 graph 不可用；不能只写 `upper_api_scan_not_proven`。

## evidence_type

- 目标 evidence_type：`robot_runtime_material`。
- 可接受降级 evidence_type：`blocked_with_root_cause`。
- 不可计为完成的 evidence_type：`software_guard`、`readback_only`、`http_200_only`、`ui_display_only`。

## 非目标

- 不证明真实建图完成、地图 artifact 可用、AMCL、Nav2 路径执行或固定路线通过。
- 不证明 PC WASD、真实控车、robot ACK、`safe_to_control=true`、底盘 HIL 或 delivery success。
- 不证明 O2 真实/受控电梯图片、OpenCV field eval 或跨楼层送达。
- 不更新 `OKR.md`，本 sprint 前置计划不直接上调 O9/O3/O7。

## 对应责任 Engineer

- Robot Software Engineer：主责实现、验证、修复和 runtime 证据。
- Full-stack Software Engineer：只在需要时做 PC 同源 readback/smoke 事实补充，不扩大 UI。
- Product Manager / OKR Owner：验收口径、evidence type、sprint 留档和后续 OKR 收口。
