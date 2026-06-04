# Final: Runtime Material Epic

## 收口结论

方向判断：**继续，但继续收紧完成度口径**。本轮证明团队已经能按 O8 做跨 owner Epic 证据治理，也拿到了部分真实上位机 runtime material；但 rober 的产品北极星仍没有完成现场闭环。普通用户价值仍卡在 O2/O3/O7/O1 的真实电梯图片、SLAM/map/localize runtime、PC operator 现场链路、stop-first HIL。

本轮 OKR 调整：

- O7：约 88% -> 约 89%。理由是 `upper_http_405` 已由 Robot Software 修复并部署到真实上位机 8787，Full-Stack 通过 PC 同源代理复测 `POST /api/o7/direct-upper/operator-report`，返回 HTTP 200、`accepted_by_workstation=true`、`upper_request.ok=true`、`failure_reason=none`，evidence_ref=`2026.06.04_17-18_operator_report_pc_same_origin_retest`。
- O8：约 35% -> 约 40%。理由是本轮完成首轮有效 Epic governance evidence：owner notes、evidence type gate、blocker scan、owner health、side-to-side、final 和 OKR/log 更新。
- O1：保持约 95%。理由是非运动 `/dev/ttyS5 @115200`、`T=130 -> T=1001` 3/3 是有效 `robot_runtime_material`，但没有 `field_hil_material`、运动 pulse、stop/post-status、ROS feedback 或 `safe_to_control=true`，所以只记录材料增强不涨分。
- O3：保持约 73%。理由是上位机 ROS2 与包安装存在，但 application nodes 未运行，`/scan`、`/map`、AMCL、TF、Nav2 lifecycle 和 artifact 均缺。
- O2：保持约 72%。理由是无真实/受控电梯图片 manifest，fixture eval 只能算 `software_guard`，状态仍是 `needs_real_image_manifest`。
- O5/O6：保持 O5 约 84%、O6 约 82%，本轮不触达 production live material。

## 本轮核心抓手

核心抓手是把“真实材料不足”从泛泛风险变成 owner 可执行的 root cause：

1. Robot Software：启动受监督 non-motion ROS2 runtime，采 fresh `/scan`、`/map`、TF、AMCL/Nav2 或明确 supervisor blocker。
2. Full-Stack：把已通过的 PC operator report 写入链路接到 UI/operator workflow，可展示同一 evidence ref 和 fail-closed 边界，但不能启用控车完成态。
3. Algorithm：采集真实/受控 elevator image manifest，不再扩 fixture 代替 field eval。
4. Hardware：只有现场看护、净空、急停和授权同时满足，才做 stop-first low-speed pulse；否则继续 `safe_to_control=false`。
5. Product：每轮只让 `robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material` 支撑产品涨分。

## 责任 Engineer 和验收口径

| 优先级 | 下一步 | Owner | 验收口径 |
| --- | --- | --- | --- |
| P0 | O3/O7 non-motion ROS2 runtime | Robot Software Engineer | `/scan` once/hz、`/lidar/raw_packet` fresh、`/map` 或 map artifact、TF/AMCL/Nav2 lifecycle；缺失时写 root cause。 |
| P0 | O7 operator report UI/field-chain integration | Full-Stack Engineer + Robot Software Engineer | PC UI/operator flow 能展示和回放 `2026.06.04_17-18_operator_report_pc_same_origin_retest` 同类 evidence；保持 `safe_to_control=false`，不包装成控车。 |
| P0 | O2 controlled elevator manifest | Robot Algorithm Engineer + 现场 owner | `trashbot.elevator_image_manifest.v1`，真实/受控图片满足 field gate，OpenCV eval 输出 false positive/negative 和不可判定策略。 |
| P1 | O1 stop-first HIL | Hardware Infra Engineer + Full-Stack Engineer | operator preflight、现场看护、净空、急停、低速短 pulse、auto-stop/post-status、`T=1001` 同场、operator report、视频/现场记录。 |
| P1 | O8 持续治理 | Product Manager / OKR Owner | 下一轮 final 继续复核最近 2 轮 blocker、evidence type、owner health 和是否有虚假涨分。 |

## 风险、阻塞和证据链缺口

