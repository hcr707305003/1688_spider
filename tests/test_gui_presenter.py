import unittest

from gui.url_collector_app import build_summary, classify_log_level


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

    def test_classifies_log_levels_for_colored_output(self):
        self.assertEqual(classify_log_level('[SUCCESS] 页面采集完成'), 'success')
        self.assertEqual(classify_log_level('正在下载详情图片 14 / 20'), 'active')
        self.assertEqual(classify_log_level('[WARNING] 使用备用解析方式'), 'warning')
        self.assertEqual(classify_log_level('错误：页面解析失败'), 'error')
        self.assertEqual(classify_log_level('输出目录：C:/products/1'), 'default')


if __name__ == '__main__':
    unittest.main()
