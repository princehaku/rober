# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - Pre Start

## 轮次定位

本轮主题：把 O1 的 `hil_pass` 阻塞从“本机无串口导致 blocked”推进到“docker preflight 可复验，真实硬件 run 一到位即可执行”。

本轮只创建下一轮 sprint 入口文档，不修改 OKR、不把软件证据升级为实机通过。当前本机条件只有 docker，无真实 WAVE ROVER/ESP32/Orange Pi 串口设备；因此本轮目标是为下一位 `hardware-engineer` 建立可执行、可追责、可复跑的准入链路。

## 已读依据

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/tech-done.md`
- `sprints/2026.05.11_09-10_hil-pass-route-replay-crosscheck/final.md`

## 证据基线

| 证据 | 结论 | 本轮采用方式 |
| --- | --- | --- |
| `OKR.md` 当前快照 | O1 硬件协议可信底盘约 75%，仍缺真实 WAVE ROVER `hil_pass` evidence packet、`/odom`、`/imu/data`、`/battery` 实机样本 | O1 继续作为第一优先级 |
| 09-10 `tech-done.md` | `--help`/`--status`/`py_compile` 为 software proof；`--move-test` 因 `/dev/ttyUSB0` 不存在失败 | 下轮先做 docker preflight，再做真实串口 run |
| 09-10 `final.md` | `hil_pass` blocked，O2/O3 不得先于 O1 解除进入实机通过状态 | 本轮保持 O1 -> O2 -> O3 顺序 |
| `docs/vendor/VENDOR_INDEX.md` | WAVE ROVER 使用 UART newline-delimited JSON；vendor Raspberry Pi 默认 `/dev/ttyAMA0` 115200，Orange Pi 实际设备名需上机确认；不得硬编码 Raspberry Pi UART 路径 | 真实 run 只要求串口参数可显式传入，不在文档中猜测设备名 |

## CEO 口径

1. 聚焦 O1：HIL docker preflight -> real run。
2. 本机没有真实硬件，不能制造 `hil_pass` 结论。
3. docker 只能证明环境、脚本、依赖和命令链路可运行，不能替代 WAVE ROVER 串口交互。
4. O2/O3 当前只能保留 `software_proof`，必须等待 O1 真实 run 后再评审是否联动提升。
5. 不修改 `OKR.md`，避免用新文档启动动作虚增完成度。

## 上轮遗留与本轮处置

| 类型 | 遗留 | 本轮处置 |
| --- | --- | --- |
| P0 | `/dev/ttyUSB0` 在 09-10 执行宿主机不可见，`--move-test` 返回失败 | 将串口设备可见性写成真实 run 前置 gate，并要求 docker 使用 `EXTRA_DOCKER_ARGS="--device=<real_serial_device>"` |
| P0 | 真实 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 未形成 | tech-plan 明确真实 run 必须产出这些文件，且 source 才能标 `hil_pass` |
| P1 | O2/O3 有软件对账能力，但没有同一 run 的真实硬件样本 | 本轮只保留 O2/O3 为后续对账消费者，不作为主交付 |
| P1 | 串口设备名不能从 vendor Raspberry Pi 示例直接搬到 Orange Pi | 依据 `docs/vendor/VENDOR_INDEX.md`，要求上机确认实际设备名并通过参数传入 |

## 本轮组织链路

CEO -> Product Manager / OKR Owner -> Engineers

| 角色 | 本轮后续任务 |
| --- | --- |
| `product-okr-owner` | 锁定 O1 优先级、范围边界、验收口径和 sprint 入口文档 |
| `hardware-engineer` | 下一阶段主责：在 docker 中完成 preflight，并在真实串口环境执行 WAVE ROVER move-test |
| `robot-software-engineer` | 只在真实 run 后补充 O2 task_record/evidence_ref 对账入口 |
| `autonomy-engineer` | 只在真实 run 后补充 O3 fixed-route/status/replay 同 evidence_ref 对账 |
| `full-stack-software-engineer` | 本轮无主任务；后续仅消费 `hil_pass`/blocked 状态用于用户可读诊断 |

## P0/P1 风险

| 等级 | 风险 | Gate |
| --- | --- | --- |
| P0 | 把 docker preflight 误写成 `hil_pass` | 所有 docker 结果只能标 `software_proof` 或 preflight pass |
| P0 | 无真实串口时继续尝试关闭 O1 | `ls -l <serial_device>` 与容器内设备可见性是 real run 前置 gate |
| P1 | 真实设备名不是 `/dev/ttyUSB0` | 设备名由上机发现结果决定，命令参数显式传入 |
| P1 | O2/O3 抢跑 closed | O1 未有真实 `hil_pass` evidence packet 前，O2/O3 只能写 partial/software proof |

## 本文件 Gate

- 已将 09-10 blocked 事实、OKR O1 约 75% 状态、vendor 串口事实和本机 docker-only 环境写入本轮起点。
- 允许进入 `prd.md`，定义产品验收口径。
