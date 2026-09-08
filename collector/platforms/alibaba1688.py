"""1688 商品平台适配器。"""

import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from collector.exporter import export_product
from collector.runtime_paths import build_auto_collector_command, build_parser_command

from .base import CollectionRuntime, CollectionTarget, PlatformAdapter


_OFFER_PATH = re.compile(r'^/offer/(\d+)\.html$')


class Alibaba1688Adapter(PlatformAdapter):
    platform = '1688'
    display_name = '1688'

    def matches(self, url: str) -> bool:
        try:
            parsed = urlsplit(url.strip())
        except ValueError:
            return False
        return (
            parsed.scheme in {'http', 'https'}
            and (parsed.hostname or '').lower() == 'detail.1688.com'
            and _OFFER_PATH.fullmatch(parsed.path) is not None
        )

    def prepare(self, url: str) -> CollectionTarget:
        source_url = url.strip()
        if not self.matches(source_url):
            raise ValueError('请输入有效的 1688 商品详情链接')
        parsed = urlsplit(source_url)
        match = _OFFER_PATH.fullmatch(parsed.path)
        product_id = match.group(1)
        normalized_url = urlunsplit(('https', 'detail.1688.com', parsed.path, '', ''))
        return CollectionTarget(self.platform, product_id, source_url, normalized_url)

    def collect(self, target: CollectionTarget, runtime: CollectionRuntime) -> Dict[str, Any]:
        products_dir = runtime.data_root / 'products'
        html_path = products_dir / f'{target.product_id}.html'
        output_dir = products_dir / target.product_id

        runtime.stage('启动浏览器', 15, '正在启动 Chrome')
        runtime.run_process(build_auto_collector_command(target.normalized_url, products_dir))

        runtime.stage('保存页面', 35, '正在检查页面内容')
        self._validate_page(html_path)

        runtime.stage('解析数据', 50, '正在解析商品信息')
        runtime.stage('下载资源', 65, '正在解析并下载商品资源')
        runtime.run_process(build_parser_command(html_path))

        runtime.stage('生成结果', 90, '正在生成 product.json')
        result = export_product(html_path, output_dir, target)
        result['output_dir'] = str(output_dir)
        return result

    @staticmethod
    def _validate_page(html_path: Path) -> None:
        if not html_path.exists() or html_path.stat().st_size < 1000:
            raise RuntimeError('未保存到有效的商品页面')
        html_content = html_path.read_text(encoding='utf-8', errors='replace')
        title = BeautifulSoup(html_content, 'html.parser').title
        title_text = title.get_text(' ', strip=True) if title else ''
        blocked_words = ('登录', '验证码', '安全验证', 'login', 'captcha')
        if not title_text or any(word.lower() in title_text.lower() for word in blocked_words):
            raise RuntimeError('当前页面可能是登录或验证码页面，请在 Chrome 中处理后重试')
