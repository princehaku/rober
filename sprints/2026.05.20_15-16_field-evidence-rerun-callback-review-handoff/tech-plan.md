# Sprint 2026.05.20_15-16 Field Evidence Rerun Callback Review Handoff - Tech Plan

## 1. 技术目标

实现 `field_evidence_rerun_callback_review_handoff`：只读消费 `field_evidence_rerun_callback_review_decision` artifact / summary，把 review decision、owner handoff、next required evidence、rerun guidance 和 blocker summary 打包成 metadata-only handoff artifact / summary。

证据边界固定为：

- `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5，因为 O5 下一步 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；Docker-only 主机无法提供。
3. 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` live 仍 unresolved / material pending，且本机没有真实 2D LiDAR / ToF / WAVE ROVER/UART/HIL 材料。
4. 本 sprint 选择 O2/O3/O4，是因为 `12-13`、`13-14`、`14-15` 已连续把现场证据链推进到 callback review decision；本轮是该链路的下一跳 handoff，不是重复缺真实材料 blocker。

## 3. 文件范围与 owner

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py`
- `tests/test_field_evidence_rerun_callback_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/field_evidence_contracts.md`（如存在；否则更新最接近的 evidence contract 文档）

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py tests/test_field_evidence_rerun_callback_review_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_field_evidence_rerun_callback_review_handoff
python3 pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py --help
rg -n "field_evidence_rerun_callback_review_handoff|software_proof_docker_field_evidence_rerun_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools tests docs/interfaces
git diff --check -- pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py tests/test_field_evidence_rerun_callback_review_handoff.py pc-tools/README.md docs/interfaces
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_status_contract.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary|field_evidence_rerun_callback_review_handoff|software_proof_docker_field_evidence_rerun_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_status_contract.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

验收命令：

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/tmp/mobile_web_status_json_check.txt
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/tmp/mobile_fixture_json_check.txt
rg -n "现场证据复跑复核交接|field_evidence_rerun_callback_review_handoff|software_proof_docker_field_evidence_rerun_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile docs/product
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

Product 在 Engineer 返回后收口，允许改动：

- `sprints/2026.05.20_15-16_field-evidence-rerun-callback-review-handoff/tech-done.md`
- `sprints/2026.05.20_15-16_field-evidence-rerun-callback-review-handoff/side2side_check.md`
- `sprints/2026.05.20_15-16_field-evidence-rerun-callback-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
rg -n "field_evidence_rerun_callback_review_handoff|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_field_evidence_rerun_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_15-16_field-evidence-rerun-callback-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_15-16_field-evidence-rerun-callback-review-handoff
```

## 4. 接口影响

- 新增 PC schema：`trashbot.field_evidence_rerun_callback_review_handoff.v1`。
- 新增 summary schema：`trashbot.field_evidence_rerun_callback_review_handoff_summary.v1`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary`。
- mobile/web 新增只读 panel；不得改变控制动作 gating。

## 5. 风险与验证围栏

- 只跑围栏验证，不新增宽泛 regression。
- 不访问真实硬件、外部云或真实手机。
- 若任一 worker 发现验收命令失败，必须先定位并修复；不能把第一轮失败直接作为最终结果。
