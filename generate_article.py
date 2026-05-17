#!/usr/bin/env python3
"""
記事自動生成スクリプト
使い方: python generate_article.py
カテゴリ指定: python generate_article.py --category ai|money|gadget
"""

import anthropic
import os
import json
import random
import argparse
from datetime import datetime
from pathlib import Path

TRACKING_ID = os.environ.get("AMAZON_TRACKING_ID", "sei722406-22")
STATE_FILE = Path(".generation_state.json")

# ── カテゴリ1: AI業務効率化 ───────────────────────────────────────────────
TOPICS_AI = [
    {"title": "Claude vs ChatGPT 徹底比較【事務職が使うならどっち？】", "keyword": "Claude ChatGPT 比較 事務", "emoji": "🤖", "tag": "AI業務効率化", "slug": "claude-vs-chatgpt-office", "category": "ai"},
    {"title": "Notion AI 使い方完全ガイド【議事録・資料作成を自動化】", "keyword": "Notion AI 使い方 業務効率化", "emoji": "📝", "tag": "AI業務効率化", "slug": "notion-ai-guide-office", "category": "ai"},
    {"title": "Cursor AIエディタ 入門【コードを書かなくても使える活用術】", "keyword": "Cursor AI エディタ 入門", "emoji": "✨", "tag": "AI業務効率化", "slug": "cursor-ai-beginner", "category": "ai"},
    {"title": "Gamma AIでプレゼン資料を10分で作る方法", "keyword": "Gamma AI プレゼン 自動生成", "emoji": "🎨", "tag": "AI業務効率化", "slug": "gamma-ai-presentation", "category": "ai"},
    {"title": "ChatGPTで営業メールを自動作成【テンプレ付き】", "keyword": "ChatGPT 営業メール 自動作成", "emoji": "📧", "tag": "AI業務効率化", "slug": "chatgpt-sales-email", "category": "ai"},
    {"title": "Google Gemini 活用法【Googleスプレッドシート連携で作業激減】", "keyword": "Google Gemini 活用 スプレッドシート", "emoji": "💡", "tag": "AI業務効率化", "slug": "google-gemini-spreadsheet", "category": "ai"},
    {"title": "Perplexity AI の使い方【Google検索よりも速い情報収集術】", "keyword": "Perplexity AI 使い方 検索", "emoji": "🔍", "tag": "AI業務効率化", "slug": "perplexity-ai-usage", "category": "ai"},
    {"title": "Microsoft Copilot 活用【Word/Excel/Teamsでの実践ガイド】", "keyword": "Microsoft Copilot 活用 Word Excel", "emoji": "🪟", "tag": "AI業務効率化", "slug": "microsoft-copilot-guide", "category": "ai"},
    {"title": "Otter.ai 文字起こし 使い方【会議議事録を自動化する手順】", "keyword": "Otter.ai 文字起こし 会議", "emoji": "🎙️", "tag": "AI業務効率化", "slug": "otter-ai-transcription", "category": "ai"},
    {"title": "DeepL vs Google翻訳【ビジネス英語で精度が高いのはどっち？】", "keyword": "DeepL Google翻訳 比較 ビジネス", "emoji": "🌐", "tag": "AI業務効率化", "slug": "deepl-vs-google-translate", "category": "ai"},
    {"title": "NotebookLM 使い方【PDF・資料を瞬時に要約するAIノート】", "keyword": "NotebookLM 使い方 PDF要約", "emoji": "📚", "tag": "AI業務効率化", "slug": "notebooklm-usage", "category": "ai"},
    {"title": "Canva AI 資料作成【デザイン知識ゼロでもおしゃれな資料が作れる】", "keyword": "Canva AI デザイン 資料作成", "emoji": "🖼️", "tag": "AI業務効率化", "slug": "canva-ai-design", "category": "ai"},
    {"title": "AI議事録ツール おすすめ5選【Zoom・Teams対応】", "keyword": "AI 議事録 自動化 Zoom Teams", "emoji": "📋", "tag": "AI業務効率化", "slug": "ai-minutes-tools-top5", "category": "ai"},
    {"title": "月額AIサブスク コスパ比較【Claude・ChatGPT・Gemini どれを選ぶ？】", "keyword": "AI サブスク コスパ 比較 Claude ChatGPT", "emoji": "💰", "tag": "AI業務効率化", "slug": "ai-subscription-compare", "category": "ai"},
    {"title": "ChatGPTプロンプト 書き方入門【業務で使える鉄板フレーズ集】", "keyword": "ChatGPT プロンプト 書き方 業務", "emoji": "✍️", "tag": "AI業務効率化", "slug": "chatgpt-prompt-guide", "category": "ai"},
    {"title": "AI翻訳・文書作成ツール おすすめ比較 2026", "keyword": "AI 翻訳 文書作成 ツール 比較", "emoji": "📄", "tag": "AI業務効率化", "slug": "ai-document-tools-2026", "category": "ai"},
    {"title": "Slack AI 活用術【メッセージ要約・検索で情報収集を高速化】", "keyword": "Slack AI 活用 要約 効率化", "emoji": "💬", "tag": "AI業務効率化", "slug": "slack-ai-usage", "category": "ai"},
    {"title": "AIで経費精算を効率化【おすすめアプリと自動化の手順】", "keyword": "AI 経費精算 効率化 アプリ", "emoji": "🧾", "tag": "AI業務効率化", "slug": "ai-expense-report", "category": "ai"},
    {"title": "AI画像生成 入門【Midjourney・DALL-E 3 使い比べ】", "keyword": "AI 画像生成 Midjourney DALL-E 入門", "emoji": "🎭", "tag": "AI業務効率化", "slug": "ai-image-generation-intro", "category": "ai"},
    {"title": "AIチャットボット 比較【カスタマー対応・社内FAQを自動化】", "keyword": "AI チャットボット 比較 業務 自動化", "emoji": "🤖", "tag": "AI業務効率化", "slug": "ai-chatbot-compare", "category": "ai"},
]

