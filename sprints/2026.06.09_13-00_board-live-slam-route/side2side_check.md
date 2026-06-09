# Board Live SLAM Route Sprint Side-by-side Check

## 验收口径对照

| PRD/tech-plan 要求 | 本轮结果 | 状态 |
| --- | --- | --- |
| 使用 CEO 提供的真实 SSH 入口尝试上位机执行 | 已尝试 `ssh root@192.168.1.11 -p 37878`，返回 `No route to host` | 失败，已定位到网络可达性 |
| 记录 topic 探测结果 | 未执行到远端 ROS2，无法获得 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` 状态 | 未完成 |
| 产出 `map.yaml` 或 map image | SSH 不通，未进入 SLAM/map 阶段 | 未完成 |
| 产出 `route.csv` 或 recorder manifest | SSH 不通，未进入 route recorder 阶段 | 未完成 |
| 产出 fixed-route YAML 或 replay/dry-run 日志 | 没有 `route.csv`，无法转换和回放 | 未完成 |
| 失败时保留命令、错误和下一步 owner | 已在 `tech-done.md` 记录 SSH、ping、nc、ARP、ifconfig、netstat 摘要和 owner | 完成 |
| 不提交凭证、token、私钥或远端大文件 | 未复制远端文件，未记录敏感材料 | 完成 |

## 用户验收结论

本轮没有拿到 `board_live_slam_route_evidence_pack` 的成功证据包。可验收的结果是失败边界已经从“本机没有 ROS2/Docker”推进到“真实上位机地址当前网络不可达”，并且错误发生在 SSH 认证和 ROS2 之前。

当前不能声称已完成真实建图、路线采集、fixed-route replay 或 rosbag 证据。

## 下一轮重试入口

网络恢复后，下一轮不需要重做产品规划，直接从 `tech-plan.md` 的 SSH 环境探测继续：

```bash
ssh root@192.168.1.11 -p 37878
```

如果 `192.168.1.11` 已变化，应先替换为路由器/DHCP 后台确认的新 IP，再继续执行 ROS2 topic smoke、`learn.launch.py`、save map、route conversion 和 dry-run。
