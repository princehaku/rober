# 2026.06.01 10-11 LiDAR ROS2 Driver Skeleton

sprint_type: micro

## 用户价值和产品北极星

本轮把 LiDAR 从“参考资料已入库”推进到“ROS2 软件骨架可验证”，让后续真实上车前已有清晰接口、参数和默认关闭的接入点。北极星仍是低成本 ROS2 自主垃圾投递机器人：传感器能力服务于固定路线、避障、SLAM/Nav2 和可复盘诊断，不把 software reference 或 mock skeleton 夸大成真实硬件闭环。

## OKR 映射和方向判断

- Objective：O1 打通官方硬件协议，建立可信底盘控制层。
- 当前判断：从 `90%+ mock/software completion` 保守更新为 `约 91% software_reference + mock skeleton`。
- 方向判断：继续，不暂停、不替换。LiDAR reference ingest + ROS2 skeleton 是 O1 的软件推进，但真实 LiDAR、真实串口、TF、Nav2/SLAM 和 150000 波特率稳定性仍为 `not_proven`。

## 实际改动

- Robot Software 已在 `ros2_trashbot_hardware` 实现 LiDAR parser/driver skeleton。
- `bringup.launch.py` 已接入 gated LiDAR node，默认 `lidar_enabled=false`，避免无串口或无雷达时阻塞整车 bringup。
- LiDAR 参数已按 mock/serial 可配置方向推进，支持保留 `serial_port`、`serial_baudrate`、`frame_id`、raw packet topic 和 scan output 的后续切换入口。
- Product closeout 本轮只更新 `OKR.md`、`docs/process/okr_progress_log.md` 和本 `tech-done.md`，不改代码、launch、vendor 文件或硬件文档。

## 2026-06-01 12:42 CST 一致性修正

- 修正 `docs/hardware/lidar_ros_reference.md` Stage 2 口径：LiDAR driver/parser 归属 `ros2_trashbot_hardware`，不再写成 `ros2_trashbot_nav`。
- 新增 `docs/interfaces/lidar_ros2_closed_loop.md`，固定 Driver executable 为 `ros2_trashbot_hardware lidar_driver`，Parser module 为 `ros2_trashbot_hardware.lidar_packets`。
- 复核 `bringup.launch.py` gated LiDAR node：已指向 `package='ros2_trashbot_hardware'` 和 `executable='lidar_driver'`，不需要迁移代码。
- 复核 OKR：当前 O1 已写 `ros2_trashbot_hardware` LiDAR skeleton，未发现需要改成 nav 或从 nav 改回 hardware 的 OKR 漂移。
- 路径纠偏：请求中的 `sprints/2026.06.01_10-11_lidar-ros2-closed-loop/tech-done.md` 当前不存在；本轮按仓库实际 sprint `sprints/2026.06.01_10-11_lidar-ros2-driver-skeleton/tech-done.md` 留档。

## 已采用证据

- 上一轮 reference ingest：`docs/vendor/lidar_ros/`、`docs/vendor/VENDOR_INDEX.md`、`docs/hardware/lidar_ros_reference.md` 和 `sprints/2026.06.01_09-10_lidar-reference-ingest/tech-done.md`。
- Hardware Infra 只读复核结论：`150000` baud、`0xAA 0x55`、`LSN`、`/lidar/raw_packet`、`laser_frame`、LaserScan output 都是 `source=software_reference`，不是 `source=hil_pass`。
- Coordinator verification passed：
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'`：`Ran 7 OK`
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'`：`Ran 11 OK`
  - `PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh`：passed；interfaces 6 OK、hardware 33 OK、nav 52 OK、bringup 11 OK、behavior 841 OK、vision 13 OK。
  - `git diff --check`：scoped files passed。

## Product closeout 验证结果