# ── カテゴリ2: マネー最適化 ───────────────────────────────────────────────
TOPICS_MONEY = [
    {"title": "クレジットカード ポイント還元率ランキング 2026年最新版", "keyword": "クレジットカード ポイント還元率 ランキング", "emoji": "💳", "tag": "マネー最適化", "slug": "credit-card-point-ranking-2026", "category": "money"},
    {"title": "楽天カード vs 三井住友カード【どっちが得か徹底比較】", "keyword": "楽天カード 三井住友カード 比較", "emoji": "💳", "tag": "マネー最適化", "slug": "rakuten-vs-smcc-compare", "category": "money"},
    {"title": "サブスク見直し 節約術【月3万円削減できた6つのポイント】", "keyword": "サブスク 見直し 節約 削減", "emoji": "✂️", "tag": "マネー最適化", "slug": "subscription-review-savings", "category": "money"},
    {"title": "固定費削減 チェックリスト【今すぐできる12項目】", "keyword": "固定費 削減 チェックリスト 節約", "emoji": "📊", "tag": "マネー最適化", "slug": "fixed-cost-reduction-checklist", "category": "money"},
    {"title": "新NISA おすすめ証券会社 比較 2026", "keyword": "新NISA 証券会社 比較 おすすめ", "emoji": "📈", "tag": "マネー最適化", "slug": "new-nisa-securities-2026", "category": "money"},
    {"title": "楽天証券 vs SBI証券【新NISAはどちらがお得？】", "keyword": "楽天証券 SBI証券 比較 NISA", "emoji": "🏦", "tag": "マネー最適化", "slug": "rakuten-vs-sbi-nisa", "category": "money"},
    {"title": "格安SIM 乗り換えガイド【スマホ代を月5,000円以上節約する方法】", "keyword": "格安SIM 乗り換え 節約 スマホ", "emoji": "📱", "tag": "マネー最適化", "slug": "mvno-switch-guide", "category": "money"},
    {"title": "ふるさと納税 初心者向け完全ガイド【損しない申込み手順】", "keyword": "ふるさと納税 初心者 手順 節税", "emoji": "🎁", "tag": "マネー最適化", "slug": "furusato-nozei-beginner", "category": "money"},
    {"title": "iDeCo 節税効果 シミュレーション【会社員が得する掛金の決め方】", "keyword": "iDeCo 節税 シミュレーション 会社員", "emoji": "📉", "tag": "マネー最適化", "slug": "ideco-tax-simulation", "category": "money"},
    {"title": "電力会社 乗り換え 節約【年間2万円以上節約できる比較手順】", "keyword": "電力会社 乗り換え 節約 比較", "emoji": "⚡", "tag": "マネー最適化", "slug": "electricity-switch-savings", "category": "money"},
    {"title": "保険 見直し 不要な特約を整理【削れる保険料の見つけ方】", "keyword": "保険 見直し 不要 特約 節約", "emoji": "🛡️", "tag": "マネー最適化", "slug": "insurance-review-guide", "category": "money"},
    {"title": "ポイ活 効率的な貯め方【楽天・Tポイント・dポイント一元管理術】", "keyword": "ポイ活 ポイント 貯め方 効率", "emoji": "⭐", "tag": "マネー最適化", "slug": "point-activity-guide", "category": "money"},
    {"title": "年会費無料クレカ おすすめ5選【特典・還元率で選ぶ】", "keyword": "クレジットカード 年会費無料 おすすめ 還元率", "emoji": "💳", "tag": "マネー最適化", "slug": "no-fee-creditcard-top5", "category": "money"},
    {"title": "マネーフォワードME 使い方【家計を自動集計して節約する手順】", "keyword": "マネーフォワード 使い方 家計 節約", "emoji": "📊", "tag": "マネー最適化", "slug": "moneyforward-me-guide", "category": "money"},
    {"title": "家計簿アプリ 比較 2026【無料・有料のおすすめ6選】", "keyword": "家計簿 アプリ 比較 無料 おすすめ", "emoji": "📱", "tag": "マネー最適化", "slug": "kakeibo-app-compare", "category": "money"},
    {"title": "投資信託 初心者向け選び方【新NISAで買っていい銘柄の基準】", "keyword": "投資信託 初心者 選び方 NISA 銘柄", "emoji": "📈", "tag": "マネー最適化", "slug": "mutual-fund-beginner", "category": "money"},
    {"title": "ボーナス 運用 おすすめ【使い道で将来の資産が変わる分け方】", "keyword": "ボーナス 運用 おすすめ 資産形成", "emoji": "💰", "tag": "マネー最適化", "slug": "bonus-investment-guide", "category": "money"},
    {"title": "副業 確定申告 節税【20万円以下でも申告した方が得なケース】", "keyword": "副業 確定申告 節税 20万", "emoji": "📝", "tag": "マネー最適化", "slug": "side-job-tax-return", "category": "money"},
    {"title": "電子マネー 比較【Suica・PayPay・楽天Pay どれが一番得？】", "keyword": "電子マネー 比較 Suica PayPay 楽天Pay", "emoji": "📲", "tag": "マネー最適化", "slug": "e-money-compare", "category": "money"},
    {"title": "医療費控除 申請方法【確定申告で取り戻せる金額の計算手順】", "keyword": "医療費控除 申請 確定申告 計算", "emoji": "🏥", "tag": "マネー最適化", "slug": "medical-deduction-guide", "category": "money"},
]

