# Local WebRTC Camera Smoke Micro Sprint

## sprint_type

micro

## 实际改动

- 新增 `onboard/scripts/local_webrtc_camera_smoke.py`：Orange Pi LAN-only WebRTC 摄像头 smoke 服务，使用 `aiohttp + aiortc + OpenCV` 提供 `/`、`/health`、`/devices`、`/offer`。服务明确 `safe_to_control=false`、`sends_commands=false`，不启动 ROS2、Nav2、UART、WAVE ROVER 或任何底盘运动控制。
- 新增 `onboard/scripts/local_webrtc_camera_smoke.sh`：短启动封装，支持 `PORT`、`ROBER_CAMERA_SOURCE`、`WIDTH`、`HEIGHT`、`FPS` 环境变量。
- 新增 `docs/interfaces/o7_local_webrtc_camera_smoke.md`：记录 LAN-only WebRTC smoke 接口、vendor 来源边界、失败定位和安全边界。
- 更新 `onboard/README.md`：补充 Orange Pi 本地 WebRTC 摄像头 smoke 启动方式和诊断接口。
- 追加 `--self-test-url` 机器可读 offer-level 自检：客户端读取 `/health`、`/devices`，依赖齐全时向 `/offer` 发 recvonly SDP，验证 answer 并等待首帧；依赖缺失、服务不可达、offer 拒绝或首帧超时都会输出结构化 `degraded/failed` JSON。
- 更新 `onboard/scripts/local_webrtc_camera_smoke.sh`：支持 `ROBER_WEBRTC_SELF_TEST_URL`、`ROBER_WEBRTC_SELF_TEST_TIMEOUT`、`ROBER_WEBRTC_REQUIRE_FRAME`，方便本机或 SSH 远端复验。

## Vendor 来源边界

- 已读取 `docs/vendor/VENDOR_INDEX.md`、`docs/interfaces/o7_realtime_hardware_sources.md` 和 `docs/vendor/waveshare_wave_rover/ugv_rpi/app.py`。
- 本轮只借鉴 vendor Raspberry Pi app 中 `aiortc`、`/offer`、`/video_feed` 和摄像头来源的参考形态；不把 vendor Raspberry Pi app 视为 rober Orange Pi 已验证证据。

## 远端摄像头探测

目标远端：`ssh root@192.168.1.11 -p 37878`。

已执行短超时探测：

```bash
timeout 12s ssh -o BatchMode=yes -o ConnectTimeout=5 -o ServerAliveInterval=3 -o ServerAliveCountMax=1 -p 37878 root@192.168.1.11 'hostname; uname -a; ps -p 1 -o comm=; command -v python3; python3 --version; ls -l /dev/video* 2>/dev/null || true; command -v v4l2-ctl || true; ...'
```

关键输出：

- hostname：`op-z3-b6.home`
- kernel/arch：`Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64`
- init：`systemd`
- Python：`/usr/bin/python3`，`Python 3.10.12`
- 摄像头节点：`/dev/video0`、`/dev/video1`、`/dev/video2`
- `v4l2-ctl`：`/usr/bin/v4l2-ctl`
- `v4l2-ctl --list-devices`：
  - `USB Composite Device: DV20 USB` -> `/dev/video0`、`/dev/video1`、`/dev/media0`
  - `cedrus` -> `/dev/video2`、`/dev/media1`
- OpenCV 真实读帧：
  - `opencv_open_0: True`
  - `opencv_read_0: True (480, 640, 3)`

## 依赖安装结果

初始依赖探测：

- `cv2: ok`
- `aiohttp: ok`
- `aiortc: missing`
- `av: missing`

已执行带超时的系统包安装，不走 pip 编译：

```bash
timeout 240s ssh -o BatchMode=yes -o ConnectTimeout=5 -o ServerAliveInterval=10 -o ServerAliveCountMax=2 -p 37878 root@192.168.1.11 'DEBIAN_FRONTEND=noninteractive apt-get install -y python3-aiortc python3-av'
```

关键输出：