本轮 Product closeout 要求运行：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.01_10-11_lidar-ros2-driver-skeleton/tech-done.md
grep -n "LiDAR\|lidar\|source=software_reference\|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.06.01_10-11_lidar-ros2-driver-skeleton/tech-done.md | head -80
```

结果将在本文件提交前由 Product closeout 执行并以最终回复为准。

本轮一致性修正追加验证：

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'
# Ran 5 tests in 0.000s; OK

python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
# Ran 11 tests in 0.078s; OK

python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup
# exit 0

PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh
# interfaces: Ran 6 tests OK
# hardware: Ran 31 tests OK
# nav: Ran 52 tests OK
# bringup: Ran 11 tests OK
# behavior: Ran 841 tests in 550.341s OK
# vision: Ran 13 tests in 0.838s OK
# 观察到 Python ResourceWarning: unclosed socket，但 unittest exit 0。

docker --version
# The command 'docker' could not be found in this WSL 2 distro.
# Docker Humble build 未运行；原因是当前 WSL 发行版没有可用 docker CLI / Docker Desktop WSL integration。

LiDAR nav-package drift grep
# exit 1，无匹配；未发现 LiDAR driver/parser 仍指向 nav 包。

git diff --check -- docs/hardware/lidar_ros_reference.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.01_09-10_lidar-reference-ingest/tech-done.md sprints/2026.06.01_10-11_lidar-ros2-driver-skeleton/tech-done.md
# exit 0
```

## KR 拆解、更新或历史归档

- KR 更新：O1 新增 LiDAR software_reference + mock skeleton 进展，作为 ROS2 `/scan` 软件接口和 gated launch 的前置闭环。
- 历史归档：本轮没有已完成 KR 移入历史区。LiDAR 仍留在 O1 当前推进区，因为真实硬件/HIL/TF/Nav2/SLAM 未完成。
- 历史记录位置：`docs/process/okr_progress_log.md` 的 `2026-06-01 10-11` 条目和本文件。

## 本轮核心抓手

核心抓手是把 `source=software_reference` 与 `source=hil_pass` 分开：软件 skeleton 可以推进 O1 软件完成度，但验收口径必须明确 gated node 默认关闭、mock/serial 可切换、真实上车证据另收集。

## 需要做什么

- Robot Software Engineer：继续保持 skeleton 的 ROS2 interface、parser 和 launch contract 可测，后续支持真实 `/scan` 运行证据接入。
- Hardware Infra Engineer：真实上车前复核 LiDAR USB 设备、供电、线缆、150000 波特率、串口权限和安装位姿。
- Robot Algorithm Engineer：真实 `/scan` 可用后验证 TF、SLAM/Nav2 订阅和建图/避障效果。
- Product Manager / OKR Owner：维护 O1 进度边界，禁止把 software_reference 误写成 HIL pass。

## 优先级和验收口径

- P0：保持 `lidar_enabled=false` 默认安全边界，不能让无雷达环境影响 bringup。
- P0：software skeleton 验收以 focused LiDAR unittest、bringup launch contract test、smoke tests 和 scoped diff-check 为准。
- P1：下一轮真实硬件验收必须产出 `ros2 topic hz /scan`、`ros2 topic echo --once /scan`、TF `base_link -> laser_frame`、Nav2/SLAM 订阅证据和 150000 波特率稳定性记录。

## 对应责任 Engineer

- 主责：Robot Software Engineer。
- 事实复核：Hardware Infra Engineer。
- 后续算法闭环：Robot Algorithm Engineer。
- 产品 closeout：Product Manager / OKR Owner。

## 剩余风险、阻塞和证据链缺口

- 真实 LiDAR、真实串口、真实 Orange Pi USB 设备、供电、权限和线缆稳定性仍 `not_proven`。
- `150000` 是非标准波特率，当前只属于 `source=software_reference`，未证明目标 USB-UART、宿主系统和容器透传稳定支持。
- `laser_frame` 到 `base_link` 的 TF 未实测，Nav2/SLAM 尚未消费真实 `/scan`。
- 参考 README 提到无角度修正，真实导航前仍需评估角度误差。
- 本轮不证明 WAVE ROVER、TF、Nav2/SLAM、真实 LiDAR HIL、真实现场路线或 PR #5 完成。
- Docker/Humble build 在本 WSL 环境未运行，因为 `docker` 命令不可用；这不影响本轮 Python/静态 contract 验证结论，但仍不等于容器内 ROS2 build 证据。

## 完成前反思

- 需求满足：已把 Product closeout 归入 micro sprint，并把 O1 wording 更新为保守进展。
- 范围控制：Product closeout 只允许改三份文档；代码、launch、vendor 文件和硬件文档不在本轮 Product 写范围。
- 未处理 TODO：无新增代码 TODO；剩余事项全部记录为真实硬件/TF/Nav2/SLAM 验收缺口。
- 验证缺口：Product 只做文档 diff-check 和关键字 grep；工程验证采用 Coordinator 已通过的 focused tests/smoke 证据。
