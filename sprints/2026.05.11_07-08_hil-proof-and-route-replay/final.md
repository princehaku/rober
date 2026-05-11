# Sprint 2026.05.11 07-08 HIL proof and route replay - Final

## 状态

- 阶段：final completed
- 时间：2026-05-11 14:47 Asia/Shanghai
- Owner：`product-okr-owner`
- 范围：仅收口当前 sprint 既有结果，不新增任务与文件范围。

## 结论

- 本轮状态：**Blocked**
- 主因：未完成 `hardware` 实机 `hil_pass` 采样，导致 O1/O3/O2 的 run-level 一致性复盘无法闭环。

## Completion classification

- Sprint overall：**Blocked**
- O1（HIL proof）：**Blocked**
- O3（route replay）：**Partial**（软件层一致性完成，缺 run-level 实跑回放）
- O2（consistency replay）：**Partial**（字段契约完成，缺 run-level 失败/超时/取消样本）
- 关键证据：`evidence/run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30/` 的 run 产物为 BLOCKED，不能视作 `hil_pass` 成功。
- 核心结果：
  1. `scripts/hardware_smoke_wave_rover.py --help`、`--status` 可执行；`py_compile` 通过。
  2. `hardware --move-test` 因 `/dev/ttyUSB0` 不存在失败：`ERROR: serial failure: [Errno 2] could not open port /dev/ttyUSB0`。
  3. `fixed_route` dry-run + `route_utils` py_compile 通过。
  4. `route_progress` 已补齐 `checkpoint/current_index/target/failure_code/evidence_ref` 一致性并支持 `evidence_ref` 覆盖复盘。
  5. `task_orchestrator/task_record` 测试与编译通过。
  6. 未产出 `command.txt / serial.log / feedback_T1001.log / odom_once.jsonl / imu_once.jsonl / battery_once.jsonl`。

## 阻塞项

1. **硬件链路阻塞（最高优先）**
   - 运行环境缺少可访问串口 `/dev/ttyUSB0`。
   - 归因：run-time 设备约束，不是软件契约本身。

2. **run-level 跑数缺失**
   - 同一 `evidence_ref` 下未形成 O1+O3+O2 一致闭环数据。
   - dry-run 阶段已完成 `route_progress` 字段一致性复盘，实车 run 复盘仍待补齐。

3. **验收边界未达成**
   - `source` 虽可枚举，但未出现成功 `hil_pass` 的实机样本。

## 下一步建议

1. 在可上机环境重跑：
   - `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`
   - 将 `evidence_ref` 统一写入 `command.txt / serial.log / feedback_T1001.log / odom_once.jsonl / imu_once.jsonl / battery_once.jsonl`。
2. 以同一 `evidence_ref` 再跑一次 fixed-route replay（需支持 route+task record 复盘）。
3. 产出一条可复查失败/超时 run-level 记录后再将 O2 视作通过。

## 是否更新 OKR 进度

- 本轮不更新 O1/O2/O3 百分比：仍保持“待实机闭环”。
- 原因：本轮无 `hil_pass` 实机样本，未能把 `software_proof` 升级为已验证实机结果。
