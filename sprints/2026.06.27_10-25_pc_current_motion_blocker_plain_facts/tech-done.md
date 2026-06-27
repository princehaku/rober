# PC 当前事实：摄像头共享、自移动和 Nav2 卡点口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首页当前事实的摄像头行明确写出“共享预览支持多人观看”，并继续显示当前页面数、共享流状态和是否独占，避免把无首帧误判成浏览器独占。
  - 首页当前事实的自由移动行明确写出“低速自移动不依赖雷达新鲜度”，区分“能低速自由移动”和“能按建图验收收口”。
  - Nav2/行程卡点文案从“不是雷达阻塞”收紧为“不是雷达或相机阻塞；卡在执行窗口 wheel raw L/R 非零复验”，避免把 action succeeded 误判成完整自动驾驶已经动过。
- `pc-tools/workstation/test/App.test.ts`
  - 更新摄像头共享预览、自由移动、Nav2 wheel raw L/R 卡点相关断言，锁住普通用户口径。

## 验证结果

- 已通过定向前端测试：
  - `npm test -- App.test.ts --testNamePattern "current facts|共享|camera|free-roam|free movement|Nav2|wheel|radar|键盘"`
  - 结果：`Test Files 1 passed (1)`，`Tests 93 passed | 68 skipped (161)`。
- 已通过完整前端验证：
  - `npm run lint`
  - `npm run build`
  - `npm test`
  - `git diff --check`
  - 结果：lint 通过；build 通过（保留 Vite chunk size warning）；`Tests 282 passed (282)`；diff check 通过。
- 已重启 PC API：
  - `launchctl submit -l rober.pc.api.7001 ... HOST=0.0.0.0 PORT=7001 npm run api`
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - `/tmp/rober-pc-api-7001.out` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 已读 live summary：
  - 摄像头：`source_first_frame_failed`，`source_usage_status=not_in_use`，`shared_preview_exclusive_camera_claim=false`，当前不是页面独占，但设备没有输出首帧。
  - 自由移动：`start_ready=true`，`artifact_only=true`，`cmd_vel_publish_enabled=false`，当前未发布运动，勾安全确认后可从固定 start 入口启动。
  - Nav2：`goal_execution_result_status=succeeded`，但 `goal_execution_base_feedback_lr_nonzero_proven=false`，`L/R=0/0`，下一轮应以 `ros` 模式重新执行并复验执行窗口 wheel raw L/R。

## 剩余风险

- 本轮没有执行真实摄像头 reset、真实自由移动或真实 Nav2 重新发车；真实运动仍需现场 operator 勾安全确认后再操作。
- 当前 live 摄像头读回仍是“设备没人占用但无首帧”，更像 USB/输入/格式/供电或 camera backend 无帧，不是页面独占。
- 当前 live Nav2 已有 `goal_succeeded`，但 wheel raw L/R 同窗口非零仍未证明；需要现场安全确认后用 `ros` 模式重新执行路线并读取执行窗口 L/R。
