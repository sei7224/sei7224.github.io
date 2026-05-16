#!/usr/bin/env python3
"""
記事自動生成スクリプト
使い方: python generate_article.py
"""

import anthropic
import os
import json
import random
from datetime import datetime
from pathlib import Path

TRACKING_ID = os.environ.get("AMAZON_TRACKING_ID", "sei722406-22")

# 記事テーマ一覧（毎日1つずつ消費）
ARTICLE_TOPICS = [
    {"title": "ワイヤレスイヤホン おすすめ5選【2026年版】", "keyword": "ワイヤレスイヤホン", "emoji": "🎧", "tag": "イヤホン", "slug": "wireless-earphone-top5"},
    {"title": "コードレス掃除機 人気モデル比較【一人暮らし〜ファミリー向け】", "keyword": "コードレス掃除機", "emoji": "🧹", "tag": "掃除機", "slug": "cordless-vacuum-compare"},
    {"title": "在宅ワーク向けWebカメラ おすすめ5選【画質別】", "keyword": "Webカメラ テレワーク", "emoji": "💻", "tag": "PC周辺機器", "slug": "web-camera-top5"},
    {"title": "ロボット掃除機 おすすめ比較【2026年最新】", "keyword": "ロボット掃除機", "emoji": "🤖", "tag": "掃除機", "slug": "robot-vacuum-2026"},
    {"title": "ノイズキャンセリングヘッドホン おすすめ5選", "keyword": "ノイズキャンセリング ヘッドホン", "emoji": "🎵", "tag": "ヘッドホン", "slug": "noise-canceling-headphone"},
    {"title": "モバイルバッテリー おすすめ10選【容量別】", "keyword": "モバイルバッテリー", "emoji": "🔋", "tag": "スマホアクセサリ", "slug": "mobile-battery-top10"},
    {"title": "スマートスピーカー 比較【Amazon Echo vs Google Nest】", "keyword": "スマートスピーカー", "emoji": "🔊", "tag": "スマート家電", "slug": "smart-speaker-compare"},
    {"title": "電動歯ブラシ おすすめ5選【コスパ重視】", "keyword": "電動歯ブラシ", "emoji": "🦷", "tag": "健康家電", "slug": "electric-toothbrush-top5"},
    {"title": "空気清浄機 おすすめ比較【6畳〜20畳対応】", "keyword": "空気清浄機", "emoji": "💨", "tag": "空調・環境家電", "slug": "air-purifier-compare"},
    {"title": "メカニカルキーボード おすすめ5選【在宅ワーク向け】", "keyword": "メカニカルキーボード", "emoji": "⌨️", "tag": "PC周辺機器", "slug": "mechanical-keyboard-top5"},
    {"title": "4Kモニター おすすめ比較【27インチ〜32インチ】", "keyword": "4Kモニター", "emoji": "🖥️", "tag": "PC周辺機器", "slug": "4k-monitor-compare"},
    {"title": "スマートウォッチ おすすめ5選【2026年版】", "keyword": "スマートウォッチ", "emoji": "⌚", "tag": "ウェアラブル", "slug": "smartwatch-top5"},
    {"title": "ポータブル電源 おすすめ比較【キャンプ・防災用】", "keyword": "ポータブル電源", "emoji": "⚡", "tag": "アウトドア", "slug": "portable-power-compare"},
    {"title": "Bluetoothスピーカー おすすめ5選【防水モデルも】", "keyword": "Bluetoothスピーカー 防水", "emoji": "📻", "tag": "スピーカー", "slug": "bluetooth-speaker-top5"},
    {"title": "電気ケトル おすすめ比較【温度調節機能付き】", "keyword": "電気ケトル 温度調節", "emoji": "☕", "tag": "キッチン家電", "slug": "electric-kettle-compare"},
]

ARTICLE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | ガジェットレビューラボ</title>
  <meta name="description" content="{description}">
  <link rel="stylesheet" href="/css/article.css">
</head>
<body>

<header id="header">
  <div class="header-inner">
    <div class="site-logo"><a href="/"><span class="accent-bar"></span>ガジェットレビューラボ</a></div>
    <div class="site-tagline">買って後悔しない家電・ガジェット情報サイト</div>
  </div>
</header>
<nav id="nav">
  <div class="nav-inner">
    <ul class="nav-menu">
      <li><a href="/">トップ</a></li>
      <li><a href="/articles/wireless-earphone-top5.html">イヤホン</a></li>
      <li><a href="/articles/cordless-vacuum-compare.html">掃除機</a></li>
      <li><a href="/articles/web-camera-top5.html">PC周辺機器</a></li>
      <li><a href="/articles/smart-speaker-compare.html">スマート家電</a></li>
      <li><a href="/about.html">運営者情報</a></li>
      <li><a href="/contact.html">お問い合わせ</a></li>
    </ul>
  </div>
</nav>

<div class="breadcrumb">
  <div class="breadcrumb-inner">
    <a href="/">ホーム</a> › <a href="/">{tag}</a> › {title}
  </div>
</div>

<div class="article-header">
  <div class="article-header-inner">
    <span class="tag">{tag}</span>
    <h1>{emoji} {title}</h1>
    <div class="article-meta">
      <span>📅 更新：{date}</span>
      <span>⏱ 読了：約5分</span>
    </div>
  </div>
</div>

<div class="container">
  <div class="notice">
    ※ 当サイトはAmazonアソシエイト・プログラムの参加者です。リンク経由でご購入いただくと紹介料が発生します（購入者の負担増なし）。
  </div>

  <div class="prose">
    {body}
  </div>
