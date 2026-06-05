# Final: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 收口结论

本轮 O10 Epic 有效完成一段 no-motion AMCL/Nav2 runtime proof collector 和 live
blocker artifact。用户价值是把"下一步 AMCL/Nav2 为什么不成立"从抽象风险变成
live 8787 可回放证据：canonical map inputs ready，但 AMCL/Nav2 包、lifecycle 和
ROS topics 均未达到 runtime 条件。

方向判断：**继续**。北极星和 O10 方向不变，但下一轮抓手应从接口/readback 切到
AMCL/Nav2 安装、launch 和 lifecycle bringup；缺资源时升级 CEO 决策，不能把
`blocked_with_root_cause` 写成可导航。

## 逐 Owner 结果

| Owner | 结果 | Evidence type | 证据 |
| --- | --- | --- | --- |
| Robot Software Engineer | Pass as blocked artifact | `blocked_with_root_cause` | 新增 collector；8787 `POST /api/nav2/proof/refresh` 返回 `blocked_with_root_cause`；`GET /api/nav2/proof/latest` artifact `status=loaded`。 |
| Product Manager / OKR Owner | Pass | stage closeout | 补齐 Epic 文档链，更新 O10/O8 涨分、历史归档、不可越界和下一步 CEO blocker。 |

## 核心证据

- 本地验证通过：`python3 -m compileall -q onboard/scripts onboard/src`；
  `python3 -m unittest onboard.scripts.test_upper_robot_api` Ran 38 OK skipped=4；
  `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'` Ran 87 OK skipped=4；
  `git diff --check -- onboard/scripts docs/navigation docs/interfaces sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic` exit 0。
- 远端部署通过：`upper_robot_api.py` 和 `o10_amcl_nav2_runtime_proof.py`
  已同步到 `root@192.168.1.11:/root/rober/onboard/scripts/`，并重启
  `trashbot-upper-robot-api.service`，service active。
- live proof：`POST /api/nav2/proof/refresh` 返回 `blocked_with_root_cause`；
  `GET /api/nav2/proof/latest` artifact `status=loaded`，path 为
  `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。
- root causes：canonical map inputs ready，YAML/PGM 可读；但
  `nav2_amcl_missing`、`nav2_planner_missing`、`nav2_controller_missing`；
  map_server/amcl/planner/controller lifecycle not active；`/scan`、`/map`、
  `/amcl_pose` 未发布；ROS graph 只有 `/parameter_events` 和 `/rosout`。
- 安全边界：no `/cmd_vel`，no `/api/base/manual`，no `/initialpose`，
  no Nav2 goal，no HIL，`safe_to_control=false`。

## OKR 更新

| Objective | 调整 | 理由 |
| --- | --- | --- |
| O10：受控送达闭环实战战役 | 约 10% -> 约 12% | live 8787 blocker artifact 成立，readiness chain 从输入护栏推进到可回放 root-cause 定位。 |
| O8：Epic 交付节奏与证据治理 | 约 50% -> 约 51% | 远端部署、验证结果、root causes、not_proven 边界和下一步 owner 抓手收口。 |
| O3：建图、定位、Nav2 与固定路线 | 保持约 77% | 本轮证明的是 AMCL/Nav2 runtime blocked，不是 localization、path generation 或 path execution。 |
| O7：PC 运营调试平台 | 保持约 94% | 8787 endpoint/readback 有材料，但没有 PC 端消费或 browser workflow。 |
| O9：短周期真实材料破局战役 | 保持约 22% | 本轮不是新的 continuous radar、field/HIL 或 runtime success breakthrough。 |

O1/O2/O5/O6 保持：本轮没有 HIL、真实电梯 eval、production cloud 或 production archive material。

## 历史归档

`KR-O10-AMCL-Nav2-Runtime-Collector` 作为阶段完成项归档到本 sprint：
`tech-done.md`、`side2side_check.md` 和 `final.md`。验收结论是
blocked artifact 成立，剩余风险是 AMCL/Nav2 runtime 本身仍未成立。该归档不移除
O10 当前推进区的 AMCL/Nav2 任务，只是关闭"为什么不成立没有证据"这个缺口。

## CEO 决策 blocker

本轮发现的 Product/OKR 决策 blocker 是：下一轮需要决定是否允许 Robot Software /
Robot Algorithm 进入 AMCL/Nav2 runtime install/launch 专项，补齐 `nav2_amcl`、
planner/controller、map_server/amcl/planner/controller lifecycle 和 `/scan`、`/map`、
`/amcl_pose` runtime。若现场/远端资源不足，需要 CEO 决定提供资源、暂停该 KR，
或切换到 O2 电梯图片 / O1 stop-first HIL。

## 不得越界

本轮不证明 map 可导航、AMCL localization、Nav2 path generation、Nav2 path execution、
fixed route、HIL、delivery success、PC WASD、WAVE ROVER ACK、真实电梯识别、真实手机验收、
production cloud 或 `safe_to_control=true`。
