# PC Nav2 Map Readback Summary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlSummaryResponse.readback_summary` 新增 `map`、`localization`、`nav2` 三个短摘要。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从现有只读 endpoint 和 `o3_proof_summary` 派生地图、定位、Nav2 摘要。
  - `localization.robot_pose_status` 明确区分 `map_pose_observed` 和 `pose_signal_observed_without_map_coordinates`，避免只有 AMCL/TF 信号时把小车坐标画到地图。
  - `nav2` 摘要直接暴露 `path_generated/path_generation_succeeded/path_point_count/path_preview_point_count/path_preview_frame_id`，让完整路线是否已生成更直观。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary 新摘要字段，确认不改变控制锁定边界。
- `pc-tools/workstation/test/App.test.ts`
  - 同步默认 fixture 的新增字段，保持默认未加载口径不误触发 wheel blocker。
- `docs/product/pc_tools_workstation.md`
  - 记录新 readback 摘要和 live 口径。

本轮继续不调用 subagent；CEO 已明确要求去掉 subagent 调用。

## 验证结果

- `npm test -- catalog.test.ts`
  - 103 tests passed。
- `npm test -- App.test.ts`
  - 135 tests passed。
- `npm test`
  - 238 tests passed。
- `npm run build`
  - TypeScript 与 Vite build passed；保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 68612。
- Live readback：
  - `GET http://127.0.0.1:7001/api/robot-control/summary?refresh=1` 返回 `readback_summary.map.status=map_once_artifact_metadata_observed`、`map.map_once_observed=true`。
  - 同一响应返回 `readback_summary.nav2.path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`path_preview_frame_id=map`。
  - 同一响应返回 `readback_summary.localization.robot_pose_status=pose_signal_observed_without_map_coordinates`，说明当前只能证明定位信号，不能证明有可贴到地图的小车坐标。

## 剩余风险

- 这轮只把 map/localization/nav2 读回状态变得所见即所得，不执行 NavigateToPose。
- 当前 live 状态仍显示路线已生成但小车 map 坐标未读到，完整 Nav2 路线执行仍不能放行。
- 相机仍为 `source_selected_not_probed` 且 `last_successful_frame=null`，建图/自动扫图仍被相机首帧门禁拦住。
