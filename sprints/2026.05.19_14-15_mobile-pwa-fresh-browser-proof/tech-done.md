# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - Tech Done

## sprint_type: epic

Run time: 2026-05-19 14:23 Asia/Shanghai。

## Full-Stack Task A 实际改动

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
  - 新增 `--fresh-profile` 和 `--require-console-zero`，默认不传 flag 时继续输出旧 `mobile_current_pwa_field_trial_browser_*` artifact 和旧 evidence boundary。
  - fresh browser proof mode 使用独立临时 Chromium profile，输出 `mobile_pwa_fresh_browser_proof_390x844.json/png`、`mobile_pwa_fresh_browser_proof_768x900.json/png`、`mobile_pwa_fresh_browser_proof_summary.json`。
  - fresh mode 固定 evidence boundary 为 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`，summary 写入 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not_proven`。
  - 增加 CDP `Runtime.consoleAPICalled`、`Runtime.exceptionThrown`、`Log.entryAdded` 捕获；`--require-console-zero` 下 console/runtime error count 必须为 0。
  - 增加当前 shell marker、service-worker registration、`mobile_pwa_cache_recovery` marker、`/api/status`/`/api/diagnostics` no-store header、service-worker 动态控制面 bypass/no-store 静态断言。
  - Chromium 启动或 CDP setup 失败会写 failure summary，并通过 context manager 清理进程和临时 profile；`/favicon.ico` 自动请求返回 204，避免 console-zero 被浏览器默认图标噪声污染。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 增加 fresh flags、summary schema、fresh evidence boundary、console-zero 捕获、service-worker marker、动态 no-store/bypass、fail-closed summary 字段的静态 smoke tests。
- `docs/product/mobile_user_flow.md`
  - 记录 fresh browser proof gate 的命令入口、artifact 名称、service-worker/cache recovery/no-store 检查、console-zero 语义和 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate` 边界。
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence/`
  - 生成 fresh proof summary、per-viewport JSON 和 screenshots。

## 用户旅程变化和触点收益

普通用户触点没有新增控制动作；收益是现场 owner 在真实手机验收前，可以先用 fresh Chromium profile 证明当前 `mobile/web` shell 不是旧缓存壳，Start/Confirm/Cancel 仍 fail-closed，动态控制面仍 no-store/bypass cache，且当前页面没有 console/runtime error。

## 接口影响

- 不新增 `/cmd_vel`、ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel 或 robot command API。
- `phone_browser_acceptance_gate.py` CLI 兼容旧用法；只有显式传 `--fresh-profile` 时切换到 fresh artifact 名称和 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`。
- fresh proof artifact 是本地 software proof，不是 `/api/status` runtime schema，也不授权机器人控制。

## 验证结果

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 127 tests in 0.860s
OK
```

```text
python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py
passed
```

```text
node --check mobile/web/app.js
passed
```

```text
node --check mobile/web/service-worker.js
passed
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence --fresh-profile --require-console-zero
viewport=390x844 passed=true ... phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate
viewport=768x900 passed=true ... phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate
summary=sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence/mobile_pwa_fresh_browser_proof_summary.json ok=true evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate fresh_profile=true require_console_zero=true
```

## 剩余风险

