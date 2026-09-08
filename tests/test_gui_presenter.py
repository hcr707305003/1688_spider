import unittest

from gui.url_collector_app import build_summary


class GuiPresenterTests(unittest.TestCase):
    def test_builds_complete_summary(self):
        summary = build_summary({
            'title': '测试商品',
            'price': {'main_price': {'price': 29.5}},
            'sku_matrix': [{}, {}, {}],
            'downloaded_files': {
                'counts': {
                    'main_images': 5,
                    'color_images': 1,
                    'detail_images': 20,
                    'videos': 1,
                },
            },
            'shop_info': {'shop_name': '测试店铺'},
            'output_dir': 'C:/products/1',
        })
        self.assertEqual(summary['price'], '¥29.50')
        self.assertEqual(summary['sku_count'], '3')
        self.assertEqual(summary['image_count'], '26')
        self.assertEqual(summary['video_count'], '1')
        self.assertEqual(summary['shop'], '测试店铺')

    def test_handles_missing_fields(self):
        summary = build_summary({})
        self.assertEqual(summary['title'], '未获取商品标题')
        self.assertEqual(summary['price'], '未获取')
        self.assertEqual(summary['sku_count'], '0')
        self.assertEqual(summary['image_count'], '0')


if __name__ == '__main__':
    unittest.main()
