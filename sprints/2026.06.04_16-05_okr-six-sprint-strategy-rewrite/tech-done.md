# 2026.06.04 16-05 OKR Six-Sprint Strategy Rewrite Tech Done

## sprint_type

micro

## Owner

product-okr-owner

## 本轮目标

本轮是单 owner 文档 micro sprint，只做 OKR 复盘、进度日志和本 sprint 留档，不改产品代码、测试代码、硬件配置或其他文档。

核心目标是复盘最近 6 个迭代，判断 O5/O6 连续 Micro 和重复 blocker 是否已经偏离 rober 北极星，并把下一轮执行约束写回 OKR：后续不能继续 micro 化，必须启动跨 owner Epic，用真实 runtime、HIL、现场图片、地图或 operator workflow 证据推动 O2/O3/O7/O1。

## 实际改动

- `OKR.md`
  - 重写当前 OKR 复盘内容，新增“最近 6 个迭代问题”和员工状态判断。
  - 新增 Objective 8：Epic 交付节奏与证据治理，并写入 `KR-O8-Epic-Cadence`、`KR-O8-Evidence-Type-Gate`、`KR-O8-Repeated-Blocker-Stop`、`KR-O8-Owner-Health`。
  - 保持 O2/O3/O7/O1 为真实能力主线，明确没有真实材料不涨分。
  - 将 O5 从约 96% 打回约 84%，O6 从约 96% 打回约 82%，并写明不再抢占下一轮主线的理由和不涨分边界。
  - 明确下一轮实现类 sprint 必须是 Epic，不能继续用 Micro、runbook、collector、fixture 或 software guard 替代真实交付。
- `docs/process/okr_progress_log.md`
  - 在 2026-06-04 系列顶部追加 `2026-06-04 16-05｜OKR six-sprint strategy rewrite` 对应记录。
  - 记录最近 6 个迭代、O5/O6 打回原因、O8 新增、员工状态和下一轮 Epic KR。
- `sprints/2026.06.04_16-05_okr-six-sprint-strategy-rewrite/tech-done.md`
  - 创建本 micro sprint 留档，记录实际改动、验证结果、失败定位、剩余风险和 OKR/员工状态摘要。

## 最近 6 个迭代问题

| Sprint | 问题判断 | 证据边界 |
| --- | --- | --- |
| `08-09_o5-o6-upper-ssh-preflight` | 增强了 SSH collector preflight/failure classification，但没有 accepted live artifact。 | `software_guard`，O5/O6 不涨分。 |
| `09-10_o5-o6-upper-ssh-live-material` | SSH 可达，但 artifact 为 `fail_closed`，blocked 在 PC base URL、cloud base URL、remote bearer token。 | 重复消费生产配置 blocker，不是 production live material。 |
| `10-11_agent-proactive-kr-reward-rule` | 主动 KR 奖励规则落地，但这是流程资产，不是产品 KR 完成。 | 可进入 O8，不给 O1-O7 涨分。 |
| `10-11_o5-o6-upper-ssh-installed-probe` | installed probe 同步成功，但仍 `fail_closed`，同一 URL/token/cloud blocker 未解。 | O5/O6 96% 口径虚高，需要打回。 |
| `11-12_okr-strategy-reset-real-control-slam-elevator` | Product 打回 O1/O2/O3/O7 的方向正确，但只完成口径重置。 | 没有 runtime/HIL 证据。 |
| `12-13_real-control-slam-elevator-field-epic` | 四个 L2 owner 并行完成 software guard，但没有真实 runtime/HIL/现场图片/地图/控车。 | 方向继续，比例不涨；下一轮必须进真实材料 Epic。 |

综合判断：最近 6 个迭代的问题不是 agent 没产出，而是产出过多停在入口、runbook、fixture、fail-closed artifact 和 software guard。它们有工程价值，但不能继续包装成产品完成度。

## 员工状态判断

