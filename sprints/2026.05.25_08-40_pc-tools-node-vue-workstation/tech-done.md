# PC Tools Node/Vue Workstation Tech Done

## sprint_type

epic

## 实际改动

- 在 `pc-tools/workstation/` 新增 PC-only Node.js + Vue 3 + Vite + TypeScript 工作站。
- 新增只读 Node API：
  - `GET /api/health`
  - `GET /api/tools/evidence`
  - `GET /api/tools/training-labeling`
  - `GET /api/route/debug-summary`
  - `GET /api/proof-boundary`
- 新增 Vue UI 四个入口：Route Debug、Evidence Tools、Training/Labeling、Proof Boundary。
- Route Debug 摘要映射旧 `trashbot.pc_route_debug_console.v1` 字段，并固定 `console_controls=read_only`。
- Evidence Tools 只做文件清单、分类、测试配对和 docstring 摘要索引，不执行 Python gate。
- 所有 API/UI 固定暴露或继承 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- 更新 `docs/product/pc_tools_workstation.md`，记录第一阶段产品边界、禁止声明和验证方式。

本轮未改动 `pc-tools/evidence/**`、`pc-tools/route/**`、`onboard/**`、`mobile/**`、`cloud-relay/**`、硬件配置、ROS2 launch 或 vendor 文档事实。

## 验证结果

`cd pc-tools/workstation && npm install`

```text
added 350 packages in 20s
```

补充 `@vue/tsconfig` 后重跑：

```text
up to date in 2s
```

`cd pc-tools/workstation && npm run build`

```text
vite v7.3.3 building client environment for production...
✓ 12 modules transformed.
dist/index.html                 0.41 kB │ gzip:  0.28 kB
dist/assets/index-DODnbetI.css  2.65 kB │ gzip:  1.02 kB
dist/assets/index-BeHHTF_5.js  68.27 kB │ gzip: 26.64 kB
✓ built in 670ms
```

`cd pc-tools/workstation && npm run test`

```text
Test Files  2 passed (2)
Tests  5 passed (5)
```

测试覆盖：

- `delivery_success=false`
- `primary_actions_enabled=false`
- `console_controls=read_only`
- API/UI 不包含 `/cmd_vel`
- API/UI 不包含 `/dev/tty`
- Evidence index 只索引 Python 文件和测试配对，不执行旧 gate

`cd pc-tools/workstation && npm run lint`

```text
eslint .
```

命令退出码为 0。

`python -m unittest discover pc-tools/route -p "test_*.py"`

```text
Ran 7 tests in 0.071s
OK
```

本地 API/UI 启动 smoke：

```text
pc-tools workstation API listening on http://127.0.0.1:8787
GET /api/health -> source=software_proof, proof_status=not_proven,
safe_to_control=false, delivery_success=false, pc_only=true
```

注释比例自检：

```text
pc-tools/workstation/src: 697 nonblank lines, 140 comment lines, 20.09%
```

## 失败定位与修复

- 第一轮 `npm run build` 失败：缺 `.vue` 声明、server 类型导入未使用 type-only、`replaceAll` 目标库不匹配。已新增 `src/env.d.ts`、改为 type-only import，并改用 `split(path.sep).join("/")`。
- 第一轮 `npm run test` 失败：UI 未在 `onMounted` 调用 `refresh()`。已接入加载逻辑。
- 第一轮 `npm run lint` 失败：ESLint 未正确处理 Vue SFC 的 TypeScript parser。已补 flat config parserOptions，并关闭单行模板换行噪声规则。
- 启动 smoke 失败：Express 5 不接受 `app.get("*")` 通配写法。已改为无路径 fallback middleware。
- 第二轮 `npm run test` 被早期错误编译残留的 `dist-server/test/*.js` 干扰。已在 Vitest exclude 中排除 `dist/**` 和 `dist-server/**`，并在 `.gitignore` 排除构建与运行产物。

## 剩余风险

- 本轮只证明 PC 本地 Node/Vue 工作站可安装、构建、测试、lint、只读索引旧 gate；不证明真实 ROS2、Nav2、fixed-route、硬件、HIL、真实手机、云端或交付成功。
- Route Debug 第一阶段不读取 live route JSON；旧 route console 的运行态字段仅做 fail-closed 映射。
- Training/Labeling 仍是占位入口，未接真实数据集、训练流水线或标注 UI。
- 本轮没有提升 Objective 5 外部证明完成度。
