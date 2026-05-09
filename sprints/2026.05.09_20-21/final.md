# Sprint 2026.05.09_20-21 Final

## 文档阶段门禁

- 前置文档：`side2side_check.md`。
- 前置 gate：PRD vs 实现、OKR/KR、接口、文档、测试和 P0 风险对照完成，且 P0 全部 closed。
- 当前阶段：FINAL。
- 本阶段完成条件：PMO 收集完成情况、验证证据、OKR 进度、技术遗留和下轮 backlog。
- 如果本文件早于 side2side gate 被预创建，则在 gate 完成前只能视为 invalid draft，不得作为有效收口证据。

## 收口状态

当前为新一轮迭代启动阶段，尚未允许最终收口。

## 已完成

- 建立 sprint 目录：`sprints/2026.05.09_20-21/`。
- 建立强制留档文件：
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
- 完成 P9/P8/P7 分工入口：
  - P9 定方向：送垃圾闭环可信化。
  - P8 拆轮次：P0/P1、owner、里程碑、证据要求。
  - P7 已开始执行：测试红绿、接口补强、终态诊断透传、文档边界修正。
- 补强 `TrashCollection.Result` 机器可判定终态：`error_code`、`final_state`。
- 将 navigation timeout 映射为一等状态机事件 `timed_out`。
- 修正 README / hardware docs 中缺少 vendor/HIL 支撑的硬件能力说法。

## OKR 进度变化

| OKR | 当前推进 |
| --- | --- |
| Objective 1 | 本轮已把硬件事实源和 HIL 缺口列入 P0 |
| Objective 2 | 既有送垃圾状态机已存在，本轮补强 timeout 与 action 终态诊断；验收仍 open |
| Objective 3 | 既有 route/waypoint dry-run 已存在，本轮仍需 Docker/ROS2 与更深结果路径验证 |
| Objective 4 | 本轮明确视觉不作为送达成功前提 |
| Objective 5 | 本轮保持手机用户最小闭环，不做完整 App |

## 证据索引

| 证据 | 路径 | 状态 |
| --- | --- | --- |
| Sprint 启动留档 | `sprints/2026.05.09_20-21/` | done |
| 本地 smoke | `scripts/run_smoke_tests.sh` | passed after latest P7 code/docs edits: 13 + 18 + 7 + 79 + 1 tests OK |
| ROS2 Humble build | Docker Humble `colcon build --symlink-install` | blocked: Docker unavailable in current WSL distro |
| WAVE ROVER HIL | `docs/acceptance/wave_rover_hil_evidence.md` 或本轮 HIL 记录 | pending |

## P0/P1 状态

P0 尚未清零，本文件不能作为完成证明。P0 状态以 `side2side_check.md` 为准。

P1 需要在本轮执行结束时明确 owner 和下一轮入口。

## 剩余风险

- 本轮本地 smoke 已通过，但它只能证明 Python 语法和包内静态/逻辑测试，不证明 ROS2 Humble 构建或实机行为。
- 本轮尚未运行 Docker Humble build；`docker --version` 显示当前 WSL 2 distro 找不到 Docker，因此不能证明 ROS2 Humble 构建通过。
- 本轮尚未上车，因此不能证明串口设备名、速度路径、反馈字段、停止路径在实机可用。
- 任何关于引脚、电压、UART 路径、波特率、命令 ID、速度映射、反馈字段或机械尺寸的完成结论，都必须引用 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件。
- `AGENTS.md` 已存在未提交修改，本轮新增文件不应回滚或覆盖该用户/既有改动。

## 下一步建议

1. 运行 `scripts/run_smoke_tests.sh` 建立基线。
2. 按 `tech-plan.md` 优先处理 P0：行为状态机、route dry-run、硬件事实审计。
3. 可用 Docker Humble 时运行 ROS2 构建。
4. 上车前补齐 HIL 步骤与证据模板，上车后再关闭硬件 P0。
