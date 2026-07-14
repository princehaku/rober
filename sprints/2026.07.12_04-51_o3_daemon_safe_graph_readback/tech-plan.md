# Tech Plan - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target: execute daemon-safe stop/start + 8s graph readback as the previous artifact `next_live_command` equivalent and preserve a same-run no-motion artifact.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 当前只剩真实 production/external evidence 缺口，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external production readback。support-only、readback、wrapper、probe-only 和 readiness packet 已不能继续计分。本轮继续 O3/O1 no-motion lane，是因为上一轮已经给出 `next_live_command` 等价 daemon-safe stop/start + 8s graph readback；这是当前环境里唯一能继续缩短 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence 前置 blocker 的有效动作。

## OKR 映射和方向判断

- 用户价值和产品北极星：让现场调试继续朝同 run 可执行路线闭环推进，而不是停在 support-only surface。北极星仍是普通手机用户一键发车完成固定路线送垃圾。
- 方向判断：`继续` O3/O1 no-motion runtime recovery。
- O5 判断：`暂停` support-only/readback/wrapper 计分动作。
- O6/O7 判断：`暂停` 新 surface 或 consumer-only 工作。
- KR 历史归档：本轮计划阶段 `不归档`。只有出现 mission-grade same-run evidence 才能进入 closeout 归档判断。

## KR 拆解

1. KR-A：执行 daemon-safe stop/start + 8s graph readback，拿到 same-run artifact。
2. KR-B：在 artifact 中明确 daemon status、node list、topic list、lifecycle visibility 和 next step。
3. KR-C：全程保持 no-motion false fields，不把 graph readback 误算为 path generation、route execution、delivery、HIL 或 production success。

## 本轮核心抓手

### 1. 执行上一轮 `next_live_command` 等价动作

围绕上一轮 final 建议的命令序列，执行 daemon-safe 版本的：

- `ros2 daemon status`
- `ros2 daemon stop`
- `ros2 daemon start`
- `timeout 8 ros2 node list`
- `timeout 8 ros2 topic list`

输出需要进入本 sprint artifact，至少包含 return code、elapsed time、timeout boundary 和 stdout/stderr tail。

### 2. 把 8s graph readback 固化为可复验 artifact

artifact 必须能回答：

- daemon state 是否恢复；
- graph list 是否恢复；
- lifecycle/localization 是否仍 blocked；
- 下一条 live command 是继续 lifecycle/localization gate，还是继续 daemon/DDS/runtime split。

### 3. 保持 no-motion 围栏

graph/lifecycle/localization ready 前，严格保持：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## Engineer Assignment

主责：`robot-software-engineer`

原因：当前任务集中在 ROS2 runtime helper、artifact 合同、targeted tests 和导航文档，同一 owner 可以单线闭环，不需要并行拆给其他角色。

## 允许工程文件范围

Implementation owner 允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/tech-done.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/`

Implementation owner 不允许修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 任何历史 sprint 文件
- 产品代码、测试代码、硬件配置、launch 参数范围外文件
- O5/O6/O7 support-only code path

## 接口影响

- helper artifact 允许 additive 扩展，但不能破坏既有字段读取。
- 文档同步仅限导航/no-motion 读法，不扩展到 O5/O6/O7 surface。
- Safety contract 保持 fail-closed。

## 验收命令

Implementation owner 应执行并在 `tech-done.md` 记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

true-board no-motion helper 应围绕上一轮 `next_live_command` 等价动作产出 artifact；如果 board 不可达，也必须留下 fail-closed 结果和失败边界。

本轮 Product 计划文档验收命令：

```bash
rg -n "sprint_type: epic|daemon-safe|8s graph|OKR 最低优先级核对|robot-software-engineer|path_generation_attempted=false|safe_to_control=false" sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback
```

```bash
git diff --check -- sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback
```

## No-Motion Boundary

graph/lifecycle/localization ready 前不得尝试：

- `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- WAVE ROVER UART
- 任何 robot motion / route execution / delivery action

如果 artifact 或日志显示上述动作发生，本轮直接判为越界，不可验收。

## Product Closeout 口径

closeout 时必须按下面规则判断：

1. 只有出现 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence，才允许调整 `OKR.md` 百分比。
2. 如果只得到 daemon-safe graph/lifecycle/localization supporting artifact，则 `OKR.md` 百分比继续 `不调整`。
3. 如果没有 mission-grade evidence，则 `不归档` KR，仍只记录为 O3/O1 supporting diagnostic delta。
4. 如果 daemon-safe stop/start + 8s graph readback 没有比上一轮提供更窄的 blocker 或更明确的 next step，则 closeout 需要按“接近同一 blocker 重复消费”处理。

## 风险、阻塞和要补齐的证据链

- 风险 1：8s graph budget 仍不足，只能继续证明 timeout，而不能恢复 lifecycle visibility。
- 风险 2：daemon stop/start 成功但 node/topic graph 仍 blocked，说明 DDS/domain/runtime 仍需继续收窄。
- 风险 3：graph readback 恢复也不等于 localization ready，仍缺 `/amcl_pose`、`map->odom`、same-run path generation。
- 缺失证据链：same-run path generation、route execution、delivery/operator acceptance、current live HIL、production external evidence。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建或更新：

- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/pre_start.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/prd.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/tech-plan.md`

执行阶段完成后需要继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
