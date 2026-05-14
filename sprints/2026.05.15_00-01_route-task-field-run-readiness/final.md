# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - Final

sprint_type: epic

## 收口摘要

本轮完成 `software_proof_docker_route_task_field_run_readiness_gate`。工程侧把 PC route debug console、route_task operator review、execution bundle、diagnostics 和 mobile 只读面板串成下一次真实路线-任务联跑前的 readiness handoff。

核心产物不是 delivery success，而是可执行材料清单、同一 `evidence_ref` 要求、缺失材料、可运行命令、phone/support-safe summary 和严格 `not_proven` 边界。

## 实际交付

- Task A `autonomy-engineer`：新增 `route_task_field_run_readiness` CLI/artifact 与测试，更新 PC/navigation 文档。
- Task B `robot-software-engineer`：diagnostics metadata-only 消费 readiness artifact，更新接口文档和 55 个 diagnostics tests。
- Task C `full-stack-software-engineer`：mobile/web 新增只读 field-run readiness panel，更新 fixture、entrypoint tests 和 product flow 文档。
- Task D `product-okr-owner`：完成 sprint closeout、OKR 4.1 和 progress log 更新。

## 验证结果

- Task A：py_compile pass；`test_route_task_field_run_readiness.py` `Ran 5 tests OK`；CLI `--help` pass；临时 JSON `--once-json` pass，输出 `overall_status=ready_for_field_run_materials`、`evidence_ref=file:run-001.json`、`delivery_success=false`；required `rg` pass；scoped diff check pass；untracked 新文件 `git diff --check --no-index` pass。
- Task B：py_compile pass；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics` `Ran 55 tests OK`；required `rg` pass；scoped diff check pass。
- Task C：mobile unittest `Ran 6 tests OK`；py_compile pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。
- Task D：`rg` 命中本轮 sprint、OKR/progress 目标关键词和边界词；scoped `git diff --check` 无输出，两条命令均 exit 0。

## OKR 更新

- Objective 2：约 82% -> 约 83%。理由：field-run readiness artifact + diagnostics + mobile read-only consumption 已把下一次真实路线-任务联跑材料清单、同一 `evidence_ref` handoff 和 phone-safe 复盘口径打通为软件证据。
- Objective 3：约 82% -> 约 83%。理由：固定路线/任务软件链路已从 PC route debug console 推进到可执行 field-run readiness handoff，能指导下一次真实 Nav2/fixed-route 或 fixed-route 现场材料采集。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他 external proof。
- Objective 1：保持约 75%。本轮没有真实 WAVE ROVER、串口/UART、HIL、`T=1001` feedback 或底盘实机样本。
- Objective 4：保持约 95%。手机端新增的是只读 readiness panel，不是新的真实手机设备/browser/production app 验收。

## 明确不证明

本轮不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 后续建议

下一轮按 `OKR.md` 重新排序。Objective 5 仍是最低，但若仍没有真实公网/4G/OSS/CDN/DB/queue 材料，不要继续堆本地 O5 metadata。更可执行的推进方向是使用本轮 readiness handoff 组织一次真实路线-任务 field run，采集同一 `evidence_ref` 下的 route status、task record、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary。
