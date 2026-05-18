# Sprint 2026.05.18_09-10 Route Task Field Retest Acceptance Brief - Tech Plan

## 1. 执行策略

本轮是 Epic sprint，必须并行启动 3 个 owner 子 agent：Autonomy、Robot、Full-stack。三个 owner 文件范围互不重叠，接口通过 `route_task_field_retest_acceptance_brief` summary schema、safe `evidence_ref`、`software_proof_docker_route_task_field_retest_acceptance_brief_gate` 和 Robot/mobile alias 对齐。

Product Owner 只负责本计划、验收口径和后续留档，不直接修改产品代码、测试代码或硬件配置。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：否。
3. 不针对理由：Objective 5 下一步真实进展需要至少一种外部材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof。本机只有 Docker，O5 stop rule 继续成立，继续堆本地 metadata depth 不会产生有效 OKR 进展。
4. 下一个不选 Objective 1 的理由：Objective 1 约 81%，但最近 2026.05.17_20-21 到 23-24 已连续消费 WAVE ROVER/HIL 本地包装，当前仍无真实串口 `/dev/ttyUSB*`、`feedback_T1001`、`/odom`、`/imu`、`/battery` 或 operator HIL report。本轮不得继续包装同一硬件 blocker。
5. 本轮选择：继续 PR #4 merged 后的 route/elevator field materials 回填路线，针对 Objective 2 / Objective 3 / Objective 4 的 actionable gap：`route_task_field_retest_acceptance_brief` 的 PC/Robot/mobile contract 一致性。
6. PR #5 处理：PR #5 review 指出的 hardware baseline / 2D LiDAR / ToF / vendor-source 问题真实材料仍缺，本轮不做硬件材料包装，避免把 software proof 写成 SKU/source/receipt/install/wiring/calibration/HIL-entry 证据。

## 2. 当前事实和接口缺口

- PC evidence 已有 `pc-tools/evidence/route_task_field_retest_acceptance_brief.py` 和 `pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py`，但缺顶层 `tests.test_route_task_field_retest_acceptance_brief` 入口。
- `docs/product/mobile_user_flow.md` 和 `mobile/web/app.js` 已声明/消费 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`。
- Robot diagnostics 已有 `summarize_route_task_field_retest_acceptance_brief` 和 `route_task_field_retest_acceptance_brief` / `route_task_field_retest_acceptance_brief_summary` 输出，但 `status_payload` 仍需补 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` alias。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，并只归入 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。

## 3. 并行 owner 分工

### Autonomy Algorithm Engineer

文件范围：

- `tests/test_route_task_field_retest_acceptance_brief.py`
- `pc-tools/evidence/README.md` 或 `pc-tools/README.md` 中与 acceptance brief gate 直接相关的小段落
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/tech-done.md` 中 Autonomy 小节

任务：

- 新增顶层 unittest wrapper，使 `python3 -m unittest tests.test_route_task_field_retest_acceptance_brief` 调到既有 `pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py`。
- 核对 PC gate fail-closed contract：unsupported schema、缺 safe `evidence_ref`、evidence_ref mismatch、drill console 未 ready、unsafe copy、success wording、`delivery_success=true`、`primary_actions_enabled=true` 必须保持 blocked/not_proven。
- 必要时同步 README，只写 acceptance brief gate 的命令和证据边界，不扩展硬件或云证明。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_brief.py tests/test_route_task_field_retest_acceptance_brief.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_brief
rg -n "route_task_field_retest_acceptance_brief|software_proof_docker_route_task_field_retest_acceptance_brief_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
git diff --check -- pc-tools tests sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
```

### Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/tech-done.md` 中 Robot 小节

任务：

- 在 diagnostics `status_payload` 中补齐 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` safe alias，值应为 sanitized `route_task_field_retest_acceptance_brief_summary`。
- focused unittest 覆盖 alias、缺输入 blocked、summary-only source、nested wrapper、unsafe fields 和 disabled actions。
- 保持所有技术注释为中文，新增复杂逻辑注释解释为什么只输出 safe alias，不读取 raw artifact/control payload。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_acceptance_brief|robot_diagnostics_route_task_field_retest_acceptance_brief_summary|software_proof_docker_route_task_field_retest_acceptance_brief_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
git diff --check -- onboard/src/ros2_trashbot_behavior sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
```

### User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/tech-done.md` 中 Full-stack 小节

任务：

- 验证 mobile/web 从 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` 读取 acceptance brief；若现有逻辑已覆盖，只补 fixture/test 证据。
- 保持 panel 只读展示：acceptance status、safe evidence ref、pass/fail criteria、required evidence packet、owner handoff、safe copy、boundary。
- 确保 Start Delivery、Confirm Dropoff、Cancel 仍不被 acceptance brief 打开；copy/export 只包含 whitelist metadata。
- 同步 `docs/product/mobile_user_flow.md` 中 Robot alias、evidence boundary 和 not_proven 表述；不得写成真实 phone/browser proof。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_brief|robot_diagnostics_route_task_field_retest_acceptance_brief_summary|software_proof_docker_route_task_field_retest_acceptance_brief_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
```

## 4. 集成验收

三个 owner 返回后，Product Owner 只做证据核对和 sprint 留档，不直接修产品代码。若任一验证失败，必须把失败定位和重试任务交回对应 owner。

集成验收命令：

```bash
rg -n "route_task_field_retest_acceptance_brief|robot_diagnostics_route_task_field_retest_acceptance_brief_summary|software_proof_docker_route_task_field_retest_acceptance_brief_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web docs/product/mobile_user_flow.md sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
git diff --check -- pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web docs/product/mobile_user_flow.md sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief
git diff --stat
```

## 5. 风险边界

- 本轮只证明 repo-local / Docker-local software proof，不证明真实 route/elevator field pass。
- 本轮不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- `delivery_success=false` 和 `primary_actions_enabled=false` 是验收硬门槛，任何 enabled action 或 success phrasing 都必须 fail closed。
- 若 broad `git diff --check` 被无关 whitespace noise 阻塞，只使用 touched-file scoped diff check，并在 `tech-done.md` 写明。
- 完成后若仅有 software proof，`OKR.md` 进度不应大幅提升；closeout 只能保守更新证据链与缺口。

## 6. 本轮不创建的文档

规划阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。实现未完成前不得预生成 `tech-done.md`、`side2side_check.md` 或 `final.md`。
