"""将解析结果导出为统一的 product.json。"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from utils.parser import HTMLParser

from .platforms.base import CollectionTarget


def _downloaded_files(output_dir: Path) -> Dict[str, Any]:
    groups = {
        'main_images': sorted(path.name for path in output_dir.glob('T_*') if path.is_file()),
        'color_images': sorted(path.name for path in output_dir.glob('color_*') if path.is_file()),
        'detail_images': sorted(path.name for path in output_dir.glob('C_*') if path.is_file()),
        'videos': sorted(path.name for path in output_dir.glob('video_*') if path.is_file()),
    }
    return {
        'files': groups,
        'counts': {name: len(files) for name, files in groups.items()},
        'total': sum(len(files) for files in groups.values()),
    }


def export_product(html_path: Path, output_dir: Path, target: CollectionTarget) -> Dict[str, Any]:
    html_content = html_path.read_text(encoding='utf-8')
    parser = HTMLParser(html_content)
    info = parser.get_all_info()
    info.pop('platform', None)
    info.pop('product_url', None)
    color_options = info.pop('color_options', []) or []

    result = {
        'platform': target.platform,
        'product_id': target.product_id,
        'source_url': target.source_url,
        'normalized_url': target.normalized_url,
        'collected_at': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),
        'title': info.pop('title', None),
        'description': info.pop('description', None),
        'product_code': info.pop('product_code', None),
        'price': info.pop('price', None) or {},
        'attributes': info.pop('attributes', []) or [],
        'sku_matrix': info.pop('sku_matrix', []) or [],
        'shop_info': info.pop('shop_info', None) or {},
        'ship_from': info.pop('ship_from', None),
        'sales_count': info.pop('sales_count', 0),
        'min_order': info.pop('min_order', 1),
        'resources': {
            'main_images': info.pop('main_images', []) or [],
            'color_options': [
                {'name': name, 'url': url}
                for name, url in color_options
            ],
            'detail_images': info.pop('detail_images', []) or [],
            'videos': info.pop('videos', []) or [],
        },
        'downloaded_files': _downloaded_files(output_dir),
        'platform_data': info,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'product.json'
    output_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8',
        newline='\n',
    )
    return result
