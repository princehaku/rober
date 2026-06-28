# 2026.06.29 04:00 Nav2 lifecycle dependency preflight

## sprint_type

micro

## 实际改动

- `onboard/scripts/o11_nav2_lifecycle.sh`
  - 新增 `nav2_bringup` 启动前依赖检查。
  - 如果依赖缺失，脚本会写 `state=failed_missing_dependency`、明确缺失包和安装建议，再退出；不再只把 `package 'nav2_bringup' not found` 埋在 launch log 里。
  - 保持原安全边界：`start` 仍只启动 Nav2 stack-only manager，不发送 `NavigateToPose`、`/cmd_vel`、manual、free-roam、delivery 或 WAVE ROVER 运动命令。
- `onboard/tests/test_o11_nav2_lifecycle_script.py`
  - 新增静态回归，锁定 `nav2_bringup` preflight、结构化失败状态和 `ros-humble-nav2-bringup` 安装提示。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-06-29 现场复核：摄像头无首帧不是页面独占；小车低速自由移动不以雷达/摄像头 ready 为前置；当前 Nav2 旧缺包 blocker 已消失，但仍卡在 `map -> base_link`、AMCL pose、当前 `/scan` 和 fresh route proof。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步记录本轮 Nav2 现场失败分层，以及 start 后立即 stop 释放串口的安全边界。
- 真车部署
  - 已同步 `onboard/scripts/o11_nav2_lifecycle.sh` 到 `root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh`。
  - 本轮远端只执行 `bash -n` 和 `status`，没有执行 Nav2 start、goal、manual、free-roam、delivery 或 `/cmd_vel`。

## 验证结果

- 通过：`bash -n onboard/scripts/o11_nav2_lifecycle.sh`。
- 通过：`python3 -m unittest onboard.tests.test_o11_nav2_lifecycle_script`，3 tests OK。
- 通过：`git diff --check`。
- 通过：远端 `bash -n /root/rober/onboard/scripts/o11_nav2_lifecycle.sh`。
- 通过：远端 `/root/rober/onboard/scripts/o11_nav2_lifecycle.sh status` 返回
  `running=false/state=stopped`、`motion_requires_explicit_goal_execute=true`、
  `sends_base_motion_commands=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮没有执行真实 Nav2 route goal、manual、free-roam start、delivery 或 `/cmd_vel`，因此仍不声明完整路线执行、wheel raw L/R 非零或 delivery success。
- 当前现场 Nav2 start 已能加载 stack，但完整自动驾驶仍需处理 `map -> base_link`/AMCL pose/当前 `/scan`/fresh route proof，并排查 ESP32 bridge 串口读空或多进程占用。
- 摄像头 `/dev/video1` 仍是 UVC 无首帧，不是网页独占；需要检查 USB/输入/供电或换 known-good UVC。
