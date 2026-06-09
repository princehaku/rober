# Board Live SLAM Route Sprint Final

## 收口状态

状态：blocked。

阻塞根因：当前开发主机无法到达 CEO 提供的真实上位机地址 `192.168.1.11:37878`。SSH、ping、nc 均在网络层返回 `No route to host` 或 100% 丢包，ARP 显示 `192.168.1.11` 为 incomplete。

## 本轮完成的事

- 读取 `AGENTS.md`、`OKR.md` 和本 sprint `tech-plan.md`。
- 按要求读取 `docs/vendor/VENDOR_INDEX.md` 前 180 行。
- 执行本机 `git status --short`，确认已有 `.codex/agents/*`、`.codex/registry.toml` 和旧 sprint 未提交改动，本轮未覆盖或提交这些文件。
- 尝试真实上位机 SSH：`ssh root@192.168.1.11 -p 37878`。
- 补充网络诊断：`ping`、`nc`、`ssh -vvv`、`arp -an`、`ifconfig`、`netstat -rn`。
- 新增本 sprint `tech-done.md`、`side2side_check.md`、`final.md`，记录失败证据、边界和下一步 owner。

## OKR 影响

本 sprint 原目标是临时激活归档 O3「可验证导航与固定路线」的现场验证 lane，产出真实 map/route/replay/rosbag 证据。

由于未能进入上位机，本轮不能提升 O3 真实现场验证进度，也不能为 O7 PC 路线回放或 O2 真实送达提供新材料。

## 未完成事项

- 未登录真实上位机。
- 未确认远端 ROS2/Humble 或工作区路径。
- 未探测 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
- 未启动 `learn.launch.py`。
- 未保存地图。
- 未生成 `route.csv`、keyframe/manifest、fixed-route YAML、dry-run/replay JSONL 或 rosbag。
- 未修改 `docs/product/pc_tools_workstation.md`，因为没有新增真实路线材料消费说明。

## 风险和下一步

下一步必须先恢复本机到上位机的网络可达性：

1. 现场确认 Orange Pi/上位机已开机、入网，SSH 服务端口 `37878` 仍有效。
2. 在路由器或随身 WiFi 后台确认当前 IP 是否仍为 `192.168.1.11`。
3. 排查 Mac 是否在访客网络、VPN 隔离、AP client isolation 或错误 WiFi 下。
4. 本机先验证 `arp -an` 能解析目标 IP，`nc -vz 目标IP 37878` 能连通，再恢复本 sprint tech-plan 的 ROS2 执行链。

## 完成前反思

- 没有扩大文件范围到代码、launch、硬件配置或 docs/product。
- 没有把失败包装成路线证据成功。
- 没有使用 mock 替代本轮明确要求的真实上位机优先执行。
- 当前剩余 blocker 不是算法代码问题，而是现场网络/SSH 入口不可达。