# ── カテゴリ3: 賢い消費・ガジェット ─────────────────────────────────────
TOPICS_GADGET = [
    {"title": "ワイヤレスイヤホン おすすめ5選【2026年版 価格帯別】", "keyword": "ワイヤレスイヤホン おすすめ 2026", "emoji": "🎧", "tag": "賢い消費・ガジェット", "slug": "wireless-earphone-top5-2026", "category": "gadget"},
    {"title": "コードレス掃除機 人気モデル比較【一人暮らし〜ファミリー向け】", "keyword": "コードレス掃除機 比較 おすすめ", "emoji": "🧹", "tag": "賢い消費・ガジェット", "slug": "cordless-vacuum-compare-2026", "category": "gadget"},
    {"title": "在宅ワーク向けWebカメラ おすすめ5選【画質・価格で選ぶ】", "keyword": "Webカメラ テレワーク おすすめ", "emoji": "💻", "tag": "賢い消費・ガジェット", "slug": "web-camera-top5-2026", "category": "gadget"},
    {"title": "ロボット掃除機 おすすめ比較 2026【自動ゴミ収集付きも】", "keyword": "ロボット掃除機 おすすめ 2026", "emoji": "🤖", "tag": "賢い消費・ガジェット", "slug": "robot-vacuum-2026-v2", "category": "gadget"},
    {"title": "ノイズキャンセリングヘッドホン おすすめ5選【テレワーク・通勤向け】", "keyword": "ノイズキャンセリング ヘッドホン おすすめ", "emoji": "🎵", "tag": "賢い消費・ガジェット", "slug": "noise-canceling-headphone-2026", "category": "gadget"},
    {"title": "モバイルバッテリー おすすめ10選【容量・重さ・充電速度別】", "keyword": "モバイルバッテリー おすすめ 容量 比較", "emoji": "🔋", "tag": "賢い消費・ガジェット", "slug": "mobile-battery-top10-2026", "category": "gadget"},
    {"title": "スマートウォッチ おすすめ5選【Apple Watch以外も比較】", "keyword": "スマートウォッチ おすすめ 比較 2026", "emoji": "⌚", "tag": "賢い消費・ガジェット", "slug": "smartwatch-top5-2026", "category": "gadget"},
    {"title": "メカニカルキーボード おすすめ5選【在宅ワーク・静音モデルも】", "keyword": "メカニカルキーボード おすすめ 静音 テレワーク", "emoji": "⌨️", "tag": "賢い消費・ガジェット", "slug": "mechanical-keyboard-2026", "category": "gadget"},
    {"title": "4Kモニター おすすめ比較【27〜32インチ 在宅ワーク向け】", "keyword": "4Kモニター おすすめ 27インチ テレワーク", "emoji": "🖥️", "tag": "賢い消費・ガジェット", "slug": "4k-monitor-2026", "category": "gadget"},
    {"title": "QOL向上ガジェット おすすめ10選【生活の質を上げるアイテム】", "keyword": "QOL ガジェット おすすめ 生活 改善", "emoji": "✨", "tag": "賢い消費・ガジェット", "slug": "qol-gadget-top10", "category": "gadget"},
    {"title": "スマートホーム入門【おすすめデバイスと導入手順】", "keyword": "スマートホーム 入門 おすすめ デバイス", "emoji": "🏠", "tag": "賢い消費・ガジェット", "slug": "smarthome-beginner-guide", "category": "gadget"},
    {"title": "在宅ワーク 快適グッズ まとめ【デスク周り必需品15選】", "keyword": "在宅ワーク グッズ デスク おすすめ", "emoji": "🖥️", "tag": "賢い消費・ガジェット", "slug": "telework-goods-2026", "category": "gadget"},
    {"title": "空気清浄機 おすすめ比較【6畳〜20畳対応 花粉・PM2.5対策】", "keyword": "空気清浄機 おすすめ 比較 花粉", "emoji": "💨", "tag": "賢い消費・ガジェット", "slug": "air-purifier-2026", "category": "gadget"},
    {"title": "電動歯ブラシ おすすめ5選【コスパ重視・替えブラシ安いモデル】", "keyword": "電動歯ブラシ おすすめ コスパ", "emoji": "🦷", "tag": "賢い消費・ガジェット", "slug": "electric-toothbrush-2026", "category": "gadget"},
    {"title": "ポータブル電源 おすすめ比較【キャンプ・防災・停電対策】", "keyword": "ポータブル電源 おすすめ キャンプ 防災", "emoji": "⚡", "tag": "賢い消費・ガジェット", "slug": "portable-power-2026", "category": "gadget"},
    {"title": "Bluetoothスピーカー おすすめ5選【防水・コスパ重視モデル】", "keyword": "Bluetoothスピーカー おすすめ 防水 コスパ", "emoji": "📻", "tag": "賢い消費・ガジェット", "slug": "bluetooth-speaker-2026", "category": "gadget"},
    {"title": "電気ケトル おすすめ比較【温度調節付き・コーヒー・紅茶向け】", "keyword": "電気ケトル 温度調節 おすすめ コーヒー", "emoji": "☕", "tag": "賢い消費・ガジェット", "slug": "electric-kettle-2026", "category": "gadget"},
    {"title": "加湿器 おすすめ 2026【超音波・気化式・スチーム式 比較】", "keyword": "加湿器 おすすめ 比較 超音波 2026", "emoji": "💧", "tag": "賢い消費・ガジェット", "slug": "humidifier-2026", "category": "gadget"},
    {"title": "コスパ最強 家電 おすすめ10選【2026年 買って良かった】", "keyword": "コスパ 家電 おすすめ 買って良かった", "emoji": "🏆", "tag": "賢い消費・ガジェット", "slug": "cospa-kaden-top10-2026", "category": "gadget"},
    {"title": "スマートスピーカー 比較【Amazon Echo vs Google Nest 2026】", "keyword": "スマートスピーカー 比較 Echo Google Nest", "emoji": "🔊", "tag": "賢い消費・ガジェット", "slug": "smart-speaker-2026", "category": "gadget"},
]

