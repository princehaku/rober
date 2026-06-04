# Tech Done: OKR Strategy Reset

## sprint_type

epic

## 实际改动

- `OKR.md`
  - 将 O2/O3 从历史归档区撤回当前推进区。
  - 将 O1 从约 97% 打回约 95%。
  - 将 O2 从历史归档“软件完成 ~99%”打回约 72%。
  - 将 O3 从历史归档“软件完成 ~99%”打回约 73%。
  - 将 O7 从约 98.9% 打回约 88%。
  - 保持 O5/O6 约 96%，但明确下一轮不以云端 runbook/status 面作为最高优先级。
  - 新增或重写 KR：PC WASD 现场控车、雷达一键开启/关闭、建图/SLAM/定位 lifecycle、OpenCV 电梯 taxonomy/ROI/rule/offline eval/ROS2 state integration、ACK/T=1001 同场证据。
- `docs/process/okr_progress_log.md`
  - 追加本轮 OKR 打回原因、证据来源和剩余风险。
- 本 sprint 文档
  - 新增 `pre_start.md`、`prd.md`、`tech-plan.md` 和 `tech-done.md`，记录本轮产品判断、owner 切分、验收口径和下一轮 Epic 要求。

## OKR 改动摘要

| Objective | 原口径 | 新口径 | 原因 |
| --- | --- | --- | --- |
| O1 | 约 97% | 约 95% | LiDAR `/scan` smoke 可计入，但 PC WASD 真实控车、底盘 HIL、ACK/T=1001 同场和 ROS feedback topic 未证明 |
| O2 | 历史归档软件完成 ~99% | 当前推进区约 72% | 电梯 assisted delivery 停在合同、dry-run、fixture 和 ORB visual gate，不是 OpenCV 电梯识别或实景进出电梯 |
| O3 | 历史归档软件完成 ~99% | 当前推进区约 73% | `learn.launch.py`/Nav2 include 不等于 `/map` artifact、reset/save/load、AMCL 定位或 Nav2 消费 `/scan`+map |
| O7 | 约 98.9% | 约 88% | PC WASD/按钮只是软件入口；雷达无一键 start/stop；建图/定位控制未接 ROS2 |
| O5 | 约 96% | 约 96% | 本轮不新增真实生产云材料 |
| O6 | 约 96% | 约 96% | 本轮不新增真实生产数据链材料 |

## 被打回进度和理由

- **O2 打回**：旧归档把电梯状态链和 dry-run 当成软件完成，但 CEO 要求的是进出电梯 OpenCV 打标和识别。当前没有门线/轿厢/楼层语义识别、真实训练样本质量、offline eval、ROS2 状态机真实接入或受控实景材料。
- **O3 打回**：旧归档把学习入口和 fixed-route dry-run 视作接近完成，但当前没有 `/map` 建图证据、reset_map/load_map、PC/upper map API、AMCL lifecycle、`/initialpose`、Nav2 消费 `/scan` 或路径执行。
- **O7 打回**：PC 已有 WASD/按钮和同源代理，但不证明真实小车能被 PC 控制；雷达只有状态/证据，没有一键开启/关闭；建图/定位没有 PC 控制面。
- **O1 打回**：`T=1001 observed` 是 vendor feedback material，不是 robot ACK/HIL；`/dev/ttyS5` 可写入口和 LiDAR `/scan` 首个 smoke 不证明底盘闭环安全、ROS feedback topics 或 Nav2/SLAM 消费。

## 下一轮 Epic 推荐 owner 切分

| Owner | 下一轮 Epic 主责 |
| --- | --- |
| User Touchpoint Full-Stack Engineer | PC WASD 真实 operator workflow、雷达一键 start/stop、建图/定位控制、stop/急停/operator report |
| Robot Software Engineer | 8787/upper map lifecycle、SLAM Toolbox、AMCL `/initialpose`、Nav2 lifecycle glue、电梯状态机接入 |
| Robot Algorithm Engineer | OpenCV 电梯 taxonomy、样本/ROI/rule baseline、offline eval、Nav2 map quality metrics |
| Hardware Infra Engineer | WAVE ROVER 现场安全前提、底盘 low-speed pulse、stop/post-status、`T=1001` 同场材料、LiDAR start/stop/udev/长稳 |

## 验证结果

- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator`
  - 结果：通过，exit 0，无 whitespace error 输出。
- `rg -n "WASD|雷达|建图|SLAM|定位|OpenCV|电梯|打回|Epic" OKR.md sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator docs/process/okr_progress_log.md`
  - 结果：通过，exit 0；命中 `OKR.md`、本 sprint 四个文档和 `docs/process/okr_progress_log.md`，覆盖 WASD、雷达、建图、SLAM、定位、OpenCV、电梯、打回和 Epic。

## 剩余风险

- 本轮是文档和 OKR 口径重置，不产生新 runtime、HIL、OpenCV、SLAM 或 PC 控车证据。
- 下一轮 Epic 必须补全完整六文档；本轮受 CEO 给定文件范围限制，只写到 `tech-done.md`。
- O4 仍留在历史区；若后续 CEO 要求真实手机端发车/状态/接管验收，应单独拉回当前推进区。
- 真实电梯/路线/底盘现场验证受安全场地、观察员、急停和硬件可用性限制；开发阶段可用 mock/fixture，但不得据此涨真实完成度。
