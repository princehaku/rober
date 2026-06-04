# Tech Done: Runtime Material Continue

## sprint_type

sprint_type: epic

## 实际改动

本轮由主会话完成 Epic 启动文档，四个 L2 owner 已按 `tech-plan.md` 并行派发。Robot Algorithm owner 的 O2 改动在关闭后落盘，主会话做了协调验收；其他三个 owner 没有 owner note 或可验收材料，已关闭以避免自动化线程无限挂起。

已落盘文件：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `owner_notes/robot-algorithm-engineer.md`

本轮新增 O2 vision checker/template 相关代码和 evidence 文件；未改硬件配置或 launch 参数。

## Owner 执行结果

| Owner | 预期抓手 | 执行结果 | Product 判定 |
| --- | --- | --- | --- |
| Robot Software Engineer | O3/O7 non-motion ROS2 runtime，fresh `/scan` 或 supervisor blocker | 子 agent 连续超时，无 owner note 落盘 | 不涨 O3/O7；下一轮需更窄派单，只做 fresh `/scan` 或只做 supervisor blocker。 |
| Robot Algorithm Engineer | O2 elevator image manifest 查找/eval 或采集模板 | 新增 manifest checker、采集模板和 blocker artifact；checker 输出 `blocked_missing_real_or_controlled_images` | 推进 O2 执行抓手，但没有真实/受控图片，不涨 O2。 |
| User Touchpoint Full-Stack Engineer | O7 PC operator evidence 展示/回放 | 子 agent 连续超时，无 owner note 落盘 | 不涨 O7；上一轮 operator report route 材料仍有效，但本轮无新增 workflow 证据。 |
| Hardware Infra Engineer | O1 stop-first HIL 准入或非运动 blocker | 子 agent 连续超时，无 owner note 落盘 | 不涨 O1；继续保持 `safe_to_control=false`。 |

## 验证结果

主会话对 sprint 文档和 O2 checker 做协调级检查：

```bash
git diff --check -- sprints/2026.06.04_19-20_runtime-material-continue
```

结果：通过，无输出。

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|最近 2 轮 blocker|evidence type|O2|O3|O7|O1" sprints/2026.06.04_19-20_runtime-material-continue
```

结果：能检出 Epic 类型、OKR 最低优先级核对、最近 2 轮 blocker、evidence type gate 和 O2/O3/O7/O1 分工。

本轮没有运行产品测试、ROS2 runtime、PC build/lint 或 HIL；这些必须由下一轮 L2 owner 重新执行。

O2 checker 验证：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template pc-tools/evidence/templates/elevator_image_manifest_collection_template.json
```

结果摘要：

```text
status=blocked_missing_real_or_controlled_images
evidence_type=blocked_with_root_cause
can_run_opencv_eval=false
field_eval_ready=false
image_kinds.real_or_controlled=0
template_placeholders=8
```

视觉包测试：

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test
```

结果：

```text
Ran 20 tests in 1.170s
OK
```

## OKR 影响

- O2：保持约 72%。新增真实/受控图片采集模板和 checker，但没有真实/受控图片 manifest。
- O3：保持约 73%。没有 fresh `/scan`、`/map`、TF、AMCL 或 Nav2 lifecycle 材料。
- O7：保持约 89%。上一轮 operator report route 进展保留，本轮没有新增 PC workflow 材料。
- O1：保持约 95.5%。没有 field HIL 或 ROS feedback topic。
- O8：保持约 40%。本轮创建了 Epic 文档链，但 L2 执行超时，不能作为治理涨分。

## 失败定位

本轮新增 blocker：`subagent_execution_timeout`。

根因判断：

1. Robot Software、Full-Stack、Hardware 三个 L2 任务 prompt 仍然偏大，且同时包含远程 SSH、代码变更、测试和 owner note，容易卡住。
2. 自动化线程需要强时限，不能等待无落盘结果无限延长。
3. 下一轮应把 L2 派单拆窄到单一命令链，例如只做 `fresh /scan`、只做 `elevator manifest template`、只做 `PC operator readback`、只做 `vendor/HIL preflight`。

## 剩余风险

- 19-20 只有 O2 采集模板/checker 这种 execution guard，不能宣称 O2 field material 完成。
- 当前可提交的功能性进展主要来自已存在的 17-18 operator report route、真实 8787 部署和 PC 同源复测材料。
- O2/O3 仍是最低产品主线；下一轮必须直接拿真实/受控图片和 fresh ROS2 runtime，否则继续停滞。
