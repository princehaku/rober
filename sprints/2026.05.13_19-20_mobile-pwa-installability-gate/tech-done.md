# Sprint 2026.05.13_19-20 Mobile PWA Installability Gate - Tech Done

## Sprint 类型

- `sprint_type: epic`
- 主目标：Objective 4 手机用户体验/PWA installability software proof
- 关联目标：Objective 5 仅作为 cloud-relay hosted surface 背景，不上调
- 证据边界：`software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`

## 用户价值和产品北极星

用户价值：普通用户未来打开云中转入口时，应进入同一份可安装、可离线解释、默认安全的手机 PWA；在真实手机、真实公网和 production app 尚未闭环前，团队至少需要可复现的 Docker/local hosted browser/PWA 证据，证明手机入口静态安装条件、离线壳和控制面隔离没有明显倒退。

产品北极星：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。手机入口必须让用户理解状态、异常和支持交接，同时保持 Start/Confirm/Cancel fail-closed；ACK 只能表达 accepted/processing evidence，不能写成 delivery success。

## OKR 映射

- Objective 4 KR1/KR5/KR7：cloud-hosted PWA installability gate 把 `mobile/web/` 从本地 browser proof 推进到 cloud-relay hosted URL 上的 manifest、service worker、offline shell、视口和 browser evidence bundle 可验收形态。
- Objective 5 KR1/KR6：本轮只复用上一轮 cloud-relay same-origin static hosting surface，不新增真实公网、4G、OSS/CDN 或 production DB/queue 材料，因此 Objective 5 不上调。

## 实际改动

Task A Full-stack 已完成：

- 新增 `pc-tools/evidence/cloud_hosted_pwa_installability_gate.py`，通过 cloud-relay hosted URL 验证 `mobile/web/` PWA。
- 产出 `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/evidence/cloud_hosted_pwa_installability_summary.json`，`ok=true`，`hosted_url=http://127.0.0.1:61214/`，`evidence_boundary=software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`。
- Browser checks 390x844 与 768x900 均 passed：primary actions disabled、Diagnostics/Support available、browser acceptance bundle visible/copyable、无 horizontal overflow、ACK visible 且 not delivery success。
- `not_proven` 保留真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实送达。

Task B Robot 已完成：

- 只改 remote bridge/protocol/static tests 和 `docs/interfaces/ros_contracts.md`，未改生产实现。
- 增加 `cloud_hosted_mobile_pwa_installability_gate`、`pwa_installability_metadata`、`browser_installability_bundle` metadata-only remote bridge 围栏。
- 覆盖无 command 时不触发 collect/confirm_dropoff/cancel、不 POST ACK、不推进 `last_ack_id`、不持久化 cursor；valid collect mixed metadata 只执行 command envelope。

Task C Product closeout 已完成：

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前快照、第 6 节、第 7 节。
- 更新 `docs/process/okr_progress_log.md` 顶部 19-20 条目。

## 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/cloud_hosted_pwa_installability_gate.py --output-dir sprints/2026.05.13_19-20_mobile-pwa-installability-gate/evidence
ok=true
evidence_boundary=software_proof_docker_cloud_hosted_mobile_pwa_installability_gate
hosted_url=http://127.0.0.1:61214/
browser 390x844 passed
browser 768x900 passed
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 14 tests ... OK
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py
Ran 112 tests in 52.197s OK
```

说明：Task B 返回中有一个 socket `ResourceWarning`，exit 0，不影响本轮 targeted tests 通过。

Task C 验收命令由 Product closeout 收口后执行，结果记录在 `final.md`。

## 偏差和范围控制

- 本轮没有改产品运行代码、硬件配置、Nav2/fixed-route 或 HIL 路径的 Product closeout 范围外文件。
- Objective 4 由约 70% 谨慎上调到约 72%；Objective 5 保持约 68%；Objective 1/2/3 不调整。
- 本轮证明的是 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`，不是真实手机设备验收、真实 PWA install prompt、production app、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 剩余风险

- 无真实 iPhone/Android device behavior。
- 无真实 PWA install prompt。
- 无 production app。
- 无 public HTTPS/TLS、真实 4G/cloud、OSS/CDN live traffic、production DB/queue。
- 无 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