| 角色 | 状态 | 下一轮要求 |
| --- | --- | --- |
| User Touchpoint Full-Stack Engineer | 执行力强，但最近 O5/O6 Micro 偏多，偏离真实 operator workflow。 | 转向 O7 真实 8787/browser runtime，优先 PC radar/map/localize/manual 现场材料。 |
| Robot Software Engineer | 12-13 已把 upper API/map/localize/elevator readback guard 做实。 | 接 ROS2 runtime、SLAM `/map`、AMCL、Nav2 lifecycle 和真实 command hook。 |
| Robot Algorithm Engineer | OpenCV taxonomy、ROI/rule baseline、Nav2 map quality fixture 已可复跑。 | 接真实或受控图片 manifest 和真实 map artifact，不再只扩 fixture。 |
| Hardware Infra Engineer | HIL 安全边界、vendor 引用和 LiDAR/base 隔离准入清楚。 | 满足安全条件时做 stop-first 低速 pulse；不满足时升级 blocker。 |
| Product Manager / OKR Owner | 已打回 O1/O2/O3/O7，本轮继续打回 O5/O6 并新增 O8。 | 每轮收口必须查 Micro/Epic 比例、最近 2 轮 blocker 和 evidence type。 |

## OKR 调整

- O2/O3 继续是产品主线：普通用户价值仍是跨楼层 trash delivery，不是 collector 或 status 面。
- O7 是把真实能力变成 operator workflow 的入口，下一轮必须连接真实 8787/browser runtime。
- O1 是安全和硬件可信底座，HIL、`T=1001` 同场边界、ROS feedback topic 和 `safe_to_control` 仍不能越界。
- O5/O6 继续存在，但降为支线；若没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 或真实上车数据，不得涨分。
- O8 新增为组织执行 Objective，约束 Epic 节奏、evidence type、重复 blocker 和 owner health；O8 不新增产品能力，也不能替代 O1-O7 的真实材料。

## 下一轮必须 Epic

本轮是文档 micro，但后续执行不能继续 micro 化。下一轮实现类 sprint 必须是跨 owner Epic，至少覆盖 O2/O3/O7/O1 中两个 Objective，并完整产出：

`pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`

最低要求：

- `tech-plan.md` 必须包含 OKR 最低优先级核对、最近 2 轮 blocker scan、evidence type gate、owner health 检查和不继续 O5/O6 Micro 的理由。
- `tech-done.md` 必须按 owner 记录真实命令、artifact、失败定位和 not_proven 边界。
- `final.md` 必须复核是否真的产出 `robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material`；没有真实材料时不得涨产品 Objective。

## 验证结果

已运行：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_16-05_okr-six-sprint-strategy-rewrite/tech-done.md
```

结果：通过，无 whitespace error。

```bash
rg -n "O8|最近 6 个迭代|Micro|Epic|KR-O8|2026-06-04 16-05" OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_16-05_okr-six-sprint-strategy-rewrite/tech-done.md
```

结果：通过，三份文件均命中 O8、最近 6 个迭代、Micro/Epic、KR-O8 和 2026-06-04 16-05 相关内容。

```bash
git diff -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_16-05_okr-six-sprint-strategy-rewrite/tech-done.md
```

结果：通过，diff 仅包含允许范围内的 OKR、进度日志和本 sprint 留档改动。

## 失败定位

本轮没有命令失败。

本轮定位到的产品/组织问题是：O5/O6 在最近 6 个迭代里重复消费 URL/token/cloud 配置 blocker，虽然不断增强 collector 和 installed probe，但没有形成 accepted live artifact；12-13 的 O2/O3/O7/O1 Epic 方向正确，但仍停在 software guard，缺真实 runtime/HIL/现场材料。因此本轮选择打回 O5/O6、增加 O8，并把下一轮约束为真实材料 Epic。

## 剩余风险

- 本轮是文档 micro，不产生真实 runtime、HIL、现场图片、地图、PC 控车、生产云或手机用户验收材料。
- O8 只是治理约束，不证明产品能力；后续必须靠 Epic 真实材料给 O1/O2/O3/O7/O5/O6 涨分。
- O5/O6 打回是基于证据边界收紧，不代表 collector、archive、acceptance queue 等软件入口无价值；它们后续只能在真实生产材料就绪时再支撑涨分。
- 如果下一轮继续拆成 Micro 或继续围绕同一 O5/O6 blocker 产出 fail-closed artifact，必须升级 CEO 决策或切回 O2/O3/O7/O1。

## 完成前反思

- 需求满足：已在 OKR、进度日志和 sprint 留档中写入最近 6 个迭代问题、员工状态、O8、新 KR、O5/O6 打回和下一轮 Epic 约束。
- 文件范围：只涉及 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint `tech-done.md`，未改产品代码、测试代码、硬件配置或其他文档。
- 验证缺口：按本轮文档任务已完成 diff check、关键词检索和 diff 复核；真实硬件/ROS2/云端验证不属于本 micro sprint。
