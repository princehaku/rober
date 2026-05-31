# 2026.05.29 00-01 upper-computer-deploy

sprint_type: micro

## 实际改动

- `onboard/scripts/docker_humble_build.sh`
  - 增加 `docker build --help` 能力探测。
  - 支持 `--progress` 的 Docker CLI 保持原构建参数。
  - 只有 legacy builder 的 Orange Pi 上自动省略 `--progress`，并输出 `docker_build_progress_arg=unsupported_legacy_builder`，避免旧 Docker CLI 在构建前直接失败。
- `onboard/README.md`
  - 增补 Orange Pi 上位机部署说明。
  - 明确 `/root/rober` 这类独立目录、rsync 排除派生产物、legacy builder 降级和国内 Docker registry/DNS 排查边界。
- 远端机器配置（未写入仓库）
  - 目标：`root@192.168.1.11 -p 37878`。
  - Docker daemon DNS 已改为 `114.114.114.114`、`223.5.5.5`。
  - Docker registry mirrors 已从旧的 `dockerproxy.com`、USTC、NJU 组合改为国内可尝试入口：`docker.1ms.run`、`docker.1panel.live`、`hub.rat.dev`、`docker.m.daocloud.io`、`mirror.ccs.tencentyun.com`。

## 远端部署目录

- 部署目录：`/root/rober`
- 部署方式：`rsync -az --mkpath` 通过 SSH 同步。
- 同步排除：`.git/`、`build/`、`install/`、`log/`、`__pycache__/`、`*.pyc`、`node_modules/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`。
- 同步范围：`AGENTS.md`、`OKR.md`、`onboard/`、`docs/`、`scripts/`。

## 验证结果

### SSH 与系统探测

