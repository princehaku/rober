# PRD: O9 Narrow Runtime Material Epic

## 用户价值

用户不需要理解 SSH、ROS2、雷达 topic、OpenCV 或 WAVE ROVER；用户需要的是小车能安全知道环境、能被 PC/手机可信监控、能识别电梯场景，并在现场安全不足时明确停住。O9 当前约 18%，问题不是缺更多描述，而是缺真实/受控材料。

## 产品北极星

继续做低成本自主垃圾投递机器人：用户交付垃圾，小车沿固定路线送达垃圾站，必要时人工协助跨电梯，并在异常时安全停止和留下证据。

## 本轮范围

必须覆盖四个单 artifact：

| Owner | Artifact | 用户价值 | evidence_type |
| --- | --- | --- | --- |
| Full-stack Software Engineer | PC 同源 refresh 复验证据 | operator 能确认 PC 按钮/API 真正触发 live upper 8787，而不是只看本地 mock/readback。 | `robot_runtime_material` 或 `blocked_with_root_cause` |
| Robot Software Engineer | continuous radar/status 或 SLAM `/map` lifecycle 证据 | 建图/定位/固定路线获得下一步 runtime 材料，不重复 01-02 latest proof。 | `robot_runtime_material` 或 `blocked_with_root_cause` |
| Robot Algorithm Engineer | 真实/受控电梯图片 manifest + OpenCV eval | 电梯 assisted delivery 从 fixture 转向真实/受控图片，产出误判和人工接管边界。 | `robot_runtime_material` 或受控 field 前置材料 |
| Hardware Infra Engineer | stop-first HIL 决策门 artifact | 现场安全满足才允许低速 pulse；不满足时让 CEO 明确补资源或暂停。 | `field_hil_material` 或 `blocked_with_root_cause` |

## 非目标

- 不更新 `OKR.md`，不因计划文档上调完成度。
- 不把 PC 同源 readback 写成 PC 控车成功。
- 不把 fresh scan proof 或 `/api/radar/status` readback 写成 continuous radar ready、SLAM 完成、Nav2 可用。
- 不把 fixture 电梯图片写成真实/受控电梯材料。
- 不在缺少现场看护、净空、急停和授权时做 HIL 运动。

## 验收口径

- PC 同源：必须能通过 PC 链路触发 live 8787 `POST /api/radar/scan-proof/refresh`，并展示 hz、TF、`runtime_summary_fallback_used`、fresh proof 与 `continuous_scan_status=not_proven` 边界。
- continuous radar/SLAM：必须产生新 evidence ref；要么收敛 `/api/radar/status` continuous blocker，要么产出 SLAM `/map` once、map artifact、metadata 和失败原因。
- 真实/受控电梯：manifest 必须标注样本来源、门线/轿厢/楼层屏 ROI、不可判定样本；OpenCV eval 必须输出 false positive、false negative、阈值和人工接管策略。
- stop-first：只有现场看护、净空、急停、授权满足时才允许低速短 pulse；否则必须输出 CEO blocker，不允许 HIL pass 文案。

## 风险和证据链

- 当前上位机入口：`ssh root@192.168.1.11 -p 37878`。
- 关键风险：远端 8787 未加载最新代码、PC parser/UI 仍失败、SLAM `/map` 缺 runtime、真实/受控电梯图片没有、现场 HIL 安全条件不足。
- 需要补齐的证据链：每个 owner 后续必须在 `tech-done.md` 写实际命令、输出片段、artifact path、evidence_type、失败定位和剩余风险。
