# Field HIL Execution Pack

本文是 2026-06-10 现场 HIL 执行包。目标是把当前远程证据转成现场人员可执行的
人工预检、运动准入、受控动作顺序和 artifacts 归档要求。

本轮文档只规定下一轮现场执行方法；不得把本文当作已经完成真实物理运动、相机可见内容、
导航级地图或送达闭环的证据。

## 已读来源与硬件事实

本执行包采用以下本地资料和近期 sprint 证据，不凭记忆推断硬件参数：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/final.md`
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/tech-done.md`
- `sprints/2026.06.10_00-45_integrated-sensor-motion-capture/final.md`
- `sprints/2026.06.10_00-45_integrated-sensor-motion-capture/tech-done.md`
- `sprints/2026.06.10_03-45_lidar_motion_delta_retry/tech-done.md`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/tech-done.md`
- `sprints/2026.06.10_04-15_wave_rover_min_actuation_probe/tech-done.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/vision/board_camera_publisher.md`
- `docs/hardware/wave_rover_json_bridge.md`

采用的硬件事实：

- WAVE ROVER 上下位机链路是 UART，一行 UTF-8 JSON 以 `\n` 结束。
- vendor Raspberry Pi 示例默认底盘串口是 `/dev/ttyAMA0 @ 115200`，但 Orange Pi
  实板串口必须以现场枚举和实测为准；近期实板证据使用 `/dev/ttyS5 @ 115200`。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`。
- `json_cmd.h` 定义 `CMD_ROS_CTRL=13`，示例 `{"T":13,"X":0.1,"Z":0.3}`，但当前项目
  已验证路径仍使用 `command_mode:=speed` 的 `T=1` 差速速度命令。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、
  `CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143`、`FEEDBACK_BASE_INFO=1001`。
- 当前 ROS2 bridge 的 `/trashbot/stop` 发送 `{"T":1,"L":0,"R":0}` 停车。
- `/odom` 仍是 ROS-side command integration，不是实测编码器或轮速里程计。

## 当前证据矩阵

| 项目 | 状态 | boundary | source sprint |
| --- | --- | --- | --- |
| LiDAR `/scan` | proven | `/dev/ttyACM0 @ 150000` 可发布聚合 `/scan`，健康帧可达到 `ranges_count>=80`、`finite_count>=80`、`angle_span_deg>=90`；不等于机械标定或运动证明。 | `2026.06.10_00-25`、`2026.06.10_03-45`、`2026.06.10_04-15` |
| camera device/topic | proven | `/dev/video1` 是 DV20 USB UVC capture，OpenCV 可读，`/camera/image_raw` 可收到 `640x480 bgr8`；但画面近黑。 | `2026.06.10_04-00` |
| camera visible content | not proven | `visible_content_proven=false`；OpenCV 与 ROS 样本均 `non_black_ratio=0.0`、`edge_count=0`，不能用于路线关键帧、视觉定位、障碍识别或远程可视验收。 | `2026.06.10_04-00` |
| map/route | boundary | no-motion 与 integrated artifacts 已有 `map.yaml/.pgm`、`route.csv`、keyframes、manifest；`/odom` 是 synthetic 或 command integration，不是导航级地图或真实路线。 | `2026.06.10_00-25`、`2026.06.10_00-45` |
| base UART | proven | `esp32_bridge` 可连接 `/dev/ttyS5 @ 115200 command_mode:=speed`；该设备路径是当前实板证据，不是 Orange Pi 通用默认。 | `2026.06.10_00-45`、`2026.06.10_03-45`、`2026.06.10_04-15` |
| base feedback `T=1001` | boundary | debug JSONL 已记录数百条 `T=1001`，电压样本可见；但 `/battery`、`/imu/data` topic 对齐在 integrated capture 未闭环，`left_speed/right_speed` 仍为零。 | `2026.06.10_00-45`、`2026.06.10_03-45`、`2026.06.10_04-15` |
| motion | not proven | 低速 `/cmd_vel` 阶梯 `0.03/0.05/0.07/0.09m/s` 均能 stop，但 `physical_motion_lidar_delta_proven=false`，`wheel_feedback_lr_nonzero_proven=false`；没有肉眼或外部视频。 | `2026.06.10_03-45`、`2026.06.10_04-15` |
| stop/API restore | proven | `/trashbot/stop` 多轮返回 `success=True`；probe 后 `trashbot-upper-robot-api.service` 已恢复 `active`，串口无本轮 ROS 残留占用。 | `2026.06.10_00-45`、`2026.06.10_03-45`、`2026.06.10_04-15` |
| delivery | not proven | `delivery_success=false`；当前没有 Nav2 实跑、真实路线导航、投放/返回或现场送达闭环。 | `2026.06.10_04-15` |

