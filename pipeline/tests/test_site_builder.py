import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "site_builder", ROOT / "scripts" / "site_builder.py"
)
SITE_BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SITE_BUILDER)


class SiteBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = json.loads(
            (ROOT / "content" / "products" / "example-draft.json").read_text(encoding="utf-8")
        )
        cls.site = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))

    def test_draft_renders_noindex_and_default_image(self):
        document = SITE_BUILDER.render_article(self.product, self.site, draft=True)
        self.assertIn('content="noindex,nofollow"', document)
        self.assertIn("../../assets/default-product.svg", document)
        self.assertNotIn('rel="sponsored', document)

    def test_external_image_requires_rights_before_publish(self):
        product = copy.deepcopy(self.product)
        product["status"] = "published"
        product["compliance"]["facts_verified"] = True
        product["compliance"]["editorial_reviewed"] = True
        product["image"]["src"] = "https://manufacturer.example/product.jpg"
        self.assertIn("external image requires image.rights_verified", SITE_BUILDER.publication_blockers(product))

    def test_affiliate_link_requires_article_disclosure_before_publish(self):
        product = copy.deepcopy(self.product)
        product["status"] = "published"
        product["compliance"]["facts_verified"] = True
        product["compliance"]["editorial_reviewed"] = True
        product["affiliate_links"] = [
            {"label": "販売ページを見る", "url": "https://merchant.example/item"}
        ]
        self.assertIn(
            "affiliate links require compliance.ad_disclosure",
            SITE_BUILDER.publication_blockers(product),
        )

    def test_reviewed_article_emits_sponsored_link(self):
        product = copy.deepcopy(self.product)
        product["status"] = "published"
        product["compliance"].update(
            {
                "facts_verified": True,
                "editorial_reviewed": True,
                "ad_disclosure": "この記事にはアフィリエイト広告が含まれます。"
            }
        )
        product["affiliate_links"] = [
            {"label": "販売ページを見る", "url": "https://merchant.example/item"}
        ]
        self.assertEqual([], SITE_BUILDER.publication_blockers(product))
        document = SITE_BUILDER.render_article(product, self.site, draft=False)
        self.assertIn('rel="sponsored nofollow noopener"', document)
        self.assertNotIn("noindex,nofollow", document)

    def automated_product(self):
        product = copy.deepcopy(self.product)
        product["status"] = "published"
        product["source"].update(
            {
                "id": "apple-newsroom-jp",
                "url": "https://www.apple.com/jp/newsroom/2026/05/example-product/",
                "allowed_for_automation": True,
            }
        )
        product["compliance"].update(
            {
                "facts_verified": True,
                "editorial_reviewed": True,
                "automation_policy": "official_release_no_image_no_affiliate_v1",
                "automation_verified_at": "2026-05-26",
                "review_actor": "Codex automation",
            }
        )
        return product

    def test_automation_policy_allows_official_release_without_commercial_assets(self):
        self.assertEqual([], SITE_BUILDER.publication_blockers(self.automated_product()))

    def test_automation_policy_blocks_external_image_and_affiliate_link(self):
        product = self.automated_product()
        product["image"].update(
            {
                "src": "https://www.apple.com/product.jpg",
                "rights_verified": True,
                "rights_basis": "example",
            }
        )
        product["affiliate_links"] = [
            {"label": "販売ページを見る", "url": "https://merchant.example/item"}
        ]
        blockers = SITE_BUILDER.publication_blockers(product)
        self.assertIn("automated publication may not include external images", blockers)
        self.assertIn("automated publication may not include affiliate links", blockers)

    def test_automation_policy_blocks_unapproved_source(self):
        product = self.automated_product()
        product["source"]["url"] = "https://manufacturer.example/product-release"
        product["source"]["id"] = "another-source"
        blockers = SITE_BUILDER.publication_blockers(product)
        self.assertIn("automated publication source is not permitted", blockers)
        self.assertIn("automated publication source host is not permitted", blockers)

    def test_automation_policy_requires_verification_record(self):
        product = self.automated_product()
        product["compliance"]["automation_verified_at"] = ""
        self.assertIn(
            "automation_verified_at is required for automated publication",
            SITE_BUILDER.publication_blockers(product),
        )

    def test_sitemap_contains_published_article_path(self):
        site = copy.deepcopy(self.site)
        site["base_url"] = "https://news.example.test"
        product = copy.deepcopy(self.product)
        product["status"] = "published"
        document = SITE_BUILDER.render_sitemap(site, [product])
        self.assertIn(
            "https://news.example.test/articles/sample-usb-c-dock/",
            document,
        )

if __name__ == "__main__":
    unittest.main()
