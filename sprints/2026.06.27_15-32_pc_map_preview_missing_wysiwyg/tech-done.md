# 2026-06-27 15:32 PC map preview missing WYSIWYG

## sprint_type: micro

## 设计结论

本轮修正普通首屏的建图缺口显示。live 状态里 PC 已能从
`/api/robot-control/map/preview` 看到真实地图图像，但上车端 summary 的
`readback_summary.free_roam.mapping_missing` 仍可能保留旧的 `fresh_map_preview` token。

正确口径：

- 如果 PC 本地已经显示 `preview_forwarded + image_data_url`，普通界面不再把
  `fresh_map_preview` 展示成“地图画面未刷新”。
- 相机首帧、地图记录未启动、雷达 freshness 等缺口仍按 summary/readback 原样保留。
- 该修正只影响只读 UI 文案，不修改上车 summary，不启动地图记录、free-roam、manual、Nav2、
  delivery、stop，也不发布 `/cmd_vel`。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainMapPreviewImageLoaded()`，以 PC 实际显示的地图图像判定本地 map preview 是否已满足。
  - 新增 `freeRoamMappingMissingPlainLabelsForVisibleState()`，在图像已显示时仅移除
    `fresh_map_preview` 对应的“地图画面未刷新”缺口。
  - 建图事实条和 free-roam 建图 readiness 改用“当前缺口”口径，避免把本地已满足的画面状态继续归因到上车端缺口。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归测试：summary 仍带 `fresh_map_preview`，但 PC map preview 已显示真实图像时，首屏不再出现“地图画面未刷新”。
  - 更新自由移动/建图分层测试，匹配 App 挂载时已自动读到地图 preview 的现有行为。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 PC 本地图像状态覆盖旧 `fresh_map_preview` token 的 WYSIWYG 口径和安全边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "uses the visible map preview|splits free movement"`
  - `Tests 2 passed | 165 skipped`
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Tests 294 passed`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 保留既有 Vite chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation run lint`

## 剩余风险

- live 相机仍可能无首帧，因此建图验收仍应保留 `camera_first_frame` 缺口。
- live 地图记录未启动时，`mapping_active` 仍会保留为当前缺口；这不阻塞安全确认后的低速自由移动。
- 本轮未执行任何运动 POST；真实 free-roam / Nav2 行程复验仍需要 operator 明确现场安全确认后再触发。
