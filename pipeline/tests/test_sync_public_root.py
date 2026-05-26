import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sync_public_root", ROOT / "scripts" / "sync_public_root.py"
)
SYNC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SYNC)


class SyncPublicRootTests(unittest.TestCase):
    def test_sync_removes_only_articles_removed_from_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "dist"
            destination = root / "public"
            (source / "articles" / "new-product").mkdir(parents=True)
            (destination / "articles" / "old-product").mkdir(parents=True)
            (destination / "articles" / "manual-page").mkdir(parents=True)

            (source / "build-manifest.json").write_text(
                json.dumps({"published": ["new-product"]}), encoding="utf-8"
            )
            (destination / "build-manifest.json").write_text(
                json.dumps({"published": ["old-product"]}), encoding="utf-8"
            )
            (source / "index.html").write_text("new index", encoding="utf-8")
            (source / "articles" / "new-product" / "index.html").write_text(
                "new product", encoding="utf-8"
            )
            (destination / "articles" / "old-product" / "index.html").write_text(
                "old product", encoding="utf-8"
            )

            removed = SYNC.sync_public_root(source, destination)

            self.assertEqual(["old-product"], removed)
            self.assertFalse((destination / "articles" / "old-product").exists())
            self.assertTrue((destination / "articles" / "manual-page").exists())
            self.assertEqual(
                "new product",
                (destination / "articles" / "new-product" / "index.html").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(
                "new index", (destination / "index.html").read_text(encoding="utf-8")
            )

    def test_sync_rejects_manifest_without_published_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "dist"
            destination = root / "public"
            source.mkdir()
            destination.mkdir()
            (source / "build-manifest.json").write_text("{}", encoding="utf-8")

            with self.assertRaises(SYNC.SyncError):
                SYNC.sync_public_root(source, destination)


if __name__ == "__main__":
    unittest.main()
