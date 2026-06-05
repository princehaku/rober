# PRD: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 产品问题

13-14 已证明 canonical map proof 输入护栏，但 CEO 和工程团队仍无法从用户可读
材料中判断 AMCL/Nav2 到底卡在哪里。继续说"Nav2 未就绪"价值有限；需要把原因
落成 live 8787 artifact，让下一轮安装、launch、lifecycle bringup 和 PC 状态展示
有明确事实边界。

## 用户价值和北极星

北极星仍是普通手机用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站/桶点位，
异常时安全停止、请求人工协助并留下可复盘证据。本轮不直接让用户发车，但能让
团队知道"为什么还不能发车"，避免把 map artifact 可读误判成可导航。

## 需求

| 需求 | 验收 |
| --- | --- |
| no-motion AMCL/Nav2 runtime proof collector | 只读检查 canonical map inputs、Nav2/AMCL package、lifecycle、ROS topics 和安全字段 |
| 8787 refresh/latest API | `POST /api/nav2/proof/refresh` 和 `GET /api/nav2/proof/latest` 可部署、可 readback |
| `/api/nav2/status` 暴露 proof routes | operator 能看到 proof refresh/latest route 入口 |
| live blocker artifact | 远端返回 `blocked_with_root_cause`，并列出 `nav2_amcl_missing`、`nav2_planner_missing`、`nav2_controller_missing` 等 root causes |

## OKR 映射

- O10：可小幅上涨，因为新增 live 8787 可回放 blocker artifact，受控送达 readiness
  从输入护栏推进到 runtime 缺口定位。
- O8：可小幅上涨，因为 Epic 证据链、验证结果、不可越界项和后续 owner 抓手清晰。
- O3/O7/O9：不涨。本轮没有 AMCL localization、Nav2 path、PC 消费、continuous radar
  或新的真实材料 breakthrough。

## 非目标

本轮不证明 map 可导航、AMCL localization、Nav2 path generation、path execution、
fixed route、HIL、WAVE ROVER ACK、delivery success、PC WASD、真实手机验收或
`safe_to_control=true`。
