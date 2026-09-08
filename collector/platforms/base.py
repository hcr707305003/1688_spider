"""平台适配器公共接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Protocol, Sequence


@dataclass(frozen=True)
class CollectionTarget:
    """经过平台适配器校验和规范化的采集目标。"""

    platform: str
    product_id: str
    source_url: str
    normalized_url: str


class CollectionRuntime(Protocol):
    """适配器可使用的运行时能力。"""

    project_root: Path
    data_root: Path

    def stage(self, name: str, progress: int, message: str) -> None:
        ...

    def log(self, message: str) -> None:
        ...

    def run_process(self, command: Sequence[str]) -> None:
        ...


class PlatformAdapter(ABC):
    """一个商品平台的链接识别和采集实现。"""

    platform = 'unknown'
    display_name = '未知平台'

    @abstractmethod
    def matches(self, url: str) -> bool:
        """链接是否属于当前平台。"""

    @abstractmethod
    def prepare(self, url: str) -> CollectionTarget:
        """校验链接并生成规范化采集目标。"""

    @abstractmethod
    def collect(self, target: CollectionTarget, runtime: CollectionRuntime) -> Dict[str, Any]:
        """完成采集并返回 GUI 可展示的结果。"""
