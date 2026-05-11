# Sprint 2026.05.11_23-24 HIL Packet Crosscheck Bridge - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-11 23:00 Asia/Shanghai
- 主责 owner：`robot-software-engineer`
- 协作方式：`robot-software-engineer` 单线闭环实现；`hardware-engineer` 只读确认 HIL gate output contract；`autonomy-engineer` 只读确认 fixed-route status/replay 字段。

## 目标

把 `scripts/hil_evidence_packet_gate.py` 的 gate 输出接入 `scripts/evidence_crosscheck.py` 的 run-level 校验，让 O3/O2 crosscheck 能明确区分：

1. `real-run aligned`：HIL gate 输出 `status=hil_pass`，且 HIL gate、route status/replay、task record 使用同一 `evidence_ref`。
2. `blocked`：HIL gate 输出 `status=blocked`，或 gate output 缺失/不可解析/缺 `evidence_ref`。
3. `software proof only`：HIL gate 输出 `status=software_proof`，route/task 可以继续做软件复账，但不能被声明为 real-run aligned。

本轮实现阶段不得要求当前无硬件机器产生真实 `hil_pass`。

## 事实来源和近期证据

- `OKR.md` 4.1：O1 约 75%，低于 O2/O3/O4/O5；O1 仍缺真实 WAVE ROVER `hil_pass` evidence packet。
- 最新提交 `d4c4089`：已交付 `scripts/hil_evidence_packet_gate.py`，可在 Docker-only 文件层判定 HIL packet 为 `blocked`、`software_proof` 或 `hil_pass`。
- `sprints/2026.05.11_22-23_hil-evidence-packet-gate/final.md`：synthetic `hil_pass` 只是 gate 逻辑验证，不是实车证据；真实 packet 通过后，需要用相同 `evidence_ref` 连接 O2/O3 crosscheck。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 已有 same-`evidence_ref` software proof，但后续要接真实 HIL + fixed-route + task record。
- CEO 约束：本机没有真实硬件，只有 Docker；继续、功能往前走；测试只围栏；优先推进低完成度 OKR。

## 实现阶段文件范围

建议允许 `robot-software-engineer` 修改：

- `scripts/evidence_crosscheck.py`
- 最小 targeted fixture 文件或临时生成 fixture 的测试脚本，位置由 Engineer 按仓库现有模式选择
- `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/tech-done.md`

如现有测试结构适合，允许补充最小围栏测试：

- `tests/` 下与 `evidence_crosscheck.py` 直接相关的最小测试文件

禁止触碰：

- `.codex/config.toml`
- UI、operator diagnostics、Nav2 route execution、task orchestrator 状态机
- WAVE ROVER 硬件配置、launch 参数或 vendor 文件
- 宽泛测试矩阵和大范围重构

## 任务拆解

### Task 1：确认 HIL gate output contract

Owner：`robot-software-engineer`

只读咨询：`hardware-engineer`

工作内容：

- 阅读 `scripts/hil_evidence_packet_gate.py`，确认当前 machine-readable 输出字段。
- 最低需要消费字段：
  - `status`
  - `evidence_ref`
  - `blocked_reason` 或失败项列表
- 若脚本当前只向 stdout 输出 JSON，`evidence_crosscheck.py` 新增输入应读取保存后的 JSON 文件。
- 若字段名与本计划不同，按现有脚本事实适配，但必须在 `tech-done.md` 写清映射。

验收命令建议：

```bash
python3 scripts/hil_evidence_packet_gate.py --help
```

预期：只确认 CLI/output contract，不要求真实硬件。

### Task 2：为 evidence_crosscheck 增加 HIL gate input

Owner：`robot-software-engineer`

工作内容：

- 为 `scripts/evidence_crosscheck.py` 增加可选参数，例如：

```bash
--hil-gate-output <path>
```

- 当该参数存在时，读取 JSON payload 并参与 mismatch 计算。
- 当该参数缺失时，保持现有 route/task software proof crosscheck 行为，但输出不得暗示 real-run aligned。
- 当参数存在但文件缺失、不可解析或缺 `status`/`evidence_ref` 时，返回非 0。

验收命令建议：

```bash
python3 -m py_compile scripts/evidence_crosscheck.py
python3 scripts/evidence_crosscheck.py --help
```

### Task 3：实现 real-run aligned 规则

Owner：`robot-software-engineer`

工作内容：

