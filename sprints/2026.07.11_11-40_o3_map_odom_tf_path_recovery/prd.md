# O3 Map Odom TF Path Recovery PRD

## 用户价值

普通用户最终需要的是“把垃圾送到固定点位”的可靠闭环。当前云端和 PC 侧已经有大量 archive/readback/consumer 能力，但缺少同 run localization/path success 时，后续 O6/O7 只能消费历史或 support-only 材料，无法形成新的 mission artifact delta。

本轮产品价值是把真实板 no-motion 定位链路从“AMCL pose 已出现但 TF 不出”推进到“可定位、可生成路径”或拿到可执行的 AMCL TF 根因，为下一轮 route execution / delivery material 做前置。

## OKR 映射

- 直接推进：O3 现场 Nav2/localization/path lane。
- 间接支撑：O1 当前缺口中的 `current same-run path generation success` 与 `Nav2 route execution success`。
- 暂不推进：O5/O6/O7 wrapper/readback；没有新 mission material 前不提高百分比。

## 需求

1. helper 必须能在 managed runtime 内确认 AMCL 是否具备发布 `map->odom` 的必要条件。
2. helper 必须区分：
   - AMCL 参数错误；
   - `/scan` 没有进入 AMCL；
   - `/map` 未被 AMCL 消费；
   - `/initialpose` 已发布但未触发 filter/TF；
   - frame contract 不一致；
   - helper 等待窗口不足；
   - TF 已出但 source inventory 未正确采集。
3. 外层 preflight 必须能回读 helper 最终 body，除非 helper 本身超过明确记录的硬 timeout。
4. 所有证明都必须保持 no-motion。

## 不做范围

- 不修改 WAVE ROVER UART、速度映射、电压、引脚、机械或 vendor 参数。
- 不新增 O5 production readiness packet。
- 不做 O6/O7 新 wrapper 或 UI 展示。
- 不宣称 live route execution、HIL pass、safe-to-control 或 delivery success。

## 验收结果定义

优先成功口径：

- real-board artifact 出现 `map_to_odom=true`；
- 若 path opt-in 同时开启，则出现 `path_generated=true` 且 `path_point_count>0`；
- safety fields 仍全部 false。

可接受的 fail-closed 口径：

- `map_to_odom=false`，但 root cause 从笼统 `map_to_odom_not_observed` 细化到 AMCL broadcast 条件中的具体失败项；
- 外层 preflight 能自然回读该最终 root cause；
- 产出下一轮明确 live 命令。