- APT 源：`http://repo.huaweicloud.com/ubuntu-ports jammy/universe arm64 Packages`
- 安装包包含 `python3-aiortc 1.3.0-3`、`python3-av 8.1.0-3build1`、`libsrtp2-1`、`python3-aioice`、`python3-pylibsrtp` 等。
- 安装完成后复查：
  - `cv2: ok`
  - `aiortc: ok`
  - `aiohttp: ok`
  - `av: ok`

## 同步与启动尝试

已同步本轮必要文件到 `/root/rober/`：

```bash
rsync -av -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=5' onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/local_webrtc_camera_smoke.sh root@192.168.1.11:/root/rober/onboard/scripts/
rsync -av -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=5' docs/interfaces/o7_local_webrtc_camera_smoke.md root@192.168.1.11:/root/rober/docs/interfaces/
```

第一次启动尝试因 `pkill -f local_webrtc_camera_smoke.py` 匹配到当前远端 shell 命令行，导致 SSH 会话返回 `code 255`；后续短超时 SSH 曾短暂 timeout，但 ping 证明主机仍可达。已按最小风险方式改为不再使用 `pkill`。

第二次启动命令：

```bash
timeout 15s ssh -o BatchMode=yes -o ConnectTimeout=3 -o ServerAliveInterval=2 -o ServerAliveCountMax=1 -p 37878 root@192.168.1.11 'cd /root/rober && : > /tmp/rober-local-webrtc-camera.log && nohup env PORT=8088 ROBER_CAMERA_SOURCE=0 bash /root/rober/onboard/scripts/local_webrtc_camera_smoke.sh >>/tmp/rober-local-webrtc-camera.log 2>&1 & sleep 2; curl -s http://127.0.0.1:8088/health; echo; curl -s http://127.0.0.1:8088/devices; echo; ps -ef | grep "[l]ocal_webrtc_camera" || true; ss -ltnp 2>/dev/null | grep ":8088" || true; tail -80 /tmp/rober-local-webrtc-camera.log 2>/dev/null || true'
```

该窗口内进程已出现：

```text
python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source 0 --width 640 --height 480 --fps 15
```

## 验证结果

本地静态验证：

```bash
python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py
bash -n onboard/scripts/local_webrtc_camera_smoke.sh
git diff --check -- onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/local_webrtc_camera_smoke.sh docs/interfaces/o7_local_webrtc_camera_smoke.md onboard/README.md
```

结果：均通过。

用户中断后的收口口径：

- 已停止所有远端等待和远端启动尝试。
- 当前最终交付口径按“中断后未再做远端确认”处理；由于此前出现过 SSH timeout / 会话异常，最终不再追加新的 SSH 状态证明。
- 因此，服务状态在本次收口中标记为 `not_reconfirmed_after_interrupt`；需要人工用下面最短命令确认当前进程、端口和日志。

远端服务确认：

```bash
timeout 10s ssh -o BatchMode=yes -o ConnectTimeout=3 -o ServerAliveInterval=2 -o ServerAliveCountMax=1 -p 37878 root@192.168.1.11 'echo "==ps=="; ps -ef | grep "[l]ocal_webrtc_camera" || true; echo "==ss=="; ss -ltnp 2>/dev/null | grep ":8088" || true; echo "==health=="; curl --max-time 3 -sS http://127.0.0.1:8088/health || true; echo; echo "==devices=="; curl --max-time 3 -sS http://127.0.0.1:8088/devices || true; echo; echo "==index=="; curl --max-time 3 -sS http://127.0.0.1:8088/ | head -5 || true; echo; echo "==log=="; tail -120 /tmp/rober-local-webrtc-camera.log 2>/dev/null || true'
```

关键输出：

- 进程：`python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source 0 --width 640 --height 480 --fps 15`
- 端口：`LISTEN 0 128 0.0.0.0:8088`
- `/health`：
  - `status: ready`
  - `imports.aiohttp: true`
  - `imports.aiortc: true`
  - `imports.cv2: true`
  - `imports.av: true`
  - `lan_only: true`
  - `cloud_relay: false`
  - `turn_required: false`
  - `sends_commands: false`
  - `safe_to_control: false`
  - `active_peer_connections: 0`
