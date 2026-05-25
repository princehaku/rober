"""视觉 gate 的 OpenCV runtime adapter。

离线 proof 只依赖这里的 matcher 协议；测试可以替换 matcher，runtime 才接触
OpenCV descriptor 细节。
"""

from pathlib import Path
from typing import Any, Optional, Tuple

try:
    import cv2
except ImportError:  # pragma: no cover - 最小环境会走 UnavailableImageMatcher。
    cv2 = None


PASSED = 'passed'
IMAGE_UNREADABLE = 'image_unreadable'
NO_DESCRIPTORS = 'no_descriptors'


class OrbImageMatcher:
    """ORB matcher 适配器；阈值判断留给 proof 层统一处理。"""

    def __init__(self) -> None:
        if cv2 is None:
            raise RuntimeError('OpenCV is not available')
        # ORB 数量固定为 600，是为了和 fixed_route_autonomy 的在线 gate 保持同一量级。
        self.orb = cv2.ORB_create(600)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def _descriptors_for(self, image_path: Path) -> Tuple[Optional[Any], str]:
        image = cv2.imread(str(image_path))
        if image is None:
            return None, IMAGE_UNREADABLE
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        if descriptors is None or len(keypoints) == 0:
            return None, NO_DESCRIPTORS
        return descriptors, PASSED

    def __call__(
        self,
        keyframe_path: Path,
        live_frame_path: Path,
        _threshold: int,
    ) -> Tuple[str, int, str]:
        """返回 status/match_count/detail，让 proof 层决定是否通过。"""
        key_descriptors, key_status = self._descriptors_for(keyframe_path)
        if key_status != PASSED:
            return key_status, 0, f'keyframe {key_status}: {keyframe_path}'
        live_descriptors, live_status = self._descriptors_for(live_frame_path)
        if live_status != PASSED:
            return live_status, 0, f'live frame {live_status}: {live_frame_path}'
        matches = self.matcher.match(key_descriptors, live_descriptors)
        return PASSED, len(matches), 'descriptors matched'


class UnavailableImageMatcher:
    """OpenCV 不可用时仍输出结构化失败，而不是让 proof 崩掉。"""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def __call__(
        self,
        _keyframe_path: Path,
        _live_frame_path: Path,
        _threshold: int,
    ) -> Tuple[str, int, str]:
        return NO_DESCRIPTORS, 0, f'image matcher unavailable: {self.reason}'