## 现场人工预检

现场人员必须先完成以下检查并拍照或录像，未通过不得进入运动 gate：

- 相机：拆除镜头盖、保护膜和遮挡；确认镜头不是朝向地面暗处、机壳内壁或纯黑表面。
- 光照：让摄像头对准有纹理的高对比目标，打开室内灯或补光灯。
- USB 相机：轻触线缆和接口确认不松动；若补光后仍黑，准备更换 USB 口或相机本体。
- 底盘状态：明确底盘是落地还是架空；若架空，必须确认轮子不会碰到线缆、人员或桌面边缘。
- 电机供电：确认 WAVE ROVER 电机电源已打开，电池电压在现场可接受范围，充电线不会限制轮子。
- 急停/遥控/模式：确认急停未按下，遥控器或模式开关允许上位机控制；如有手柄接管，先恢复到上位机控制模式。
- 安全空间：车体前后左右至少留出可观察的空旷缓冲区，移除线缆、支架、杂物和易卷入物。
- 人员站位：一名 operator 操作命令，一名 observer 站在侧后方拍摄并准备物理断电/急停；任何人不得站在车体正前方或车轮旁。

## 允许运动前 gate

以下 gate 必须全部通过，才允许发送任何非零 `/cmd_vel`、更高 `T=1` 或更高速度：

- stop service：运动前先调用 `/trashbot/stop`，必须返回 `success=True`；失败即停止本轮。
- UART：确认 `/dev/ttyS5 @ 115200` 当前由本轮 `esp32_bridge` 独占，且日志出现 `Connected to WAVE ROVER ESP32`。
- battery/feedback：采集 `T=1001` debug JSONL，至少看到新鲜 `v` 电压字段；若电压缺失、异常跳变或 parser 错误，停止。
- LiDAR scan：baseline `/scan` 至少 3 帧健康聚合帧，满足 `ranges_count>=80`、`finite_count>=80`、`angle_span_deg>=90`。
- camera visible：运动前优先复跑相机可见性；若仍黑场，只允许外部视频作为运动证据，不允许把 ROS camera 当可视证据。
- 外部视频记录：observer 必须从侧后方连续录制轮子、地面参考物和整车姿态，视频开始前口播时间、step、速度和是否架空。
- API service 管理：如需停止 `trashbot-upper-robot-api.service` 释放串口，必须记录停止前状态；结束后必须恢复 `active`。
- 清场条件：现场人员口头确认清场；任何人员、宠物、线缆或不稳定物体进入安全空间时不得运动。
- operator report intake：现场人工材料必须按
  `docs/hardware/field_hil_operator_report_template.md` 提交到 `/api/operator/report`；
  该入口只写材料 artifact，不能替代 `/trashbot/stop`、robot ACK、`T=1001` feedback、
  HIL 结果或 motion proof。

## 受控运动 HIL 顺序

所有步骤都必须带 stop、最大时长和 abort 条件。任一步失败，立即停止本轮，不进入后续更高速度。

### Step 0：相机可见性复跑

- 动作：在补光和高对比目标前复跑 OpenCV direct + ROS `/camera/image_raw` 双路径采样。
- stop：本步不运动，不需要非零 `/cmd_vel`；仍需确认 `/trashbot/stop` 可用后再进入后续 step。
- 最大时长：5 分钟。
- abort：设备打不开、ROS topic 无图像、画面仍黑且现场无法解释、控制项无法恢复。
- 通过条件：`visible_content_proven=true` 必须有非黑像素、动态范围/纹理和保存的 frame artifact；均匀亮屏不算通过。

