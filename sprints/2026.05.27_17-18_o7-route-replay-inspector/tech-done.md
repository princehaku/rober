# O7 Route Replay Inspector Micro Sprint

sprint_type: micro

## 实际改动

- 扩展 `trashbot.o7.cloud_archive_tasks.v1`，新增 `route_replay_inspector` 只读检查视图。
- inspector 从 selected task 提取最多 5 条轨迹帧、最多 5 条事件时间线、最多 5 条关键帧 ref，并固定 cursor 初始状态 `playing=false`、`safe_to_play=false`、`speed=0`。
- blocked 输入、坏 JSON、unsafe copy、success/control/real API claim 继续 fail-closed，inspector 返回空 sample 和 false cursor。
- `O7 Previews` 的 `Cloud Archive Tasks` 区块新增 inspector 展示：selected task、map frame、frame count、sample frames、event timeline、keyframe refs、cursor false fields。
- 同步更新 PC workstation 产品边界和 O7 cloud archive/operator console 接口文档。

## 验证结果

已运行：

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`✓ built in 2.02s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  31 passed (31)`。
- `cd pc-tools/workstation && npm run lint`：通过。`eslint .` 无错误输出。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_17-18_o7-route-replay-inspector`：通过，无 whitespace error。

失败定位和修复：

- 第一轮 `npm run build` 失败于测试里使用 `Array.at()`，当前 TS lib 不包含 ES2022；已改为索引访问。
- 第一轮 `npm run test` 失败于旧 event summary 断言只期望 1 条 event type；新增 inspector fixture 后 selected task 有 2 条 event，已更新断言并重跑通过。

## 剩余风险

- 当前仍是本地 fixture software proof，不连接 O6 真实云归档、ROS2、硬件或机器人控制链路。
- inspector 只证明 selected task 的限量安全字段可读，不证明真实历史路线逐帧回放可播放。