- O3/O7：8787 live 不等于 ROS2 runtime nodes live；当前缺 command hook/supervisor 和 fresh topic/artifact。
- O7：operator report route 已通，但只是非运动 evidence artifact；还没有 PC WASD、stop/急停、ACK、现场视频或 production archive ingestion。
- O2：没有图片 manifest 时算法无可验收 field material；fixture eval 不能涨分。
- O1：非运动 `T=1001` 不等于 robot ACK、HIL 或 ROS feedback；运动前仍需现场安全准入。
- O5/O6：真实生产云、4G、DB/queue、OSS、phone/browser 仍缺，本轮不应抢主线。

## 历史记录位置

- O7 `upper_http_405` blocker 解除记录在 `docs/process/okr_progress_log.md` 的 `2026-06-04 17-18` 节，以及 `owner_notes/robot-software-engineer-operator-report-deploy.md`、`owner_notes/full-stack-software-engineer-operator-report-retest.md`。
- O8 治理 KR 进展记录在 `docs/process/okr_progress_log.md` 的 `2026-06-04 17-18` 节，以及本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`。
- O1/O2/O3 未完成 KR 不进入完成归档；只记录 blocker 和下一步。

## 新 KR / CEO 决策点

本轮不新增正式 KR，只把既有 KR 的下一步验收口径收紧。需要 CEO/现场负责人决策：

- 是否在下一轮提供现场看护、物理净空、人工急停和明确授权，用于 O1/O7 stop-first 低速 pulse。
- 是否安排受控电梯图片采集，回填 `trashbot.elevator_image_manifest.v1`，否则 O2 会继续停在 `needs_real_image_manifest`。

## 验证记录

Product 收口验证命令：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_17-18_runtime-material-epic/tech-done.md sprints/2026.06.04_17-18_runtime-material-epic/side2side_check.md sprints/2026.06.04_17-18_runtime-material-epic/final.md
```

结果：exit code 0，无输出。

```bash
rg -n "O7|O8|upper_http_405|operator_report|T=130|T=1001|needs_real_image_manifest|not_proven|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_17-18_runtime-material-epic
```

结果：exit code 0。关键命中包括：

```text
OKR.md:228 O7 约 89%，真实上位机 8787 operator report route 已部署，PC 同源代理可写入并回放同一 evidence_ref。
OKR.md:229 O1 保持约 95%，`T=130 -> T=1001` 3/3 是材料增强但不涨。
OKR.md:232 O8 约 40%，首轮跨 owner Epic 完成治理证据链。
docs/process/okr_progress_log.md:43 O8 约 35% -> 约 40%。
docs/process/okr_progress_log.md:44 O7 约 88% -> 约 89%，operator report route 已部署并由 PC 同源代理复测。
docs/process/okr_progress_log.md:45 O1 保持约 95%，`safe_to_control=true` 仍未证明。
sprints/2026.06.04_17-18_runtime-material-epic/tech-done.md:31 evidence_ref=`2026.06.04_17-18_operator_report_pc_same_origin_retest`。
sprints/2026.06.04_17-18_runtime-material-epic/side2side_check.md:25 O2 `needs_real_image_manifest`。
```

说明：该 `rg` 命令按用户要求扫描整个 sprint 目录，因此也会命中 `owner_notes/full-stack-software-engineer.md`
里 18:12 CST 的旧 `upper_http_405` 失败记录；最终收口以之后的
`owner_notes/robot-software-engineer-operator-report-deploy.md` 和
`owner_notes/full-stack-software-engineer-operator-report-retest.md` 为准，结论是旧 blocker 已解除。

## 完成前反思

- 本轮没有回滚或覆盖他人代码改动；产品代码、测试代码、硬件配置、owner notes、pre_start/prd/tech-plan 均未被 Product 修改。
- O7/O8 的小涨分有证据来源和边界；没有把 O1/O2/O3 的 blocker 包装成完成。
- 没有把 happy path 写成闭环；所有 not_proven 边界仍保留。
- 剩余最大风险是下一轮如果不直接采 ROS2 runtime、图片 manifest 和 HIL，O2/O3/O1 会继续被 blocker 消费。
