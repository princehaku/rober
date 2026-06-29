# 2026.06.29 18:42 Nav2/base mode status readback

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `/api/base/status` 顶层新增 `base_command_mode`、`nav2_base_command_mode`，让 PC 和脚本能直接读到当前手控/路线执行默认底盘模式。
  - `/api/nav2/status` 顶层新增 `base_command_mode`、`nav2_base_command_mode`、`nav2_goal_execute_default_base_command_mode`，避免只从旧 Nav2 执行 artifact 反推下一次模式。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary key-values 白名单新增 `base_command_mode`，保留既有 `nav2_base_command_mode` 读取逻辑。
- `onboard/tests/test_upper_robot_api.py`
  - 补齐 base status、Nav2 status 的只读模式字段断言，防止回归成内层-only 字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-06-29 18:42 起的只读状态契约和 WAVE ROVER 协议来源。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_o11_nav2_goal_execution_proof`
  - 结果：`Ran 95 tests in 0.211s / OK`
- 已通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o11_nav2_goal_execution_proof.py`
- 已通过：`npm run build`（`pc-tools/workstation`）
  - 结果：TypeScript app/server build 与 Vite build 通过；仅保留既有 chunk-size warning。
- 已通过：`git diff --check`
- 已部署并只读验证上位机：
  - `scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`
  - 清理占用 8787 的旧 orphan `python3 upper_robot_api.py` 后，`systemctl restart trashbot-upper-robot-api.service` 成功，8787 当前由 systemd 新进程监听。
  - `/api/base/status` 摘要：`base_command_mode=ros`、`nav2_base_command_mode=ros`、`wheel_lr_nonzero=false`、`sends_motion_commands=false`
  - `/api/nav2/status` 摘要：`base_command_mode=ros`、`nav2_base_command_mode=ros`、`nav2_goal_execute_default_base_command_mode=ros`、`status=path_ready_with_service_blockers`、`sends_motion_commands=false`

## 剩余风险

- 本轮只补“下一次底盘命令模式可见性”，不发送真实运动命令，也不证明 Nav2 实车路线已经闭环。
- 现场 live 最新 artifact 仍显示上一轮 `pwm` 路线 action succeeded 但 `wheel raw L/R=0/0`；需要在安全确认后用新默认 `ros` 或后续回退 `speed` 模式重跑，才能证明自动驾驶实际动了。
- 摄像头共享预览已能说明不是页面独占，但 live 首帧仍未出；真实画面还需要检查 USB、输入源、供电或 known-good UVC。
