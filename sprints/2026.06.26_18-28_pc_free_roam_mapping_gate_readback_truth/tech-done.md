# PC free roam mapping gate readback truth

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 free-roam runtime gate 汇总：当当前 readback 已证明 `managed_runtime_started=true` 时，`mapping_active` gate 会被提升为 ready。
  - 这样 PC summary 不再出现同一响应里“一边显示地图 runtime 已启动，一边显示地图记录未启动”的矛盾。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 stale free-roam artifact + 当前 map runtime 已启动的合同测试。
  - 测试确认 summary 使用当前 readback 纠偏，不把旧 runtime artifact 的 `mapping_active=blocked` 原样展示给普通界面。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "free-roam"` 通过：4 passed。
- `npm test` 通过：2 files, 229 tests passed。
- `npm run build` 通过；Vite 仍有单 chunk 大于 500 kB 的既有提示。
- 已重启 PC Node 到 detached `screen` 会话 `rober-pc-7001`，监听 `*:7001`。
- 只读现场验证：
  - `http://127.0.0.1:7001/api/health` 正常。
  - `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `connection=readable`、`free_roam_start_ready=true`、`map_started=true`。
  - 同一响应中的 `mapping_active` gate 已为 `ready`，证据为“当前读回已证明地图记录 runtime 已启动”。
  - 自动扫图 runtime 仍为 `state=stopping`、`artifact_only=true`、`cmd_vel_publish_enabled=false`，本轮没有触发发车。

## 剩余风险

- 当前运行态仍要求现场重新勾安全确认，`operator_confirmed` gate 保持 blocked，这是正确的现场确认边界。
- 自动扫图 runtime 仍处于“现场请求停止”后的 artifact-only 状态；真实自移动需要现场点击 start 并观察。
- 当前 wheel raw 仍为 `L/R=0/0`，非零轮速证明还没完成。
- 雷达 latest fresh 当前读回为 `false`，但上车 start 设计允许低速降级移动；现场仍需继续监看雷达和停止兜底。