- `hil_gate.status == "hil_pass"` 才允许进入 real-run aligned 通过路径。
- `hil_gate.status == "blocked"` 必须追加 mismatch，输出 blocked reason。
- `hil_gate.status == "software_proof"` 必须追加 mismatch，说明 software proof only。
- 未知 status 必须追加 mismatch。
- `hil_gate.evidence_ref` 必须与 route status 派生的 `evidence_ref` 一致。
- 如提供 task record，也必须继续沿用现有 task record evidence_ref 对齐逻辑。

验收命令建议：

```bash
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <hil_pass_same_ref_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <blocked_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <software_proof_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <hil_pass_wrong_ref_fixture>
```

预期：

- same-ref `hil_pass` fixture：exit 0，`CHECK summary: mismatches=0`。
- `blocked` fixture：exit non-zero。
- `software_proof` fixture：exit non-zero。
- wrong-ref `hil_pass` fixture：exit non-zero。

### Task 4：保持 O2/O3 software proof 路径清晰

Owner：`robot-software-engineer`

只读咨询：`autonomy-engineer`

工作内容：

- 不破坏现有 route status/replay/task record 对齐逻辑。
- 没有 `--hil-gate-output` 时，脚本仍可用于 software proof 围栏。
- 输出中应清楚区分 route/task alignment 和 HIL real-run alignment，避免用户把无 gate 的通过结果当成真实 HIL。

验收命令建议：

```bash
python3 scripts/evidence_crosscheck.py <existing_route_status_fixture> --task-record <existing_task_record_fixture>
```

预期：现有 software proof fixture 仍按原规则通过或失败；不新增真实 HIL 断言。

### Task 5：Sprint 执行记录和收口

Owner：`robot-software-engineer`

工作内容：

- 更新 `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。
- 结论必须写清：本轮是 crosscheck bridge ready，不是实车 HIL pass。
- 如使用 synthetic `hil_pass` fixture，只能写成 logic validation。

验收命令建议：

```bash
git diff --check -- scripts/evidence_crosscheck.py sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/tech-done.md <any_targeted_fixture_or_test_files>
```

注意：只检查 touched files，避免无关 README whitespace 干扰。

## 接口影响

- 新增 `scripts/evidence_crosscheck.py` CLI 参数，不改变 ROS2 package API。
- 不改变 WAVE ROVER UART JSON 协议语义。
- 不改变 task orchestrator、fixed-route runtime 或 operator UI contract。
- 新增逻辑只负责 run-level evidence alignment，不负责驱动底盘或生成真实 HIL packet。

## 本轮 Product 文档验收命令

本轮 Product 文档必须运行：

```bash
test -f sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/pre_start.md && test -f sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/prd.md && test -f sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/tech-plan.md
git diff --check -- sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/pre_start.md sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/prd.md sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/tech-plan.md
```

## 实现阶段围栏命令

实现 owner 必须按实际文件范围运行最小围栏：

```bash
python3 -m py_compile scripts/evidence_crosscheck.py
python3 scripts/evidence_crosscheck.py --help
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <hil_pass_same_ref_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <blocked_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <software_proof_fixture>
python3 scripts/evidence_crosscheck.py <route_status_fixture> --task-record <task_record_fixture> --hil-gate-output <hil_pass_wrong_ref_fixture>
git diff --check -- <touched files>
```

## 风险边界

- 当前机器无真实串口，不能完成真实 `hil_pass`。
- synthetic `hil_pass` fixture 只能证明 bridge logic，不得升级 OKR 完成度。
- HIL gate output 格式如仍不稳定，Engineer 需要先以最小兼容方式读取并记录映射。
- O2/O3 真正升级仍等待同一 `evidence_ref` 下的真实 HIL packet、fixed-route replay 和 task record。

## 完成前反思清单

- 是否仍以 O1 -> O3 -> O2 为主线，没有漂移到 UI 或宽泛 route 功能？
- 是否明确区分 `blocked`、`software_proof`、`hil_pass`？
- 是否让 `blocked`/`software_proof` gate output 在 real-run crosscheck 中失败？
- 是否没有在无硬件机器上声明真实 HIL 通过？
- 是否只改允许文件，且未触碰 `.codex/config.toml`？
- 是否运行了围栏命令，或记录了无法运行的具体原因？
- 是否把实现结果写入 `tech-done.md`，并在需要时更新 `side2side_check.md` / `final.md`？
