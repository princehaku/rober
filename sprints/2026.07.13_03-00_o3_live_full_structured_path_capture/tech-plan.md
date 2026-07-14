# 2026.07.13 03:00 O3 live full structured path capture - tech-plan

## 任务分工

- `robot-algorithm-engineer`: 单 owner 闭环执行本轮实现、live no-motion capture、验证、修复和 `tech-done.md`。
- `product-okr-owner`: 在算法结果返回后做 Product acceptance，更新 `side2side_check.md`、`final.md`，必要时保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 文件范围

`robot-algorithm-engineer` 可改范围：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/**`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/tech-done.md`

`product-okr-owner` 可改范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/side2side_check.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/final.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/product/**`

## 技术方案

1. 基于上轮 helper/export contract，重新运行 strict no-motion `ComputePathToPose` live capture。
2. 把本轮 live capture 的 raw artifact 和 summary 写入本 sprint artifacts。
3. 优先验证 `path_structured_pose_count=21`；如果现场输出不是 21，写清本轮新 blocker 和实际 observed count。
4. 复验 no-motion invariants：禁止 `/cmd_vel`、`/api/base/manual`、`NavigateToPose`、controller/BT、WAVE ROVER UART，所有 safety/delivery/HIL/control flags 保持 false。
5. 若 helper 需要小修才能持久化完整字段，由 algorithm owner 在文件范围内修复并补单测。

## 验收命令

`robot-algorithm-engineer` 必须运行并记录输出：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
python3 -m json.tool sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json >/tmp/live_full_structured_path_capture_summary.pretty.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path("sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json")
data = json.loads(p.read_text())
proof = data.get("proof", data)
assert proof.get("publishes_cmd_vel") is False
assert proof.get("calls_base_manual") is False
assert proof.get("uses_base_uart") is False
assert proof.get("robot_control_executed") is False
assert proof.get("route_execution_success") is False
assert proof.get("delivery_success") is False
assert proof.get("hil_pass") is False
print("live_full_structured_path_capture_safety_ok")
PY
rg -n "path_structured_pose_count|path_generated|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass|next_evidence_required|blocked_reason" sprints/2026.07.13_03-00_o3_live_full_structured_path_capture
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_03-00_o3_live_full_structured_path_capture
```

如果真实 live capture 依赖现场 host/ROS runtime 而当前 worker 环境不可访问，worker 必须：

- 写出 fail-closed summary，明确 `blocked_reason`
- 说明是否已经尝试命令、在哪一步缺权限/缺 runtime/缺网络/缺板端
- 不把历史 artifact 复用成新 live proof

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中最低 Objective 是 O5，约 85%。
2. 本 sprint 不直接针对 O5；本 sprint 针对 O1/O3 strict no-motion path proof lane。
3. 不针对 O5 的原因：O5 当前可加分条件是真实 external production evidence。当前环境没有公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实手机/browser 验收；继续做 readiness/checklist/wrapper 会第三次消费 support-only blocker。本轮选择 O1/O3 的 next additive live material，避免重复包装。

## 风险边界

- 即便 `path_structured_pose_count=21` 成立，也只证明 planner-only no-motion path material。
- 它仍不是 route execution、fixed-route movement、delivery/operator acceptance、HIL、safe-to-control 或 production cloud evidence。
- 若只能得到 fail-closed blocker，本轮 OKR 百分比保持 flat，但 blocker 必须比上一轮更窄。
