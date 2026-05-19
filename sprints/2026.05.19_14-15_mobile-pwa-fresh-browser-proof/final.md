# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - Final

## sprint_type: epic

Run time: 2026-05-19 14:29 Asia/Shanghai。

## 1. 收口结论

本轮 `mobile_pwa_fresh_browser_proof` 完成 Product closeout。Full-Stack 已实现 fresh Chromium profile proof、console-zero gate、service-worker dynamic no-store/bypass 检查、summary/screenshot artifacts 和 `docs/product/mobile_user_flow.md` 同步；Robot final review 已确认没有新增 robot command path、`/cmd_vel`、ACK 发送或动态控制缓存/重放风险。

本轮只证明 Objective 4 的 local fresh browser software proof，不证明真实手机/browser acceptance、production app、真实 PWA prompt/user choice、Objective 5 external proof、Objective 1 HIL、PR #4 route/elevator field pass、PR #5 real materials、dropoff/cancel completion 或 delivery success。

## 2. 实际改动

Full-Stack Task A 已完成并在 `tech-done.md` 留档：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/evidence/`

Robot final review 已在 `tech-done.md` 留档，仅更新 sprint 文档，不修改产品代码。

Product closeout 更新：

- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/side2side_check.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Full-Stack worker 报告：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 127 tests in 0.860s
OK
```

```text
python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py
passed

node --check mobile/web/app.js
passed

node --check mobile/web/service-worker.js
passed
```

Fresh browser gate：

```text
viewport=390x844 passed=true ... fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate
viewport=768x900 passed=true ... fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate
summary=.../mobile_pwa_fresh_browser_proof_summary.json ok=true evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate fresh_profile=true require_console_zero=true
```

Robot final review：

- 通过。未发现新增 robot command path、`/cmd_vel` 控制入口、ACK 发送路径或动态控制请求缓存/重放逻辑。
- 本地 fixture 只做 GET no-store probe，不提交 ACK、不推进 cursor、不触发 Start/Confirm/Cancel 或 robot command。
- Generated summary 保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

Product closeout 验收以最终命令输出为准：

- closeout file existence check
- required `rg`
- scoped `git diff --check`

## 4. OKR 收口

| Objective | 收口判断 |
| --- | --- |
| Objective 5 | 保持约 68%。O5 blocker review 结论不变：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof，不继续用本地 metadata depth 提高完成度。 |
| Objective 1 | 保持约 81%。O1 blocker review 结论不变：没有 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，也没有 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。 |
| Objective 2 | 保持约 99%。本轮不新增 PR #4 route/elevator field material，也不证明真实 dropoff/cancel completion、delivery result 或 delivery_success。 |
| Objective 3 | 保持约 99%。本轮不证明真实 Nav2/fixed-route、route completion signal、现场 task record、真实路线采集或同一 safe `evidence_ref` 上车复账。 |
| Objective 4 | 保持约 99%。可记录 local fresh browser proof：当前 `mobile/web` shell 在 fresh Chromium profile 下通过两档 viewport、console-zero、service-worker no-store/bypass 和 fail-closed 检查；但这不是真实手机/browser acceptance。 |

## 5. PR #4 / PR #5 边界

- PR #4：本轮没有 route/elevator field pass、真实电梯门状态、目标楼层确认、人工协助记录、真实 Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion 或 delivery result。
- PR #5：本轮没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，也没有 WAVE ROVER/UART/HIL 材料。
- Fresh browser proof 只能减少 Objective 4 本地软件预检噪声，不得拿来关闭 PR #4 或 PR #5 的真实材料缺口。

## 6. 剩余风险和下一步证据

剩余风险全部保持 `not_proven`：

- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 phone/browser acceptance 未证明。
- Objective 5 external proof 未证明：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 均未发生。
- Objective 1 HIL 未证明：WAVE ROVER/UART、真实 `feedback_T1001`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report 未发生。
- Objective 2 / Objective 3 现场闭环未证明：PR #4 field pass、真实 Nav2/fixed-route、真实 task record、dropoff/cancel completion、delivery result 和 delivery success 未发生。

下一轮若要提高真实完成度，必须拿真实外部或现场材料：O5 的公网/4G/OSS/CDN/DB/queue/worker/cutover，O1 的 WAVE ROVER/UART/HIL 或 PR #5 sensor materials，或 O4 的真实手机/browser field evidence。没有这些材料时，不应继续把本地 software proof 写成真实验收。
