# Tech Done

sprint_type: micro

## 实际改动

- 普通首屏地图雷达 marker 新增降级 WYSIWYG 口径：当没有 `scan_preview_points`、没有 map-frame 位姿，但 `safe_command_boundary.free_roam_autonomy_gates` 的 `obstacle_clear.evidence` 明确包含 `最近障碍 Xm` 时，地图 marker 显示 `雷达已运行/待刷新/启动中，最近障碍 Xm`。
- 地图 caption 同步说明 `实时雷达未返回点数组，只显示最近障碍 Xm`，坐标口径说明该距离不贴到地图，避免把局部距离误看成真实地图坐标。
- 更新 App 回归测试，覆盖默认首屏、雷达待刷新、雷达启动后自动刷新和启动中 pending marker 的最近障碍距离展示；无路线时普通首屏坐标口径改用 `目标线未显示`，避免把工程词重新带回默认首屏。
- 更新 `docs/product/pc_tools_workstation.md`，记录该降级展示只消费 summary gate，不伪造点云、不推导障碍坐标、不发送任何运动或 Nav2/送达命令。

## 验证结果

- 通过：`npm test -- test/App.test.ts`，118 个用例通过。
- 通过：`npm test`，2 个测试文件、214 个用例通过。
- 通过：`npm run build`，TypeScript app/server 与 Vite production build 通过；Vite 仍提示单 chunk 超过 500 kB 的既有 warning。
- 通过：`npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 `npm run api` 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `TCP *:7001`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`、`robot_api_connection.status=readable`、`loaded_count=14`，并读到 `obstacle_clear.evidence=最近障碍 0.04m`、`lidar_fresh.evidence=雷达距离 0.04m，延迟 0.06s`。本次 live 同时已有 `scan_preview_point_count=8` 和 map-frame `robot_pose`，因此线上地图会优先使用真实雷达点贴图路径；本轮新增的最近障碍距离 marker 是点数组或定位缺失时的降级 WYSIWYG 路径。

## 剩余风险

- 本轮只改善 PC 地图上雷达最近障碍距离的 WYSIWYG 展示，不证明真实 scan 点贴图、真实 AMCL/map-frame 位姿、自动避障通过、wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success。
- 当前 live 上位机仍显示最近障碍约 `0.04m` 且自动扫图门禁未放行；PC 只能如实显示，不应解锁自动扫图运动。
