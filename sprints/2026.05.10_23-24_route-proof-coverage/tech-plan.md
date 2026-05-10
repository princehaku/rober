# Sprint 2026.05.10 23-24 Route Proof Coverage - Tech Plan

## 状态

- 阶段：tech-plan completed，可直接进入 implementation。
- 时间：2026-05-10 23:24 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 执行方式：双 owner 并行（文件范围互不重叠）。

## 执行声明

本 `tech-plan` 已具备 owner、文件范围、接口边界、验收命令与风险边界。下一步由工程子 agent 直接实现，不停留在抽象计划。

## 目标

优先推进 Objective 3：在无 HIL 条件下把 fixed-route 路线可验证性从“有状态”推进到“有覆盖率证明 + 有阻塞原因 + 可被 operator 消费”。

## 并行任务拆解（强制并行）

### Owner A：`autonomy-engineer`

职责：Objective 3 导航能力切片，产出 route proof coverage。

文件范围（仅允许）：

- `src/ros2_trashbot_nav/`
- `docs/navigation/`

禁止范围：

- `src/ros2_trashbot_behavior/`
- `docs/interfaces/`
- 任何硬件驱动、vendor 文档、launch 硬件参数

实现任务：

1. 在 nav 路径补齐 route proof summary 结构化输出：
   - `coverage_rate`
   - `covered_checkpoints`
   - `total_checkpoints`
   - `missing_checkpoints`
   - `gate_status`
   - `last_block_reason`
2. 对 fixed-route dry-run / visual gate 相关状态输出补充统一语义。
3. 在 `docs/navigation/` 固化字段定义、计算口径、失败语义。
4. 增加 nav 包 targeted unittest 护栏，覆盖：
   - 全覆盖
   - 部分覆盖
   - 缺 checkpoint
   - visual gate 未通过

### Owner B：`full-stack-software-engineer`

职责：operator/diagnostics 展示与契约对齐切片。

文件范围（仅允许）：

- `src/ros2_trashbot_behavior/`
- `docs/interfaces/`

禁止范围：

- `src/ros2_trashbot_nav/`
- `docs/navigation/`
- 任何硬件驱动、vendor 文档、launch 硬件参数

实现任务：

1. 在 behavior/operator 侧消费 route proof summary，不重算 coverage 口径。
2. diagnostics/operator 输出可读状态：
   - `ready`
   - `waiting_visual_gate`
   - `insufficient_coverage`
   - `blocked`
3. 在 `docs/interfaces/` 明确该 contract 来自 nav proof 字段透传/映射，不引入第二口径。
4. 增加 behavior 包 targeted unittest 护栏，覆盖：
   - proof 正常透传
   - proof 缺字段降级
   - blocked 原因展示
   - unknown/empty 场景

## 接口边界（A/B 对齐）

- A 输出（source of truth）：`route_proof_summary`。
- B 消费（不重算）：只做字段映射与人类可读状态归类。
- 边界约束：
  - `coverage_rate` 只能由 A 计算。
  - B 不得根据本地样本重复推导 coverage。
  - 若字段缺失，B 必须标记为 `unknown`，不得伪造 `ready`。

## 验收命令（实现阶段必须执行）

以下命令由对应 owner 子 agent 执行并在 `tech-done.md` 回填关键日志。

### Owner A：`autonomy-engineer`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_*py'
PYTHONDONTWRITEBYTECODE=1 bash -lc "changed_py=$(git diff --name-only -- src/ros2_trashbot_nav docs/navigation | grep -E '\\.py$' || true); if [ -n \"$changed_py\" ]; then python3 -m py_compile $changed_py; else echo 'no python files changed for py_compile'; fi"
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
git diff --check -- src/ros2_trashbot_nav docs/navigation sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md sprints/2026.05.10_23-24_route-proof-coverage/final.md
```

### Owner B：`full-stack-software-engineer`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'
PYTHONDONTWRITEBYTECODE=1 bash -lc "changed_py=$(git diff --name-only -- src/ros2_trashbot_behavior docs/interfaces | grep -E '\\.py$' || true); if [ -n \"$changed_py\" ]; then python3 -m py_compile $changed_py; else echo 'no python files changed for py_compile'; fi"
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
git diff --check -- src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md sprints/2026.05.10_23-24_route-proof-coverage/final.md
```

## 风险边界

- 不做硬件实机/HIL，不输出“上车成功”结论。
- 不做跨模块大重构，避免引入额外回归面。
- 若任一 owner 验证失败，必须先定位修复再回填证据，不得带失败收口。

## 本轮不做什么

- 不做硬件实机（WAVE ROVER、串口、相机上车）。
- 不做 Nav2 全链路实跑验证。
- 不做模型训练、数据标注平台升级。
- 不做超出上述四个目录的重构。

## 优先级和验收口径

- P0：双 owner 并行推进，文件范围零重叠。
- P0：`route_proof_summary` contract 在 A 输出与 B 展示一致。
- P0：两位 owner 都提供 unittest + py_compile + smoke + scoped diff-check 证据。
- P1：缺字段和异常状态降级可读，不误导为可发车。

## 完成前自检

- 是否严格服务 Objective 3 的最低完成度补齐。
- 是否坚持“功能往前走，测试做护栏”。
- 是否明确写出“本轮不做什么”。
- 是否把剩余风险限定为软件证据，不夸大到实机能力。