- 本轮证据边界仅为 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`；不证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、PR #4 field pass、PR #5 real materials、dropoff/cancel completion 或 delivery success。
- fresh browser proof 仍使用本机 Chromium-family 浏览器和 fixture server；真实手机 browser/device acceptance 需要现场 owner 提供真实设备材料。

## Robot Platform Engineer - Task B 最终控制边界复核

Run time: 2026-05-19 14:27 Asia/Shanghai。

### 实际改动

- 仅更新本文件的 Robot final review 段。
- 未修改 `pc-tools/evidence/phone_browser_acceptance_gate.py`、`mobile/web/service-worker.js`、`mobile/web/app.js`、`docs/product/mobile_user_flow.md` 或任何 robot command / ACK / diagnostics / `/cmd_vel` / ROS2 / hardware 控制逻辑。

### 最终结论

- 通过。最终 `mobile_pwa_fresh_browser_proof` 没有新增 robot command path、`/cmd_vel` 控制入口、ACK 发送路径或动态控制请求缓存/重放逻辑。
- `phone_browser_acceptance_gate.py` 仍是本地 fixture browser proof gate：HTTP handler 只实现 `do_GET`，仅为 `/api/status`、`/api/diagnostics`、静态 PWA 文件和 `/favicon.ico` 返回 no-store 响应；未发现 `do_POST` 或 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` handler。
- fresh proof 会对 `/api/status?fresh_browser_probe=1` 和 `/api/diagnostics?fresh_browser_probe=1` 做 GET no-store 探针，并点击 diagnostics UI 做可见性检查；这些动作只命中本地 fixture server，不提交 ACK、不推进 cursor、不触发 Start/Confirm/Cancel 或 robot command。
- `service-worker.js` 最终仍把非 GET、`/api/*`、`/robots/*`、commands、ACK、diagnostics、collect/dropoff/cancel 全部归为动态控制面，并用 `fetch(event.request, { cache: "no-store" })` 绕过缓存；summary 里的 `service_worker_static_assertions` 对应检查全部为 `true`。
- 生成的 `mobile_pwa_fresh_browser_proof_summary.json` 两个 viewport 均为 `passed=true`，`ack_not_delivery_success=true`，`service_worker_dynamic_no_store_status=passed`，`console_zero_status=passed`，`console_error_count=0`，并保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### 验收命令结果

```text
$ rg -n "cmd_vel|ACK|ack|diagnostics|/api/|/robots/|cache: .no-store.|no-store|mobile_pwa_fresh_browser_proof|safe_to_control|primary_actions_enabled|delivery_success|do_POST|send_response|fetch\(" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/service-worker.js mobile/web/app.js docs/product/mobile_user_flow.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence/mobile_pwa_fresh_browser_proof_summary.json
命中 6739 行，关键命中：
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:21 ack_not_delivery_success=true
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:61 statusCacheControl=no-store
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:62 diagnosticsCacheControl=no-store
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:73 ack_bypass=true
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:74 diagnostics_bypass=true
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:210 delivery_success=false
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:211 primary_actions_enabled=false
sprints/.../mobile_pwa_fresh_browser_proof_summary.json:212 safe_to_control=false
mobile/web/service-worker.js:24 后端状态、诊断、机器人命令和 ACK 都是动态控制面，必须 no-store。
mobile/web/service-worker.js:26 path.startsWith("/api/")
mobile/web/service-worker.js:27 path.startsWith("/robots/")
mobile/web/service-worker.js:29 path.includes("/ack")
mobile/web/service-worker.js:30 path.includes("/diagnostics")
mobile/web/service-worker.js:31 path === "/api/collect"
mobile/web/service-worker.js:32 path === "/api/dropoff/confirm"
mobile/web/service-worker.js:33 path === "/api/cancel"
mobile/web/service-worker.js:86 event.respondWith(fetch(event.request, { cache: "no-store" }));
pc-tools/evidence/phone_browser_acceptance_gate.py:258 def do_GET(self):
pc-tools/evidence/phone_browser_acceptance_gate.py:267 if parsed.path == "/api/status":
pc-tools/evidence/phone_browser_acceptance_gate.py:270 if parsed.path == "/api/diagnostics":
pc-tools/evidence/phone_browser_acceptance_gate.py:393 def service_worker_static_assertions():
pc-tools/evidence/phone_browser_acceptance_gate.py:815 fetch('/api/status?fresh_browser_probe=1', {cache: 'no-store'})
pc-tools/evidence/phone_browser_acceptance_gate.py:822 fetch('/api/diagnostics?fresh_browser_probe=1', {cache: 'no-store'})
pc-tools/evidence/phone_browser_acceptance_gate.py:1180 delivery_success=False
pc-tools/evidence/phone_browser_acceptance_gate.py:1181 primary_actions_enabled=False
pc-tools/evidence/phone_browser_acceptance_gate.py:1182 safe_to_control=False
未发现 do_POST 命中。
```

