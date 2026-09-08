import json
import tempfile
import unittest
from pathlib import Path

from collector.exporter import export_product
from collector.platforms.base import CollectionTarget


class ExporterTests(unittest.TestCase):
    def test_exports_utf8_product_json_and_download_counts(self):
        html = '''<!doctype html>
        <html><head>
          <title>测试商品 - 1688.com</title>
          <meta property="og:title" content="测试商品">
        </head><body>
          <a href="https://detail.1688.com/offer/1234567890.html">1688.com</a>
          <img src="https://cbu01.alicdn.com/img/ibank/O1CN01TestImage1234567890-0-cib.jpg">
        </body></html>'''
        target = CollectionTarget(
            '1688',
            '1234567890',
            'https://detail.1688.com/offer/1234567890.html?spm=test',
            'https://detail.1688.com/offer/1234567890.html',
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            html_path = root / '1234567890.html'
            output_dir = root / '1234567890'
            output_dir.mkdir()
            html_path.write_text(html, encoding='utf-8')
            (output_dir / 'T_1.jpg').write_bytes(b'jpeg')

            result = export_product(html_path, output_dir, target)
            raw = (output_dir / 'product.json').read_bytes()
            saved = json.loads(raw.decode('utf-8'))

        self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(saved['title'], result['title'])
        self.assertIn('测试商品', saved['title'])
        self.assertEqual(saved['downloaded_files']['counts']['main_images'], 1)
        self.assertEqual(saved['source_url'], target.source_url)
        self.assertEqual(saved['normalized_url'], target.normalized_url)


if __name__ == '__main__':
    unittest.main()
