"""Operator gateway static-surface contract markers.

该模块不服务生产请求；它给静态检查和 py_compile 验收提供一个稳定锚点，
避免本地 fallback HTML 的 support bundle 入口只存在于大字符串里而难以追踪。
"""


PHONE_SUPPORT_HANDOFF_ENTRY_IDS = (
    # 这些 id 必须和 operator_gateway_http.py 内的 HTML 保持一致，供静态测试定位。
    "supportHandoffButton",
    "supportBundlePanel",
    "supportBundleSafeCopy",
    "supportCopyButton",
)

PHONE_SUPPORT_HANDOFF_COPY = (
    # ACK 语义放在静态锚点中，防止后续 UI 改文案时误把 ACK 写成送达成功。
    "支持交接摘要用于失败或 blocked 复现；ACK 不代表送达成功。"
)
