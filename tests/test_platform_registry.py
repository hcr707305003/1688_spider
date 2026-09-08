import unittest

from collector.platforms import Alibaba1688Adapter, PlatformRegistry, UnsupportedPlatformError


class PlatformRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = PlatformRegistry([Alibaba1688Adapter()])

    def test_matches_and_normalizes_1688_offer(self):
        target = self.registry.prepare(
            'https://detail.1688.com/offer/1021866455459.html?spm=test#details'
        )
        self.assertEqual(target.platform, '1688')
        self.assertEqual(target.product_id, '1021866455459')
        self.assertEqual(
            target.normalized_url,
            'https://detail.1688.com/offer/1021866455459.html',
        )

    def test_rejects_unknown_and_spoofed_domains(self):
        invalid_urls = [
            '',
            'https://item.taobao.com/item.htm?id=1',
            'https://item.jd.com/1.html',
            'https://detail.1688.com.example.com/offer/1021866455459.html',
            'https://detail.1688.com/offer/not-a-number.html',
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(UnsupportedPlatformError):
                    self.registry.prepare(url)

    def test_new_adapter_can_be_registered_without_gui_changes(self):
        class DemoAdapter(Alibaba1688Adapter):
            platform = 'demo'

            def matches(self, url):
                return url == 'https://demo.test/item/1'

        self.registry.register(DemoAdapter())
        self.assertEqual(self.registry.match('https://demo.test/item/1').platform, 'demo')


if __name__ == '__main__':
    unittest.main()