- `/devices`：
  - `/dev/video0`、`/dev/video1`、`/dev/video2` 均 `exists/readable/writable=true`
  - USB 摄像头：`USB Composite Device: DV20 USB`
- `/`：返回 HTML 页面头部。

本轮追加的本地自检护栏与验证：

```bash
python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py
bash -n onboard/scripts/local_webrtc_camera_smoke.sh
git diff --check -- onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/local_webrtc_camera_smoke.sh docs/interfaces/o7_local_webrtc_camera_smoke.md onboard/README.md sprints/2026.06.01_00-01_local-webrtc-camera/tech-done.md
```

结果：均通过，无输出。

服务不可达路径：

```bash
python3 onboard/scripts/local_webrtc_camera_smoke.py --self-test-url http://127.0.0.1:65535 --self-test-timeout 1
```

关键输出：

```json
{"lan_only": true, "reason": "health_unreachable", "robot_control_executed": false, "safe_to_control": false, "sends_commands": false, "status": "failed", "target": "http://127.0.0.1:65535", "turn_required": false}
```

说明：该命令验证自检客户端在服务不可达时能输出机器可读失败原因，且保持 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。

本地短生命周期诊断服务路径：

```bash
PORT=18088 python3 onboard/scripts/local_webrtc_camera_smoke.py --host 127.0.0.1 --port 18088
python3 onboard/scripts/local_webrtc_camera_smoke.py --self-test-url http://127.0.0.1:18088 --self-test-timeout 2
```

关键输出：

```json
{"health": {"ok": true, "status": 200}, "devices": {"ok": true, "status": 200}, "reason": "webrtc_client_dependency_missing", "robot_control_executed": false, "safe_to_control": false, "sends_commands": false, "status": "degraded", "target": "http://127.0.0.1:18088"}
```

说明：本地 WSL 环境缺 `aiohttp/aiortc/av/cv2`，因此只能证明 HTTP 诊断 + 自检降级语义；没有把该 degraded 结果冒充为 answer/首帧成功。

远端 Orange Pi offer-level 自检：

```bash
rsync -av -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=5' onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/local_webrtc_camera_smoke.sh root@192.168.1.11:/root/rober/onboard/scripts/
rsync -av -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=5' docs/interfaces/o7_local_webrtc_camera_smoke.md root@192.168.1.11:/root/rober/docs/interfaces/
timeout 20s ssh -o BatchMode=yes -o ConnectTimeout=5 -o ServerAliveInterval=3 -o ServerAliveCountMax=1 -p 37878 root@192.168.1.11 'cd /root/rober && python3 onboard/scripts/local_webrtc_camera_smoke.py --self-test-url http://127.0.0.1:8088 --self-test-timeout 8'
```

关键输出：

```json
{"answer_received": true, "connection_state": "connected", "first_frame": {"height": 480, "pts": 0, "width": 640}, "first_frame_received": true, "health": {"json": {"host": "op-z3-b6.home", "imports": {"aiohttp": true, "aiortc": true, "av": true, "cv2": true}, "lan_only": true, "robot_control_executed": false, "safe_to_control": false, "sends_commands": false, "status": "ready", "turn_required": false}}, "offer_http_status": 200, "status": "ok"}
```

说明：该证据把上轮“HTTP 页面/health/devices 可访问”推进到机器可读 `/offer` answer、WebRTC connected 和真实摄像头首帧读取。命令只访问本机 HTTP/WebRTC smoke，没有启动 ROS2/Nav2/UART/WAVE ROVER，没有发送机器人控制命令。

访问 URL：

```text
http://192.168.1.11:8088/
```

日志路径：

```text
/tmp/rober-local-webrtc-camera.log
```

当前最短手动确认命令：

