# Sprint 2026.05.11 09-10 HIL pass and route replay crosscheck - Final

## 状态

- 阶段：final draft
- 时间：2026-05-11 16:47 Asia/Shanghai
- Owner：`autonomy-engineer`
- 结论：软件复盘闭环通过；硬件 run-level 复核仍待补

## 本轮结论

- O3 fixed-route 软件复盘对齐方向已推进：route 状态字段按 `evidence_ref` 统一复用。
- 已补齐只读对账脚本 `scripts/evidence_crosscheck.py`，用于 status/replay 与 task_record 的 run-level 回放一致性核验。
- O1 WAVE ROVER move-test 硬件 smoke 已尝试完成同一 run-level 证据 `run_20260511T094018Z_hil_pass_speed0p050_dur0p30`，但失败于主机串口缺失。
- 真机 `hil_pass` 样本尚未形成（环境约束），O3 本轮以软件复现为主，复盘脚本可用于补齐后复验。
- O2 traceability 回归已收敛：`result_path/evidence_ref/failure_code/human_intervention_required/state_transition_history` 在 operator gateway 与 diagnostics 统一优先级重算，减少单链路字段回落漂移。
- O2 细化修复：在 diagnostics 端新增 fallback 策略，`task_record` 不可读或缺失时优先取 `last_task.state_transition_history`，并为未显式声明 `evidence_ref` 的 `last_task` 维持 `result_path` 兼容回退。

## 风险与阻塞

- 无真实运行样本时，task_record 侧 route_progress 对账依赖 `nav_result.evidence` 兜底，缺字段会显示为可追踪差异而非失败吞掉。
- 缺少同一 run 的真实 task_record 文件，`evidence_ref` 联动仍需上机回放完成后补齐。
- 本轮新增 O1 风险：`/dev/ttyUSB0` 在当前执行宿主机不可见，导致 `source=hil_pass` 证据无法升级为真实串口交互样本。
- task_record 读取失败场景下，可追溯字段依赖 `latest_status/last_task` fallback；若 last_task 也缺失，应在真实 HIL 回放中补齐 task_record 以避免历史链条断层。

## 下一步

1. 在有硬件条件下，固定一轮 `evidence_ref` 并同时记录：
   - fixed-route status JSON
   - route replay jsonl
   - task_record JSON
2. O1 先恢复串口链路（如通过 `EXTRA_DOCKER_ARGS=\"--device=/dev/ttyUSB0\" bash scripts/docker_humble_dev.sh` 或本机确认真实 `/dev/ttyUSB*`）并复跑：
   - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200 --evidence-ref <new_ref>`
   - 必须产出 `command.txt`/`serial.log`/`feedback_T1001.log`/`odom_once.jsonl`/`imu_once.jsonl`/`battery_once.jsonl`
2. 用 `python3 scripts/evidence_crosscheck.py <status> --task-record <task_record> --evidence-ref <same_ref>` 验证字段闭环。
3. 若 task_record 对账仍有差异，按行为端 contract 补齐 `route_progress` 写入路径。
