# O7 Consumer Detail Route Replay Tech Done

## sprint_type

sprint_type: epic

## 1. 实际改动

本轮由 `full-stack-software-engineer` 单线完成，收口时间：2026-06-09 10:11:23 CST。

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 将 O7 route replay 主路径切到 O6 consumer detail adapter 返回的 `trajectory / events / evidence / labeling / inference / tunnel_status`。
  - 新增 consumer-detail route replay player：Play/Pause、Previous frame、Next frame、Reset cursor、range cursor 均只修改浏览器本地 state。
  - 新增 consumer-detail trajectory minimap：只消费有限数值型 `x_m/y_m`，无坐标时 `blocked_not_proven`，单点时显示 `readonly_consumer_detail_trajectory_single_point`。
  - 新增事件、证据、labeling、inference、tunnel 摘要浏览，均只展示白名单短摘要。
  - 将旧 archive fixture route replay player 拆成 `fixtureRouteReplay*` 状态和函数，作为次路径 / debug fallback，与 consumer 主路径 cursor 隔离。
  - 保留 `safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 等 fail-closed copy。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 O6 consumer detail mock 轨迹帧、事件、证据、标注和推理样本。
  - 增加 UI 断言，确认页面出现 `local_consumer_detail_cursor_ready`、`readonly_consumer_detail_trajectory_ready`、consumer evidence/event/inference refs。
- `pc-tools/README.md`
  - 记录 O7 consumer read primary path 的 route replay 用户流程和本地播放边界。
  - 明确旧 Cloud Archive Tasks route replay player 仅为次路径 / debug fallback。
- `docs/product/pc_tools_workstation.md`
  - 增补 `o7ConsumerReadAdapter.ts` 架构位置、后端 fail-closed 规则和 O7 consumer detail route replay 产品边界。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 增补 PC O7 consumer read adapter endpoint、请求策略、fail-closed 条件和 route replay 主路径接口语义。

## 2. 验证结果

在 `/Users/m1/apps/rober/pc-tools/workstation` 执行：

```bash
npm run build
```

结果：通过。关键输出：`✓ 31 modules transformed`，`✓ built in 1.12s`，随后 server TypeScript build 通过。

```bash
npm run test
```

结果：通过。关键输出：`Test Files  2 passed (2)`，`Tests  42 passed (42)`。

```bash
npm run lint
```

结果：通过。关键输出：`eslint .` 无报错。

在 `/Users/m1/apps/rober` 执行：

```bash
git diff --check
```

结果：通过，无 whitespace/error 输出。

## 3. 失败定位与修复

首轮 `npm run build` 失败：

```text
Identifier 'resetRouteReplayCursor' has already been declared.
```

根因是上一段未提交改动把旧 fixture route replay 和新 consumer route replay 共用了同一组 cursor/computed/function，且重复声明了 `resetRouteReplayCursor`。已修复为：

- `routeReplay*`：consumer detail 主路径。
- `fixtureRouteReplay*`：archive fixture 次路径 / debug fallback。
- 加载 archive 只重置 fixture cursor；加载 consumer detail 只重置 consumer cursor。

修复后 build/test/lint/diff-check 全部通过。

## 4. 剩余风险

- 当前仍是 local/mock software proof；没有证明真实公网云、真实 production DB/queue、真实 OSS/CDN、真实 ROS2 `/tf`、真实地图叠加或真实机器人运动。
- O6 consumer detail 的数据来自本机回环 relay adapter；生产 O6 consumer read、鉴权、延迟和真实数据质量未验证。
- Play/Pause 是浏览器本地定时器，仅用于逐帧复盘，不是云端 playback session。
- 旧 fixture route replay 仍保留为 debug fallback，后续如果产品决定完全移除 fixture fallback，需要另开 sprint 清理。

## 5. 用户旅程变化

operator 在 O7 Previews 中的主流程变为：

1. 输入本机回环 O6 relay base URL。
2. 点击 `Load consumer task list` 拉取任务列表。
3. 选择 task 或输入 task id。
4. 点击 `Load consumer task detail` 拉取 detail。
5. 在 consumer-detail route replay player 中逐帧检查轨迹、状态、证据 ref、事件摘要、labeling/inference 摘要和 tunnel latest known status。

旧的本地 archive fixture player 仍可用于调试样本，但不再是 O7 route replay 的主产品路径。

## 6. 接口影响

- 未新增生产接口，未改 O6 consumer read contract。
- PC 端继续通过 `GET /api/o7/consumer-read/tasks?baseUrl=<local-loopback-url>` 和 `GET /api/o7/consumer-read/tasks/<task_id>?baseUrl=<local-loopback-url>` 消费 O6。
- 前端只消费 PC adapter 结果，不在浏览器直连 relay，不引入 bearer/token 输入框。
- 所有控制、安全和生产连接字段保持 false：`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
