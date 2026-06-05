# PRD: O10 AMCL/Nav2 Readiness + Browser Workflow + Field Gates

## 用户价值和产品北极星

本轮 PRD 的目标是让 O10 从“能读到正确路径的地图材料”推进到“可以判断是否具备受控送达下一步条件”。对普通手机用户而言，这不是一个后台技术任务，而是未来能否安全完成送垃圾任务的关键前置：

- 机器人需要知道当前 map 是否足以进入定位和规划准备。
- 运营人员需要在 PC 浏览器里一键触发和查看材料，避免只靠 SSH/curl。
- 电梯跨楼层需要真实/受控图片，而不是只靠离线假样本。
- 任何可能运动的 HIL 都必须先 stop-first、安全授权、可急停。

产品北极星保持：低成本 trash delivery，不做机械臂捡垃圾，不要求普通用户理解 ROS2、串口、map file 或硬件调试。

## 背景事实

- 08-09 已取得 no-motion `/scan` once、`/map` once、metadata、PGM/YAML 落盘和 latest/readback clean success。
- 12-13 已完成 Path Contract Lock：canonical latest JSON 为 `/root/rober/onboard/runtime/map_lifecycle_latest.json`，canonical map artifacts 为 `/root/rober/onboard/runtime/maps`。
- 当前 O10 约 7%，只计入 Path Contract Lock；AMCL/Nav2、PC browser workflow、电梯图片 eval、stop-first HIL 都未完成。
- 本轮不能重复消费 latest/readback/status，也不能把 PC curl/API smoke 写成浏览器验收。

## 范围内

### KR-O10-AMCL-Nav2-Readiness

基于 canonical latest JSON 指向的真实 map artifact，形成 AMCL/Nav2 readiness 前置材料：

- 读取 map artifact 和 metadata。
- 校验 map frame、resolution、width/height、origin、waypoint manifest 是否一致。
- 准备同一 `map` frame 的 fixed-route waypoint manifest。
- 在 no-motion 边界内验证 AMCL/Nav2 lifecycle、`/initialpose` 或 planner/controller 可进入 readiness 状态。
- 如果无法启动 lifecycle 或地图质量不足，输出 root cause 与下一步修复命令。

验收结论只能是 readiness / blocked，不得写成地图可导航、路线通过或真实送达。

### KR-O10-PC-Button-Workflow

把 PC proof 从 API smoke 推进到浏览器按钮级 workflow：

- 浏览器或 Playwright 点击 refresh scan proof、map proof latest、localize/map control 相关按钮。
- UI 展示 hz、TF、fallback、artifact、failure reason、canonical path、fail-closed 安全字段。
- 失败时必须显示 upper path、HTTP 状态、adapter/source 或 not_proven reason。
- 截图、Playwright trace 或浏览器日志必须落到本轮 evidence 或 tech-done 描述中。

验收结论只能是 browser workflow proof / blocked，不得写成 PC WASD、真实控车、HIL 或 production operator workflow 完成。

### KR-O10-Elevator-Image-Eval

电梯 assisted delivery 从 fixture 向真实/受控图片 eval 推进：

- 收集或引用真实/受控电梯图片 manifest。
- manifest 必须包含 image refs、拍摄场景、目标楼层或门状态标签、同一 evidence_ref、样本边界。
- OpenCV eval 输出 false positive、false negative、uncertain、阈值、混淆项和人工接管策略。
- 如果无图片资源，产出 CEO 决策 blocker，说明需要什么资源、多少张样本、怎样采集。

验收结论不能写成真实电梯识别完成、目标楼层识别完成或跨楼层送达完成。

### KR-O10-Stop-First-HIL-Gate

建立 stop-first HIL 决策门：

- 现场看护、净空、急停/断电、授权四项齐备才允许低速 pulse。
- 低速 pulse 必须先 stop/preflight，再短 pulse，再 stop/post-status，再 operator report。
- 不满足任一前提时，产出 CEO 决策 blocker，不做运动，不写 HIL pass。
- 所有材料必须引用 vendor 文档来源，不凭记忆写引脚、电压、UART、波特率、JSON 指令或反馈协议。