```bash
timeout 8s ssh -o BatchMode=yes -o ConnectTimeout=3 -o ServerAliveInterval=2 -o ServerAliveCountMax=1 -p 37878 root@192.168.1.11 'ps -ef | grep "[l]ocal_webrtc_camera" || true; ss -ltnp 2>/dev/null | grep ":8088" || true; curl --max-time 3 -sS http://127.0.0.1:8088/health || true; echo; tail -80 /tmp/rober-local-webrtc-camera.log 2>/dev/null || true'
```

## 失败定位

- 已修正一次本地/远端探测命令引号问题；该问题不代表板端依赖失败。
- 初始阻塞为缺少 `aiortc` 和 `av`；已通过 Ubuntu arm64 APT 系统包解决。
- 第一次启动确认失败的根因是 `pkill -f local_webrtc_camera_smoke.py` 匹配当前 SSH shell 命令行并中断会话；第二次不使用 `pkill` 后服务已启动并可访问。
- 本轮已补自动 POST WebRTC offer 的自检客户端；远端 Orange Pi 已验证 answer、connected 和 640x480 首帧。浏览器播放体验、持续帧率和弱网恢复仍未覆盖。

## 剩余风险

- 真实同 WiFi 浏览器播放、首帧时间、延迟、ICE 状态、浏览器控制台错误仍未覆盖；新增自检可先补机器级 answer/首帧证据。
- 摄像头可能被 ROS2 感知、录制或其他进程独占；当前 smoke 第一版限制单 peer，但未实现跨进程共享采集。
- Orange Pi CPU/温度/长期帧率未做压测；当前只验证短时服务和 OpenCV 单帧读取。
- 本轮明确不覆盖公网访问、STUN/TURN、云 relay、鉴权、弱网恢复。
- 本轮没有启动底盘、UART、WAVE ROVER、Nav2、ROS2 launch 或 HIL；底盘安全保持未触碰状态。

## 协同需求

- Full-Stack：后续如要把该 LAN-only 页面接入 PC/手机入口，需要补 UI/鉴权/只读观看边界。
- Hardware：如浏览器播放失败或摄像头被占用，需要协助确认 USB/CSI 摄像头供电、驱动、权限和设备独占策略。
- Autonomy：后续若要和 ROS2 视觉/导航共享摄像头，需要定义图像源复用策略，避免多进程抢占 `/dev/video0`。
- Product：当前是 LAN-only smoke，不是普通用户公网视频能力；如要进入 O7 产品验收，需要明确是否继续走云 relay/公网 RTC。

## Product closeout

- 用户价值和北极星：本轮把 O7 的视频能力从纯 mock/contract 推进到远端 Orange Pi LAN-only WebRTC 摄像头机器级 smoke，服务于“普通用户最终可在手机/PC 只读查看机器人状态”的北极星，但当前仍是开发/运营调试证据，不是普通用户公网视频产品能力。
- OKR 映射和方向判断：映射 Objective 7，方向判断为继续。`OKR.md` 将 O7 从 `90%+ mock/software completion` 小幅调整为 `约 92% software + LAN camera smoke evidence`；不替换、不暂停，不调整 O1/O5/O6。
- KR 拆解和归档：本轮只推进 O7 真实 RTC/视频缺口中的“LAN-only 机器级 offer/首帧 smoke”子项；没有完整 KR 达到产品完成态，因此不移动到历史归档区。
- 核心抓手和下一步：优先补真实同 WiFi 浏览器播放、首帧时间、延迟、ICE 状态、浏览器控制台和短时稳定性，再决定云 relay/公网 RTC/TURN/鉴权路线。
- 优先级、验收口径和 owner：P0 由 Full-Stack 继续负责浏览器播放与 PC/手机入口；Hardware 只在摄像头供电、设备权限或独占问题出现时介入；Autonomy 只在需要与 ROS2 视觉/导航共享 `/dev/video0` 时介入。
- 风险和证据链缺口：不证明真实浏览器播放体验、长期帧率/延迟/CPU/温度、云 relay、公网 RTC、TURN、鉴权、ASR/TTS、手控/Nav2、真实 robot ACK 或真实上车任务闭环；本轮没有启动底盘、UART、WAVE ROVER、Nav2、ROS2 launch 或 HIL。
