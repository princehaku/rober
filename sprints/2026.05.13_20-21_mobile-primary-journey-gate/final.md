# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - Final

## 结论

本 sprint 完成 `software_proof_docker_mobile_primary_journey_gate`。Task A 把 `mobile/web/` 首屏推进为普通用户可理解的“三步主路径”，Task B 补齐 robot metadata-only compatibility fence，Product closeout 已把证据同步到 sprint 留档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 实际改动汇总

Task A `full-stack-software-engineer`：

- 改动 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`。
- 首屏新增目标垃圾站、已放入垃圾确认、发车安全 gate。
- Start gate 消费 destination、手动 load confirmation、`command_safety`、cloud/device/browser readiness、operation log、action feedback。
- `/api/collect` payload 保留 `target`，ACK 保持 accepted/processing only。

Task B `robot-software-engineer`：

- 改动 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`。
- 新增 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` metadata-only fence。
- metadata-only response 不触发 collect/confirm_dropoff/cancel、不 POST ACK、不推进或持久化 cursor。
- valid collect + mixed metadata 只执行 command envelope，未改 production `remote_bridge.py`。

Task C `product-okr-owner`：

- 创建 `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前进度快照和 `docs/process/okr_progress_log.md`。

## 验证结果

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 15 tests in 0.004s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

scoped git diff --check
exit 0
```

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 106 tests in 53.759s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

scoped git diff --check
exit 0
```

Task C closeout 验证见本轮最终执行输出。

## OKR 最低优先级核对回顾

tech-plan 记录的最低完成度 Objective 是 Objective 5，约 68%。本 sprint 没有直接针对 Objective 5，理由是当时没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。

收口时该理由仍成立：Task A/B 没有新增真实外部 O5 材料，只有 Docker/local `mobile/web` 主路径和 robot metadata-only fence。因此本轮不重复消费 O5 blocker，不提升 Objective 5；Objective 4 可基于手机主路径 software proof 从约 72% 谨慎上调到约 73%。Objective 1/2/3 不调整。

## 证据边界

`software_proof_docker_mobile_primary_journey_gate` 是 Docker/local software proof，只证明：

- `mobile/web/` 能渲染目标垃圾站、已放入垃圾确认、发车安全 gate。
- Start 在缺字段、blocked、offline、pending ACK、manual takeover、缺 destination 或未确认 load 时 fail closed。
- `/api/collect` 仍保留 `target` 兼容。
- robot metadata-only response 不触发 command、不 POST ACK、不推进或持久化 cursor。

明确 `not_proven`：这不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。

ACK、HTTP accepted 和 action receipt 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed、Nav2/fixed-route success、WAVE ROVER movement、HIL pass 或 true task completion。

## 剩余风险

- Objective 5 仍缺真实外部材料，保持约 68%。
- 真实手机设备、production app、真实 PWA install prompt 仍未验收。
- 真实公网/4G/OSS/CDN/production DB queue 仍未验收。
- Nav2/fixed-route、WAVE ROVER、HIL、真实投放和真实送达仍未验收。
