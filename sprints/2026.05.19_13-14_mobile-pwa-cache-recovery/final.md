# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - Final

## sprint_type: epic

Run time: 2026-05-19 14:20 Asia/Shanghai。

## 1. 收口结论

本轮 `mobile_pwa_cache_recovery_gate` 完成 Product closeout。Full-Stack 已实现 versioned service-worker cache recovery、network-first navigation/current shell、old mobile shell cache cleanup、offline shell refresh button，并保持 Start Delivery、Confirm Dropoff、Cancel fail-closed。Robot read-only review 未发现控制面扩大，且 cleanup narrowing 已由 Full-Stack 修正。

本轮只能记录为 Objective 4 的本地 Browser QA cache recovery `software_proof`。它不证明真实 iPhone/Android、真实 PWA prompt/user choice、production app、真实 phone/browser acceptance、Objective 5 external proof、Objective 1 HIL、PR #4 route/elevator field pass、PR #5 真实 2D LiDAR / ToF materials 或 delivery_success。

## 2. 实际改动

- Full-Stack product/code changes 已在 `tech-done.md` 留档：`mobile/web/service-worker.js`、`mobile/web/offline.html`、`mobile/web/app.js`、`mobile/web/manifest.webmanifest`、`mobile/web/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- Product closeout 更新：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 3. 验证结果

- Full-Stack 首轮：`python3 mobile/web/test_mobile_web_entrypoint.py` -> `Ran 124 tests in 0.859s OK`；`py_compile` pass；`node --check mobile/web/app.js` pass；`node --check mobile/web/service-worker.js` pass；required `rg` pass；scoped `git diff --check` pass。
- Browser validation：local `mobile/web` served and fresh in-app browser tab loaded current shell. DOM proof: `hasCurrentShell=true`、`hasOfflineShell=false`、`marker=mobile_pwa_cache_recovery`、`boundary=software_proof_docker_mobile_pwa_cache_recovery_gate`、Start/Confirm/Cancel disabled。
- Robot read-only review：dynamic control paths (`/api/*`, `/robots/*`, commands, ACK, diagnostics, non-GET) remain no-store/bypass cache；cache recovery marker is only DOM dataset/postMessage for static shell cache and no robot command path。
- Full-Stack 二次修正后：`python3 mobile/web/test_mobile_web_entrypoint.py` -> `Ran 124 tests in 0.920s OK`；`py_compile` pass；`node --check mobile/web/service-worker.js` pass；required `rg` pass；scoped diff check pass。
- Product closeout required file check、required `rg` 与 scoped `git diff --check` 需以最终命令输出为准；本文件收口后执行。

## 4. OKR 回顾

- Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof，O5 stop rule 继续成立。
- Objective 1 保持约 81%。本轮没有 WAVE ROVER/UART/HIL、`feedback_T1001`、`odom/imu/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF materials。
- Objective 4 保持约 99%。本轮只减少本地 Browser QA stale shell 噪声，不提升真实手机/browser acceptance。
- Objective 2/3 保持约 99%。本轮不证明 PR #4 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、cancel completion、delivery result 或 delivery_success。

## 5. 剩余风险和下一步证据

- 需要可清空日志的 fresh browser context 或真实设备浏览器复核，解决 in-app browser dev logs 保留恢复前旧 cached app.js console error 的证据噪声。
- 下一步若要提高 Objective 5，必须拿到真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- 下一步若要提高 Objective 1，必须拿到真实 WAVE ROVER/UART/HIL、`feedback_T1001`、`odom/imu/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF materials。
- 下一步若要提高 Objective 4，必须做真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 或真实 phone/browser acceptance。

## 6. 证据边界

本轮所有结论保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。不得把 Browser QA cache recovery、service-worker marker、offline shell refresh button、DOM proof、Robot read-only review 或 scoped tests 写成真实手机通过、真实 route/elevator field pass、HIL、production cloud proof 或真实 delivery success。
