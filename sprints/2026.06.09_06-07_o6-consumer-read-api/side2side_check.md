# O6 Consumer Read API Side-to-Side Check

## 对照目标

- PRD/tech-plan 要求新增统一消费侧查询面
- 不改既有 `/api/o6/archive/*`、`/api/o6/tunnel/*` contract
- 聚合 task、events、evidence、labels、inference、tunnel latest known status
- 支持 `view=summary` 和 `include=...`
- 保持 fail-closed 和 `not_proven` 边界

## 对照结果

### 1. 接口形态

- 已实现 `GET /api/o6/consumer/tasks`
- 已实现 `GET /api/o6/consumer/tasks/<task_id>`
- 保持既有 O6 archive/tunnel endpoint 不变

### 2. 聚合完整性

- task summary：已聚合
- trajectory：已聚合，可 summary 裁剪
- events：已聚合，按时间升序，保留 inference 特例字段
- evidence：已聚合，兼容 string/dict 摘要
- labeling：已聚合，保持 `pending|partial|labeled`
- inference：已从 `model_inference.*` events 抽摘要
- tunnel：已提供 latest known robot snapshot，并显式声明非 task 时间对齐

### 3. fail-closed

- missing task：已覆盖
- robot mismatch：已覆盖
- unknown include：已覆盖
- unknown view：已覆盖
- invalid/oversized limit：已覆盖
- unsafe query：已覆盖
- no labels / no inference / no tunnel：已覆盖

### 4. 证明边界

- `proof_status=not_proven`：保持
- `safe_to_control=false`：保持
- `connects_cloud_production=false`：保持
- `robot_control_executed=false`：保持
- 未引入真实云、真实手机、真实机器人控制或真实交付成功声明

## 验收结论

- 本轮实现满足 tech-plan 中的 O6-KR6 统一消费侧 REST 查询面要求
- 可作为 PC / 后续手机消费的统一只读入口继续推进
- 边界仍是 local/mock software proof
