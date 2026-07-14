# Product Requirements Document
- sprint_type: epic
- 状态：需求已冻结，允许按 tech plan 派发实施。
- 产品方向：优先取得真实上位机同窗定位 runtime 证据，停止 support-only 包装。
- OKR 映射：O1（94%）下的 O3 live localization strict-no-motion 恢复。
- 非目标：不解决 O5 production endpoint/凭证，不执行路线或履约。
## 问题与用户价值
- current graph 无 `/map_server`、`/amcl`，导致定位链路无法形成 live 证据。
- compact fix 当前仅为 `local_fix_not_live_verified`，不能作为运行时完成证明。
- 用户需要可复验、同一窗口、无运动风险的定位 runtime 事实。
## 需求
- Algorithm 必须连接 `root@192.168.1.11`，SSH 端口 `37878`。
- 必须使用现有 helper 的 `--strict-no-motion --managed-runtime-opt-in`。
- 必须使用设备上既有 map YAML 启动 localization-only runtime。
- 必须重部署 compact collector 后再采集，避免沿用旧二进制或旧结果。
- 必须在同一采集窗口观察 `/scan` 与 `/amcl_pose`。
- 必须记录 dynamic `map->odom` 的 AMCL endpoint、timestamp 与 freshness。
- Robot Software 仅只读核对 launch/graph/source，并返回事实给 Algorithm。
## 强制安全边界

- 严禁 `--path-generation-opt-in`。
- 严禁 planner、controller、NavigateToPose。
- 严禁发布或触发 `cmd_vel`、base/manual、motion。
- 任一 guard 不满足即 fail-closed，不得降级成带运动的验证。

## 验收口径

- 同窗证据显示 localization runtime 节点存在且来源可说明。
- `/scan`、`/amcl_pose` 均有当前窗口时间戳与 freshness 结论。
- `map->odom` 为 dynamic AMCL 端点且具备可核对时间戳；静态 TF 不算通过。
- 采集结果明确 cleanup 状态和残留进程检查。
- 结果必须标注 `safe_to_control=false`、`route_execution_success=false`。
- 结果必须标注 `delivery_success=false`、`hil_pass=false`。

## 风险与不计分项

- map YAML 缺失、AMCL 不出 pose、TF 过期或 `/scan` QoS 超时均可能阻塞。
- 仅启动成功、仅 graph 截图、仅本地修复或旧窗口证据均不验收。
- 未得到同窗 live 证据前，OKR 百分比保持不变。
