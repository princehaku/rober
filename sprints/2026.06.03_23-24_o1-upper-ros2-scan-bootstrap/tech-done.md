# O1 Upper ROS2 Scan Bootstrap Micro Sprint

## sprint_type

micro

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`
- `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`，仅作为历史 ROS1/protocol comparison，不作为当前 ROS2 source of truth。

本轮采用的 LiDAR 事实边界：当前 ROS2/STC source of truth 是 `docs/vendor/lidar_pkg_ros2-main/`；`150000` baud、`A5 60` 启动、`A5 00 A5 65 A5 65` 停止、`0xAA 0x55` packet sync、`/scan` 来自该本地 vendor 资料。历史 `docs/vendor/lidar_ros/` 只用于对照 raw packet topic 形态。

## 实际改动

- 修改 `onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh`：
  - 新增 `UBUNTU_APT_MIRROR` / `--ubuntu-apt-mirror`，默认 `https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports`。
  - 在安装 ROS2 runtime 前备份 `/etc/apt/sources.list` 到 `/etc/apt/sources.list.o1-bootstrap.bak`。
  - 将 Ubuntu ports sources 写为 `[arch=arm64]`，避免远端已启用的 `armhf` foreign architecture 继续拉取 armhf 索引并放大坏镜像 blocker。
  - 不移除 foreign architecture，不启动 ROS2 driver，不打开 LiDAR 串口，不写 `/dev/ttyS5`。

未修改 `OKR.md`、`docs/process/okr_progress_log.md` 或其他 docs/process 文件。本轮真实 `/scan` 未观察到，因此不提升 O1 百分比。

## 远端验证结果

入口与路径：

- 用户指定上位机 SSH：`ssh root@192.168.1.11 -p 37878`
- 首次执行验收命令：
  - `ssh root@192.168.1.11 -p 37878 'bash /root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh'`
  - 结果：`bash: /root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh: No such file or directory`
- 只读检查发现远端同名脚本位于 `/root/rober/onboard/` 根目录，而不在验收路径 `/root/rober/onboard/scripts/`。
- 已同步本地允许范围内 O1 脚本到远端 `/root/rober/onboard/scripts/` 并设为 executable。

第二次 bootstrap：

- 已进入脚本并确认平台：
  - `[o1-bootstrap] os=ubuntu version=22.04 codename=jammy arch=arm64`
- 失败于远端原有华为云 Ubuntu ports mirror：
  - `File has unexpected size ... Mirror sync in progress?`
  - 远端 `dpkg --print-architecture=arm64`
  - 远端 `dpkg --print-foreign-architectures=armhf`
  - `/etc/apt/sources.list` 全部指向 `http://repo.huaweicloud.com/ubuntu-ports/`

只读/低风险定位：

- 使用临时 apt source 验证 `https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports` + `[arch=arm64]` 可以完成 `apt-get update`。
- 该验证不安装包、不启动 ROS2、不打开任何串口。

第三次 bootstrap：

- 同步修复后的 bootstrap 到远端验收路径后重新执行同一验收命令。
- 观察到：
  - `[o1-bootstrap] backed up /etc/apt/sources.list to /etc/apt/sources.list.o1-bootstrap.bak`
  - `[o1-bootstrap] configured Ubuntu apt mirror=https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports arch=arm64`
  - 基础包安装进入 `apt-get install -y curl gnupg lsb-release locales software-properties-common`
  - `/var/log/apt/history.log` 记录本轮 upgrade `curl/gnupg/locales/libcurl4` 等基础包。

截至 `2026-06-03T23:46:26+08:00` 的只读 SSH 检查：

```text
ps:
bash /root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh
apt-get install -y curl gnupg lsb-release locales software-properties-common
/usr/bin/dpkg --status-fd 28 --configure --pending
/usr/share/debconf/frontend /var/lib/dpkg/info/locales.postinst configure 2.35-0ubuntu3.8
/bin/bash /usr/sbin/locale-gen
localedef -i zh_CN -c -f UTF-8 -A /usr/share/locale/locale.alias zh_CN.UTF-8

pgrep:
apt-get install -y curl gnupg lsb-release locales software-properties-common
/usr/bin/dpkg --status-fd 28 --configure --pending
/bin/sh /var/lib/dpkg/info/locales.postinst configure 2.35-0ubuntu3.8
/bin/bash /usr/sbin/locale-gen
localedef -i zh_CN -c -f UTF-8 -A /usr/share/locale/locale.alias zh_CN.UTF-8

runtime files:
/opt/ros/humble/setup.bash: missing
/root/rober/onboard/install/setup.bash: missing
```

没有发现 `colcon` 进程。没有发现脚本专属输出文件：

- `/tmp/o1_ros2_humble_arm64_bootstrap.log` missing
- `/root/rober/onboard/o1_ros2_humble_arm64_bootstrap.log` missing
- `/root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.log` missing

## blocker

当前 blocker 不是 LiDAR、不是 WAVE ROVER、不是 ROS2 driver 缺陷；它是远端 bootstrap 仍停留在 Ubuntu 基础包安装的 locale 生成阶段：

- 原 blocker：华为云 Ubuntu ports mirror index 同步不一致，叠加远端 `armhf` foreign architecture 导致 apt update 失败。
- 已做最小修复：bootstrap 改为 arm64-only 清华 Ubuntu ports mirror，并已越过 apt update blocker。
- 当前运行中 blocker：`locales.postinst` 正在全量 `locale-gen/localedef`，apt/dpkg 尚未自然结束。

在该进程自然结束前，不应启动新的 apt、colcon、ROS2 或 LiDAR smoke。

## 安全边界

本轮未运行 LiDAR smoke，未启动 ROS2 LiDAR driver，未观察真实 `/scan`、`/lidar/raw_packet` topic 或 TF。

本轮没有打开或写入 `/dev/ttyS5`，没有发送 WAVE ROVER `T=1/T=13/T=130/T=131`，没有调用 `/api/base/manual`，没有发布 `/cmd_vel`，没有声明 `safe_to_control=true`。

远端第三次 bootstrap 只执行 apt/bootstrap 路径；它不应触发 LiDAR `A5 60` 或任何底盘命令。

## 剩余风险

- 远端 apt/dpkg 仍在运行，若被中断，可能留下 half-configured package，需要后续只读确认后再决定是否执行 `dpkg --configure -a`；本轮没有启动该修复命令。
- ROS2 Humble runtime 仍未安装完成，`/opt/ros/humble/setup.bash` 仍缺失。
- `/root/rober/onboard/install/setup.bash` 仍缺失，`colcon build` 尚未开始。
- LiDAR ROS2 `/scan` once/hz、`/lidar/raw_packet` once、`tf2_echo base_link laser_frame` 均未验证。
- O1 仍不能写成 HIL pass、真实 `/scan` proven、SLAM/Nav2 消费 proven、运动控制安全或 `safe_to_control=true`。

## 本地验证

已由 Hardware Infra Engineer 执行：

```bash
bash -n onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh onboard/scripts/o1_lidar_ros2_scan_smoke.sh
# passed

git diff --check -- onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh sprints/2026.06.03_23-24_o1-upper-ros2-scan-bootstrap/tech-done.md
# passed
```
