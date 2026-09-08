"""平台适配器。"""

from .alibaba1688 import Alibaba1688Adapter
from .registry import PlatformRegistry, UnsupportedPlatformError

__all__ = ['Alibaba1688Adapter', 'PlatformRegistry', 'UnsupportedPlatformError']