### Step 1：低速外部视频/肉眼确认

- 动作：沿已验证 ROS2 path 发送不超过上一轮上限的短脉冲，优先从 `linear.x=0.03m/s` 开始，逐步到 `0.09m/s` 以内。
- stop：每个 step 结束立即发布零速并调用 `/trashbot/stop`；operator 手必须停留在 stop 命令或急停路径上。
- 最大时长：每步 publish window 不超过 `0.18s`；每步之间至少停 3 秒并观察。
- abort：stop 失败、串口异常、LiDAR topic 停止、feedback parser 报错、车体异常抖动、轮子卷线、observer 看不清、人员进入安全区。
- 通过条件：外部视频清楚记录轮子或车体相对地面参考物发生可见位移，同时本轮 stop 成功且清场成功。

### Step 2：判断是否允许 higher `T=1` 或 higher speed

只有 Step 1 后仍无异常且现场确认电机供电、急停、遥控/模式、底盘落地/架空状态正确，才允许讨论更高 `T=1` 或更高速度。允许条件：

- 低速 step 已有外部视频证明真实运动，或现场确认低速无运动是因为起动阈值不足且安全空间足够。
- `/trashbot/stop` 在本轮至少连续两次成功。
- `T=1001` debug JSONL 正常增长，无电压异常、JSON parse 错误或串口断开。
- observer 能连续拍到整车、轮子和地面参考物。
- 若切换 direct vendor `T=1`，必须仍保留 ROS bridge stop 或等价 UART 零速兜底，且不得绕过人工急停。

更高速度执行边界：

- 每次只提升一个小阶梯；不得直接跳到巡航速度、Nav2 或 autonomous mode。
- 每步先口播 speed/expected command，再执行，执行后立刻 stop。
- 任一 step 出现真实运动后，先停止并归档，不继续追求更快速度。

### Step 3：真实 route/map 证据

只有 `physical_motion_lidar_delta_proven=true` 或外部视频证明真实运动、且 stop/API restore 全部通过后，才允许做短距离真实路线采集。

- 动作：低速手动直线或小范围移动，采集 `/scan`、route、keyframes、map、feedback JSONL。
- stop：每段采集前后调用 `/trashbot/stop`。
- 最大时长：单段不超过 10 秒；总运动距离以现场安全空间为上限。
- abort：定位漂移严重、map 明显撕裂、route 与视频不一致、wheel feedback 异常、相机仍不可见但任务依赖视觉。
- 通过条件：视频、route、scan metrics 和 map/keyframes 能对齐同一次真实移动。

## 成功判据

以下布尔值只有在对应 artifacts 齐备时才能写成 true：

- `visible_content_proven=true`
  - OpenCV direct 与 ROS `/camera/image_raw` 至少一路保存清晰 frame。
  - frame 中有非黑内容、纹理或边缘，且 metrics 证明不是纯黑、纯白或均匀灰。
  - artifact 包含原始图片、metrics JSON、设备 facts 和 operator report。
- `physical_motion_lidar_delta_proven=true`
  - baseline/post `/scan` 均健康，至少满足 `ranges_count>=80`、`finite_count>=80`、`angle_span_deg>=90`。
  - scan delta 满足既有保守阈值：`paired_bins>=40`、`median_abs_diff_m>=0.03`、`changed_bin_ratio>=0.12`。
  - 外部视频或 operator report 能解释运动方向和现场环境变化，排除单纯传感器噪声。
- `wheel_feedback_lr_nonzero_proven=true`
  - 本轮 WAVE ROVER `T=1001` debug JSONL 中，motion/post 时间窗出现任一 `abs(left_speed)>0` 或 `abs(right_speed)>0`。
  - 同一时间窗 command log、stop log 和视频能对齐，排除旧 artifact 或 stale sample。
- `real_route_map_proven=true`
  - `route.csv`、keyframes、manifest、map yaml/pgm 来自同一轮真实移动。
  - route 位移与外部视频、LiDAR delta 或其他现场观察一致。
  - 明确标注 `/odom` 来源；如果仍是 command integration，不能写成实测里程计。
