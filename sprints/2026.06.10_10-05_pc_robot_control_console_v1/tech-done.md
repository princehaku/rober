# 2026-06-10 10:05 PC Robot Control Console V1

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 实际改动

- `pc-tools/workstation` 新增 `Robot Control` tab，入口文件为 `src/components/RobotControlConsolePanel.vue`，由 `App.vue` 和 `WorkstationTabs.vue` 接入。
- 新增 Node 只读 Robot API 代理合同 `GET /api/robot-control/summary?baseUrl=<robot-api-base-url>`，实现文件为 `src/server/robotControlSummary.ts`，并在 `src/server/index.ts` 注册 route、在 `src/shared/contracts.ts` 固化 `trashbot.pc_tools_workstation.robot_control_summary.v1`。
- 前端 client 新增 `getRobotControlSummary()`，Vue 不直接跨域访问上位机。
- 页面展示七区块：`task_id selector`、Robot API connection、O3 proof summary、route replay / Mock fallback、evidence / keyframe / labeling readiness、manual/nav safe command boundary、Camera/LiDAR/Base readback。
- 危险动作只显示 locked placeholder：`/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start、keyboard control、map click goal 均不调用、不发布。
- 新增/更新 Vitest 覆盖 Robot Control UI、Robot API proxy summary、unsafe URL fail-closed、危险 true 字段 fail-closed。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，说明 workstation 已进入 Robot API 控制台 V1，但危险动作仍 fail-closed。

## 接口影响

- 新增 PC workstation 本地 endpoint：`GET /api/robot-control/summary?baseUrl=<robot-api-base-url>`。
- Node 代理只允许 GET status/latest/readback 白名单 endpoint：`/api/status`、O3 proof latest、operator report latest、Camera/LiDAR/Base status/latest/readback。
- `baseUrl` 拒绝空值、非 HTTP、credentials、query/hash、非回环或非 RFC1918 局域网 host。
- 响应递归扫描 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`robot_control_executed=true` 等危险字段，命中后 blocked。
- 响应固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 验证结果

运行时间：2026-06-10 22:27:53 CST。

```bash
cd pc-tools/workstation && npm run build
```

最终通过。输出包含：`✓ 33 modules transformed.`、`✓ built in 952ms`。

```bash
cd pc-tools/workstation && npm run test
```

最终通过。输出：`Test Files  2 passed (2)`、`Tests  54 passed (54)`。

```bash
cd pc-tools/workstation && npm run lint
```

最终通过，无 error/warning 输出。

```bash
git diff --check
```

通过，无 whitespace error。

```bash
rg -n "Robot Control|task_id|O7|Mock|真实|状态|safe_to_control|primary_actions_enabled|delivery_success|/api/base/manual|cmd_vel|path_generated" pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/README.md
```

通过，命中 README、产品文档、组件、合同和测试中的目标 token。

## 失败定位与修复

- 第一轮 `npm run build` 失败：`src/server/robotControlSummary.ts` 的 IPv4 解构变量 `b` 被 TypeScript 判定可能为 `undefined`。已改为带 fallback 的索引读取后重跑通过。
- 第一轮 `npm run test` 失败：新增 Robot Control 测试误用了现有 `listenJson()`，该 helper 只服务 `/api/o7/realtime-elevator/snapshot`，导致 Robot API 多 endpoint readback 全部 404。已新增专用 `listenRobotApiReadback()`，只用于测试任意 GET readback JSON，不实现 POST 或运动控制，重跑通过。
- 第一轮 `npm run lint` 退出码为 0 但有 4 个 Vue self-closing warning。已手动改为非 self-closing input，重跑无 warning。

## 剩余风险

- 本轮只完成 PC Robot Control Console V1 的软件侧 Node/Vue 合同与 mock/local HTTP 测试，不证明真实上位机、真实 Camera/LiDAR/Base、真实 O3 path_generated、真实 Nav2 goal、真实 `/cmd_vel`、真实 `/api/base/manual`、HIL 或 delivery success。
- Robot API base URL 允许回环和 RFC1918 局域网 HTTP；真实部署时仍需在网络层控制访问范围。
- O6 consumer detail 仍依赖既有本机回环 adapter；真实 O6/云端生产链路、真实任务归档、真实 keyframe 和真实 labeling submit 未在本轮证明。
- 本轮保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，不发布 `/cmd_vel`，不调用 `/api/base/manual`。
