# sprint_type: micro

## 实际改动

- PC summary 新增 `current_motion_verification_pack_*` 顶层短字段，把当前可现场验证的运动动作压成一个普通用户动作包。
- PC 首屏 `plain-current-motion-verification-pack` DOM 同步暴露该动作包，展示主动作、三个可执行动作、起点/停止/读回端点、缺失证据和最小预检边界。
- 文档同步说明：该包节点本身只读，不发车、不启动 Nav2/manual/keyboard/free-roam/建图、不提交送达、不发送 stop；真正运动仍只能由各动作按钮在现场安全确认后触发。

## 验证结果

- 已运行 `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed (2)`，`247 passed (247)`。
- 已运行 `cd pc-tools/workstation && npm run build`：通过，Vite/TypeScript 构建成功；仍有既有单 chunk 大小提示。
- 已运行 `cd pc-tools/workstation && npm run lint`：通过。
- 已运行 `git diff --check`：通过。
- Live `0.0.0.0:7001` summary 验证：
  - 当前 PID `182` 监听 `*:7001`。
  - `GET /api/robot-control/summary` 返回 `current_motion_verification_pack_status=ready_for_safety_confirm`。
  - `current_motion_verification_pack_action_ids=[run_nav2_route,hold_keyboard,start_free_move]`。
  - `current_motion_verification_pack_action_display_labels=[重跑图上行程并复验轮速,键盘连续手控,自由自助移动]`。
  - `current_motion_verification_pack_primary_action_id=run_nav2_route`，`current_motion_verification_pack_ready_action_count=3`。
  - `current_motion_verification_pack_minimal_precheck_safety_only=true`，`current_motion_verification_pack_camera_preflight_required=false`，`current_motion_verification_pack_radar_preflight_required=false`。
  - `current_motion_verification_pack_sends_motion_when_clicked=false`，`current_motion_verification_pack_readback_sends_motion=false`。

## 剩余风险

- 本轮未执行真实运动/HIL；`current_motion_verification_pack_*` 只减少现场操作理解成本，不证明完整 Nav2、键盘连续或自由移动已经通过。
- 相机仍是硬件缺口：当前 live 读回仍显示只剩相机首帧/USB 高速链路处理，建图启动仍等待相机首帧。