ALL_TOPICS = TOPICS_AI + TOPICS_MONEY + TOPICS_GADGET
CATEGORIES = ["ai", "money", "gadget"]

ARTICLE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | マネー最適化ラボ</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title} | マネー最適化ラボ">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="マネー最適化ラボ">
  <meta property="og:url" content="https://manegori-lab.com/articles/{slug}.html">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title} | マネー最適化ラボ">
  <meta name="twitter:description" content="{description}">
  <link rel="canonical" href="https://manegori-lab.com/articles/{slug}.html">
  <link rel="stylesheet" href="/css/article.css">
</head>
<body>

<header id="header">
  <div class="header-inner">
    <div class="site-logo"><a href="/"><span class="accent-bar"></span>マネー最適化ラボ</a></div>
    <div class="site-tagline">事務・営業・企画職のためのAI活用メディア</div>
  </div>
</header>
<nav id="nav">
  <div class="nav-inner">
    <ul class="nav-menu">
      <li><a href="/">トップ</a></li>
      <li><a href="/category/ai.html">AI業務効率化</a></li>
      <li><a href="/articles/claude-vs-chatgpt-office.html">ツール比較</a></li>
      <li><a href="/about.html">運営者情報</a></li>
      <li><a href="/contact.html">お問い合わせ</a></li>
    </ul>
  </div>
