# O7 真实相机单帧关键帧捕获

## 目标和证据边界

`onboard/scripts/o7_live_camera_keyframe_capture.py` 在不启停 camera/机器人 runtime、
不写 ROS topic、不控制底盘的前提下，先做一次 daemon-off ROS graph inventory，
gate clean 后最多订阅一帧 `sensor_msgs/msg/Image`，并把唯一媒体二进制写为 sprint-local
`keyframe.png`。它服务 `trashbot.o7.live_camera_keyframe_manifest.v1` 的 O6/O7
annotation lineage，不是视频流、RTC、隐私批准、生产标注、路线执行、送达、HIL 或
safe-to-control 证明。

硬件资料入口采用 `docs/vendor/VENDOR_INDEX.md`。该索引只证明项目硬件栈包含 Orange Pi
以及本地 vendor 上位机 camera/WebRTC 参考资料；它不能证明当前实机 camera 型号、
设备路径、安装姿态、分辨率或 ROS topic。本 helper 因此不使用任何设备路径/分辨率默认值，
只依据本轮 ROS graph 自发现的 `sensor_msgs/msg/Image` publisher。

## 两阶段 gate

1. `inventory` 在一个 SSH shell 内 source ROS，设置 `ROS2CLI_NO_DAEMON=1`，记录 daemon
   pid 集合 pre/post，执行有界 `ros2 topic list -t` 与候选 `ros2 topic info`，并验证
   `rclpy`、`sensor_msgs.msg.Image` 可导入。
2. 首选 `/camera/image_raw`。canonical 缺席时只允许唯一无歧义的兼容 Image topic；
   canonical wrong type、零 publisher、多个兼容候选、daemon drift 或依赖失败全部
   fail closed，capture invocation count 为 `0`。
3. gate clean 后 `capture-one` 只创建一次 SSH subscription，hard subscription timeout
   最多 `12s`，收到首帧立即退出。timeout、layout、encoding、stamp、PNG 或 hash 失败后
   capture invocation count 固定为 `1`，不重试。
4. helper 只终止自己创建的 SSH process group，不使用 `pkill`、`killall` 或 broad kill。

## Schema 与 lineage

manifest 冻结字段为：

```text
task_id, source_mode, source_proof, topic, message_type,
publisher_count_at_inventory, stamp_sec, stamp_nanosec, width, height,
step, encoding, is_bigendian, media_basename, media_byte_size, sha256,
captured_at_utc, inventory_ssh_invocation_count,
single_frame_capture_invocation_count, redaction_boundary,
annotation_ready, blocked_reasons, not_proven
```

O6/O7 三层 lineage 必须逐项保持：

```text
task_id + sha256 + topic + stamp + width + height + encoding
```

clean live 固定 `source_proof=live_single_frame_captured`、invocation `1/1`、
`annotation_ready=true`。blocked inventory 为 `1/0`；capture 已启动后失败为 `1/1`，
但 `annotation_ready=false`。

## Encoding、layout 与 canonical PNG

当前只接受能够无损、无外部依赖解释的 `rgb8`、`bgr8`、`rgba8`、`bgra8`、`mono8`。
helper 校验正尺寸、`step >= width * channels`、`len(data) == step * height`，允许 row
padding 但不会把 padding 写入 PNG。所有成功帧转换为 8-bit RGB PNG，媒体 identity
以最终 PNG 的 byte size 和 SHA-256 为准。unsupported encoding、坏 layout、全零 stamp
均 fail closed，不生成假图。

`annotation_ready=true` 只表示稳定 metadata/media identity 可供标注入口消费；本轮不做
自动可见内容或人脸/隐私判定，因此 `visible_content` 与 `privacy_approved` 继续列入
`not_proven`。

## 隐私和二进制边界

- raw pixels 仅在 helper 内存中转换；唯一落盘二进制是 sprint-local `keyframe.png`。
- JSON 禁止 bytes、raw pixel arrays、base64、data URL、绝对路径、远端 host 与 HTTP URL。
- manifest/API/UI 只消费 basename、size、hash、topic/stamp、尺寸、encoding 和
  `redaction_boundary`；UI 固定 metadata-only。
- `privacy_review_status=pending_not_approved`，不得显示为隐私已批准。

## 运行方式

先运行离线合同：

```bash
python3 -m py_compile \
  onboard/scripts/o7_live_camera_keyframe_capture.py \
  onboard/tests/test_o7_live_camera_keyframe_capture.py
python3 -m unittest discover -s onboard/tests \
  -p 'test_o7_live_camera_keyframe_capture.py' -v
```

真实 inventory 只能执行一次：

```bash
python3 onboard/scripts/o7_live_camera_keyframe_capture.py inventory \
  --ssh-target <approved-target> \
  --ssh-port <approved-port> \
  --ros2cli-no-daemon \
  --max-inventory-ssh-invocations 1 \
  --inventory-output <sprint>/artifacts/algorithm/read_only_camera_inventory.json \
  --manifest-output <sprint>/artifacts/algorithm/live_camera_keyframe_manifest.json \
  --receipt-output <sprint>/artifacts/algorithm/live_camera_keyframe_capture_receipt.json
```

只有 inventory artifact 为 clean 才执行一次 capture：

```bash
python3 onboard/scripts/o7_live_camera_keyframe_capture.py capture-one \
  --ssh-target <approved-target> \
  --ssh-port <approved-port> \
  --inventory-input <sprint>/artifacts/algorithm/read_only_camera_inventory.json \
  --max-single-frame-capture-invocations 1 \
  --timeout-s 12 \
  --media-output <sprint>/artifacts/algorithm/keyframe.png \
  --manifest-output <sprint>/artifacts/algorithm/live_camera_keyframe_manifest.json \
  --receipt-output <sprint>/artifacts/algorithm/live_camera_keyframe_capture_receipt.json
```

## Mission Objective 0 与安全字段

只有本轮真实首帧、PNG、size/hash 和 manifest 全 clean 时
`current_run_artifact_delta=true`。`external_artifact_delta=false`、
`live_control_delta=false`、`user_action_delta=false` 始终固定，所以 Mission Objective 0
仍未满足。所有状态均固定：

```text
safe_to_control=false
robot_control_executed=false
route_execution_success=false
delivery_success=false
hil_pass=false
```

本 helper 不发布 `/initialpose`、`/cmd_vel`，不调用 `/api/base/manual`、NavigateToPose、
service/action write，不触碰 UART，不重跑 `/scan` inventory，也不启动或停止 camera runtime。
