# PC 雷达贴图与建图 Gate 分层

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 增强 `plain-field-acceptance-radar-map-proof`。
  - 当雷达贴图仍是 `not_current`，但建图缺口只剩 `camera_first_frame` 时，现场验收卡明确显示：雷达贴图只阻塞当前所见，不阻塞自由移动，也不阻塞当前建图 gate。
  - DOM 新增 `data-radar-map-blocks-wysiwyg`、`data-radar-map-blocks-mapping-start`、`data-radar-map-blocks-free-move`、`data-radar-map-mapping-missing-reasons`、`data-radar-map-mapping-gap-plain` 和 `data-radar-map-movement-scope-plain`。
- `pc-tools/workstation/test/App.test.ts`
  - 既有雷达贴图 proof 测试补充 gate scope 断言。
  - 新增当前真机口径场景：雷达贴图未贴当前图，但 `mapping_start_missing_reasons=[camera_first_frame]`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达贴图 WYSIWYG 缺口与建图/自由移动 gate 分层合同。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 235 passed (235)`。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`，`Tests 190 passed (190)`。
- 已通过：`git diff --check`。
- 已通过：`npm --prefix pc-tools/workstation run lint`。
- 已通过：`npm --prefix pc-tools/workstation run build`。
  - Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`，`Tests 425 passed (425)`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，新监听 PID `22103`。
- 已通过：只读 smoke `GET /` 和 `GET /map` 均返回 200。
- 已通过：只读 summary smoke `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_wysiwyg_missing_surface_ids=[camera,radar_map_points]`。
  - `radar_overlay_status=not_current`、`radar_overlay_current_point_count=0`、`radar_overlay_source_point_count=174`。
  - `radar_overlay_blocks_wysiwyg=true`、`radar_overlay_blocks_free_move=false`。
  - `mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`。
  - `free_move_start_ready=true`、`camera_current_visible=false`。

## 剩余风险

- 本轮只修正 PC 现场验收卡的只读解释和 DOM 合同，没有刷新雷达、没有启动雷达 lifecycle，也没有执行 Nav2、manual、keyboard、free-roam、建图、delivery 或 stop。
- 完整目标仍未实机闭环：相机首帧、雷达贴图当前点、同窗口 wheel L/R 非零、delivery success、键盘按住窗口轮速/松开停稳和自由移动运行读数仍需现场复验。
