# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - Tech Plan

## 目标

把 browser proof 从旧 `phone_browser_acceptance_gate.py` 口径迁移到当前 `mobile/web/` 静态 PWA 入口，产出本 sprint 独立 `evidence/` 下的 screenshot/json/summary，并用 robot compatibility fence 保证 browser acceptance metadata 不会被 backend 当作 command、ACK 或 cursor 消费。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 67%；次低是 Objective 4：手机用户体验与低成本量产边界，约 68%。
2. 本 sprint 不直接针对最低 Objective 5，转向 Objective 4 的真实 browser 验收缺口。
3. 理由：Objective 5 下一步必须引入真实外部云/OSS/CDN/DB/queue/4G 证据；最近两轮 `2026.05.13_12-13_cloud-db-queue-external-probe-gate` 与 `2026.05.13_14-15_oss-cdn-live-probe-gate` 已分别把 DB/queue 与 OSS/CDN 外部 probe 做成 blocked-by-design 软件证明。当前 Docker-only 主机没有这些外部条件，继续 O5 会重复消费同一类外部证据 blocker。因此本轮转向次低 Objective 4，补真实本地 Chromium-family browser proof / Docker-local browser software proof 缺口。

## 设计原则和证据边界

- browser proof 必须验证当前 `mobile/web/` 静态入口，不能验证旧 onboard fallback 或过时 HTML。
- evidence 写入 `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/`。
- 允许声明：真实本地 Chromium-family browser proof / Docker-local browser software proof。
- 禁止声明：真实 iPhone/Android 手机设备、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。

## Task A - Full-stack Software Engineer

Owner: `full-stack-software-engineer`

任务：
- 修复/迁移 `pc-tools/evidence/phone_browser_acceptance_gate.py`，使其服务并验证当前 `mobile/web/` PWA。
- 输出 screenshot/json/summary evidence 到 `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/`。
- 同步 `mobile/README.md`、`docs/product/mobile_user_flow.md`。
- 仅在必要时新增或调整少量 fenced unittest，避免把本轮做成测试扩张。

文件范围：
- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `mobile/test_mobile_web_entrypoint.py`（仅需要时）
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/README.md docs/product/mobile_user_flow.md mobile/test_mobile_web_entrypoint.py
```

验收口径：
- gate run 成功时，`evidence/` 下必须能看到 screenshot、JSON 和 summary。
- summary 必须写清 evidence boundary、not_proven、ACK semantics。
- 如果真实 browser 依赖缺失，必须返回失败定位和 blocked evidence，不得用 unittest 替代 browser proof。

## Task B - Robot Software Engineer

Owner: `robot-software-engineer`

任务：
- 只做 metadata-only compatibility fence。
- 如果 Task A 引入新的 evidence boundary 或 acceptance summary 字段，更新 `docs/interfaces/ros_contracts.md` 和 remote bridge/protocol tests，证明这些字段不触发 backend action、不 POST ACK、不推进内存 cursor、不持久化 `last_terminal_ack_id`。
- 如果 Task A 没新增后端字段，只读确认并在 `tech-done.md` 报告无需 robot runtime 改动。

文件范围：
- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

验收口径：
- 新 metadata 字段不得进入 command/status/ACK envelope。
- remote bridge 不得因为 browser acceptance evidence 推进 cursor、POST ACK 或写 `last_terminal_ack_id`。
- 如果无需改动，必须把“无 runtime 改动”和依据写入 Task B 返回结果。

## Task C - Product OKR Owner

Owner: `product-okr-owner`

任务：
- 等待 Task A/B 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 根据 A/B evidence 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 收口时明确 Objective 4 是否可保守上调；如果 browser gate 未跑通，则不得上调 OKR，只记录 blocked evidence。

文件范围：
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/tech-done.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/side2side_check.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_16-17_mobile-web-browser-proof-gate
```

验收口径：
- `tech-done.md` 必须记录 Task A/B 实际改动、验证结果、偏差和剩余风险。
- `side2side_check.md` 必须对照用户验收：真实本地 browser proof 是否落盘、是否仍未证明真机/production app/PWA install prompt。
- `final.md` 必须回顾本轮不做 O5 的理由是否仍成立，并写清下一步。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 只按实际证据更新，不得把 browser proof 写成真实手机或 production app。

## 并行执行要求

- Task A 与 Task B 可并行启动；Task B 若需要 Task A 字段清单，可先做只读接口边界确认，再根据 A 输出补一次 fence。
- Task C 必须等待 Task A/B 返回后再收口。
- 主节点只做任务派发、等待、验收和 sprint 留档整合；产品代码、测试代码和工程验证由对应子 agent 完成。

## 风险和回滚边界

- 不回滚他人改动；若文件已有并行改动，子 agent 必须适配并在返回中说明。
- 只修改列出的文件范围；不得扩大到硬件、Nav2、cloud relay production runtime 或真实凭证配置。
- 若 browser 依赖不可用，本轮以 blocked evidence 收口，不能用静态 unittest 冒充 browser proof。
- 若新增 metadata 字段产生 robot compatibility regression，Task B 必须定位并修复；未修复前 Task C 不更新 OKR 完成度。
