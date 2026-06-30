# PC Free Roam Stop Request Summary Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.free_roam` 新增停止请求结构化字段：
    `stop_request_pending`、`free_roam_stop_request_pending`、`start_will_clear_stop_request`、
    `motion_start_blocked_by_stop_request` 和 `stop_request_status_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary 层直接派生外部停止请求状态，区分 `stop_required=true` 的 locked 态和真实现场/外部停止请求。
  - `free_move` action card 优先消费 summary 结构化字段；只有旧字段缺失时才回退到 `stop_required` / `decision_state`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 free-roam action card fallback 优先读取 summary 结构化字段，避免把 locked 态误显示成“当前有停止请求”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 同步 fixture 和断言，覆盖 summary free-roam stop request 字段。
- `docs/product/pc_tools_workstation.md`
  - 同步产品合同：summary/readback 和首屏 DOM 必须优先消费结构化停止请求字段。

## 验证结果

- `npm test -- test/catalog.test.ts -t "free-roam autonomy runtime state|does not treat stop_required locked"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "labels free-roam start as clearing"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-D0UEmy34.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `66510`，新监听进程为 `node` PID `83345`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `assets/index-D0UEmy34.js` 和 `assets/index-1TFDR4Wy.css`；JS bundle 命中 `free_roam_stop_request_pending` 与 `start_will_clear_stop_request`。
- live summary 检查：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 200；`readback_summary.free_roam.stop_request_pending=true`、`start_will_clear_stop_request=true`、`motion_start_blocked_by_stop_request=false`，白话为“当前有停止请求；开始自由移动会先清除停止请求，不作为启动阻塞。”

## 剩余风险

- 本轮只改 PC summary 和首屏只读合同，不自动清除停止请求、不启动自由移动、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实自由移动、键盘连续手控、Nav2 路线重跑和 wheel raw L/R 非零仍需要现场安全确认后做 HIL 验证。