```text
$ git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof
通过；无输出。
```

### 失败定位

- 未发现 Robot 控制边界失败。
- 未发现 ACK 发送、robot command path、`/cmd_vel` 控制入口、动态控制请求缓存/重放、或 service-worker 控制策略放宽。

### 剩余风险

- 该复核仍是静态/control-boundary acceptance 加本地 evidence artifact 复核；它不等同于真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云/4G、Nav2/fixed-route、WAVE ROVER/UART/HIL、PR #4 field pass、PR #5 real materials、dropoff/cancel completion 或 delivery success。
- fresh proof 的 diagnostics probe 是本地 fixture GET no-store 探针；若未来把 gate 指向真实 backend，应重新确认 diagnostics endpoint 仍无副作用。

## Product Closeout

Run time: 2026-05-19 14:29 Asia/Shanghai。

### 用户价值和产品北极星

本轮把上一轮 cache recovery 留下的旧日志噪声收成可复核的 fresh browser proof：现场 owner 在进入真实手机验收前，可以用独立 Chromium profile 证明当前 `mobile/web` shell 可干净打开、无 console/runtime error、service-worker 不缓存动态控制面，且 Start Delivery、Confirm Dropoff、Cancel 仍 fail closed。

产品北极星保持不变：普通用户的手机入口必须显示当前可信状态和安全边界，而不是被旧 PWA cache 或旧 console log 误导；控制动作必须在缺少真实材料时保持关闭。

### OKR 映射和 KR 拆解

- Objective 4 KR7：记录 `mobile_pwa_fresh_browser_proof` 作为真实手机/browser 验收前的本地软件护栏。该证据只覆盖本机 fresh Chromium profile、两档 viewport、console-zero、service-worker cache recovery marker、dynamic no-store/bypass 和 phone-safe fail-closed copy。
- Objective 5：保持约 68%，本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。
- Objective 1：保持约 81%，本轮没有 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF 材料。
- Objective 2 / Objective 3：保持约 99%，本轮没有 PR #4 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、dropoff/cancel completion、delivery result 或 `delivery_success=true`。

### 本轮核心抓手和责任 Engineer

- Full-Stack Engineer：已完成 fresh browser proof gate、tests、product doc 和 evidence artifacts。
- Robot Platform Engineer：已完成控制边界复核，确认没有新增 robot command path、`/cmd_vel`、ACK 发送或动态控制缓存/重放风险。
- Product Manager / OKR Owner：本段负责 Product closeout，并继续更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

### 优先级、验收口径和证据链

- P0 验收通过：`python3 mobile/web/test_mobile_web_entrypoint.py` 报告 `Ran 127 tests ... OK`；`py_compile`、`node --check mobile/web/app.js`、`node --check mobile/web/service-worker.js` 通过；fresh browser gate 在 `390x844` 和 `768x900` 均 `passed=true`、`console_error_count=0`、summary `ok=true`。
- Product 验收口径：本轮可写入 Objective 4 local fresh browser proof，但不得写成真实手机/browser acceptance、production app、真实 PWA prompt/user choice、O5 external proof、O1 HIL、PR #4 field pass、PR #5 real materials、dropoff/cancel completion 或 delivery success。
- 必须保留：`software_proof_docker_mobile_pwa_fresh_browser_proof_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### 剩余风险

- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实 phone/browser acceptance 仍未证明。
- Objective 5 真实外部材料、Objective 1 WAVE ROVER/UART/HIL 和 PR #5 真实 2D LiDAR / ToF 材料仍未补齐。
- PR #4 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery result 和 delivery success 仍未证明。
