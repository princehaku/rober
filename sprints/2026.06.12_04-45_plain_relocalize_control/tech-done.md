# 2026-06-12 04:45 Plain Relocalize Control

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通 `.simple-user-console` 的 `移动/导航` 卡片增加 `重新定位` 按钮。
  - 按钮复用既有 `resetLocalizationProof()`，只走固定 `POST /api/robot-control/localize/reset` 代理。
  - 普通首屏只显示 `定位中 / 已定位 / 定位失败` 这类短状态，不显示 `定位重置`、AMCL、initialpose、endpoint、proof 或 raw/readback。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏 contract：允许 `重新定位`，继续禁止 `定位重置`、AMCL、initialpose、Nav2、proof、HIL、`/cmd_vel`、`/api/base/manual`。
  - 将定位 reset 交互测试从高级按钮迁移到普通 `重新定位` 按钮，并验证高级细节仍只在默认关闭诊断区。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通用户契约：首屏允许用户语言 `重新定位`，工程词仍禁入首屏。
- `docs/navigation/fixed_route_workflow.md`
  - 记录普通 PC `重新定位` 入口的 no-motion 边界和真实 PC proxy/readback 证据。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录本轮未改硬件配置、未发底盘运动、未写 WAVE ROVER UART 的边界。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 1 file passed, 17 tests passed.
- 真实 PC proxy：
  - artifact: `artifacts/01_pc_proxy_plain_relocalize.json`
  - `proxy_status=refresh_forwarded`
  - `remote_endpoint=/api/localize/reset`
  - `remote_http_status=200`
  - `latest_proof_status=nav2_no_motion_localization_runtime_observed`
  - `initialpose_published=true`
  - `amcl_pose_observed=true`
  - `localization_reset_observed=true`
  - `managed_runtime_cleanup_ok=true`
  - `hard_dangerous_true_fields=[]`
- 上位机二次回读：
  - artifact: `artifacts/02_upper_localize_latest_after_plain_relocalize.json`
  - `status=localization_reset_observed`
  - `initialpose_published=true`
  - `amcl_pose_observed=true`
  - `localization_reset_observed=true`
  - `managed_runtime_cleanup_ok=true`
- Browser DOM smoke：
  - artifact: `artifacts/03_browser_plain_relocalize_dom.json`
  - `.simple-user-console` 存在。
  - 普通首屏按钮包含 `重新定位` 与 `停止`。
  - 默认高级诊断未展开。
  - 普通首屏未出现 `定位重置`、`initialpose`、`AMCL`、`Nav2`、`proof`、`HIL`、`/cmd_vel`、`/api/base/manual`。

## 剩余风险

- 本轮只证明 PC 普通触点可以触发 no-motion AMCL 定位材料，不证明 NavigateToPose、controller、固定路线执行、真实底盘移动、HIL pass 或 delivery success。
- 当前地图质量仍有 `free=0` blocker；进入定位移动前需要重新采到含 free cell 的真实地图。
- 相机 `/dev/video1` 首帧仍存在 timeout 风险，PC 实时图传可见内容尚未恢复。
- 非 stop 运动 gate 仍缺外部视频、可见图传、左右轮非零反馈和 LiDAR motion delta 材料。
