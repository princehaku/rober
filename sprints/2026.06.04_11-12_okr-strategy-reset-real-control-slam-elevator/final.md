# Final: OKR Strategy Reset

## sprint_type

epic

## 最终结论

本轮 Epic 完成的是 Product/OKR 口径重置和下一轮真实能力 Epic 边界定义，不新增 runtime 完成度，不新增代码能力，不证明 PC 真实控车、雷达一键开关、SLAM/定位、OpenCV 电梯识别、HIL 或 O5/O6 accepted live material。

方向判断：继续，但从“连续 micro sprint 堆 software proof”调整为“下一轮跨 owner Epic 打真实能力闭环”。当前最高优先级为 O2/O3，其次 O7/O1，O5/O6 保持继续但不抢占下一轮真实现场能力。

## 实际改动

- `OKR.md`
  - O2/O3 从历史归档撤回当前推进区。
  - O1 从约 97% 打回约 95%。
  - O2 从历史归档软件完成约 99% 打回约 72%。
  - O3 从历史归档软件完成约 99% 打回约 73%。
  - O7 从约 98.9% 打回约 88%。
  - O5/O6 保持约 96%，明确只有真实生产云、4G/公网、DB/queue、OSS、phone/browser、上车数据材料才涨分。
- `docs/process/okr_progress_log.md`
  - 追加 2026-06-04 11-12 OKR 打回记录、证据来源、owner 切分和剩余风险。
- `sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/`
  - 补齐 Epic 六文档链：`pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`。

## OKR 收口

| Objective | 最终口径 | 方向判断 | 历史/当前处理 |
| --- | --- | --- | --- |
| O1：硬件协议可信底盘 | 约 95% | 继续并打回 | 当前推进区 |
| O2：可送垃圾任务 + 电梯 assisted delivery | 约 72% | 调整 | 从历史归档撤回当前推进区 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 调整 | 从历史归档撤回当前推进区 |
| O5：云中转控制面 | 约 96% | 继续 | 保持，不涨分 |
| O6：云端核心后端 | 约 96% | 继续 | 保持，不涨分 |
| O7：PC 运营调试平台 | 约 88% | 继续并打回 | 当前推进区 |

本轮没有已完成 KR 进入历史完成区；本轮是已完成口径纠偏，不是业务能力完成。O2/O3 旧“软件完成约 99%”记录保留在 `docs/process/okr_progress_log.md` 作为历史，不再占用当前 OKR 完成度。

## 打回证据和不可外推边界

### O2

打回原因：电梯 assisted delivery 当前材料停在合同、dry-run、fixture 和 ORB visual gate。

不可外推：OpenCV 电梯语义识别、楼层 OCR、目标楼层确认、真实进出电梯、跨楼层送达、真实手机用户验收。

### O3

打回原因：`learn.launch.py`、`/trashbot/save_map` Trigger 和 Nav2 include 只是入口。

不可外推：`/map` artifact、reset/save/load、AMCL `/initialpose`、定位恢复、Nav2 消费 `/scan`+map、路线现场通过。

### O7

打回原因：PC WASD/按钮和同源代理只证明软件链路；雷达没有一键开启/关闭；建图定位没有 PC -> ROS2 控制链。

不可外推：真实 PC WASD 控车、真实雷达开关、真实建图控制、真实定位恢复、production operator workflow、robot ACK 或 HIL。

### O1

打回原因：`/dev/ttyS5` 可写、非运动 `T=130 -> T=1001` 和 LiDAR 首个 `/scan` smoke 不等于底盘闭环。

不可外推：`safe_to_control=true`、HIL pass、robot ACK、真实 `/odom`、`/imu/data`、`/battery`、SLAM/Nav2 消费、闭环运动安全。

## O5/O6 处理

O5/O6 不涨分，继续约 96%。本轮没有 accepted live material，也没有真实生产云、真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实 robot command 执行、真实 OSS/推理或真实上车数据回放。

后续 O5/O6 可继续推进，但涨分必须来自 production 级材料，而不是 collector、runbook、status/readback、fail-closed artifact 或只读文档。

## 下一轮 Epic Owner 切分

| Owner | 文件/能力边界 | 验收口径 |
| --- | --- | --- |
| User Touchpoint Full-Stack Engineer | PC operator workflow、WASD、雷达 start/stop、建图/定位控制、operator report | 真实 PC browser 复跑；W/S/A/D/Space/X 和 stop 形成 manual response、post-status、失败原因、evidence ref；雷达和建图控制只走后端 API |
| Robot Software Engineer | upper API、SLAM Toolbox、map lifecycle、AMCL、Nav2 lifecycle、电梯状态链 | `/map` once、map file、metadata、reset/save/load、AMCL pose、TF、Nav2 lifecycle 和电梯状态 artifact 可回放 |
| Robot Algorithm Engineer | OpenCV 电梯识别、样本/ROI/rule baseline、offline eval、Nav2 map quality | taxonomy、样本清单、正负例、阈值、混淆项、不可判定策略和 map quality metrics 有 artifact |
| Hardware Infra Engineer | WAVE ROVER HIL、低速短 pulse、stop/post-status、`T=1001` 同场、LiDAR start/stop/udev/长稳 | 现场安全前提成立；forward/back/left/right/stop 都有日志、manual response、stop response、post-status 和 operator report |

## 下一轮验收命令建议

- Full-stack：`cd pc-tools/workstation && npm test -- --run`、`npm run build`、`npm run lint`、Playwright rendered smoke。
- Robot Software：targeted `python3 -m unittest`、`python3 -m compileall -q ...`、Docker/Humble build 或 ROS2 smoke。
- Algorithm：OpenCV offline eval artifact checker、sample manifest checker、Nav2/map quality smoke。
- Hardware：vendor-readback、serial/HIL smoke、operator report artifact、scoped `git diff --check`。

## 风险和后续影响

- OKR 表观完成度下降是主动纠偏，不是交付倒退；风险是后续 sprint 必须按真实材料交付，不能再用文案、mock 或入口补进度。
- 下一轮 Epic 跨 owner 且接口耦合，需要先补完整 `tech-plan.md`，再按 owner 分派实现和验证。
- 真实电梯、底盘和路线材料依赖现场条件，缺场地或安全观察员时只能做 mock/fixture 开发，不能写成真实完成。
- O4 暂未打回；若真实手机端发车、状态展示、接管或用户验收成为 CEO 重点，应由 Product/OKR Owner 单独拉回当前推进区。
