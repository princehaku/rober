# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - Side2Side Check

sprint_type: epic

## 用户价值对照

本轮目标是让现场验收人员不依赖开发者工具、日志或内部 JSON，也能从手机 PWA 拿到 PWA install prompt evidence 的可复制/可下载材料。Task A 已把 `mobile_pwa_install_prompt_evidence_export*` 落到手机端 export/copy/download；Task B 已证明同一 family 在 Robot 侧是 metadata-only，不会变成控制授权。

产品北极星保持不变：手机端是普通用户唯一入口，但 support/acceptance metadata 不能被写成 robot control grant、真实交付证明或真实手机验收通过。

## 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| export/copy/download 只包含白名单字段 | 通过 | Task A evidence 记录 copy/download 共用 whitelist-only JSON；`docs/product/mobile_user_flow.md` 已同步字段和敏感字段禁入清单。 |
| `safe_to_control=false` 稳定保留 | 通过 | Task A evidence、fixture/test/doc 均覆盖；Task C required `rg` 覆盖。 |
| `accepted_processing_only_not_delivery_success` 稳定保留 | 通过 | Task A evidence、mobile docs、OKR closeout 均保留 ACK 非 delivery success 口径。 |
| 缺真实设备或真实 prompt 时显示 `not_proven` | 通过 | Task A blocked-by-design fallback 与 product docs 均要求 `not_proven`。 |
| Start/Confirm/Cancel 继续 fail closed | 通过 | Task A 明确不放行主操作；Task B 证明 metadata-only 不触发 robot action。 |
| Robot metadata-only 不触发控制、ACK、cursor 或 delivery result | 通过 | Task B targeted remote bridge/protocol unittest `Ran 191 tests OK`。 |
| docs 同步 | 通过 | `docs/product/mobile_user_flow.md` 已包含 export 行为；`docs/interfaces/ros_contracts.md` 已由 Task B 同步 Robot contract。 |

## OKR 最低优先级回顾

`tech-plan.md` 中的最低优先级核对仍成立：Objective 5 仍约 68%，但本机 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration 证据。继续本地 O5 metadata depth 不能移动 O5 completion，因此本轮转向 Objective 4 的真实手机验收前置材料导出。

本轮可以谨慎把 Objective 4 从约 94% 上调到约 95%，因为手机端材料链从 event capture 推进到 export/copy/download，并且 Robot compatibility fence 已闭合。Objective 5 必须保持约 68%。

## 证据边界

- 证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`
- Schema family：`mobile_pwa_install_prompt_evidence_export` / summary / copy
- Canonical schema：`trashbot.mobile_pwa_install_prompt_evidence_export.v1`
- 证据性质：Docker/local mobile software proof + Robot metadata-only compatibility proof

不证明：

- 真实 iPhone/Android device behavior
- production app
- 真实 PWA prompt/user choice
- Objective 5 external proof
- 公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration
- Nav2/fixed-route、WAVE ROVER、HIL
- dropoff/cancel completion 或 delivery success

## 未处理 TODO / 范围检查

- 未发现本轮收口需要新增 `docs/product/mobile_user_flow.md` 内容；Task A 已完成必要同步。
- Task C 未修改 `mobile/web`、fixtures、robot tests、`docs/interfaces/ros_contracts.md`、硬件、launch、Nav2 或 behavior runtime。
- 工作树中存在 A/B worker 的允许范围改动，Task C 只引用并收口，不回滚或覆盖。
