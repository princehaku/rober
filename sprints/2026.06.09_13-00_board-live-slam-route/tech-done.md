# Board Live SLAM Route Sprint Tech Done

## sprint_type: epic

## 自主能力目标和本轮抓手

目标功能点：`board_live_slam_route_evidence_pack`。

本轮抓手是优先使用 CEO 提供的真实上位机入口 `ssh root@192.168.1.11 -p 37878`，尝试在真实上位机上产出 topic smoke、SLAM/map、route.csv、keyframe/manifest、fixed-route YAML、dry-run/replay JSONL 或 rosbag 中至少一种可复核证据。

实际结果：未进入 ROS2、topic、SLAM 或 route 采集阶段。失败阻塞在本机到上位机的网络邻居层，`192.168.1.11:37878` 当前不可达。

## 改动文件和接口影响

实际改动：

- `sprints/2026.06.09_13-00_board-live-slam-route/tech-done.md`
- `sprints/2026.06.09_13-00_board-live-slam-route/side2side_check.md`
- `sprints/2026.06.09_13-00_board-live-slam-route/final.md`

接口影响：

- 未修改产品代码、测试代码、launch、硬件配置、串口配置或 WAVE ROVER 协议代码。
- 未修改 `docs/product/pc_tools_workstation.md`，因为没有拿到可供 PC 端消费的真实 route/map/keyframe/replay 材料。
- 未提交 SSH 凭证、token、私钥或远端大文件。

## Vendor 资料读取

已按 tech-plan 执行：

```bash
sed -n '1,180p' docs/vendor/VENDOR_INDEX.md
```

读取结论：

- 硬件事实入口为 `docs/vendor/VENDOR_INDEX.md`。
- 本轮未进入 Orange Pi 串口、WAVE ROVER UART、baudrate、JSON 指令、速度映射、反馈协议、引脚、电压、机械尺寸或固件修改阶段。
- 因此未继续打开 vendor PDF、firmware 或 `ugv_rpi` 资料；当前根因不是硬件协议事实不清，而是 SSH 目标网络不可达。

## 验收命令输出摘要

### 本机工作区状态

命令：

```bash
git status --short
```

输出摘要：

```text
 M .codex/agents/full-stack-software-engineer.toml
 M .codex/agents/product-okr-owner.toml
 M .codex/agents/robot-algorithm-engineer.toml
 M .codex/agents/robot-hardware-engineer.toml
 M .codex/agents/robot-software-engineer.toml
 M .codex/registry.toml
?? sprints/2026.06.09_11-50_agent-execution-bias-config/
?? sprints/2026.06.09_12-05_slam-route-live-run/
```

说明：这些是本轮开始前已存在的未提交改动或未跟踪目录。本轮未覆盖、回滚或提交这些文件。

### SSH 最小环境探测

命令：

```bash
ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new root@192.168.1.11 'set -e; hostname; date; command -v ros2; find / -maxdepth 4 -name setup.bash 2>/dev/null | head -20'
```

输出：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

结论：未能登录上位机，未执行到 `hostname/date/command -v ros2/find setup.bash`。

### 网络诊断

命令：

```bash
ping -c 3 -W 1000 192.168.1.11
```

输出摘要：

```text
ping: sendto: No route to host
PING 192.168.1.11 (192.168.1.11): 56 data bytes
Request timeout for icmp_seq 0
sendto: No route to host
Request timeout for icmp_seq 1
ping: sendto: No route to host
3 packets transmitted, 0 packets received, 100.0% packet loss
```

命令：

```bash
nc -vz -G 5 192.168.1.11 37878
```

输出：

```text
nc: connectx to 192.168.1.11 port 37878 (tcp) failed: No route to host
```

命令：

```bash
arp -an | egrep '192\.168\.1\.(1|11|3)' || true
```

输出：

```text
? (192.168.1.1) at 54:2b:76:16:fb:70 on en0 ifscope [ethernet]
? (192.168.1.3) at b0:f1:d8:15:75:cb on en0 ifscope permanent [ethernet]
? (192.168.1.11) at (incomplete) on en0 ifscope [ethernet]
```

命令：

```bash
ping -c 2 -W 1000 192.168.1.1
```

输出摘要：

```text
ping: sendto: No route to host
PING 192.168.1.1 (192.168.1.1): 56 data bytes
Request timeout for icmp_seq 0
sendto: No route to host
2 packets transmitted, 0 packets received, 100.0% packet loss
```