- `delivery_success=true`
  - 真实路线导航或人工辅助送达完成，包含出发、到达垃圾站/垃圾桶点位、完成投放/提醒、停止或返回。
  - 全程有 stop 可用、异常处理记录、任务日志和现场视频。
  - 单纯底盘移动、建图、route 采集或相机可见都不能单独置为 true。

## 失败/停止判据

出现任一情况必须立刻停止，记录 artifacts，不继续扩大速度或切换控制方式：

- stop 失败：`/trashbot/stop` 返回失败、超时、服务消失，或零速后仍有异常运动。
- 串口异常：`/dev/ttyS5` 被其他进程占用、`esp32_bridge` 断开、JSON parse 错误持续出现、feedback debug 停止增长。
- 反馈异常：`T=1001` 缺失、电压 `v` 缺失或异常跳变、`left_speed/right_speed` 与现场观察明显矛盾。
- 电压异常：电池电压低于现场安全阈值、供电线发热、压降导致设备重启或 LiDAR/camera 掉线。
- 相机仍黑：补光和对准高对比目标后仍 `visible_content_proven=false`；不得把黑场 keyframe 当视觉证据。
- 底盘无响应：低速阶梯和现场模式/供电检查后仍无轮动，且无 wheel feedback 非零；停止后改为机械/电气排查。
- 异常运动：突然加速、偏航、倒退、轮子空转卷线、车体从架空台面移动、底盘撞到障碍。
- 人员无法观察：observer 看不到轮子或车体，视频丢失，现场有人进入安全空间，operator 无法同时控制 stop。
- API restore 失败：本轮停止过 `trashbot-upper-robot-api.service` 但无法恢复 `active`；必须先恢复服务再收口。

## 需要归档的 artifacts

每轮现场 HIL 必须保存到 sprint artifacts，并在 `tech-done.md` 中写明路径：

- 外部视频：从预检、口播、运动 step、stop 到清场的连续视频。
- 现场照片：镜头、补光、车体落地/架空、电机供电、急停/遥控/模式、安全空间。
- command log：每个 step 的 `/cmd_vel`、expected `T=1` 或 `T=13`、持续时间、stop 结果。
- feedback JSONL：`T=1001` debug log，保留原始时间戳和 `L/R/r/p/y/v` 字段。
- scan metrics：baseline/post `/scan` frame stats、delta metrics、健康帧数量。
- camera artifacts：OpenCV/ROS frame、metrics JSON、V4L2 device facts、control restore 记录。
- route/map artifacts：`route.csv`、keyframes、manifest、`map.yaml/.pgm`，以及同轮命令和视频对齐说明。
- API restore 记录：service 停止前状态、停止原因、恢复后 `active` 和 `/api/base/status`。
- operator report：谁在现场、底盘状态、是否落地、每步观察、异常、最终布尔值。

## operator report intake

`/api/operator/report` 是现场人工材料入口，用于把 observer 的文字观察、外部视频引用、
相机可见性、wheel feedback、scan delta、route/map 和 delivery 布尔值收进同一
`evidence_ref`。它的当前实现见 `onboard/scripts/upper_robot_api.py`：

- POST `/api/operator/report` 只持久化 `runtime/operator_report_latest.json` 或
  `ROBER_OPERATOR_REPORT_ARTIFACT_PATH` 指定的 JSON 文件。
- 返回中固定包含 `operator_report_material_only=true`、`not_proven=true`、
  `report_replaces_stop_status_ack_or_hil=false`、`sends_motion_commands=false`、
  `opens_serial=false`、`hil_pass=false` 和 `delivery_success=false`。
- 当前 normalizer 保留 `operator_present`、`evidence_ref`、
  `physical_clearance_confirmed`、`emergency_stop_ready`、`observed_motion`、
  `observed_stop`、`operator_notes`/`note`、`reported_at`，并把
  `external_video_recorded`、`external_video_ref`、`visible_content_proven`、
  `camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`、
  `physical_motion_lidar_delta_proven`、`scan_delta_ref`、`real_route_map_proven`、
  `route_map_ref`、`delivery_success` 和 `site_state` 统一回写到
  `structured_hil_claims`。这些结构化字段是材料 claim，不替代 HIL pass。

