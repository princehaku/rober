# O3 AMCL Map TF Recovery Probe PRD

## 背景

当前 OKR 快照中 O5 约 `~85%`，是最低主 Objective；但真实 external production evidence 不在当前环境内。最近 sprint 已按红线转向 O3 现场验证 lane，真实上位机可达，且 `/scan` 当前窗口可观测。剩余关键阻塞是 AMCL/map/TF 未 ready，导致 no-motion planner/path proof 无法继续。

## 用户价值

普通用户最终需要的是“固定路线能可靠生成、显示并执行”，而不是旧 latest 或本地 mock 证明。本轮把定位链 blocker 下钻，有助于恢复真实路线采集和 Nav2 路径生成，后续才有材料给 O6/O7 消费。

## 需求

1. 在真实上位机 no-motion 场景下采集 AMCL/map/TF root-cause evidence。
2. 诊断内容至少覆盖：
   - `/map` topic 是否存在、是否有 publisher、是否能 echo 到 OccupancyGrid；
   - `/amcl_pose` topic/type/publisher/echo 状态；
   - `/map_server`、`/amcl`、`/planner_server` 等关键 lifecycle 或节点状态；
   - `map->odom`、`map->base_link` TF 是否可读，以及失败时的错误摘要；
   - managed map yaml 路径是否存在、可读，必要时记录 safe basename 和 sha256 短前缀；
   - no-motion `/api/nav2/proof/refresh` readback 是否仍失败。
3. 如果 root cause 显示是脚本诊断缺口，允许补 `field_route_evidence_preflight.py` 和单测；如果是上位机运行态问题，记录 artifact，不用伪造成功。
4. 输出 `tech-done.md`，写清实际改动、验证结果、失败定位、剩余风险。

## 非目标

- 不做 O5 production readiness 新 wrapper。
- 不做 O6/O7 consumer surface。
- 不宣称 delivery success、safe-to-control、HIL pass 或 route execution success。
- 不发送真实运动命令。

## 验收口径

- 有同轮 artifact 或 worker report 明确记录 AMCL/map/TF root-cause。
- 本地测试或脚本编译通过。
- 若真实板可达，必须运行 no-motion smoke；若不可达，必须说明不可达原因并保留 local dry-run fallback。
- `tech-done.md` 中必须包含 OKR 结论：是否有 same-run path/material success；没有则不调整主 OKR 百分比。
