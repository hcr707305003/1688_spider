"""源码运行和便携版运行使用的统一路径。"""

import sys
from pathlib import Path
from typing import List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


def app_root() -> Path:
    """用户看到的程序根目录。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def data_root() -> Path:
    """所有可写便携数据的根目录。"""
    return app_root() / 'data' if is_frozen() else PROJECT_ROOT


def products_root() -> Path:
    return data_root() / 'products'


def browser_data_root() -> Path:
    return data_root() / 'browser_data' if is_frozen() else PROJECT_ROOT / 'tools' / 'browser_data'


def portable_browser_paths() -> Tuple[Path, Path]:
    root = app_root() / 'browser'
    return root / 'chrome' / 'chrome.exe', root / 'chromedriver.exe'


def worker_executable() -> Path:
    return app_root() / '_collector_worker.exe'


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise RuntimeError(f'{label}缺失：{path}。请重新解压完整便携版。')
    return path


def build_auto_collector_command(url: str, output_dir: Path) -> List[str]:
    common = [url, '--chrome', '--no-extensions', '--output-dir', str(output_dir)]
    if not is_frozen():
        return [sys.executable, '-u', '-m', 'utils.auto_collector', *common]

    worker = _require_file(worker_executable(), '采集工作程序')
    browser, driver = portable_browser_paths()
    _require_file(browser, '内置浏览器')
    _require_file(driver, '内置浏览器驱动')
    return [
        str(worker),
        'auto',
        *common,
        '--portable',
        '--browser-binary', str(browser),
        '--driver-path', str(driver),
        '--user-data-dir', str(browser_data_root()),
    ]


def build_parser_command(html_path: Path) -> List[str]:
    args = [str(html_path), '--no-rebuild']
    if is_frozen():
        worker = _require_file(worker_executable(), '采集工作程序')
        return [str(worker), 'parse', *args]
    return [sys.executable, '-u', str(PROJECT_ROOT / 'main.py'), *args]
