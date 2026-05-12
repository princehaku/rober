"""Cloud relay runtime package.

本包只声明 cloud-relay 部署命名空间；不要在这里提前 import 子模块。
`python -m ros2_trashbot_cloud_relay.remote_cloud_relay` 会由 runpy 再加载一次
目标模块，提前导入会产生重复加载 warning，影响 Docker smoke 日志可信度。
"""

__all__ = []