命令：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'hostname; uname -a; pwd; command -v docker || true; command -v colcon || true; test -f /opt/ros/humble/setup.bash && echo ros_humble=yes || echo ros_humble=no'
```

关键输出：

```text
Authenticated to 192.168.1.11 using "publickey".
ssh_ok
op-z3-b6.home
Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64 GNU/Linux
/root
/usr/bin/docker
ros_humble=no
```

结论：SSH key 登录可用；远端是 Ubuntu 22.04.5/aarch64；有 Docker；没有裸机 ROS Humble；未发现 `colcon`。

### 网络与端口探测

命令：

```bash
ping -c 3 -W 2 192.168.1.11
nc -vz -w 5 192.168.1.11 37878
```

关键输出：

```text
3 packets transmitted, 3 received, 0% packet loss
Connection to 192.168.1.11 37878 port [tcp/*] succeeded!
```

结论：目标主机和 SSH 端口可达。第一次 `No route to host` 判断为链路刚恢复或临时 ARP/路由抖动。

### 目录与 Docker 探测

命令：

```bash
ssh -p 37878 root@192.168.1.11 'hostname; uname -m; sed -n "1,6p" /etc/os-release; ls -la /root /opt; docker version --format "Client={{.Client.Version}} Server={{.Server.Version}}"; docker info --format "Arch={{.Architecture}} OSType={{.OSType}} Driver={{.Driver}} Root={{.DockerRootDir}}"'
```

关键输出：

```text
op-z3-b6.home
aarch64
PRETTY_NAME="Ubuntu 22.04.5 LTS"
Client=27.3.1 Server=27.3.1
Arch=aarch64 OSType=linux Driver=overlay2 Root=/var/lib/docker
```

结论：`/root/rober`、`/opt/rober` 原本未发现；选择 `/root/rober`，避免覆盖 `/opt` 系统/容器目录。

### 安全部署同步

命令：

```bash
rsync -az --info=stats2,progress2 --mkpath -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=8' --exclude='.git/' --exclude='build/' --exclude='install/' --exclude='log/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='node_modules/' --exclude='.pytest_cache/' --exclude='.mypy_cache/' --exclude='.ruff_cache/' AGENTS.md OKR.md onboard docs scripts root@192.168.1.11:/root/rober/
```

关键输出：

```text
Number of files: 587 (reg: 496, dir: 91)
Number of regular files transferred: 496
Total file size: 175,283,011 bytes
Total transferred file size: 175,283,011 bytes
sent 117,058,619 bytes  received 9,932 bytes
```

结论：仓库上车软件与必要文档已部署到 `/root/rober`。

### 远端 Docker/Humble 构建尝试

第一次命令：

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober && bash onboard/scripts/docker_humble_build.sh'
```

关键输出：

```text
docker: 'buildx' is not a docker command.
unknown flag: --progress
```

定位：远端 Docker 缺少 `buildx`，legacy builder 不支持 `--progress`。

修复脚本并同步后第二次命令：

```bash
rsync -az -e 'ssh -p 37878 -o BatchMode=yes -o ConnectTimeout=8' onboard/scripts/docker_humble_build.sh root@192.168.1.11:/root/rober/onboard/scripts/docker_humble_build.sh
ssh -p 37878 root@192.168.1.11 'cd /root/rober && bash onboard/scripts/docker_humble_build.sh'
```

关键输出：

```text
docker_build_progress_arg=unsupported_legacy_builder
Step 1/12 : ARG ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop
Step 2/12 : FROM ${ROS_HUMBLE_BASE_IMAGE}
Get "https://registry-1.docker.io/v2/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)
```

结论：legacy builder 参数问题已绕过；构建继续失败在 Docker Hub 基础镜像拉取。

### Docker registry/DNS 定位

命令：

```bash
ssh -p 37878 root@192.168.1.11 'docker pull osrf/ros:humble-desktop'
ssh -p 37878 root@192.168.1.11 'getent hosts registry-1.docker.io || true; curl -4 -I https://registry-1.docker.io/v2/ || true; curl -4 -I https://dockerproxy.com/v2/ || true; curl -4 -I https://docker.nju.edu.cn/v2/ || true'
```

关键输出：

```text
Error response from daemon: Get "https://registry-1.docker.io/v2/": net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
dockerproxy.com: Failed to connect ... Connection refused
docker.nju.edu.cn: HTTP/2 403
docker.mirrors.ustc.edu.cn: no such host
```

结论：当前阻塞不是 SSH、不是目录、不是 ROS 包代码；是远端 Docker registry/DNS/国内镜像源不可用。

### DNS 与国内 Docker mirror 修正后复测

命令：

```bash
ssh -p 37878 root@192.168.1.11 'cat /etc/docker/daemon.json; timeout 180 docker pull osrf/ros:humble-desktop'
ssh -p 37878 root@192.168.1.11 'timeout 600 docker pull osrf/ros:humble-desktop'
ssh -p 37878 root@192.168.1.11 'timeout 900 docker pull osrf/ros:humble-desktop'
ssh -p 37878 root@192.168.1.11 'docker image inspect osrf/ros:humble-desktop --format "IMAGE={{.Id}} ARCH={{.Architecture}} OS={{.Os}} SIZE={{.Size}}" 2>/dev/null || echo IMAGE_NOT_PRESENT; docker system df || true'
```

关键输出：

```text
"dns": ["114.114.114.114", "223.5.5.5"]
"registry-mirrors": [
  "https://docker.1ms.run",
  "https://docker.1panel.live",
  "https://hub.rat.dev",
  "https://docker.m.daocloud.io",
  "https://mirror.ccs.tencentyun.com"
]
humble-desktop: Pulling from osrf/ros
23c2f449b78b: Download complete
1ac297fbc77e: Download complete
...
6104cd6dd684: Pull complete
29e3a45fbfd1: Pull complete
context canceled
IMAGE_NOT_PRESENT
Images          3         1         41.44MB   41.44MB (100%)
```

结论：DNS 和国内 mirror 修正后，远端已经能进入镜像层下载，不再停在 registry 握手；但 `osrf/ros:humble-desktop` 体积较大，三次有上限拉取（180s、600s、900s）都在最后大层前超时，最终没有生成完整镜像。为避免无期限等待，本轮停止继续拉取，保留为网络吞吐/大镜像下载 blocker。

## 失败定位

- 已修复：`docker_humble_build.sh` 原先默认传 `--progress`，远端 legacy Docker builder 不支持该参数。
- 当前阻塞：远端 Docker 仍无法完整拉取 `osrf/ros:humble-desktop`。
- 证据：修正 DNS/mirror 前，Docker Hub 超时、`dockerproxy.com` 拒绝连接、USTC mirror DNS 失败、NJU mirror 403；修正后可开始下载镜像层，但 180s/600s/900s 三次 bounded pull 均以 `context canceled` 收口，`docker image inspect` 显示 `IMAGE_NOT_PRESENT`。
- 已按 CEO 指令处理：远端 Docker daemon DNS 已配置 `114.114.114.114`，同时追加 `223.5.5.5`；Docker registry mirrors 已切换为国内可尝试入口。

## 剩余风险

- 未完成 `colcon build --symlink-install`，因为基础 Docker 镜像仍未拉取成功。
- 未完成 `ros2 pkg prefix ros2_trashbot_bringup`，因为 install 空间尚未生成。
- 未覆盖真实硬件/HIL/串口/WAVE ROVER feedback；本轮只做上位机软件部署与构建入口验证，没有启动硬件 launch，也没有改硬件参数。
- 国内 Docker mirror 可用性随时间变化，需要再次短超时验证 `docker pull osrf/ros:humble-desktop` 后再跑完整构建。

## 下一步命令

不建议继续无期限等待。下一步只做短超时：

```bash
ssh -p 37878 root@192.168.1.11 'timeout 120 docker pull osrf/ros:humble-desktop'
ssh -p 37878 root@192.168.1.11 'cd /root/rober && timeout 1800 bash onboard/scripts/docker_humble_build.sh'
```

如果国内 mirror 仍不可用，改走离线 arm64 镜像：

```bash
docker pull --platform linux/arm64 osrf/ros:humble-desktop
docker save osrf/ros:humble-desktop -o osrf-ros-humble-desktop-arm64.tar
scp -P 37878 osrf-ros-humble-desktop-arm64.tar root@192.168.1.11:/root/
ssh -p 37878 root@192.168.1.11 'docker load -i /root/osrf-ros-humble-desktop-arm64.tar'
ssh -p 37878 root@192.168.1.11 'cd /root/rober && bash onboard/scripts/docker_humble_build.sh'
```

## 协同判断

- Product：不需要，本轮是部署执行缺口收口。
- Hardware：暂不需要；未涉及 UART、串口设备、WAVE ROVER 参数或真实硬件启动。
- Autonomy：不需要；未触发 Nav2/SLAM/路线验证。
- Full-Stack：不需要；未涉及手机/Web/API。
