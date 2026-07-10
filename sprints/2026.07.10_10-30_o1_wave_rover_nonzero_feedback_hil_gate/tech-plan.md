# O1 WAVE ROVER Nonzero Feedback HIL Gate Tech Plan

## sprint_type

sprint_type: epic

## 目标

把 O1 当前“真实 WAVE ROVER 轮速 nonzero L/R 与 HIL 准入仍缺证据”的问题，先收敛成可执行的软件证据链：基于本地 vendor 资料为 WAVE ROVER feedback 采集、mock/虚拟串口回放、fail-closed 判定和 HIL 准入摘要建立后续实现范围。该计划只追求 `robot-hardware-engineer` 可单线闭环执行，不宣称真实非零轮速、不宣称真实 HIL pass。

## 用户价值和产品北极星

用户真正需要的是“上车时能知道底盘反馈是否可信、是否满足进入 HIL 的最低门槛”，而不是又一个只读 surface。把 nonzero L/R 反馈采集和 HIL gate 做成可复现的软件证据链，能减少现场调试时把零值、串口噪声或危险 payload 误当成可控底盘的风险。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 为 O1 与 O5，二者均约 85%。
2. 本 sprint 针对最低 Objective 之一：O1。
3. 本轮选择 O1 而不是继续 O5 的具体理由：
   - O5 最近几轮已经明确：没有真实 production cloud / production DB/queue / live endpoint 外部证据时，只能做回归守护，不能再靠 local/mock probe wrapper 增加 OKR。
   - O1 最近没有被连续 sprint 消费，且仍有明确的软件前置工作可做：围绕 WAVE ROVER 非零 L/R 反馈与 HIL 准入建立 fail-closed 工具链。
   - 本轮即使只能做 mock/虚拟串口验证，也能为下一次真实上车采证减少返工；而 O5 在同样前提下不会新增主 OKR 价值。

## Owner

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单线闭环，实现、测试、修复与 `tech-done.md` 留档均由 Hardware owner 完成。

## 文件范围

后续 implementation 仅允许 `robot-hardware-engineer` 修改以下范围：

- `onboard/src/ros2_trashbot_hardware/**/*`
- `onboard/tests/**/*hardware*`
- `onboard/tests/**/*wave*rover*`
- `docs/vendor/**/*wave*rover*`
- `docs/hardware/**/*.md`
- `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/tech-done.md`

明确禁止本轮 Hardware owner 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/final.md`
- 其他与本轮无关的产品、云端、O6/O7 文件

## 计划任务

### 1. Vendor 事实对齐

- 以后续实现所需的最小集合为准，复核 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料：
  - UART JSON newline framing
  - 默认 `115200`
  - chassis control / feedback 相关命令
  - 已知反馈字段与现有硬件包映射
- 在实现代码注释或文档中明确引用本地 vendor 来源，不凭记忆补协议。

### 2. 非零反馈采集与 mock 回放

- 规划一个既可接真实串口、又可接 mock/虚拟串口输入的反馈采集入口。
- 重点验证：
  - 当反馈中存在 L/R 非零样本时，能形成结构化软件摘要；
  - 当反馈缺字段、字段类型异常、全程零值、payload 不安全或流中断时，必须 fail-closed；
  - mock/虚拟串口场景可在 macOS 本地复现，不依赖真实硬件。

### 3. HIL 准入 gate

- 在采集摘要上增加 HIL 准入前置判定，只输出 ready/not-ready 风格的软件结果。
- gate 至少要覆盖：
  - 是否读到合法 feedback 帧；
  - 是否观察到非零 L/R 样本；
  - 是否存在方向信息或方向缺失说明；
  - 是否存在必须人工补证的 blocker。
- gate 输出必须 fail-closed；没有真实硬件或没有 nonzero 证据时，默认 blocked/not-proven。

### 4. 文档与 sprint 留档

- 同步更新最小必要硬件文档，说明：
  - 采用的 vendor 资料来源；
  - mock/虚拟串口验证边界；
  - 真实上车前仍需补齐的证据。
- implementation 完成后在本 sprint `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。

## 验收命令

以下命令必须能在当前 macOS 本地环境运行，且不要求真实硬件：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/**/*.py
python3 -m unittest discover -s onboard/tests -p '*hardware*.py'
git diff --check -- onboard/src/ros2_trashbot_hardware onboard/tests docs/vendor docs/hardware sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate
```

若实际文件命名需要更窄范围，可在 implementation 开始时收敛为等价 scoped 命令，但仍必须保留：

- Python `py_compile`
- 硬件包 `unittest`
- `git diff --check`

可选验证，不作为本轮阻塞条件：

```bash
bash onboard/scripts/docker_humble_build.sh
```

风险说明：Docker/Humble build 更适合做 ROS2 workspace 全局回归，但本轮目标是 O1 feedback/HIL gate 软件证据链；若 Docker 镜像、依赖或 ROS 环境异常，不应阻塞本轮计划落地。

## 接口影响

- 仅允许新增或收紧硬件反馈采集、mock 回放、HIL gate 的只读软件摘要。
- 不在本轮改变真实控制策略、launch 默认值、生产硬件参数或安全动作开关。
- 若需要新增摘要字段，必须保持缺失时 fail-closed，不默认推断真实 nonzero 或真实 HIL ready。

## 证据边界

本轮 implementation 的目标证据边界必须固定为：

- `software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`
- not true WAVE ROVER nonzero L/R feedback
- not HIL pass
- not safe_to_control

## 风险和阻塞

- 没有真实 WAVE ROVER 非零 L/R 原始反馈，本轮无法证明底盘真实运动。
- 没有真实 HIL 执行，本轮无法证明 gate 通过后现场一定可控。
- 现有仓库中的硬件包命名、测试入口和 vendor 字段映射可能存在漂移，implementation 首轮可能需要先做对齐。
- macOS 本地若缺少虚拟串口能力，必须保留纯 mock fallback，避免让计划卡死在开发机环境上。