</nav>

<div class="breadcrumb">
  <div class="breadcrumb-inner">
    <a href="/">ホーム</a> › <a href="/category/{category}.html">{tag}</a> › {title}
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
    ※ 当サイトはAmazonアソシエイト・プログラムおよびその他アフィリエイトプログラムの参加者です。リンク経由でご購入・お申込みいただくと紹介料が発生する場合があります（利用者の負担増なし）。記事内の情報は執筆時点のものです。最新情報は各公式サイトをご確認ください。
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
        <h3>カテゴリ</h3>
        <ul>
          <li><a href="/category/ai.html">AI業務効率化</a></li>
          <li><a href="/articles/claude-vs-chatgpt-office.html">ツール比較</a></li>
        </ul>
      </div>
      <div>
        <h3>人気記事</h3>
        <ul>
          <li><a href="/articles/nisa-securities-compare.html">NISA証券会社比較</a></li>
          <li><a href="/articles/perplexity-ai-usage.html">Perplexity AI 活用術</a></li>
        </ul>
      </div>
    </div>
    <p class="copy">© 2026 マネー最適化ラボ　|　当サイトはAmazonアソシエイト・プログラム参加者です。</p>
  </div>
</footer>

</body>
</html>
"""

PROMPTS = {
    "ai": """
あなたはAI・業務効率化専門のブログライターです。
事務・営業・企画職のビジネスパーソンに向けて、実践的なAI活用記事を書いてください。

テーマ：{title}
キーワード：{keyword}

【記事の構成】
1. リード文（200文字程度）：読者の悩み（時間がかかる・手作業が多い）に共感し、このAIツールで解決できることを伝える
2. このツール/サービスの特徴・選ぶ理由（H2見出しで2〜3項目）
3. 具体的な使い方・活用シーン（H2見出しで2〜3項目）：事務・営業・企画職向けの実践例を入れる
4. 料金・プランの比較（H2見出し）：無料プランと有料プランの違いを明確に
5. まとめ（100文字程度）：一言でどんな人に向くか

