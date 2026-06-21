# 2026-06-22 00:55 First-Jog Readiness Summary

## sprint_type

micro

## 功能设计

目标：继续推进“PC 上连接和控制 / 能移动”的普通用户链路，把 first-jog 能不能按下的原因从
前端临时判断提升为 PC Robot Control summary 的稳定合同。当前真实上位机状态是：
基础安全三项已经记录，但外部视频/可见相机材料仍缺；因此 first-jog 下一步不是“补轮速/雷达”，
而是先记录现场画面。

本轮设计：

- `RobotControlSummaryResponse` 新增 `first_jog_readiness_summary`。
- summary 字段包含：
  - `status`
  - `basic_safety_ready`
  - `visual_material_ready`
  - `missing_fields`
  - `next_action`
- 状态口径：
  - `not_loaded`：operator report 未加载。
  - `blocked_missing_basic_safety`：现场人员、清场或急停三项未齐。
  - `blocked_missing_visual_material`：基础三项齐，但缺外部视频或可见相机材料。
  - `ready_for_first_jog`：基础三项与视觉材料齐，可以按固定 first-jog 代理尝试。
- 普通首屏消费该 summary，避免前端和后端各自推导 readiness。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlSummaryResponse` 新增 `first_jog_readiness_summary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 first-jog readiness 推导函数。
  - `failClosed` 和正常 summary 都输出该字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `移动/导航` 使用 `first_jog_readiness_summary.visual_material_ready` 判断 `待记录/待试动`。
- `pc-tools/workstation/test/App.test.ts`
  - summary fixture 增加 readiness 字段，并同步缺视觉材料场景。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 readiness summary 正常 ready 与缺视觉材料两类断言。

## 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：通过，80 tests passed。
- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，19 tests passed。
- `cd pc-tools/workstation && npm run test`：通过，99 tests passed。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- 真实 PC summary 对 `http://192.168.1.11:8787` 验证：
  - `console_status=loaded_fail_closed_summary`
  - `robot_api_connection.status=readable`
  - `operator_hil_material_summary.operator_present=true`
  - `operator_hil_material_summary.physical_clearance=true`
  - `operator_hil_material_summary.emergency_stop=true`
  - `first_jog_readiness_summary.status=blocked_missing_visual_material`
  - `basic_safety_ready=true`
  - `visual_material_ready=false`
  - `missing_fields=["external_video_or_visible_camera"]`
  - `next_action=record_visual_material`
- 关键 artifact：
  - `artifacts/01_pc_summary_first_jog_readiness_current.json`

## 剩余风险

- 本轮仍没有执行真实 first-jog；缺现场画面材料时后端会继续拒绝。
- 该 summary 只说明 first-jog 前置条件，不证明轮速非零、LiDAR motion delta、真实移动或地图可导航。
- 地图仍是 `free=0`，需要真实移动建图后才能提升。
