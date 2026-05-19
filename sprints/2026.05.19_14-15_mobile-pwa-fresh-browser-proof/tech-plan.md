# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - Tech Plan

## sprint_type: epic

Run time: 2026-05-19 14:45 Asia/Shanghai。

## 1. 目标

把现有 `pc-tools/evidence/phone_browser_acceptance_gate.py` 升级为 `mobile_pwa_fresh_browser_proof`，让 Objective 4 的本地 mobile/web browser proof 能在独立 fresh Chromium profile 中验证当前 shell、service-worker/cache recovery marker、console/runtime error 为 0、Start/Confirm/Cancel fail-closed、动态控制面 no-store/bypass cache，并产出 JSON、screenshot 和 summary。

证据边界固定为 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`。该 gate 不证明真实手机、production app、真实 PWA prompt/user choice、O5 external proof、O1 HIL、PR #4 field pass、PR #5 real materials 或 delivery success。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对的理由：Objective 5 下一步需要真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof；当前 Docker-only host 不具备这些材料，O5 stop rule 继续成立，继续做本地 O5 wrapper 会重复消费阻塞。
- 次低 Objective：Objective 1，约 81%；但本机没有 WAVE ROVER/UART/HIL 和 PR #5 真实 2D LiDAR / ToF materials，10-11 sprint 已做 `hardware_real_material_escalation_request`，不得重复包装同一 blocker。
- 本 sprint 选择 Objective 4 的理由：上一轮 `2026.05.19_13-14_mobile-pwa-cache-recovery` 留下 concrete risk，即 in-app browser dev log API 保留旧 cached app.js console error、Chrome headless fresh profile attempt 卡住；fresh browser proof 是当前 Docker-only host 可执行且能直接改善真实手机/browser 验收前预检质量的功能抓手。
- `final.md` 收口时需复核：O5/O1 blocker 是否仍成立；fresh browser proof 是否仍只作为 Objective 4 software-proof，而非真实手机或真实 delivery evidence。

## 2. 文件范围

### full-stack-software-engineer 可改

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`（仅在 summary schema 需要兼容字段时）
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md`（写入 Full-Stack 结果）

### robot-software-engineer 可读/可写留档

- 只读审查 Full-Stack diff 涉及的 `pc-tools/evidence/phone_browser_acceptance_gate.py`、`mobile/web/service-worker.js`、`mobile/web/app.js`、`docs/product/mobile_user_flow.md`。
- 可更新 `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md` 中 Robot 只读验收段。
- 不得修改 robot command path、ACK、diagnostics fetch、`/cmd_vel`、ROS2 launch、behavior、hardware 或 service-worker 控制策略，除非 Product 重新开范围。

### product-okr-owner 可改

- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/side2side_check.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 并行拆分

### Task A - full-stack-software-engineer

实现 `mobile_pwa_fresh_browser_proof` gate。

必须完成：

1. 基于现有 `phone_browser_acceptance_gate.py` 增加 fresh browser proof mode，默认使用临时 Chromium profile，运行结束清理 profile 和进程。
2. 启动本地 static server 服务 `mobile/web`，通过 fresh Chromium/CDP 打开当前 shell。
3. 等待当前 shell marker、service-worker/cache recovery marker 和主路径 UI 渲染。
4. 捕获 console/pageerror/runtime error，要求 error count 为 0。
5. 验证 Start Delivery、Confirm Dropoff、Cancel disabled。
6. 验证动态控制面 no-store/bypass cache，至少通过 service-worker/static assertions 覆盖 `/api/*`、`/robots/*`、commands、ACK、diagnostics、non-GET。
7. 输出 `mobile_pwa_fresh_browser_proof_summary.json`、viewport screenshot 和 per-viewport JSON。
8. 更新 `docs/product/mobile_user_flow.md`，写清 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate` 和 `not_proven` 边界。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
node --check mobile/web/service-worker.js
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence --fresh-profile --require-console-zero
rg -n "mobile_pwa_fresh_browser_proof|fresh browser|console|service-worker|software_proof_docker_mobile_pwa_fresh_browser_proof_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
```

### Task B - robot-software-engineer

只读/静态验收 Full-Stack diff。

必须确认：

1. Fresh browser proof gate 不新增 robot command path。
2. Service-worker 对 `/api/*`、`/robots/*`、commands、ACK、diagnostics、non-GET 仍 no-store/bypass cache。
3. Gate 不发送 ACK，不触发 diagnostics fetch 副作用，不访问或暴露 `/cmd_vel` 控制面。
4. Start Delivery、Confirm Dropoff、Cancel 仍 fail-closed；`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍成立。

验收命令：

```bash
rg -n "cmd_vel|ACK|ack|diagnostics|/api/|/robots/|cache: .no-store.|no-store|mobile_pwa_fresh_browser_proof|safe_to_control|primary_actions_enabled|delivery_success" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/service-worker.js mobile/web/app.js docs/product/mobile_user_flow.md
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
```

### Task C - product-okr-owner

收口更新 sprint docs、`OKR.md`、`docs/process/okr_progress_log.md`。

必须完成：

1. 汇总 Full-Stack 与 Robot 结果到 `tech-done.md`。
2. 用 `side2side_check.md` 对照 PRD 验收项。
3. 用 `final.md` 复核 O5/O1 blocker、PR #4/PR #5 边界和 Objective 4 software-proof。
4. 更新 `OKR.md` 4.1 与 `docs/process/okr_progress_log.md`，保持完成度保守。

验收命令：

```bash
test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md && test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/side2side_check.md && test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/final.md
rg -n "mobile_pwa_fresh_browser_proof|software_proof_docker_mobile_pwa_fresh_browser_proof_gate|Objective 5|Objective 1|Objective 4|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
```

## 4. 接口和安全边界

- 不新增 robot command API。
- 不新增 `/cmd_vel` 入口。
- 不把 browser proof summary 作为 ACK 或 command success。
- 不缓存、排队或重放动态控制请求。
- 不把 console-zero、screenshot 或 service-worker marker 写成真实手机、真实 production app、真实 PWA prompt/user choice、真实 O5 external proof、真实 O1 HIL、PR #4 field pass、PR #5 real materials 或 delivery success。
- 所有 artifact copy 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 5. 风险和失败处理

- 若 Chromium fresh profile 卡住，Full-Stack 必须实现超时、进程清理、failure summary，不得只留下挂起进程。
- 若 console error 不为 0，必须定位是当前 shell runtime error、fixture 问题、service-worker 旧 cache 还是 browser driver 问题；修复后重新运行 gate。
- 若 Robot review 发现控制面扩大，Full-Stack 必须先收窄 cache/fetch/control path，再重新运行 tests 和 gate。
- 若 fresh browser proof 只能在本地通过，Product closeout 必须写清它不是真实手机/browser acceptance。

## 6. 本轮计划文档验收命令

```bash
test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/pre_start.md && test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/prd.md && test -f sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PR #4|PR #5|mobile_pwa_fresh_browser_proof|fresh browser|console|service-worker|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|full-stack-software-engineer|robot-software-engineer|product-okr-owner" sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
git diff --check -- sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
```