验收结论只能是 `field_hil_material` 或 `blocked_with_root_cause`。

### KR-O10-Delivery-Readiness-Chain

Product 在收口阶段把四段材料串成 delivery-readiness chain：

- AMCL/Nav2 readiness：pass / blocked。
- PC browser workflow：pass / blocked。
- Elevator image eval：pass / blocked。
- Stop-first HIL gate：pass / blocked / CEO decision needed。
- 明确证据链接、证据边界、不可外推项和下一步低速受控送达条件。

## 范围外

- 不做真实送垃圾完成声明。
- 不做真实跨楼层送达完成声明。
- 不做 PC WASD 或真实控车，除非 HIL owner 在安全授权下明确执行 stop-first 低速 pulse。
- 不改 OKR.md。
- 不改上一轮 12-13 sprint 文件。
- 不扩写 latest/readback/status 或单纯 runbook。
- 不做 production cloud、4G、手机端真实验收。

## 验收口径

| 能力 | 可接受证据 | 不可接受证据 |
| --- | --- | --- |
| AMCL/Nav2 readiness | map quality + waypoint manifest + lifecycle/readiness/no-motion planner evidence 或 root cause | 只读 latest JSON、只列 map 文件、只写计划 |
| PC browser workflow | 浏览器点击、Playwright、截图或浏览器日志 + UI 展示 fail-closed 字段 | 只有 curl、只有 API unit test、只有文案 |
| 电梯图片 eval | 真实/受控图片 manifest + OpenCV eval + FP/FN/uncertain + 人工接管策略 | fixture/template/taxonomy 扩写 |
| Stop-first HIL | preflight + stop + low-speed pulse + stop/post-status + operator report，或 CEO blocker | 无授权运动、只写安全说明、只跑软件 test |
| Delivery-readiness chain | `tech-done.md`、`side2side_check.md`、`final.md` 串联 pass/blocked 和证据边界 | 聊天口头收口或把 readiness 写成 delivery success |

## 对应责任 Engineer

| Owner | 责任 |
| --- | --- |
| Robot Software Engineer | AMCL/Nav2 readiness 的 ROS2/bringup/lifecycle 接口集成，确保 no-motion 安全字段和 map path contract 消费正确。 |
| Robot Algorithm Engineer | map quality、waypoint manifest、AMCL/Nav2 readiness 评估、电梯图片 manifest 与 OpenCV eval。 |
| Full-stack Software Engineer | PC browser button workflow、same-origin API 展示、Playwright/浏览器证据和 fail-closed UI。 |
| Hardware Infra Engineer | stop-first HIL 安全前提、vendor source 复核、现场授权 blocker 或低速 pulse 材料。 |
| Product Manager / OKR Owner | 证据边界、OKR 方向、KR 收口、`tech-done.md / side2side_check.md / final.md` 和后续 OKR 更新。 |

## 需要补齐的证据链

- `robot_runtime_material`：AMCL/Nav2 readiness 和 map/waypoint material。
- `user_acceptance_material` 或 browser workflow material：PC 浏览器按钮级触发与展示。
- `field_precondition_material`：真实/受控电梯图片 manifest 和 eval。
- `field_hil_material` 或 `blocked_with_root_cause`：stop-first HIL。
- `delivery_readiness_chain`：Product 阶段收口，不等于 delivery success。

## CEO 决策点

如果本轮无法获得真实/受控电梯图片或 HIL 安全前提，需要 CEO 在下一轮前明确：

- 是否提供现场看护、净空、急停/断电和授权。
- 是否提供固定楼宇/电梯/目标楼层图片采集资源。
- 是否暂停 HIL 或电梯图片 KR，转向 AMCL/Nav2 与 PC browser workflow。
- 是否允许仅用 controlled pre-field material 先推进 O10 readiness。

