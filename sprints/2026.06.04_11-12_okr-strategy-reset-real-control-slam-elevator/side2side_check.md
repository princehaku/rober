# Side To Side Check: OKR Strategy Reset

## sprint_type

epic

## 检查结论

本轮 side-to-side 验收通过，验收对象仅限 Product/OKR 口径打回和下一轮 Epic 边界，不包含任何新增 runtime、HIL、OpenCV、SLAM、PC 控车或云端生产材料完成度。

本轮把 OKR 从“软件入口已存在”对齐回“普通用户 trash delivery 可现场验证”。北极星仍是：普通手机用户把垃圾交给低成本小车后，小车能沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。

## 用户价值核对

| 用户/触点 | 本轮前风险 | 本轮口径修正 | 验收结论 |
| --- | --- | --- | --- |
| 普通手机用户 | OKR 进度看起来接近完成，但真实送达、电梯、定位和安全接管未被证明 | 把 O2/O3 拉回当前推进区，明确真实 OpenCV、电梯状态链、SLAM/map/AMCL/Nav2 才能涨分 | 通过 |
| PC operator | PC WASD、雷达和地图能力容易被 UI/API 软件入口冒充为现场可用 | 把 O7 打回，要求真实 PC WASD、雷达 start/stop、建图/定位控制和 operator report | 通过 |
| 硬件集成 | LiDAR 首个 `/scan` 和 `T=1001` feedback 容易被外推为底盘闭环或 robot ACK | 把 O1 打回，要求低速短 pulse、stop/post-status、ACK/T=1001 同场、ROS feedback topics 和 HIL | 通过 |
| 云端材料 | O5/O6 连续 micro sprint 容易继续堆 runbook/status/readback | 明确 O5/O6 保持约 96%，没有 accepted live material 不涨分 | 通过 |

## OKR 映射和方向判断

| Objective | 本轮判断 | 当前比例口径 | 是否新增 runtime 完成度 |
| --- | --- | --- | --- |
| O1：硬件协议可信底盘 | 继续并打回 | 约 95% | 否 |
| O2：可送垃圾任务 + 电梯 assisted delivery | 调整，撤回当前推进区 | 约 72% | 否 |
| O3：建图、定位、Nav2 与固定路线 | 调整，撤回当前推进区 | 约 73% | 否 |
| O5：云中转控制面 | 继续但不抢占下一轮 Epic | 约 96% | 否 |
| O6：云端核心后端 | 继续但等待真实上车材料 | 约 96% | 否 |
| O7：PC 运营调试平台 | 继续并打回 | 约 88% | 否 |

方向判断：继续推进 rober 北极星，但调整当前优先级。下一轮应从 O2/O3 的真实送达和建图定位缺口切入，同时联动 O7 PC operator workflow 和 O1 现场 HIL；O5/O6 保持当前口径，等待真实云、4G、production DB/queue、OSS、phone/browser 或上车数据材料。

## 打回证据边界

### O2 打回边界

- 可计入：产品 contract、dry-run evidence schema、fixture/diagnostics、ORB visual gate 软件材料。
- 不可外推：真实相机电梯识别、门线/轿厢/楼层语义识别、目标楼层确认、OpenCV rule baseline 有效、实景进出电梯、跨楼层送达。
- 下一步验收：OpenCV taxonomy、真实或受控样本、ROI/rule baseline、offline eval、ROS2 电梯状态机接入、受控电梯 3 次材料。

### O3 打回边界

- 可计入：`learn.launch.py` 入口、`/trashbot/save_map` Trigger、Nav2 include、首个 LiDAR `/scan` smoke。
- 不可外推：`/map` 建图完成、reset/save/load lifecycle、AMCL `/initialpose`、定位恢复、Nav2 消费 `/scan`+map、固定路线现场通过。
- 下一步验收：map artifact、metadata、AMCL pose、TF、Nav2 lifecycle、map quality metrics 和短距离/固定路线可复跑材料。

### O7 打回边界

- 可计入：PC WASD/按钮软件入口、同源 API、radar/map split、mock/fetch tests、rendered smoke。
- 不可外推：真实 PC WASD 控车、雷达一键开关、建图/定位控制、production operator workflow、stop/急停/operator report。
- 下一步验收：W/S/A/D/Space/X 现场点动、stop/post-status、operator report、雷达 `POST /api/radar/start|stop`、建图/定位按钮到 upper API/ROS2。

### O1 打回边界

- 可计入：`/dev/ttyS5 @115200` 可写入口、非运动 `T=130 -> T=1001` samples、LiDAR `/scan` once/hz、TF。
- 不可外推：`safe_to_control=true`、底盘 HIL pass、robot ACK、真实 `/odom`、`/imu/data`、`/battery`、SLAM/Nav2 消费、闭环运动安全。
- 下一步验收：低速短 pulse、stop/post-status、`T=1001` 同场材料、ROS feedback topics、LiDAR start/stop/udev/长稳和 HIL 复核。

## O5/O6 核对

O5/O6 不涨分，继续约 96%。本轮没有 accepted live material，没有证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实隧道、真实 OSS upload、真实推理 runtime 或真实上车数据回放。

O5/O6 后续只能靠真实生产云、真实蜂窝链路、真实 robot command 执行、真实生产数据链和可查询回放材料涨分；collector、runbook、readback、status 面和 fail-closed artifact 只能算采集通路或护栏。

## 下一轮真实能力 Epic

| Owner | 核心抓手 | 验收口径 |
| --- | --- | --- |
| User Touchpoint Full-Stack Engineer | PC operator workflow、WASD、雷达一键 start/stop、建图/定位控制、stop/急停/operator report | PC 浏览器现场完成 W/S/A/D/Space/X 与 stop，UI 展示 response、post-status、失败原因和 evidence ref；雷达和建图按钮不直连 ROS graph |
| Robot Software Engineer | 8787/upper API、SLAM Toolbox、AMCL `/initialpose`、Nav2 lifecycle、电梯状态机接入 | `/map`、map metadata、reset/save/load、AMCL pose、TF、Nav2 lifecycle 状态和电梯状态链 artifact 可回放 |
| Robot Algorithm Engineer | OpenCV 电梯 taxonomy、样本/ROI/rule baseline、offline eval、Nav2 map quality metrics | 样本清单、正负例、ROI/rule 输出、混淆项、阈值、不可判定策略和 map quality metrics 形成 artifact |
| Hardware Infra Engineer | WAVE ROVER 现场安全前提、底盘 low-speed pulse、stop/post-status、`T=1001` 同场材料、LiDAR start/stop/udev/长稳 | 现场净空、看护、急停可用；forward/back/left/right/stop 低速短 pulse 有 manual response、stop response、post-status、日志和 operator report |

## 剩余风险和证据缺口

- 本轮只完成 OKR 口径和 sprint 文档侧验收，不证明任何新增真实能力。
- 下一轮 Epic 跨四个 owner，接口耦合强，必须先写清 tech-plan 的文件范围、接口契约和验收命令。
- 真实电梯、底盘和路线验证依赖场地、安全观察员、急停和硬件状态；开发阶段允许 mock/fixture，但不得据此上调真实完成度。
- O4 暂留历史归档；若 CEO 后续要求真实手机发车、状态、接管或验收，应单独拉回当前推进区。
