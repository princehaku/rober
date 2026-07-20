# PRD

- sprint_type: epic
- 状态：planning
- 唯一目标：在 fresh authorization 下，以 stdin JSON transport 完成 O3/O1 readiness 判定；仅 `READINESS_GO=true` 才允许进入一次有界导航。

## 验收边界

- 授权：`ceo_20260721_0025_operator_watch_route_clear_physical_limit_v4`。
- Phase A start/proof/latest/owned-stop exactly once，no retry。
- 本地 `jq -c` 提取、解析、hash、count；仅通过 stdin pipe 传给远端 curl，禁止 inline JSON。
- HTTP 200、旧 nested success、software proof、transport success 均不替代 readiness 或 mission 成功。
