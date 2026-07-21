# Pre-start：O1 轮速反馈根因诊断

## Sprint 元数据

- `sprint_type: epic`
- 目标 Objective：O1「打通官方硬件协议，建立可信底盘控制层」
- 主责 owner：`robot-hardware-engineer`
- 状态：`closed_blocked_before_implementation_by_subagent_runtime`
- 证据边界：`non_motion_offline_and_remote_readonly_diagnostics_only`

## 路由与用户价值

当前主进度最低的是 O5（约 85%），但 production provider/runtime 同根因 blocker 已消费 `2/2`，本轮不得再次包装。
O6/O7 各约 93%，其路线执行入口需要独占维护窗口释放 systemd/UART holder；CEO 本轮授权了运动、operator 看护、路线
清空与物理限位，但没有授权 stop/restart/kill service、抢占 UART 或修改 firmware。O1 约 95%，上一轮 v8 已证明 nonzero
command transport 与最终停车，但 during-motion `T=1001 L/R` 仍为 `0/0`。因此本轮选择 O1 的全新、可执行入口：不运动地
定位 encoder、`mainType`、firmware、`speedGetA/speedGetB` 更新链与 bridge sampling/parser 边界，为下一次维护或 HIL 决策
提供可复验的根因分类，而不是重采 v8。

用户价值是把“轮子有动作但反馈为零”从猜测变成结构化、fail-closed 的诊断结果，减少下一次维护窗口或真实 HIL 的盲目
试错，并避免在未证明轮速反馈前错误声明 `hil_pass` 或 `safe_to_control`。

## 上轮未完成项与 blocker

- `sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/final.md` 已封存
  `ceo_20260721_0651_current_wheel_feedback_hil_v8=consumed_no_retry`。
- 禁止重复 `0.08m/s / 300ms minimal jog + readback`，禁止补采、重发或 retry。
- 已证事实：Upper 发布 6 个非零 `/cmd_vel` frame，bridge 记录 6 个 `T=11 L=164 R=164 sent=true`；同窗 3 个
  serial-derived `T=1001` pair 全为 `0/0`；dedicated stop 与最终停止已证明。
- 未证事实：实际 firmware identity、当前 `mainType`、encoder 脉冲更新、`speedGetA/speedGetB` 更新分支、raw serial bytes、
  `T=13` wire、direct `T=130` request。
- Product planning 子 agent 三次零文件/零命令空转；主节点仅按 AGENTS.md 允许的必要留档边界补齐本计划，不代替 Engineer
  实现、测试或修复。

## Owner 与范围

单 owner 闭环：`robot-hardware-engineer`。这是硬件协议、ESP32 firmware 事实与 HIL 根因诊断任务；无需为凑并行拆给
其他 owner。Engineer 必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 `json_cmd.h`、`uart_ctrl.h`、
`movtion_module.h`、`ugv_advance.h`、`WAVE_ROVER_V0.9.ino` 和 `ugv_rpi/base_ctrl.py`。

本轮允许离线代码、单测、硬件文档、当前 sprint artifacts/留档，以及对 `root@192.168.1.11:37878` 的严格只读 inventory。
范围外 dirty WIP（3 个 workstation/product tracked 文件及 `06-20`、`06-45` sprint）必须保持不动。

## 安全围栏与 anti-repeat

- `motion_command_count=0`、`stop_command_count=0`、`nonzero_command_count=0`。
- 禁止 POST/PUT/PATCH/DELETE，禁止 `/cmd_vel` publish、manual/stop/control、Nav2 goal、串口写入或 UART claim。
- 禁止 stop/restart/kill/enable/disable service，禁止 deploy，禁止 firmware flash/config mutation。
- SSH 若使用，只允许读取现有 process/service/parameter/source hash/log/inventory；任何只读 gate 不确定即 fail closed。
- 本 sprint 不证明 HIL、安全准入、路线执行或送达；不得提高主百分比，除非 Product 收口发现新的外部/现场事实类别。
- v8 exact slice 永久退役；本轮不得以不同 wrapper 重新消费同一动作窗口。

## 预期产物

- 一个可执行的离线根因诊断模块/CLI，消费 vendor 事实、v8 artifacts 和可选只读 inventory，输出稳定 schema、分类、证据与
  下一条精确维护动作。
- 单元测试覆盖 vendor 分支、v8 `0/0`、输入缺失/篡改、危险真值与 fail-closed。
- 当前上位机严格只读 inventory artifact（若连接可用）；连接不可用时记录 exit/error，不得降级为写操作。
- 同步硬件文档以及 `tech-done.md`、`side2side_check.md`、`final.md`。
