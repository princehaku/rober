# 2026-06-22 00:10 Plain First-Jog Guidance

## sprint_type

micro

## 功能设计

目标：继续推进“能在 PC 上连接和控制 / 能移动”的普通用户路径，把首屏 `移动/导航`
提示对齐 first-jog 的真实门禁。当前真实上位机已经记录基础三项
`operator_present/physical_clearance_confirmed/emergency_stop_ready=true`，但缺
外部视频或可见相机材料；first-jog 的前置条件是“基础三项 + 现场画面”，轮速非零和
LiDAR motion delta 是试动后的输出证据，不应在普通首屏被说成试动前必须补齐。

本轮设计：

- 普通首屏没有现场画面材料时显示 `待记录`，提示“先记录现场画面，再试动一下”。
- 普通首屏已有外部视频或可见相机材料时显示 `待试动`，提示“现场画面已记录；可以试动一下”。
- 高级 manual 点动仍保持完整材料门禁，继续要求外部视频、可见相机、轮速反馈和 LiDAR delta。
- 不新增运动命令、不放宽 `POST /api/robot-control/base/first-jog` 后端 preflight。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `firstJogVisualMaterialReady`，只用 `operator_hil_material_summary` 中的外部视频或可见相机 ref 判断普通 first-jog 的首屏提示。
  - 将普通首屏缺材料提示从“画面、轮子和雷达”收窄为“先记录现场画面，再试动一下”。
  - `移动前检查` 成功后的普通提示改为“还需要现场画面”，避免误导用户先补试动后才能产生的轮速/LiDAR 证据。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏回归断言，覆盖 `待记录` / `待试动` 两种状态。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通 first-jog 状态口径，高级诊断完整材料门禁不变。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，19 tests passed。
- `cd pc-tools/workstation && npm run test`：通过，98 tests passed。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- 真实上位机当前 operator report：
  - `operator_present=true`
  - `physical_clearance_confirmed=true`
  - `emergency_stop_ready=true`
  - `external_video_recorded=false`
  - `visible_content_proven=false`
- PC first-jog 固定代理当前复测：
  - `proxy_status=command_rejected`
  - `failure_reason=first_jog_preflight_required`
  - `missing_fields=["external_video_or_visible_camera"]`
  - `remote_http_status=null`
  - `robot_control_executed=false`
- 关键 artifacts：
  - `artifacts/01_upper_operator_report_current.json`
  - `artifacts/02_pc_first_jog_current_reject.json`

## 剩余风险

- 本轮只修普通首屏引导，不发送真实运动命令。
- 当前真实上位机仍缺外部视频或可见相机材料；first-jog 仍会被后端拒绝，不会调用远端 `/api/base/manual`。
- 地图仍是 `free=0`，不能作为可导航地图。
