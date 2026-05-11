# Sprint 2026.05.11_10-11 HIL Docker Preflight To Real Run - PRD

## 产品目标

把 O1 “硬件协议可信底盘”从长期 blocked 的描述推进到可操作的两段式验收：

1. docker preflight：证明 Humble 容器、脚本入口、依赖和 evidence 目录写入链路可用。
2. real run：在真实 WAVE ROVER 串口设备可见后，用同一套命令生成 `hil_pass` evidence packet。

一句话：先让上车前检查不再模糊，再让真实硬件到位时可以直接跑出可验收证据。

## 文档阶段门禁

- 前置文档：`pre_start.md`
- 当前阶段：`prd.md`
- 阶段完成条件：OKR 映射、范围、验收口径、失败边界与 owner 清晰。
- 下一阶段：`tech-plan.md`

## OKR 映射

| 优先级 | OKR | 本轮映射 |
| --- | --- | --- |
| O1（第一优先） | Objective 1：打通官方硬件协议，建立可信底盘控制层 | 先完成 docker preflight 准入，再等待真实串口执行 `hardware_smoke_wave_rover.py --move-test` 生成 `hil_pass` evidence packet |
| O2（第二优先） | Objective 2：可恢复送垃圾任务闭环 | 仅作为真实 run 后的消费者：复用同一 `evidence_ref` 对齐 task_record 与失败恢复字段 |
| O3（第三优先） | Objective 3：可验证导航与固定路线能力 | 仅作为真实 run 后的消费者：复用同一 `evidence_ref` 对齐 route status/replay 与 task_record |

## 范围内

- 创建 10-11 sprint 入口文档：
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
- 明确 docker preflight 与 real run 的证据边界。
- 明确 `hardware-engineer` 为下一阶段主责，`robot-software-engineer`/`autonomy-engineer` 只在真实 run 后做同 evidence_ref 对账。
- 明确真实硬件 absent 时的状态：O1 继续 blocked，O2/O3 继续 software proof。
- 引用硬件事实来源：`docs/vendor/VENDOR_INDEX.md`。其中串口、波特率、JSON 指令和 Orange Pi 设备名判断不得凭记忆推断。

## 范围外

- 不修改 `OKR.md`。
- 不新增或修改产品代码、测试代码、launch 参数、硬件配置。
- 不生成假的 `hil_pass` 样本。
- 不承诺本机可完成真实 WAVE ROVER run；当前本机只有 docker。
- 不把 O2/O3 software proof 升级为实机通过。

## 用户价值

1. CEO 能清楚看到 O1 为什么还没有 closed：缺真实串口与真实 feedback/topic 样本，而不是缺文档。
2. 硬件执行者拿到真实设备后可直接按 `tech-plan.md` 执行，不再重新解释 preflight 与 real run 的边界。
3. 后续 O2/O3 对账能建立在同一 `evidence_ref` 上，避免各自拿软件样本单独宣称完成。

## 验收口径

### P0：入口文档验收

- 三份文档存在：
  - `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/pre_start.md`
  - `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/prd.md`
  - `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/tech-plan.md`
- 文档明确 O1 优先、docker-only 限制、`/dev/ttyUSB0` 缺失历史和 `software_proof`/`hil_pass` 边界。

### P1：docker preflight 验收

- 在 docker/Humble 环境中能完成上车前命令链路检查。
- 输出只允许标记为 `software_proof` 或 `preflight_pass`。
- 不得因 docker 通过而修改 O1 为 `hil_pass`。

### P0：real run 验收

- 在真实串口设备可见后运行 WAVE ROVER move-test。
- 真实 run 必须产出同一 `evidence_ref` 下的最低证据包：
  - `command.txt`
  - `serial.log`
  - `feedback_T1001.log`
  - `odom_once.jsonl`
  - `imu_once.jsonl`
  - `battery_once.jsonl`
- 只有真实串口交互与状态样本齐备时，才允许标记 `source=hil_pass`。

## 失败处理

| 失败 | 判定 | 处理 |
| --- | --- | --- |
| docker 镜像或依赖不可用 | preflight blocked | 由 `hardware-engineer` 修复容器/依赖链路，不能进入 real run |
| 宿主机无真实串口设备 | real run blocked | 保持 O1 blocked，记录 `ls -l <device>` 与容器设备映射结果 |
| 串口打开成功但无 `T=1001` 反馈 | real run partial/failed | 保留 serial log，依据 vendor JSON/feedback 资料定位协议或固件问题 |
| 只生成占位 evidence 文件 | 不通过 | 必须明确为 blocked artifact，不能作为 `hil_pass` |

## 本文件 Gate

- PRD 已定义 O1 主线、docker preflight 与 real run 的证据边界、失败处理和 owner。
- 允许进入 `tech-plan.md`。
