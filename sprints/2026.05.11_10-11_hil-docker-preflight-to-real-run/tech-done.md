# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-11 20:04 Asia/Shanghai
- 主线：O1 HIL preflight 继续推进，O2/O3 只作为同一 `evidence_ref` 的软件支撑
- 证据口径：本轮全部为 `source=software_proof`；本机无真实 WAVE ROVER 串口，未产生 `hil_pass`

## 实际改动

- `scripts/hardware_smoke_wave_rover.py`
  - `--status` 新增只读诊断：`serial_candidate_globs`、`serial_candidates`、`pyserial_available`、`hil_ready`、`blocked_reason`、`required_evidence_files`、`source_boundary`。
  - 串口候选只读扫描 `/dev/ttyUSB*`、`/dev/ttyAMA*`、`/dev/serial*`，不打开串口、不发送 WAVE ROVER JSON。
- `docs/acceptance/hil_runbook.md`、`docs/acceptance/wave_rover_hil_evidence.md`
  - 补充 `--status` 字段语义和 `source=software_proof` 边界。
- `task_orchestrator.py` / `task_record.py` / operator diagnostics
  - 补齐 fixed-route `route_progress`、`evidence_ref`、`failure_code` 等字段的 task record 与 diagnostics 透传。
- `scripts/evidence_crosscheck.py`
  - `--task-record-dir` 参与按 `evidence_ref/result_path` 自动查找 task record。
  - task record 缺 route-level 字段时返回 mismatch。

## 验证结果

- `python3 scripts/hardware_smoke_wave_rover.py --status | rg "serial_candidates|hil_ready|blocked_reason|source_boundary"`：通过，输出 `hil_ready=false`、`blocked_reason=no_serial_candidates_found`。
- scoped `python3 -m py_compile`：通过。
- behavior targeted unittest：`Ran 42 tests ... OK`。
- scoped `git diff --check`：通过。
- `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`：失败，Docker 在解析基础镜像 `docker.io/osrf/ros:humble-desktop` metadata 时返回 `encountered unknown type text/html; children may not be fetched`，容器内 preflight 未完成。

## 偏差说明

- `tech-plan.md` 最初将本轮写成 HIL preflight 入口；用户恢复写权限后，工程子 agent 同步落了 O1 preflight 诊断和 O2/O3 same-`evidence_ref` 支撑代码。
- 并发过程中曾出现偏航目录 `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/`，已删除，避免把本轮主线从 O1 漂移到 O2。
- `OKR.md` 只记录软件证据增强，不上调 O1/O2/O3 完成度。

## 剩余风险

- 本机仍无 `/dev/ttyUSB*`、`/dev/ttyAMA*`、`/dev/serial*` 候选，真实 HIL 未执行。
- Docker/Humble 镜像构建当前被 `osrf/ros:humble-desktop` metadata 解析失败阻断，需要修复 Docker registry/cache 后再跑容器内 preflight。
- O2/O3 当前只是为真实 run 后的同一 `evidence_ref` 对账准备数据结构；没有真实 fixed-route/Nav2 行驶样本，不能关闭。
