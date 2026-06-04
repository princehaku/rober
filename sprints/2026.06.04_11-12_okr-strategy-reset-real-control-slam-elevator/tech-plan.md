# Tech Plan: OKR Reset And Next Epic Boundary

## sprint_type

epic

## 本轮计划

本轮由 Product Manager / OKR Owner 执行文档重置，不修改产品代码、测试代码、硬件配置或接口文档。

步骤：

1. 读取 `AGENTS.md`、`OKR.md`、最近相关 sprint 证据和 `docs/product/elevator_assisted_delivery.md`。
2. 基于四个 L2 owner 事实复盘，重写 `OKR.md` 当前推进区。
3. 把 O2/O3 从历史归档区拉回当前推进区。
4. 打回 O1/O2/O3/O7 虚高百分比。
5. 新增或重写 PC WASD、雷达一键开关、SLAM/定位、OpenCV 电梯识别 KR。
6. 在 `docs/process/okr_progress_log.md` 追加打回原因。
7. 运行文档变更验证命令。

## 文件范围

允许修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/pre_start.md`
- `sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/prd.md`
- `sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/tech-plan.md`
- `sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/tech-done.md`

禁止修改：

- `pc-tools/**`
- `onboard/**`
- `cloud-relay/**`
- `.codex/**`
- `docs/interfaces/**`
- 除 `docs/process/okr_progress_log.md` 外的 `docs/**`

## OKR 最低优先级核对

重置后当前最低 Objective 是：

- O2：可送垃圾任务 + 电梯 assisted delivery，约 72%。
- O3：可验证导航、建图、定位与固定路线，约 73%。

本 sprint 直接针对最低 Objective：O2/O3 均从历史归档撤回当前推进区，并重写 KR 和验收口径。下一轮 Epic 也必须优先覆盖 O2/O3，同时联动 O7 和 O1，因为 PC 控车、雷达开关、建图定位和电梯 OpenCV 是同一现场闭环的四个面。

## 下一轮 Epic owner 切分

| Owner | 主责范围 | 允许改动建议 | 验收命令建议 |
| --- | --- | --- | --- |
| User Touchpoint Full-Stack Engineer | PC WASD 现场 workflow、雷达一键 start/stop、建图/定位控制、stop/急停/operator report UI/API | `pc-tools/workstation/**`、相关 `docs/product/` 或接口文档 | `cd pc-tools/workstation && npm test -- --run`、`npm run build`、`npm run lint`、Playwright rendered smoke |
| Robot Software Engineer | 8787/upper API 的 map lifecycle、SLAM Toolbox、AMCL `/initialpose`、Nav2 lifecycle glue、ROS2 state integration | `onboard/scripts/**`、`onboard/src/ros2_trashbot_*`、相关 docs | `python3 -m unittest ...`、`python3 -m compileall -q ...`、Docker/Humble build 或 targeted ROS2 smoke |
| Robot Algorithm Engineer | OpenCV elevator taxonomy、样本/ROI/rule baseline、offline eval、Nav2 map quality metrics | `onboard/src/ros2_trashbot_nav/**`、`onboard/src/ros2_trashbot_vision/**`、`pc-tools/evidence/**`、docs/product | targeted unittest、offline eval artifact smoke、sample manifest checker |
| Hardware Infra Engineer | WAVE ROVER 现场安全前提、底盘低速 pulse、stop/post-status、`T=1001` 同场材料、LiDAR start/stop/udev/长稳 | `onboard/scripts/**`、hardware docs、vendor-readback docs | vendor-readback、serial/HIL smoke、operator report artifact、scoped diff check |

## 验收命令

文档变更验证：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator
```

```bash
rg -n "WASD|雷达|建图|SLAM|定位|OpenCV|电梯|打回|Epic" OKR.md sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator docs/process/okr_progress_log.md
```

## 风险和边界

- 本轮只是 OKR/产品文档重置，不证明任何新 runtime 能力。
- 下一轮 Epic 必须补齐 `side2side_check.md` 和 `final.md`；本轮按 CEO 给定文件范围只更新到 `tech-done.md`。
- 任何 mock、fixture、dry-run 或 software proof 可以作为开发证据，但不得把百分比涨成真实现场完成。
- 硬件真实集成前仍必须按 `docs/vendor/VENDOR_INDEX.md` 复核 vendor 来源。
