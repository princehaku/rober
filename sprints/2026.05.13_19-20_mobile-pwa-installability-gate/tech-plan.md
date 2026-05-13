# Sprint 2026.05.13_19-20 Mobile PWA Installability Gate - Tech Plan

## 目标

建立 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`：在 Docker/local cloud-relay hosted URL 上验证 `mobile/web/` PWA 的 manifest、service worker、offline shell、asset route、browser evidence bundle 和 fail-closed 主操作，并用 robot compatibility fence 证明 installability/browser metadata 不会污染 command、ACK 或 cursor。

## 架构和接口边界

- Full-stack 负责手机入口和浏览器/PWA gate：只处理 `mobile/web/`、phone-safe fixture、browser evidence script、cloud-hosted static route 相关测试和产品文档。
- Robot 负责 metadata-only compatibility fence：只处理 remote bridge/protocol 测试与 ROS/remote contract 文档，不改真实动作执行语义。
- Product 负责 closeout：只在 A/B 返回后更新 sprint 收口、OKR 和进度日志；本计划阶段不改 `OKR.md`。

Evidence boundary 必须统一写成 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`。任何 closeout 都必须写明它不是真实 iPhone/Android device、production app、真实 PWA install prompt、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- 本 sprint 是否针对该最低 Objective：否，本 sprint 主目标转向 Objective 4，Objective 5 只作为 cloud-relay same-origin 托管背景。
- 不针对 Objective 5 的理由：`OKR.md` 第 6 节要求如果继续 O5，下一轮必须接入至少一种真实外部材料；当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 证据。近期 `2026.05.13_17-18_o5_external-evidence-intake-gate` 已完成本地 intake gate 但无真实外部材料，`2026.05.13_18-19_cloud-hosted-mobile-web-gate` 已完成 cloud-hosted metadata gate。继续本地 O5 depth 会重复 metadata 证明。Objective 4 仍缺真实手机/browser/PWA install prompt，且 cloud-hosted PWA installability/browser gate 可在 Docker/local + browser 围栏内推进功能。
- final.md 收口时需复核：若 A/B 期间拿到真实外部 O5 材料，Product closeout 需要重新评估 Objective 5；否则本轮只考虑 Objective 4 谨慎上调。

## Task A：Full-stack cloud-hosted PWA installability/browser acceptance gate

责任 Engineer：`full-stack-software-engineer`

允许改动文件范围：

- `pc-tools/evidence/cloud_hosted_pwa_installability_gate.py`（可新建）
- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/manifest.webmanifest`
- `mobile/web/service-worker.js`
- `mobile/web/offline.html`
- `mobile/web/icon-192.svg`
- `mobile/web/icon-512.svg`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/evidence/` 下新证据文件

禁止改动：

- Robot remote bridge 生产代码。
- WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数。
- `OKR.md`、`docs/process/okr_progress_log.md`。

实现要求：

- Gate 必须服务或访问 cloud-relay hosted `mobile/web/` surface，而不是只读本地文件。
- Manifest validation 至少覆盖 `name`、`short_name`、`start_url`、`scope`、`display=standalone`、theme/background color、icons、evidence boundary。
- Service worker validation 必须证明静态 shell 和动态控制面分离：`/api/*`、`/robots/*`、commands、ACK、diagnostics 和非 GET 不进入离线缓存、不排队、不重放。
- Browser acceptance 必须保留 390x844 与 768x900 视口，检查 Start/Confirm/Cancel disabled、Diagnostics/Support available、ACK copy、browser evidence bundle、无 horizontal overflow、关键 touch target 不小于 44px。
- Evidence summary 必须写入 sprint `evidence/`，包含 `ok`、`evidence_boundary`、`hosted_url`、`manifest`、`service_worker`、`offline_shell`、`not_proven`。
- 文档必须说明这只是 Docker/local cloud-hosted browser/PWA software proof，不是真实手机设备或真实 PWA install prompt。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/cloud_hosted_pwa_installability_gate.py --output-dir sprints/2026.05.13_19-20_mobile-pwa-installability-gate/evidence
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/cloud_hosted_pwa_installability_gate.py pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
git diff --check -- pc-tools/evidence/cloud_hosted_pwa_installability_gate.py pc-tools/evidence/phone_browser_acceptance_gate.py mobile mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.13_19-20_mobile-pwa-installability-gate
```

预期输出：

- Gate summary `ok=true`。
- `evidence_boundary=software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`。
- `not_proven` 包含真实 iPhone/Android device、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实送达。

## Task B：Robot metadata-only compatibility fence

责任 Engineer：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py`
- `docs/interfaces/ros_contracts.md`

