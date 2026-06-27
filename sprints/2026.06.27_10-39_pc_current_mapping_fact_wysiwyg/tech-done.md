# PC 首屏建图当前事实补强

sprint_type: micro

## 实际改动

- 在 PC 普通用户控制台首屏事实条新增“建图”当前事实：
  - 上车端 `mapping_ready=true`，或本轮 PC 已启动地图记录且画面、雷达都 ready 时，显示可按建图记录监看。
  - 上车端返回 `mapping_missing` 时，直接翻译成“画面首帧未出、地图记录未启动、地图画面未刷新”等用户可理解缺口。
  - 明确建图缺口不影响低速自由移动，避免把相机/雷达误读成小车能不能自己动的硬门禁。
- 补充 App 单测，覆盖建图 ready 和建图缺口但自由移动不受影响两种 UI 形状。

## 验证结果

- 已通过定向测试：`npm test -- App.test.ts --testNamePattern "free-roam autonomy|mapping acceptance|current facts"`，结果 `12 passed | 150 skipped`。
- 已通过前端 lint：`npm run lint`。
- 已通过前端生产构建：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 已通过全量前端测试：`npm test`，结果 `2 passed` test files，`283 passed` tests。
- 已通过空白检查：`git diff --check`。
- 已重启 PC 服务并确认监听：`HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`，`curl -I http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`。
- 已读取 live summary：相机 `source_first_frame_failed` 且 `shared_preview_exclusive_camera_claim=false`；自由移动 `start_ready=true`，建图缺口为 `camera_first_frame,mapping_active,fresh_map_preview`；Nav2 仍为 `goal_succeeded` 但 wheel raw `L/R=0/0`、`goal_execution_base_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮只改 PC 普通用户界面事实翻译和测试，不触发真实底盘运动、不修上车端相机首帧失败根因。
- 当前自动驾驶/Nav2 真实可动仍需要 wheel raw L/R 非零同窗口复验证据；这不是相机或雷达阻塞。
