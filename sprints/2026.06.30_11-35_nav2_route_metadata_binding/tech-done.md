# Nav2 Route Metadata Binding Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“执行图上路线”在调用 `/api/robot-control/nav2/goal/execute` 时，随请求带上当前地图路线元数据：预览点数、源点数、frame、起点和终点。
  - 这些字段只绑定执行证据，不新增发车前预检；按钮门禁仍保持勾选现场安全确认。
- `pc-tools/workstation/src/server/index.ts`
  - Node 代理归一化并限幅路线元数据，写入 `goal_request`，同时转发给上车 `/api/nav2/goal/execute`。
  - `navGoalExecutionKeyValues` 读取上车 latest/result 中的 `route_preview`，使 PC latest 摘要能回显路线点数和起终点。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlNavGoalExecutionRequest/Response.goal_request` 增加路线元数据字段。
- `onboard/scripts/upper_robot_api.py`
  - 上车 `/api/nav2/goal/execute` 接收可选 `route_preview` / route metadata 字段，并回显到 `goal_request` / latest readback。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定前端点击“执行图上路线”时，请求体包含当前地图路线的点数、源点数、起点和终点。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 Node 代理转发和 response/key values 回显路线元数据。
- `onboard/tests/test_upper_robot_api.py`
  - 锁定上车 API 回显 route preview metadata。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`onboard/README.md`
  - 同步说明完整 Nav2 路线执行证据现在绑定当前地图路线元数据，且不新增发车前预检。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "shows delivery confirmation pending on the map while final completion is in flight"`。
- 已通过：`npm test -- test/catalog.test.ts -t "Nav2 goal execution reuses minimal PC preflight"`。
- 已通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_lifts_base_motion_flags_from_latest_result`。
- `npm test -- --run`：通过，2 个测试文件、392 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Bp0AiNpA.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `57206`，页面入口引用 `index-Bp0AiNpA.js` 与 `index-1TFDR4Wy.css`。
- live bundle 检查：JS 命中 `route_preview_point_count=3`、`route_preview_source_point_count=3`、`route_start_x=3`、`route_goal_x=3`、`执行图上路线=22`。

## 剩余风险

- 本轮绑定的是路线元数据和软件回显证据；没有在真实小车上执行 Nav2 HIL。
- 完整路线是否真正到达、wheel raw L/R 是否同窗口非零、delivery success 是否闭环，仍需现场勾安全确认后执行并验收。