</div>

<footer id="footer">
  <div class="footer-inner">
    <div class="footerbox">
      <div>
        <h3>サイト情報</h3>
        <ul>
          <li><a href="/">ホーム</a></li>
          <li><a href="/about.html">運営者情報</a></li>
          <li><a href="/privacy.html">プライバシーポリシー</a></li>
          <li><a href="/contact.html">お問い合わせ</a></li>
        </ul>
      </div>
      <div>
        <h3>主要カテゴリ</h3>
        <ul>
          <li><a href="/articles/wireless-earphone-top5.html">イヤホン・ヘッドホン</a></li>
          <li><a href="/articles/cordless-vacuum-compare.html">掃除機</a></li>
          <li><a href="/articles/web-camera-top5.html">PC周辺機器</a></li>
          <li><a href="/articles/smart-speaker-compare.html">スマート家電</a></li>
        </ul>
      </div>
      <div>
        <h3>新着記事</h3>
        <ul>
          <li><a href="/articles/soundcore-p40i-review.html">Soundcore P40i レビュー</a></li>
          <li><a href="/articles/wireless-earphone-top5.html">ワイヤレスイヤホン5選</a></li>
        </ul>
      </div>
    </div>
    <p class="copy">© 2026 ガジェットレビューラボ　|　当サイトはAmazonアソシエイト・プログラムの参加者です。</p>
  </div>
</footer>

</body>
</html>
"""


def generate_article_body(client: anthropic.Anthropic, topic: dict) -> str:
    """Claude APIを使って記事本文を生成する"""
    prompt = f"""
あなたは家電・ガジェット専門のブログライターです。
以下のテーマでAmazonアフィリエイト向けのレビュー記事を書いてください。

テーマ：{topic['title']}
キーワード：{topic['keyword']}

【記事の構成】
1. リード文（200文字程度）：読者の悩みに共感し、この記事で解決できることを伝える
2. 選び方のポイント（3つ）：H2見出しで
3. おすすめ商品TOP3〜5：各商品をH3見出しで、特徴・向いている人を説明
4. まとめ（100文字程度）

【ルール】
- 具体的な商品名は「〇〇（Amazonで確認）」という形式で書く
- 各商品の後にAmazonリンクのプレースホルダー「{{AMAZON_LINK_商品番号}}」を入れる
- HTMLのh2/h3/p/ul/liタグを使って構造化する
- 読みやすく、購買意欲が高まる文体で書く
- 文字数は合計1500〜2000文字程度
"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    body = message.content[0].text

    # Amazonリンクプレースホルダーを実際のリンクに変換
    import re
    def replace_amazon_link(match):
        num = match.group(1)
        return f'<a class="btn-amazon" href="https://www.amazon.co.jp/s?k={topic["keyword"].replace(" ", "+")}&tag={TRACKING_ID}" target="_blank" rel="nofollow noopener">🛒 Amazonで価格を確認する</a>'

    body = re.sub(r'\{AMAZON_LINK_(\w+)\}', replace_amazon_link, body)
    return body


def get_next_topic(topics: list) -> dict:
    """まだ記事化していないテーマをランダムに1つ選ぶ"""
    generated = set()
    articles_dir = Path("articles")
    if articles_dir.exists():
        generated = {f.stem for f in articles_dir.glob("*.html")}

    remaining = [t for t in topics if t["slug"] not in generated]
    if not remaining:
        remaining = topics  # 全部生成済みなら最初からリセット

    return random.choice(remaining)


def save_article(topic: dict, body: str):
    """記事HTMLファイルを保存する"""
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)

    html = ARTICLE_HTML_TEMPLATE.format(
        title=topic["title"],
        description=f"{topic['keyword']}のおすすめ商品を徹底比較。選び方のポイントから人気モデルまでわかりやすく解説します。",
        tag=topic["tag"],
        emoji=topic["emoji"],
        date=datetime.now().strftime("%Y年%m月%d日"),
        body=body,
    )

    output_path = articles_dir / f"{topic['slug']}.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ 記事を生成しました: {output_path}")
    return output_path


def update_index(topic: dict):
    """index.htmlの記事一覧に新しい記事カードを追加する"""
    index_path = Path("index.html")
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")

    new_card = f"""
    <div class="article-card">
      <div class="thumb">{topic['emoji']}</div>
      <div class="content">
        <span class="tag">{topic['tag']}</span>
        <h3><a href="articles/{topic['slug']}.html">{topic['title']}</a></h3>
        <p>{topic['keyword']}のおすすめ商品を徹底比較。失敗しない選び方を解説します。</p>
        <a class="read-more" href="articles/{topic['slug']}.html">続きを読む →</a>
      </div>
    </div>
"""

    # article-gridの最初に追加
    content = content.replace(
        '<div class="article-grid" id="article-list">',
        f'<div class="article-grid" id="article-list">{new_card}'
    )
    index_path.write_text(content, encoding="utf-8")
    print(f"✅ index.htmlを更新しました")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("環境変数 ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    print("📝 記事テーマを選定中...")
    topic = get_next_topic(ARTICLE_TOPICS)
    print(f"📌 テーマ: {topic['title']}")

    print("✍️  Claude APIで記事を生成中...")
    body = generate_article_body(client, topic)

    save_article(topic, body)
    update_index(topic)

    print("🎉 完了しました！")


if __name__ == "__main__":
    main()