【ルール】
- 専門用語は平易な言葉で補足する
- 「エンジニア以外でも使える」視点を必ず入れる
- 各セクションの後にサービスリンクのプレースホルダー「{{ASP_LINK_商品番号}}」を入れる
- HTMLのh2/h3/p/ul/liタグで構造化する
- 断定表現（〜必ず〜/〜絶対に〜）は避け「〜できます」「〜が期待できます」などの表現を使う
- 文字数は合計1500〜2000文字程度
""",
    "money": """
あなたはお金・節約・資産形成専門のブログライターです。
本業を持ちながら賢くお金を管理したいビジネスパーソンに向けて、実践的な記事を書いてください。

テーマ：{title}
キーワード：{keyword}

【記事の構成】
1. リード文（200文字程度）：読者の悩み（お金が貯まらない・手続きが面倒）に共感し、この記事で得られる具体的な成果を伝える
2. 基本的な仕組み・メリットの解説（H2見出しで2〜3項目）
3. 具体的な手順・選び方（H2見出しで2〜3項目）：ステップ形式や比較表を活用
4. 注意点・デメリット（H2見出し）：公平な情報提供のため必ず記載
5. まとめ（100文字程度）：どんな人に向くか

【ルール】
- 「投資は元本保証ではありません」などの免責表現を金融情報に付ける
- 「〜すべき」などの断定は避け「〜がおすすめです」「〜を検討してみてください」を使う
- 各セクションの後にサービスリンクのプレースホルダー「{{ASP_LINK_商品番号}}」を入れる
- HTMLのh2/h3/p/ul/liタグで構造化する
- 具体的な数字（節約額・還元率・利回り）は「〜程度」「〜例」と幅を持たせる
- 文字数は合計1500〜2000文字程度
""",
    "gadget": """
あなたは家電・ガジェット専門のブログライターです。
コスパを重視してQOLを上げたいビジネスパーソンに向けて、購買判断に役立つ記事を書いてください。

テーマ：{title}
キーワード：{keyword}

