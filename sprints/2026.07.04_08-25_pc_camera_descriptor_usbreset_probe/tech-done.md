# PC 相机 USB 描述符与总线 reset 复验 micro sprint

sprint_type: micro

## 实际改动

- 继续围绕 PC 实时图传缺口做上位机只读/恢复复验，不改产品代码。
- 读取 DV20 USB 描述符：设备为 Jieli `4c4a:4a55`、UVC 1.00、bus powered `400mA`、视频 EP4 IN isochronous `3x1023`，只有一个 video streaming altsetting；描述符里 processing unit 有 `Descriptor too short` 警告。
- 读取 media graph：`/dev/video1 -> Extension 3 -> Processing 2 -> Input 1` 拓扑完整，input 0 状态为 `ok`。
- 运行 `v4l2-compliance`：驱动 capability/format/buffer 基本通过，失败集中在 control 设置，未发现格式枚举或 buffer ioctl 断裂。
- 尝试 `usbreset` 后再次直采 `MJPG 640x480@30` 与 `YUYV 320x240@20`：reset 工具在本系统未能按 ID/devpath 命中设备；随后直采仍是 `STREAMON` 成功但 0 字节。

## 验证结果

- 通过：PC 7001 继续监听 `0.0.0.0:7001`。
- 通过：`live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`。
- 通过：重新执行 PC WASD 前进/后退/stop，均 `proxy_status=command_forwarded`；前进/后退读到 `command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`stop_result_ok=true`。
- 未通过：相机仍 `camera_current_visible=false`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`；上车 health 仍是 `/dev/video1`、USB `480M`、owner `0`、CMA 正常。

## 剩余风险

- PC 端实时图传仍未完成，不能标记目标完成。
- 当前证据已经把问题进一步收窄到 DV20 上游视频输入、视频线、接口、供电、采集卡/摄像头本体或需要换 known-good UVC；软件层可继续做状态展示和诊断，但没有真实视频 payload 可转发。
- WAVE ROVER `T=1001 L/R` 仍为 `0/0`，WASD 只能证明命令链路和 IMU 动作信号，不能宣称 wheel raw 非零。
