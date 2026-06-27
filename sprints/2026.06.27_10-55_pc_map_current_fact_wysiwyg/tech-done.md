# PC 首屏地图当前事实补强

sprint_type: micro

## 实际改动

- PC 普通用户首屏 `当前事实` 新增“地图”行：
  - 真实地图图像已显示时，直接写出尺寸和可通行格数量。
  - 只读到 `map_once`/metadata 但没有 `image_data_url` 时，显示“已读到地图材料，但还没显示真实地图图像；先刷新地图画面”。
  - 完全没有地图图像时，显示“还没读到真实地图图像”。
- 补充 App 测试，防止 map artifact/metadata 被误说成真实地图画面。

## 验证结果

- 已通过定向测试：`npm test -- App.test.ts --testNamePattern "renders Robot Control V1|map artifact readback"`，结果 `2 passed | 161 skipped`。
- 已通过前端 lint：`npm run lint`。
- 已通过前端生产构建：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 已通过全量前端测试：`npm test`，结果 `2 passed` test files，`284 passed` tests。
- 已重启 PC 服务并确认监听：`HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`，`curl -I http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`。
- 已读取 live summary：`map_once_observed=true`，但 `map_free_cell_count=not_loaded`、`map_usable_for_navigation=not_loaded`。
- 已读取 live map preview：`proxy_status=preview_forwarded`、`map_name=trashbot_map`、`width=223`、`height=116`、`cell_counts.free=421`、`image_loaded=true`。

## 剩余风险

- 本轮只补 PC 首屏所见即所得事实翻译，不刷新真实地图、不执行建图、不发送 manual/Nav2/free-roam/delivery 或 `/cmd_vel`。
- live 上车端 summary 当前仍显示 `map_once_observed=true` 但 `map_free_cell_count=not_loaded`；PC map preview 可读到真实图像，因此首屏事实必须以 preview 是否加载为准，而不能只看 summary metadata。