【記事の構成】
1. リード文（200文字程度）：読者の悩みや購入前の不安に共感し、この記事で解決できることを伝える
2. 選び方のポイント（H2見出しで3項目）：購入前に確認すべき基準を具体的に
3. おすすめ商品TOP3〜5（H3見出しで各商品）：特徴・向いている人・価格帯を記載
4. まとめ（100文字程度）：タイプ別のおすすめを一言で
【ルール】
- 具体的な商品名は「〇〇（Amazonで確認）」という形式で書く
- 各商品の後にAmazonリンクのプレースホルダー「{{AMAZON_LINK_商品番号}}」を入れる
- HTMLのh2/h3/p/ul/liタグで構造化する
- 価格は「〜円前後」「〜円台」と幅を持たせる
- 文字数は合計1500〜2000文字程度
""",
}


def generate_article_body(client: anthropic.Anthropic, topic: dict) -> str:
    """Claude APIを使って記事本文を生成する（カテゴリ別プロンプト）"""
    import re
    category = topic.get("category", "gadget")
    prompt_template = PROMPTS.get(category, PROMPTS["gadget"])
    prompt = prompt_template.format(title=topic["title"], keyword=topic["keyword"])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    body = message.content[0].text

    # Markdownコードフェンスを除去（```html ... ``` や ``` ... ```）
    body = re.sub(r'```(?:html)?\n?', '', body)
    body = re.sub(r'\n?```', '', body)

    tracking = TRACKING_ID if TRACKING_ID else "sei722406-22"

    if category == "gadget":
        def replace_amazon_link(match):
            return (
                f'<a class="btn-amazon" href="https://www.amazon.co.jp/s?k='
                f'{topic["keyword"].replace(" ", "+")}&tag={tracking}" '
                f'target="_blank" rel="nofollow noopener">🛒 Amazonで価格を確認する</a>'
            )
        body = re.sub(r'\{AMAZON_LINK_(\w+)\}', replace_amazon_link, body)
    else:
        # AI・マネーカテゴリ: ASPリンクプレースホルダーをテキストリンクに変換
        # ※ ASP登録後に affiliate_links.json の URL を設定してください
        def replace_asp_link(match):
            num = match.group(1)
            link_url = get_asp_link(topic["slug"], num)
            return (
                f'<a class="btn-amazon" href="{link_url}" '
                f'target="_blank" rel="nofollow noopener">🔗 詳細・公式サイトを確認する</a>'
            )
        body = re.sub(r'\{ASP_LINK_(\w+)\}', replace_asp_link, body)

    return body


def get_asp_link(slug: str, num: str) -> str:
    """affiliate_links.json から ASP リンクを取得する（未設定時は公式TOPへ）"""
    links_file = Path("affiliate_links.json")
    if links_file.exists():
        try:
            links = json.loads(links_file.read_text(encoding="utf-8"))
            return links.get(slug, {}).get(num, "https://manegori-lab.com/")
        except json.JSONDecodeError:
            pass
    return "https://manegori-lab.com/"


def get_next_topic(specified_category: str = None) -> tuple:
    """カテゴリをラウンドロビンで選択し、未生成テーマと新しい状態を返す"""
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    generated = set()
    articles_dir = Path("articles")
    if articles_dir.exists():
        generated = {f.stem for f in articles_dir.glob("*.html")}

    if specified_category and specified_category in CATEGORIES:
        category = specified_category
    else:
        last_index = state.get("last_category_index", -1)
        category = CATEGORIES[(last_index + 1) % len(CATEGORIES)]

    category_map = {"ai": TOPICS_AI, "money": TOPICS_MONEY, "gadget": TOPICS_GADGET}
    topics = category_map[category]
    remaining = [t for t in topics if t["slug"] not in generated]
    if not remaining:
        remaining = topics  # 全テーマ消化後はリセット

    topic = random.choice(remaining)
    new_state = {**state, "last_category_index": CATEGORIES.index(category)}

    # 状態保存は記事生成成功後に main() から行う
    return topic, new_state


def save_generation_state(state: dict):
    """記事生成成功後に状態ファイルを更新する"""
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def save_article(topic: dict, body: str) -> Path:
    """記事HTMLファイルを保存する"""
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)

    description = f"{topic['keyword']}について詳しく解説。{topic['title'].split('【')[0].strip()}の選び方・比較・おすすめ情報をまとめました。"

    html = ARTICLE_HTML_TEMPLATE.format(
        title=topic["title"],
        description=description,
        tag=topic["tag"],
        category=topic.get("category", "gadget"),
        emoji=topic["emoji"],
        slug=topic["slug"],
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
    description = f"{topic['keyword']}について詳しく解説。失敗しない選び方をわかりやすくまとめました。"

    new_card = f"""
    <div class="article-card">
      <div class="thumb">{topic['emoji']}</div>
      <div class="content">
        <span class="tag">{topic['tag']}</span>
        <h3><a href="articles/{topic['slug']}.html">{topic['title']}</a></h3>
        <p>{description}</p>
        <a class="read-more" href="articles/{topic['slug']}.html">続きを読む →</a>
      </div>
    </div>
"""

    if '<div class="article-grid" id="article-list">' in content:
        content = content.replace(
            '<div class="article-grid" id="article-list">',
            f'<div class="article-grid" id="article-list">{new_card}'
        )
        index_path.write_text(content, encoding="utf-8")
        print(f"✅ index.htmlを更新しました")
    else:
        print("⚠️  index.html に article-grid が見つかりませんでした")


def main():
    parser = argparse.ArgumentParser(description="マネー最適化ラボ 記事自動生成")
    parser.add_argument("--category", choices=CATEGORIES, help="生成するカテゴリを指定 (ai/money/gadget)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("環境変数 ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    print("📝 記事テーマを選定中...")
    topic, new_state = get_next_topic(args.category)
    print(f"📌 テーマ: [{topic['category']}] {topic['title']}")

    print("✍️  Claude APIで記事を生成中...")
    body = generate_article_body(client, topic)

    save_article(topic, body)
    update_index(topic)
    save_generation_state(new_state)  # 成功後にのみ状態を保存

    print("🎉 完了しました！")


if __name__ == "__main__":
    main()