禁止改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，除非现有测试证明生产实现错误且必须最小修复；如需修复，必须在返回中单独标记。
- `cloud-relay/` runtime。
- `mobile/web/`。
- 硬件、launch、Nav2/fixed-route 配置。
- `OKR.md`、`docs/process/okr_progress_log.md`。

实现要求：

- 增加 metadata-only 样本：`cloud_hosted_mobile_pwa_installability_gate`、`pwa_installability_metadata`、`browser_installability_bundle`。
- 样本可包含 manifest/service-worker/offline-shell/browser-bundle metadata，但不得包含 command envelope。
- 验证 metadata-only response 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进 `last_ack_id`，不持久化 `last_terminal_ack_id`，不写 cursor override。
- 验证 valid collect command mixed metadata 只按 command envelope 执行动作，metadata 不改变 ACK/cursor 语义。
- 文档必须说明 installability/browser metadata 是手机/支持证据，不是 robot command、ACK、cursor、delivery success 或 HIL。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py docs/interfaces/ros_contracts.md
```

预期输出：

- remote bridge/protocol/static targeted tests `OK`。
- py_compile exit 0。
- scoped diff check exit 0。

## Task C：Product closeout

责任 Engineer：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/tech-done.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/side2side_check.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/final.md`

触发条件：

- Task A 和 Task B 都返回后执行。
- 若任一任务失败，先要求对应 Engineer 定位并重试；Product 不用失败验证直接收口。

验收命令：

```bash
test -f sprints/2026.05.13_19-20_mobile-pwa-installability-gate/tech-done.md && test -f sprints/2026.05.13_19-20_mobile-pwa-installability-gate/side2side_check.md && test -f sprints/2026.05.13_19-20_mobile-pwa-installability-gate/final.md
rg -n "software_proof_docker_cloud_hosted_mobile_pwa_installability_gate|Objective 4|Objective 5|ACK|真实 PWA install prompt|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_19-20_mobile-pwa-installability-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_19-20_mobile-pwa-installability-gate
```

## 并行启动要求

Task A 和 Task B 文件范围互不重叠，必须并行启动。Product closeout 等 A/B 完成后再执行，不与 A/B 并行改同一 sprint 收口文件。

每个 worker prompt 必须包含：

- 对应 `.codex/agents/<role>.toml` 的完整 prompt。
- 本轮任务。
- 文件范围。
- 本 tech-plan 中的验收命令。
- 输出要求：实际改动文件列表、验证命令输出、失败定位、剩余风险。

## 验证围栏

本 sprint 的验证只做围栏：

- targeted unittest。
- targeted py_compile。
- cloud-hosted PWA installability/browser gate。
- robot metadata-only compatibility fence。
- scoped `git diff --check`。

不做 broad regression、不跑真实硬件、不跑 HIL、不声称真实手机设备或 production app。

## 风险边界

- 本机没有真实硬件，不能提升 Objective 1 HIL 口径。
- 本机没有真实公网/4G/OSS/CDN/production DB queue，不能提升 Objective 5 真实外部材料口径。
- 本机 browser gate 不等于真实 iPhone/Android device behavior，也不等于真实 PWA install prompt。
- ACK、HTTP accepted 或 action receipt 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。

