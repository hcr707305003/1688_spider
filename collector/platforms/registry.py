"""商品平台适配器注册中心。"""

from typing import Iterable, List

from .base import CollectionTarget, PlatformAdapter


class UnsupportedPlatformError(ValueError):
    """输入链接没有匹配到已注册平台。"""


class PlatformRegistry:
    def __init__(self, adapters: Iterable[PlatformAdapter] = ()):
        self._adapters: List[PlatformAdapter] = []
        for adapter in adapters:
            self.register(adapter)

    @property
    def adapters(self):
        return tuple(self._adapters)

    def register(self, adapter: PlatformAdapter) -> None:
        if any(item.platform == adapter.platform for item in self._adapters):
            raise ValueError(f'平台已注册: {adapter.platform}')
        self._adapters.append(adapter)

    def match(self, url: str) -> PlatformAdapter:
        cleaned = (url or '').strip()
        if not cleaned:
            raise UnsupportedPlatformError('请输入商品链接')
        for adapter in self._adapters:
            if adapter.matches(cleaned):
                return adapter
        raise UnsupportedPlatformError('暂不支持该商品平台')

    def prepare(self, url: str) -> CollectionTarget:
        return self.match(url).prepare(url)
