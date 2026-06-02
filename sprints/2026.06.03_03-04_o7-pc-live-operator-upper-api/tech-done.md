# O7 PC Live Operator Upper API 收口

## sprint_type

micro

## 实际改动

- PC 首屏 `Rober 控制台` 保持四区块：预览、地图、操控、状态。
- `GET /api/o7/live-operator-panel` 新增 `control.base_boundary`，显示 `/dev/ttyS5 @115200`、`T=1001 not_observed_after_t130` 和 `manual control fail_closed_display_only`。
- `O7LiveOperatorPanel.vue` 状态灯显示 8787 API `not_listening_observed`，摄像头展示 8088 ready，地图明确没有真实 LiDAR `/scan` 证据，底盘控制保持锁定。
- `App.test.ts` 从过度删减的 2 条 UI smoke 恢复为合同型测试：首屏显示、方向键不发控制、live operator API fail-closed、camera 未配置不探测、offer proxy 未配置拒绝、peer close 非法 id 本地拒绝。
- 同步更新 PC 接口/产品文档，明确 PC 端不得 POST `/api/base/manual`、不得发送 `/cmd_vel`、不得发送 WAVE ROVER JSON。

## 验证结果

- `cd pc-tools/workstation && npm run test`：通过，2 test files / 69 tests passed。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 最新复跑输出 `✓ built in 1.86s`。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无输出错误。
- scoped `git diff --check`：通过，无空白或补丁格式错误。

## 剩余风险

- 8787 上位机 Robot API 的真实远端监听、真实 radar `/scan`、真实 `T=1001` feedback、robot ACK 和真实手控仍未证明。
- PC 首屏允许 camera WebRTC media preview offer/close，但该路径只属于摄像头媒体信令，不是底盘控制。
- 本轮未修改 `onboard/`、`OKR.md` 或 OKR 进度日志。
