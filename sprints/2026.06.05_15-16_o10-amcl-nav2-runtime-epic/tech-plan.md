# Tech Plan: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 计划状态

本文件为 Product/OKR 收口补齐的简洁版 tech-plan，实际实现已由 Robot Software
Engineer 完成并记录在 `tech-done.md`。后续验收以 `tech-done.md`、本轮
`side2side_check.md` 和 `final.md` 为准。

## 技术方案

1. 新增 no-motion collector：读取 canonical map proof
   `/root/rober/onboard/runtime/map_lifecycle_latest.json` 和 map artifacts，
   检查 AMCL/Nav2 包、map server/AMCL/planner/controller lifecycle、`/scan`、
   `/map`、`/amcl_pose` 等只读材料。
2. 在 upper API 增加 `POST /api/nav2/proof/refresh`、
   `GET /api/nav2/proof/latest`，并让 `/api/nav2/status` 暴露 proof routes。
3. 测试覆盖 route 不返回 405、blocked artifact 可 readback、安全字段保持 false。
4. 文档同步记录 no-motion proof artifact 边界。

## 文件范围

Robot Software 已改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/navigation/nav2_map_quality_metrics.md`

Product/OKR 收口允许改动：

- `OKR.md`
- `sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/**`

## 验收命令

Robot Software 已执行：

```bash
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest onboard.scripts.test_upper_robot_api
python3 -m unittest discover -s onboard/scripts -p 'test_*.py'
git diff --check -- onboard/scripts docs/navigation docs/interfaces sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic
```

Product/OKR 收口需执行：

```bash
test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/pre_start.md && test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/prd.md && test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/tech-plan.md && test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/tech-done.md && test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/side2side_check.md && test -f sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic/final.md
grep -R "sprint_type: epic" sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic
grep -R "blocked_with_root_cause\|no-motion\|safe_to_control=false\|nav2_amcl_missing" OKR.md sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic
git diff --check -- OKR.md sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 最低完成度 Objective 是 O10（约 10%，15-16 收口前）。
本 sprint 直接针对 O10。验收口径不是证明送达，而是形成 AMCL/Nav2 runtime
blocked artifact，并把下一步 root cause 从"抽象未就绪"收窄为缺包、lifecycle
未激活和 ROS topics 未发布。

## 风险边界

- 禁止运动：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 Nav2 goal。
- 禁止涨 O3/O9：blocked artifact 不是 AMCL/Nav2 runtime success，也不是 O9 新 breakthrough。
- 禁止涨 O7：本轮没有 PC 端消费 `/api/nav2/proof/latest` 的 browser/API material。
