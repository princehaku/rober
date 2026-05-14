# Sprint 2026.05.14_08-09 Mobile Current PWA Retest Browser Proof - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的理由：最近 `07-08` final 与 `OKR.md` 都确认本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料。继续做本地 O5 metadata 会重复消费同一 blocker，不能形成真实外部 proof。因此本轮按 stop rule 转向 Objective 4 的当前 PWA 浏览器证据补齐。

## 技术方案

### Task A：Full-stack 当前 PWA retest browser proof

Owner：`full-stack-software-engineer`

允许改动：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/evidence/`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md`

要求：

- 将上轮 `mobile_real_device_retest_request*` 首屏 panel 纳入 browser gate 的关键元素、面板期待、boundary 期待和 JSON evidence。
- 新证据边界使用 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`，保留旧 current PWA/browser proof boundary 作为兼容说明。
- 运行 focused browser gate，输出 390x844 和 768x900 截图/JSON/summary。

验收命令：

```bash
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/evidence
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md
```

### Task B：Robot metadata-only compatibility fence

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md`

要求：

- 补充 current PWA retest browser proof metadata 与 retest request metadata 的 metadata-only / valid-command mixed fence。
- 证明该 metadata 不触发 collect、confirm_dropoff、cancel、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 不改变 runtime command 语义，只补契约围栏和接口文档。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md
```

### Task C：Product closeout

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/side2side_check.md`
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/final.md`

要求：

- 等 Task A/B 返回后再更新 OKR 和 closeout。
- 明确 Objective 5 最低但因外部材料缺失不选的理由。
- 若 Task A/B 都通过，可谨慎上调 Objective 4；不得上调 Objective 5、Objective 1/2/3。

验收命令：

```bash
test -f sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md && test -f sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/side2side_check.md && test -f sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/final.md
rg -n "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate|Objective 5|Objective 4|not_proven|metadata-only|delivery success|真实设备复测请求|browser proof" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof
```

## 并行策略

Task A 和 Task B 文件范围互不重叠，必须并行启动。Task C 依赖 Task A/B 的验证结果，工程返回后再执行 closeout。

## 风险边界

- 本地 browser proof 仍是 Chromium-family proof，不是真实 iPhone/Android。
- retest request package 仍是下一轮真实设备复测材料请求，不是验收通过。
- Robot fence 只证明 metadata 不进入控制语义，不证明真实 robot action。
- Objective 5 仍需真实公网/4G/OSS/CDN/DB/queue/worker 证据才能继续完成度推进。
