# PC 自由移动 stop_required 白话修正

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `freeRoamExternalStopRequested` 判断：只有 runtime `state=stopping` 且 reason 是现场/外部停止，或存在 `external_stop_request` gate，才把状态解释为外部停止请求。
  - `stop_required=true` 不再直接映射成“当前有停止请求”，避免把“未勾安全确认”的安全锁误写成另一个 stop blocker。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/free-roam/autonomy/latest` 的 key values 新增 `external_stop_requested`，从 runtime snapshot 或 explicit gate 派生。
  - latest readiness 只用 `external_stop_requested` 或明确 stopping reason 判断停止请求，不再用 `stop_required=true` 猜测。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 summary 回归：`state=locked`、`reason=还未勾选现场安全确认`、`stop_required=true` 时，free-roam 白话不能包含“停止请求”。
  - 新增 latest route 回归：同一 live 形态下 `stop_request_pending=false`、`start_will_clear_stop_request=false`、`external_stop_requested=false`，并保持不发控制。
- `docs/product/pc_tools_workstation.md`
  - 同步产品边界：自由移动只需现场安全确认和停止兜底；`stop_required` 是保守锁车字段，不等价于外部停止请求。

## 验证结果

- `npm test -- test/catalog.test.ts -t "missing safety confirmation|safety-confirmation lock|start-ready while motion runtime is stopped"`：通过，3 passed。
- `npm test -- test/catalog.test.ts -t "HTTP first-screen budget|missing safety confirmation|safety-confirmation lock"`：通过，3 passed。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BrleZEDU.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- 7001 重启：最新代码已监听 `0.0.0.0:7001`，PID `66510`。
- live 7001 summary：真实小车当前返回 `decision_state=stopping`、`decision_reason=现场请求停止`、`stop_required=true`，因此 PC 继续显示“当前有停止请求，开始自由移动会先清除停止请求”是正确状态；误报场景 `state=locked/reason=还未勾选现场安全确认/stop_required=true` 已由 focused regression 覆盖。

## 剩余风险

- 本轮只改 PC Node 的只读解释和白话字段，不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实自由移动仍需要操作者勾选现场安全确认后才能启动；本轮不做真实发车复验。
