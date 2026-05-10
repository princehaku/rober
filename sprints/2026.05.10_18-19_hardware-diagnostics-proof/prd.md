# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - PRD

## 用户价值

Objective 1 当前软件测试已经能覆盖硬件桥的 JSON 编码、速度映射和反馈解析，但这些证据仍分散在代码、单测和 smoke 脚本里。无实机时，工程/售后同学需要一份可复盘 artifact，能回答：

- 当前采用哪些 vendor 资料作为协议依据。
- 启动时会发哪些 WAVE ROVER JSON 配置命令。
- 默认 `/cmd_vel` 会生成什么 `T=1` 左右轮命令，`T=13` 为什么仍需要 HIL。
- `T=1001` feedback 样例如何被解析为左右速度、IMU 姿态和电池电压。
- 当前配置是否满足 serial、baudrate、command mode、track width、max wheel speed 等边界。
- 下一步真实 HIL 应该按什么命令 recipe 执行。

普通用户的间接价值是：未来手机端只需要看到“底盘协议软件证据完整 / 需要上车验证 / 风险原因”，不用理解 UART、JSON、ROS2 或 vendor firmware。

## 产品北极星

把底盘控制从“代码里看起来能发命令”推进为“协议事实可追溯、配置可验证、风险可解释、HIL 有入口”的可信控制层，支撑后续手机一键送垃圾。

## OKR 映射

- Objective 1：打通官方硬件协议，建立可信底盘控制层。
  - KR1：启动配置 echo、反馈间隔、反馈流进入 proof artifact。
  - KR2：`T=1` speed mode 和 `T=13` ROS mode 的边界进入 proof artifact，`T=13` 不宣称已默认可用。
  - KR3：`T=1001` feedback sample 解析进入 proof artifact，`/odom` 继续标注为命令积分。
  - KR4：新增 diagnostics proof 单测，锁定 JSON 结构、配置边界和坏反馈容错。
  - KR5：proof/CLI 暴露核心硬件参数，不硬编码 Orange Pi 实际 UART。
- Objective 5：只做间接铺垫。本轮 artifact 可被后续 operator diagnostics 消费，但不新增手机 UI。
- Objective 2/3/4：本轮不抬进度。

## KR 拆解或更新

本轮不修改 `OKR.md`，只把 Objective 1 的小时级 KR 拆成可交付切片：

- KR-A：新增 dependency-light hardware diagnostics proof helper/CLI。
- KR-B：proof JSON 包含 vendor source、配置、启动命令、cmd_vel 样例、feedback 样例、risk flags、HIL recipe。
- KR-C：focused tests 覆盖 proof 正常路径、非法配置、坏 feedback、T=13 HIL 风险标记。
- KR-D：`tech-done.md` 记录 vendor 来源、实际改动、验证命令、接口影响和真实 HIL 剩余缺口。

## 本轮核心抓手

由 `hardware-engineer` 在 `src/ros2_trashbot_hardware/` 中新增一个不打开串口、不启动 ROS2 node 的 diagnostics/proof 模块，复用 `esp32_bridge.py` 的纯函数：

- `build_startup_config_commands()`
- `build_cmd_vel_command()`
- `parse_feedback_line()`
- `validate_startup_config()`
- `encode_json_command()`

CLI 只生成 proof JSON，不直接发命令到硬件。

## 范围

做：

- 新增 hardware diagnostics proof helper/CLI。
- 新增 console script 入口。
- 新增 focused 单测。
- 更新当前 sprint `tech-done.md`。
- 如实现引用硬件协议事实，必须在 `tech-done.md` 写明已读 vendor 来源。

不做：

- 不接真实串口，不运行真实 hardware smoke。
- 不改 `docs/vendor/`、factory firmware、AGENTS、OKR。
- 不改 launch 默认串口、波特率、速度参数。
- 不修改 behavior/nav/vision/full-stack 代码。
- 不把离线 proof 当成 HIL 或上车成功。

## 优先级

- P0：离线 proof helper/CLI + JSON artifact + focused tests。
- P0：风险标记必须明确区分 software proof 与 HIL gap。
- P0：vendor source 引用必须出现在 proof 或 tech-done 中。
- P1：CLI 输出字段稳定，后续 operator diagnostics 可直接消费。
- P2：如成本很低，可补一个 sample fixture；否则用测试临时目录生成 proof。

## 验收标准

- 能运行命令生成 proof JSON，且不需要 ROS2 daemon、真实串口或 WAVE ROVER。
- proof JSON 至少包含：
  - `vendor_sources`
  - `config`
  - `startup_commands`
  - `cmd_vel_examples`
  - `feedback_sample`
  - `risk_flags`
  - `hil_recipe`
- status/risk 至少区分：
  - `software_proof_ready`
  - `hil_required`
  - `invalid_config`
  - `feedback_parse_failed`
- 单测覆盖正常路径和关键失败路径。
- `tech-done.md` 明确写出实际改动、验证命令和结果、接口影响、剩余风险。

## 对应责任 Engineer

- `hardware-engineer`：实现、测试、修复和 `tech-done.md`。
- Product Owner：本轮只完成 PRD/tech-plan；implementation 后验收 Objective 1 的证据链是否真实推进。

## 风险、阻塞和需要补齐的证据链

- 离线 proof 不证明真实 UART、电气连接、底盘轮向、速度单位、反馈频率或 IMU/电池实测正确。
- Orange Pi 实际串口设备名仍需上车确认，不能引用 Raspberry Pi 样例路径当作本项目默认事实。
- `T=13` 是否适合作为 ROS `/cmd_vel` 映射仍需 WAVE ROVER HIL。
- 后续需要把 proof artifact 接入 operator diagnostics 或 HIL runbook，才能成为售后/手机侧可见证据。
