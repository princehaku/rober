# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - Tech Plan

## 文档阶段门禁

- 前置文档：`prd.md`
- 当前阶段：`tech-plan.md`
- 本阶段完成条件：下一阶段 owner、文件范围、接口影响、验收命令和风险边界清晰。
- 下一阶段：由 `hardware-engineer` 执行 `tech-done.md`，记录 docker preflight 与真实硬件 run 结果。

## 总体技术方案

本轮技术路线是两段式门控：

1. **Docker preflight**：先在 Humble 容器中验证脚本、依赖、参数、evidence 写入和命令可执行性。该阶段不接触真实硬件，结果只能作为 `software_proof` 或 `preflight_pass`。
2. **Real run**：在真实 WAVE ROVER 串口设备可见后，通过 docker 映射设备并执行 `hardware_smoke_wave_rover.py --move-test`，生成同一 `evidence_ref` 的真实 evidence packet。该阶段才可能产生 `source=hil_pass`。

硬件事实来源采用 `docs/vendor/VENDOR_INDEX.md`：

- WAVE ROVER 上下位通信为 UART newline-delimited JSON。
- vendor Raspberry Pi 示例为 `/dev/ttyAMA0` at `115200`，但 Orange Pi 实际串口设备名必须上机确认。
- ROS2 侧不得硬编码 Raspberry Pi 串口路径；真实 run 通过参数传入设备名。

## 执行拆分

### P0：Docker preflight

- Owner：`hardware-engineer`
- 文件范围：
  - 允许读取：`scripts/docker_humble_build.sh`、`scripts/docker_humble_dev.sh`、`scripts/hardware_smoke_wave_rover.py`、`docs/vendor/VENDOR_INDEX.md`、`docs/acceptance/*`
  - 允许更新：当前 sprint 后续 `tech-done.md`
  - 不允许修改：本轮入口文档以外的代码/配置，除非 CEO 另开实现任务
- 预期动作：
  - 构建或复用 `ros-rbs-humble:dev`。
  - 在容器中运行 smoke 脚本 `--help`、`--status`、`py_compile`。
  - 记录 docker preflight 输出、退出码和证据目录写入能力。
- 通过标准：
  - preflight 命令退出码为 0。
  - 文档明确该结果不是 `hil_pass`。

### P0：真实串口 real run

- Owner：`hardware-engineer`
- 前置条件：
  - 宿主机能看到真实串口设备，例如通过 `ls -l <real_serial_device>` 确认。
  - docker 通过 `EXTRA_DOCKER_ARGS="--device=<real_serial_device>"` 或等价方式映射串口设备。
  - 设备名、baudrate、命令模式按 `docs/vendor/VENDOR_INDEX.md` 与本机实际环境确认，不凭记忆写死。
- 预期动作：
  - 生成新的 `evidence_ref`。
  - 运行低速短时 move-test。
  - 收集 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 通过标准：
  - 串口打开成功。
  - 至少出现可追溯的底盘 feedback/T1001 与 ROS topic 样本。
  - evidence packet 中标注 `source=hil_pass`，且不是 09-10 的 blocked 占位文件。

### P1：O2/O3 同 evidence_ref 消费

- Owner：`robot-software-engineer`、`autonomy-engineer`
- 前置条件：
  - O1 real run 已形成真实 `hil_pass` evidence packet。
- 预期动作：
  - O2：用同一 `evidence_ref` 对齐 task_record、failure_code、state_transition_history、human_intervention_required。
  - O3：用同一 `evidence_ref` 对齐 fixed-route status、route replay、checkpoint/current_index/target。
- 通过标准：
  - 若无真实 run，O2/O3 保持 `software_proof`。
  - 若真实 run 存在，才允许进入 run-level 对账。

## 接口影响

- 本计划不直接修改 ROS2 topic/action/srv、launch 参数、硬件驱动或任务状态机。
- 本计划只定义下一阶段执行边界；任何代码、配置或硬件参数变更必须由对应 Engineer 子 agent 在后续实现任务中完成，并更新 `tech-done.md`。

## 验收命令（本阶段门禁）

| 层级 | 命令 | 预期 |
| --- | --- | --- |
| 文档存在 | `test -f sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/pre_start.md && test -f sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/prd.md && test -f sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/tech-plan.md` | 退出码 0 |

## 后续建议命令（由 `hardware-engineer` 执行，不作为本阶段验收）

```bash
bash scripts/docker_humble_build.sh
```

```bash
docker run --rm -v "$PWD:/ws" -w /ws ros-rbs-humble:dev bash -lc \
  "python3 scripts/hardware_smoke_wave_rover.py --help && \
   python3 scripts/hardware_smoke_wave_rover.py --status && \
   PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py"
```

```bash
EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh
python3 scripts/hardware_smoke_wave_rover.py \
  --move-test \
  --test-speed 0.05 \
  --test-duration-s 0.3 \
  --serial-port <real_serial_device> \
  --baudrate 115200 \
  --evidence-ref <new_hil_run_ref>
```

## 风险边界

- 本机只有 docker，无真实硬件；本阶段不能产生 `hil_pass`。
- 09-10 的 `/dev/ttyUSB0` 不存在是已知 blocked 证据，不应重复包装成新结果。
- 真实设备名可能不是 `/dev/ttyUSB0`；必须由上机发现结果决定。
- docker preflight 通过只能说明执行环境可用，不能证明 WAVE ROVER 运动、`T=1001` feedback 或 ROS topic 样本有效。
- O2/O3 software proof 不能越过 O1 real run gate。

## 本文件 Gate

- `tech-plan.md` 已明确 owner、范围、接口影响、验收命令与风险边界。
- 允许后续由 `hardware-engineer` 进入执行阶段并更新 `tech-done.md`。
