# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - Tech Done

## sprint_type: epic

Run time: 2026-05-19 13:55 Asia/Shanghai。

## Full-Stack 初步结果

### 实际改动

- `mobile/web/service-worker.js`：实现 `mobile_pwa_cache_recovery`，bump cache version 到 `2026.05.19-mobile-pwa-cache-recovery-v2`，导航和当前 shell 文件改为 network-first + `cache: "no-store"`，activate 清理旧 cache，动态 `/api/`、ACK、diagnostics 和控制请求继续 no-store。
- `mobile/web/offline.html`：离线页增加只刷新当前入口的恢复按钮，Start Delivery、Confirm Dropoff、Cancel 继续 disabled；copy 明确不发送、缓存、排队或重放控制请求。
- `mobile/web/app.js`：service worker 注册使用 `updateViaCache: "none"` 并主动 `registration.update()`；增加 app shell marker，便于 Browser QA 识别当前 shell，不参与控制授权。
- `mobile/web/manifest.webmanifest`：补充 cache recovery evidence boundary 和当前 cache recovery version。
- `mobile/web/test_mobile_web_entrypoint.py`：新增 `MobilePwaCacheRecoveryGateTest`，覆盖 cache version、activate cleanup、network-first navigation/current shell、offline recovery fail-closed 和控制请求 no-store。
- `docs/product/mobile_user_flow.md`：记录 `mobile_pwa_cache_recovery` 的 service-worker/offline shell 恢复策略与 `software_proof` 边界。

### 验证结果

- `python3 mobile/web/test_mobile_web_entrypoint.py`：通过，`Ran 124 tests in 0.859s OK`。
- `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`：通过，无输出。
- `node --check mobile/web/app.js`：通过，无输出。
- `node --check mobile/web/service-worker.js`：通过，无输出。
- `rg -n "mobile_pwa_cache_recovery|service-worker|offline shell|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery`：通过，命中 service-worker、offline shell、docs 和本 sprint evidence boundary 文案。
- `git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery`：通过，无输出。
- Browser validation：本地启动 `python3 -m http.server 8765 --directory mobile/web`，in-app browser fresh tab 加载 `http://127.0.0.1:8765/index.html?mobile_pwa_cache_recovery=1&fresh_tab=1`。DOM proof 显示 `title=rober 手机入口`、`hasCurrentShell=true`、`hasOfflineShell=false`、`marker=mobile_pwa_cache_recovery`、`boundary=software_proof_docker_mobile_pwa_cache_recovery_gate`、`startDisabled=true`、`confirmDisabled=true`、`cancelDisabled=true`。
- Browser validation 限制：in-app browser dev log API 保留了本轮恢复前旧 cached app.js 的历史 console error（`ReferenceError: nextEvidence is not defined`，timestamp `2026-05-19T05:12:08.898Z`），无法在该 API 内清空历史日志；后续 fresh tab DOM 已证明当前 app shell marker 和 fail-closed 按钮状态。独立 Chrome headless fresh profile 尝试用于 screenshot/console capture 时进程卡住，已终止并清理临时 profile；未提交截图。

### 剩余风险

- Browser validation 是本地 in-app browser DOM proof；不是真实 iPhone/Android、真实 PWA prompt/user choice、production app、Objective 5 external proof、HIL、route/elevator field pass 或 delivery success。
- in-app browser 历史 console log 仍可显示恢复前旧 cached app.js error；当前修复目标是让页面摆脱旧 offline shell 并有恢复路径，后续若需要严格 console 清零，需要 Product/Browser QA 用可清空日志的 fresh browser context 复核。
- 证据边界保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## Full-Stack 二次修正结果

### 实际改动

- Robot read-only review 提醒 activate cleanup 范围应收窄，避免删除同源其他非 rober mobile shell cache。
- Full-Stack 已修正 `mobile/web/service-worker.js`：activate 阶段只删除旧 `rober-mobile-shell-*` cache，保留当前 `CACHE_NAME` 与同源其他 cache。

### 验证结果

- `python3 mobile/web/test_mobile_web_entrypoint.py`：通过，`Ran 124 tests in 0.920s OK`。
- `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`：通过，无输出。
- `node --check mobile/web/service-worker.js`：通过，无输出。
- required `rg`：通过，继续命中 `mobile_pwa_cache_recovery`、`service-worker`、`offline shell`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- scoped `git diff --check`：通过，无输出。

## Robot 只读咨询结果

### 结论

- 未发现本轮扩大机器人控制面：dynamic control paths 仍保持 no-store / bypass cache，包括 `/api/*`、`/robots/*`、commands、ACK、diagnostics、non-GET。
- `mobile_pwa_cache_recovery` marker 仅用于 DOM dataset / postMessage 与静态 shell cache recovery，不进入 robot command path。
- Start Delivery、Confirm Dropoff、Cancel 仍 fail-closed；`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍成立。

### 剩余风险

- Robot 咨询是 post-diff read-only review，不是 ROS2 控制链路实机验证，不是 WAVE ROVER/UART/HIL，不是 PR #4 route/elevator field pass，也不是 PR #5 真实硬件材料证明。

## Product 收口判断

- 本轮可作为 Objective 4 local Browser QA cache recovery 的 `software_proof_docker_mobile_pwa_cache_recovery_gate` 记录。
- Objective 5 保持约 68%，因为没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- Objective 1 保持约 81%，因为没有 WAVE ROVER/UART/HIL、`feedback_T1001`、`odom/imu/battery` 或 PR #5 真实 2D LiDAR / ToF materials。
- Objective 4 保持约 99%，只记录本地 Browser QA recovery，不宣称真实 iPhone/Android、production app、真实 PWA prompt/user choice 或真实 phone/browser acceptance。