命令：

```bash
ssh -vvv -p 37878 -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new root@192.168.1.11 'hostname'
```

输出关键片段：

```text
debug1: Connecting to 192.168.1.11 [192.168.1.11] port 37878.
debug1: connect to address 192.168.1.11 port 37878: No route to host
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

### 本机网络状态

命令：

```bash
ifconfig | sed -n '1,220p'
```

输出关键片段：

```text
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.1.3 netmask 0xffffff00 broadcast 192.168.1.255
    status: active
```

命令：

```bash
netstat -rn | sed -n '1,80p'
```

输出关键片段：

```text
default            192.168.1.1        UGScg                 en0
192.168.1          link#14            UCS                   en0
192.168.1.11       link#14            UHLWI                 en0      !
```

结论：本机处于 `192.168.1.0/24`，但目标 `192.168.1.11` 的 ARP 为 incomplete，TCP/ICMP 都无法建立邻居可达性。当前不是 SSH 认证失败，也不是 ROS2 环境失败。

## 未执行到的验收项

以下命令未执行到远端，因为 SSH 网络层不可达：

- `hostname`
- `date`
- `command -v ros2`
- `find / -maxdepth 4 -name setup.bash`
- `source /opt/ros/humble/setup.bash`
- `ros2 pkg list | egrep 'ros2_trashbot_(bringup|nav|hardware|behavior)'`
- `ros2 topic list | egrep '/scan|/camera/image_raw|/odom|/tf|/map'`
- `/scan`、`/odom`、`/camera/image_raw` 的 `ros2 topic hz`
- `/tf` 的 `ros2 topic echo --once`
- `ros2 launch ros2_trashbot_bringup learn.launch.py ...`
- `/trashbot/save_map` service call
- `route_csv_to_yaml`
- `fixed_route_autonomy dry_run`
- 可选 `ros2 bag record`

## 数据、样本或调试输出变化

本轮没有产出真实上位机上的 map、route、keyframe、manifest、fixed-route YAML、replay JSONL 或 rosbag。

保留的可复核材料是网络失败证据：

- SSH：`No route to host`
- ping：`100.0% packet loss`
- nc：`No route to host`
- ARP：`192.168.1.11 at (incomplete)`
- 本机 IP：`192.168.1.3/24` on `en0`

## 失败定位

根因定位：当前开发主机无法在二层/邻居发现层到达 `192.168.1.11`。`192.168.1.11` 没有 ARP 解析结果，SSH 在建立 TCP 连接前失败。

不是以下问题：

- 不是 ROS2/Humble 缺失，因为未登录上位机。
- 不是 SSH 账号或密钥认证失败，因为没有进入认证阶段。
- 不是 `learn.launch.py`、route recorder、map saver 或 fixed-route 工具失败，因为这些命令没有机会在远端执行。

下一步 owner：

- CEO / 现场网络 owner：确认 Mac 与上位机是否在同一个 WiFi/LAN，`192.168.1.11` 是否仍是上位机当前 IP，端口 `37878` 是否仍映射 SSH。
- Hardware Infra Engineer：若上位机在线但 IP 漂移，现场检查 Orange Pi 网络、供电、SSH 服务、路由器 DHCP 租约或随身 WiFi 客户端列表。
- Robot Algorithm Engineer：网络恢复后，按 `tech-plan.md` 原命令继续执行 topic smoke、SLAM/map、route.csv、fixed-route dry-run/replay。

## 剩余风险

- 本轮没有任何真实 ROS2 topic、传感器频率、TF、map 或 route 证据，因此不能提升 O3 真实现场验证完成度。
- 如果 `192.168.1.11` 是旧 DHCP 地址，下一轮需要先确认当前上位机 IP 或固定 DHCP lease，避免继续消费同一个网络 blocker。
- 如果当前 Mac 网络被 VPN、WiFi 隔离、访客网络或 AP client isolation 影响，需要先恢复本机到上位机的 L2/L3 可达性。

## 下一步能力建设建议

1. 现场先用路由器/随身 WiFi 后台确认 Orange Pi 当前 IP、MAC 和在线状态。
2. 在本机确认能 `ping 192.168.1.1` 且 `arp -an` 能解析上位机 IP 后，再重试 SSH。
3. SSH 恢复后不要停留在环境探测，立即执行 topic smoke，并优先录制最小 rosbag 或 route recorder 输出，哪怕现场不能安全移动。
