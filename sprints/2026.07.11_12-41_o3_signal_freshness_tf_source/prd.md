# O3 Signal Freshness TF Source PRD

## 用户价值

当前机器人真实板已可启动部分 Nav2/AMCL runtime，但现场证据反复停在 `/scan`、`/amcl_pose` 和 `map->odom`。对普通用户的最终价值是稳定的一键送达；本轮的直接价值是把“定位链没 ready”拆成可执行的下一步修复条件，减少下一轮继续盲目重试。

## OKR 对齐

- 直接服务 O3/O1 的 live localization / same-run path 前置链。
- 间接服务 O6/O7 后续消费同轮 route/path/material evidence。
- O5 当前最低但被真实 external production evidence blocker 锁住，本轮不继续重复 O5 support-only 工作。

## 需求

1. O10 helper artifact 必须新增一个信号 freshness 摘要，至少覆盖：
   - `/scan`
   - `/amcl_pose`
   - `/odom`
   - `/tf`
   - `/tf_static`
2. 每个 signal 至少记录：
   - topic type 或是否缺 topic；
   - publisher/subscriber 信息中可安全落盘的摘要；
   - once probe 是否执行、是否 observed、return code、elapsed、timeout；
   - header stamp 或 transform stamp，如可解析；
   - freshness 判断和 stale reason，如可判断；
   - 不可判断时明确 `unknown`，不得猜。
3. TF source 摘要必须显式区分：
   - `/tf` dynamic edge；
   - `/tf_static` static edge；
   - `odom->base_link` 是 dynamic、static 还是未观测；
   - `map->odom` 是否来自 AMCL dynamic TF。
4. root cause 必须优先使用 signal freshness 和 TF source 事实，不再只停留在泛化 `map_to_odom_not_observed`。

## 非目标

- 不执行 `/cmd_vel`、base manual、Nav2 start/stop 或任何运动命令。
- 不证明 delivery success、route execution success、HIL pass 或 production cloud。
- 不改 O5/O6/O7 archive/readback/UI。

## 验收输出

- 更新后的 helper/test/docs。
- 本地 dry-run artifact。
- 若 SSH 可达，真实板 raw artifact。
- `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
