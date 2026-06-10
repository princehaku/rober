# PC Simple UI Regression Smoke

Run time: 2026-06-11 03:14:45 CST

## Scope

- Target: `http://127.0.0.1:5173/`
- Method: Vite local workstation + in-app Browser DOM smoke.
- Note: Vite dev server does not serve `/api/*`; the page showed API 500 notices, but the smoke only checked first-screen layout, default advanced visibility, and visible copy boundaries.

## First Screen Result

```json
{
  "url": "http://127.0.0.1:5173/",
  "title": "Rober 小车控制台",
  "cardCount": 5,
  "cardHeadings": [
    "小车连接",
    "实时画面",
    "雷达",
    "地图",
    "移动/导航"
  ],
  "allowedActionsPresent": [
    "连接/刷新",
    "打开画面",
    "关闭画面",
    "刷新雷达",
    "刷新地图",
    "地图列表",
    "检查路径",
    "停止"
  ],
  "forbiddenHits": [],
  "detailsOpenByDefault": false
}
```

## Advanced Diagnostics Result

```json
{
  "detailsOpenAfterClick": true,
  "containsAdvancedControls": [
    "保存地图",
    "开始建图（高级）",
    "启动雷达（高级）",
    "停止雷达（高级）",
    "现场点动设置 / 控制边界",
    "safe_to_control=false",
    "/api/base/manual"
  ]
}
```

## Conclusion

The Robot Control first screen is back to the simple ordinary-user layout. Engineering and high-risk controls remain available only after opening `高级诊断`.
