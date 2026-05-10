# Sprint 2026.05.11 06-07 HIL + Route E2E Hardening-2 - PRD

## 用户价值与产品北极星

把 O1 优先级回归到“能上车可复现”——以 `source=hil_pass` 的证据替代文档验收，确保下一步动作有真实闭环。

## 目标与验收意图

- 清理最近评审复发点：`hil_pass`、命令反馈映射与依赖阻塞未形成可复现证据。
- 用最小围栏推进 O1，避免扩场景和临时测试堆叠。
- O2/O3 本轮暂不扩展实现，只保留在 `hil_pass` 恢复后可顺延。

## OKR 映射（本轮聚焦 O1）

### Objective 1：HIL 可复现闭环

- KR1：第一轮 `source=hil_pass` 有明确 `run_id / evidence_ref`。
- KR2：`hil_pass` 产物包含 command、serial log、feedback、`/odom`、`/imu/data`、`/battery` 证据。
- KR3：`source=software_proof` 与 `source=hil_pass` 清晰分离，不混用为通过依据。

### Objective 1 扩展 KR：命令反馈映射复验

- KR1：复验显示 `T=143 -> T=142 -> T=131` 下发顺序与参数一致。
- KR2：`T=1001` 连续样本>=2且字段含 `L,R,r,p,y,v`。
- KR3：每次运动前后都有 `T=1,L=0,R=0` 覆盖停命令。

### Objective 1 风险 KR：依赖阻塞治理

- KR1：pyserial 缺失时阻塞告警明确，不误报 `hil_pass`。
- KR2：串口路径、波特率、参数锁定在 evidence packet 复核。

## 本轮范围（仅 O1）

### 做什么（按优先级）

1. 更新 `hardware_smoke_wave_rover.py` 以应对依赖阻塞并固定最小围栏参数（与验收命令一致）。
2. 在 `hil_runbook` 增加 run packet 与复验规则，形成可复用 `hil_pass` 包。
3. 在 `wave_rover_hil_evidence` 与 `robot_bringup_checklist` 绑定 `evidence_ref` + 主题反馈归一。

### 不做什么

- 不新增测试矩阵，不改 O2/O3 任务实现。
- 不把 `dry-run` 或 `software_proof` 标注为硬件通过。
- 不恢复到 `test_*review*py` 命名方式。

## 验收门槛（固定围栏）

- `python3 scripts/hardware_smoke_wave_rover.py --help`
- `python3 scripts/hardware_smoke_wave_rover.py --status`
- `python3 scripts/hardware_smoke_wave_rover.py --move-test --test-speed 0.05 --test-duration-s 0.3 --serial-port /dev/ttyUSB0 --baudrate 115200`

## 对应责任 Engineer

- `hardware-engineer`：O1 主责。
- `robot-software-engineer`/`autonomy-engineer`：在 O1 未阻塞前仅支持，不改核心代码。
