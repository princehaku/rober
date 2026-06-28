# PC Summary Path WYSIWYG Readback Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `/api/robot-control/summary` 的 `readback_summary.map` 新增 `path_wysiwyg_status_plain` 和 `path_wysiwyg_next_action_plain`，让 summary 直接说明图上路线是否已贴到当前地图画面。
- 同步更新 shared contract、summary fallback、catalog 测试和 App 默认 fixture，保持 map preview 与 summary 的路线 WYSIWYG 合同一致。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该变化只补只读 summary readback，不刷新地图、不准备或执行 Nav2、不发送控制命令。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`，38 passed，122 skipped。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部 passed。
- 通过：PC API 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：只读读取 `http://127.0.0.1:7001/api/robot-control/summary`，`readback_summary.map` 返回 `path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`path_preview_frame_id=map`、`path_wysiwyg_status_plain=图上路线已显示在当前地图画面。`、`path_wysiwyg_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`。

## 剩余风险

- 当前改动只补齐 summary 的路线 WYSIWYG 只读字段，不会触发地图刷新、路线准备、Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 若 `path_wysiwyg_status_plain` 显示已贴图，只证明 PC summary 当前读到了路线 overlay；完整 Nav2 运动验收仍要另看执行窗口 wheel raw L/R。
