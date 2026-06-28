# PC Path WYSIWYG First Screen Label Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- 普通首屏地图 caption 新增 `图上行程事实` 标签，直接消费 `readback_summary.map.path_wysiwyg_status_plain/path_wysiwyg_next_action_plain`。
- 新增 App 测试断言，覆盖路线未显示和 summary 确认路线已贴到当前地图画面两种状态；普通首屏继续使用“行程”口径，不把技术字段里的“路线”直接露出给普通用户。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该变化只展示只读 summary，不触发地图刷新、Nav2 或底盘控制。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，1 passed，214 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "generated trip readback"`，1 passed，214 skipped。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部 passed。
- 通过：PC API 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：只读读取 `http://127.0.0.1:7001/api/robot-control/summary`，`readback_summary.map` 返回 `path_wysiwyg_status_plain=图上路线已显示在当前地图画面。`、`path_wysiwyg_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`、`path_preview_point_count=18`、`path_preview_frame_id=map`。

## 剩余风险

- 当前改动只把已存在的路线 WYSIWYG readback 接到普通首屏，不会触发地图刷新、路线准备、Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 首屏是否实际渲染该标签仍由浏览器加载当前前端资源决定；本轮用 Vitest DOM 断言覆盖组件渲染，用 live GET 覆盖后端字段。
