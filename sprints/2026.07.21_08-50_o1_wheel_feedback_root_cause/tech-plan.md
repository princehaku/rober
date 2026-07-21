# Tech Plan：O1 轮速反馈根因诊断

## 方案概述

`robot-hardware-engineer` 单线实现一个离线、fail-closed 的诊断模块。模块不控制机器人，只把本地 vendor 源码的可核查分支、
v8 冻结 artifacts 与可选远端只读 inventory 归一为结构化 root-cause decision。其结果服务于下一次维护窗口：明确先验证
runtime firmware/`mainType`、encoder update 还是 feedback sampling，不再靠重复 motion 猜测。

## 文件范围

Engineer 只允许修改或创建以下路径：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback_root_cause.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_feedback_root_cause.py`
- `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
- `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/**`
- `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/tech-done.md`

Product 收口阶段才允许补：

- `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/side2side_check.md`
- `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

严禁修改当前 dirty WIP：`docs/product/pc_free_roam_mapping_design.md`、
`pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`pc-tools/workstation/test/App.test.ts`、`06-20`、`06-45`。

## 接口与实现步骤

1. 读取并引用 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`、`ugv_advance.h`、
   `WAVE_ROVER_V0.9.ino`、`ugv_rpi/base_ctrl.py`；用明确 symbol/line evidence 建立 vendor fact table。
2. 新模块提供 `python3 -m ros2_trashbot_hardware.wave_rover_feedback_root_cause`，参数至少包含：
   `--v8-artifact-dir`、`--vendor-source-root`、可选 `--runtime-inventory-json`、`--output`。
3. 校验 v8 identity、counts、command/feedback 时序与安全 false fields；不要修改冻结 artifacts。
4. 输出 `trashbot.wave_rover.feedback_root_cause_diagnostic.v1`。候选项必须分别记录 `status`、`evidence_refs`、
   `confidence_boundary`、`requires_maintenance`、`next_readonly_or_maintenance_action`，禁止用单一“可能是 firmware”代替证据。
5. 添加正常、缺失、冲突、非法 JSON/JSONL、危险 true、vendor symbol 缺失/冲突、runtime inventory 缺字段测试。
6. 可通过 SSH 执行一次严格只读 inventory，并写到本 sprint artifacts；只允许 `systemctl status/show/cat`、`ps`、`ss`、
   `lsof/fuser` 的只读形式、`sha256sum`、`ros2 param get/list`、`journalctl/cat/tail` 只读、GET endpoint。不得执行任何写入或
   lifecycle/control 命令。若无法证明命令只读，则跳过并记录。
7. 更新硬件文档与 `tech-done.md`，写清 vendor 来源、真实输出、首次失败/修复、零 mutation 计数和剩余维护/HIL 风险。

## 安全与 anti-repeat

- v8 authorization 已 `consumed_no_retry`，不得使用；本轮即使 CEO 重申运动授权，也不发送运动或 stop，因为本 sprint 的产品
  范围是 non-motion diagnosis。
- `motion/control/stop/nonzero/service_mutation/uart_write/firmware_mutation/retry` 全部必须为 `0`。
- 不停止或重启 `trashbot-esp32-bridge.service`；不打开 `/dev/ttyS5`；不发送 `T=11/13/130/131/900`。
- 不以 mock nonzero、源码分支或 parser pass 声明真实 encoder、HIL 或 safe-to-control。
- 本轮与 `06-20`、`06-45` loopback/browser WIP 无关，不读取其未提交结果作为根因证据。

## 验收命令

Engineer 必须运行、修复至通过并把关键原始输出写入 `tech-done.md`：

```bash
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback_root_cause.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_feedback_root_cause.py

PYTHONPATH=onboard/src/ros2_trashbot_hardware \
python3 -m unittest \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_feedback_root_cause.py

PYTHONPATH=onboard/src/ros2_trashbot_hardware \
python3 -m ros2_trashbot_hardware.wave_rover_feedback_root_cause \
  --v8-artifact-dir sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/artifacts \
  --vendor-source-root docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9 \
  --output sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json

python3 -m json.tool \
  sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json \
  >/dev/null

python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json')
d = json.loads(p.read_text())
assert d['schema'] == 'trashbot.wave_rover.feedback_root_cause_diagnostic.v1'
for key in ('hil_pass', 'safe_to_control', 'route_execution_success', 'delivery_success'):
    assert d[key] is False
assert d['motion_command_count'] == 0
assert d['service_mutation_count'] == 0
assert d['uart_write_count'] == 0
assert d['firmware_mutation_count'] == 0
print('root-cause safety assertions: PASS')
PY

python3 - <<'PY'
from pathlib import Path
p = Path('onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback_root_cause.py')
lines = [line for line in p.read_text().splitlines() if line.strip()]
comments = [line for line in lines if line.lstrip().startswith('#')]
ratio = len(comments) / len(lines) if lines else 0
print(f'chinese_comment_ratio={ratio:.2%}')
assert ratio > 0.20
PY

git diff --check -- \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback_root_cause.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_feedback_root_cause.py \
  docs/hardware/wave_rover_nonzero_feedback_hil_gate.md \
  sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause
```

若执行远端只读 inventory，还必须将完整命令 allowlist、exit code、stdout/stderr 摘要、
`motion/control/stop/nonzero/service_mutation/uart_write/firmware_mutation=0` 写入 artifact 与 `tech-done.md`。

## OKR 最低优先级核对

1. `OKR.md` 当前最低 Objective 是 O5（约 85%）。
2. 本 sprint 不针对 O5；原因是 production provider/runtime 同根因已消费 `2/2`，没有新的凭证/外部 provider 证据，继续
   本地 wrapper 会违反 anti-repeat。
3. 下一低项 O6/O7 各约 93%，但路线执行需要未获授权的 service/UART 独占维护窗口。本轮选择当前可推进且有全新根因入口的
   O1（约 95%），其输出直接降低下一次真实 HIL 的失败成本；不因此自动加分。

## 风险与停止条件

- 若只读 inventory 不能观察 runtime `mainType`/firmware identity，按 `not_observed` 收口并给出唯一 maintenance action，
  不得把缺证据当根因确认。
- 若 vendor 源与当前项目行为冲突，保留冲突并 fail closed，不改 vendor 或 firmware。
- 任一验收失败，Hardware 必须定位、修复并复验；若修复需越出 allowlist，停止并回报 Product 决策。
- 完成后交 Product 做 side-to-side 与 conservative closeout；预计主百分比 flat，KR 不归档。
