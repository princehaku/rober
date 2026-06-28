# PC Radar Overlay WYSIWYG Plain Summary

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.map` 增加 `radar_overlay_wysiwyg_status_plain` 与 `radar_overlay_wysiwyg_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把雷达 overlay 的 loaded/partial/not_current/not_loaded 状态压成独立白话，明确当前地图 marker 点数和旧来源点诊断边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏雷达点口径和地图/雷达下一步优先使用新的 WYSIWYG 字段。
- `pc-tools/workstation/test/catalog.test.ts`：补充 loaded、partial、not_current 三类雷达 overlay summary 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary 合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar overlay|map|WYSIWYG|Robot Control summary"`：通过，1 个文件，51 个测试通过，107 个跳过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `readback_summary.map.radar_overlay_status=not_current`、`radar_overlay_wysiwyg_status_plain=雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断。已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`、`radar_overlay_wysiwyg_next_action_plain=先启动雷达，再刷新地图画面。`，同时 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC 只读字段和普通首屏文案，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 自动驾驶 live 仍显示路线 action 曾成功但同窗口 wheel raw L/R=0/0 未非零；本轮不在未获现场安全确认时触发重跑，只把雷达 marker 口径收紧。