现场填写和 `curl` 示例以 `docs/hardware/field_hil_operator_report_template.md` 为准。
即使 report 或 `structured_hil_claims` 中写入 `visible_content_proven=true`、
`physical_motion_lidar_delta_proven=true`、`wheel_feedback_lr_nonzero_proven=true`
或 `delivery_success=true`，也只表示 operator 声称材料已观察到对应现象；API 顶层
仍必须保持 `hil_pass=false`、`delivery_success=false`、
`operator_report_material_only=true` 和 `report_replaces_stop_status_ack_or_hil=false`。
最终是否翻转 HIL/route/delivery 证据，仍必须由同一 `evidence_ref` 下的原始视频、
图片、`T=1001` JSONL、scan metrics、route/map artifacts 和 stop/API restore 记录
共同证明。

若现场已保存 PC manual proxy 响应、`T=1001` feedback JSON/JSONL，以及 baseline/post
scan JSON，可先在本地运行 `onboard/scripts/motion_evidence_material_review.py` 生成
`trashbot.motion_evidence_material_review.v1` 草稿。该脚本只复核文件，不接触串口、HTTP、
ROS 或运动接口；其输出只能作为 operator report 材料整理工具，不能替代现场 stop、
外部视频或原始 wheel/scan artifact。

## 下一轮最低执行建议

下一轮不要继续盲跑远程低速 probe。推荐顺序是：

1. 现场先修相机可见性，把 `visible_content_proven` 争取翻为 true。
2. 在 observer 外部视频下复跑低速 `0.03-0.09m/s` 短脉冲，先证明肉眼/视频物理运动。
3. 如果仍无运动，现场检查电机供电、急停、遥控/模式和底盘架空/落地状态后再决定是否提升 `T=1` 或速度。
4. 只有真实运动、stop、feedback、scan 和 artifacts 都闭环后，再进入 route/map 或 delivery 证明。

## 2026-06-11 18:20 live evidence sweep 补充

`sprints/2026.06.11_18-20_board_live_evidence_sweep/` 在真实上位机
`root@192.168.1.11:37878` 重新采集当前 live readback。SSH gate 通过：

```text
op-z3-b6.home
Thu Jun 11 05:49:45 PM CST 2026
active
```

本轮只执行 no-motion refresh 与 stop smoke，没有执行非 stop motion、没有调用
`/api/base/manual`、没有发布 `/cmd_vel`。operator report 仍是 no-motion smoke 材料：
`external_video_recorded=false`、`visible_content_proven=false`、
`wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`。
因此非 stop 点动门禁不满足，fail-closed 保持正确。

本轮 stop smoke 只写入 `{"T":1,"L":0,"R":0}`，HTTP 200，`stop_result.ok=true`，
`bytes_written=20`。`/api/base/status` 的非运动 `T=130` readback 读到 `T=1001`，
`read_line_count=23`、`parsed_json_count=23`，但这仍不是项目 robot ACK、轮速非零或
物理运动证明。

本轮 cleanup readback 显示 `trashbot-upper-robot-api.service active`，未见
`o1_lidar/o3_map/o10_amcl/nav2/slam/lidar_driver/camera_publisher/topic pub/cmd_vel`
残留，`ros2 topic info /cmd_vel` 返回 `Unknown topic '/cmd_vel'`。

当前矩阵更新：

| 项目 | 2026-06-11 18:20 状态 | 边界 |
| --- | --- | --- |
| LiDAR scan proof | `proven` | fresh no-motion proof `o1-lidar-scan-proof-1781171493054`，post status rate `15.926Hz`；不证明机械标定或运动。 |
| map proof | `proven` | `o3-map-lifecycle-1781171513110`，`map_once/map_file/map_metadata=true`；不证明地图质量或真实路线。 |
| Nav2 path proof | `proven` | `o10-amcl-nav2-runtime-1781171562670`，path generated succeeded，31 points；未执行路径。 |
| stop smoke | `proven` | 零速 `T=1` 写入成功；不替代外部视频或 HIL pass。 |
| non-stop motion | `not_executed` | operator report 材料不满足非 stop gate。 |
| camera visible content | `not_proven` | 仍无可见 frame artifact。 |
