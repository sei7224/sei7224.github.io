#!/usr/bin/env python3
"""
AI×シゴト | マネゴリラボ 下書き自動生成スクリプト

- 公開はせず `drafts/` フォルダに HTML を出力する（人間が編集してから articles/ へ移動して公開）
- 量より質：Helpful Content Update を踏まえた人力編集前提の運用
- AI業務効率化 1軸特化（事務・営業・企画職向け）

使い方:
    python generate_article.py
    python generate_article.py --slug claude-vs-chatgpt-office   # 特定テーマを指定
"""

import anthropic
import os
import json
import random
import argparse
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(".generation_state.json")
DRAFTS_DIR = Path("drafts")

# ── AI業務効率化テーマ（事務・営業・企画職向け）───────────────────────
# 1軸特化戦略：マネー（YMYL）とガジェットは廃止
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

ALL_TOPICS = TOPICS_AI

ARTICLE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- DRAFT: 公開前に人間レビュー・追記が必要です -->
  <meta name="robots" content="noindex,nofollow">
  <title>{title} | AI×シゴト | マネゴリラボ</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title} | AI×シゴト | マネゴリラボ">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="AI×シゴト | マネゴリラボ">
  <meta property="og:url" content="https://manegori-lab.com/articles/{slug}.html">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title} | AI×シゴト | マネゴリラボ">
  <meta name="twitter:description" content="{description}">
  <link rel="canonical" href="https://manegori-lab.com/articles/{slug}.html">
  <link rel="stylesheet" href="/css/article.css">
  <style>
    /* プロンプトボックス（コピペ用プロンプト表示） */
    .prompt-box {{ background: #f5f7fa; border-left: 4px solid #2563eb; padding: 14px 18px; margin: 14px 0; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13.5px; line-height: 1.8; white-space: pre-wrap; border-radius: 4px; color: #0f172a; }}
    .prompt-label {{ display: inline-block; background: #2563eb; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 3px; margin-bottom: 8px; font-family: -apple-system, sans-serif; letter-spacing: 1px; }}
    .compare-table th {{ background: #eef2ff; }}
    .compare-table td.product-col {{ font-weight: 600; }}
    .toc-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px 24px; margin: 24px 0; border-radius: 6px; }}
    .toc-box h3 {{ font-size: 15px; margin-bottom: 10px; color: #0f172a; }}
    .toc-box ol {{ padding-left: 22px; font-size: 13.5px; color: #334155; line-height: 1.9; }}
    .toc-box a {{ color: #2563eb; text-decoration: none; }}
    .warning-box {{ background: #fffbeb; border-left: 4px solid #d97706; padding: 14px 18px; margin: 14px 0; font-size: 14px; line-height: 1.9; border-radius: 4px; }}
    /* ヒーローイラスト枠 */
    .article-hero-visual {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #005F6B 100%); color: #fff; padding: 36px 28px; border-radius: 12px; margin: 18px 0 32px; display: grid; grid-template-columns: minmax(0, 1fr) 180px; gap: 24px; align-items: center; box-shadow: 0 16px 40px rgba(15,23,42,0.18); position: relative; overflow: hidden; }}
    .article-hero-visual::before {{ content: ""; position: absolute; top: -60%; right: -20%; width: 320px; height: 320px; background: radial-gradient(circle, rgba(96,165,250,0.25), transparent 65%); border-radius: 50%; pointer-events: none; }}
    .article-hero-visual .hero-text {{ position: relative; z-index: 1; }}
    .article-hero-visual .hero-badge {{ display: inline-block; font-size: 11px; letter-spacing: 2px; background: rgba(255,255,255,0.12); padding: 4px 10px; border-radius: 3px; margin-bottom: 12px; font-weight: bold; color: #bfdbfe; }}
    .article-hero-visual h2 {{ font-size: 24px; line-height: 1.45; color: #fff; margin: 0 0 8px; font-weight: 900; }}
    .article-hero-visual p {{ font-size: 14px; color: #dbeafe; line-height: 1.85; margin: 0; }}
    .article-hero-visual .hero-icon {{ font-size: 72px; line-height: 1; text-align: center; position: relative; z-index: 1; }}
    /* Mermaid図解 */
    .mermaid-wrapper {{ background: #fafbfc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px 18px; margin: 18px 0 28px; overflow-x: auto; }}
    .mermaid-wrapper .diagram-caption {{ font-size: 12px; color: #64748b; margin-top: 12px; text-align: center; letter-spacing: 0.5px; }}
    .mermaid {{ display: flex; justify-content: center; }}
    /* Chart.js グラフコンテナ */
    .chart-container {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 18px 0 28px; box-shadow: 0 4px 12px rgba(15,23,42,0.04); }}
    .chart-container .chart-title {{ font-size: 14px; font-weight: bold; color: #0f172a; margin-bottom: 14px; text-align: center; letter-spacing: 0.3px; }}
    .chart-container canvas {{ max-height: 360px; }}
    @media (max-width: 640px) {{
      .article-hero-visual {{ grid-template-columns: 1fr; text-align: center; padding: 28px 20px; }}
      .article-hero-visual .hero-icon {{ font-size: 60px; }}
    }}
  </style>
  <!-- Mermaid (図解描画) -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true, theme: 'default', themeVariables: {{ primaryColor: '#dbeafe', primaryTextColor: '#0f172a', primaryBorderColor: '#3B82F6', lineColor: '#64748b', fontFamily: '"Hiragino Kaku Gothic ProN", sans-serif', fontSize: '13px' }}}});</script>
  <!-- Chart.js (グラフ描画) -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-JV6VQD3TZE"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-JV6VQD3TZE');
  </script>
</head>
<body>

<header id="header">
  <div class="header-inner">
    <div class="site-logo"><a href="/"><span class="accent-bar"></span><span class="logo-main">AI×シゴト</span><span class="logo-sep">|</span><span class="logo-sub">マネゴリラボ</span></a></div>
    <div class="site-tagline">事務・営業・企画職のためのAI仕事術メディア</div>
  </div>
</header>
<nav id="nav">
  <div class="nav-inner">
    <ul class="nav-menu">
      <li><a href="/">トップ</a></li>
      <li><a href="/category/ai.html">AI業務効率化</a></li>
      <li><a href="/about.html">運営者情報</a></li>
      <li><a href="/contact.html">お問い合わせ</a></li>
    </ul>
  </div>
</nav>

<div class="breadcrumb">
  <div class="breadcrumb-inner">
    <a href="/">ホーム</a> › <a href="/category/ai.html">{tag}</a> › {title}
  </div>
</div>

<div class="article-header">
  <div class="article-header-inner">
    <span class="tag">{tag}</span>
    <h1>{emoji} {title}</h1>
    <div class="article-meta">
      <span>📅 更新：{date}</span>
      <span>⏱ 読了：約7分</span>
      <span>✍️ 著者：現役事務職ライター</span>
    </div>
  </div>
</div>

<div class="container">
  <div class="notice">
    ※ 当サイトはAmazonアソシエイト・プログラムおよびその他アフィリエイトプログラムの参加者です。リンク経由でご購入・お申込みいただくと紹介料が発生する場合があります（利用者の負担増なし）。本記事は公開時に著者が実機で検証した内容を含みます。
  </div>

  <div class="prose">
    {body}
  </div>

  <!-- TODO: 公開前に「実体験セクション」「スクショ」「失敗談」を必ず追記 -->

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
        </ul>
      </div>
    </div>
    <p class="copy">© 2026 AI×シゴト | マネゴリラボ　|　当サイトはAmazonアソシエイト・プログラム参加者です。</p>
  </div>
</footer>

</body>
</html>
"""

AI_PROMPT = """
あなたは「事務・営業・企画職向けAI業務効率化メディア『AI×シゴト | マネゴリラボ』」の編集長レベルライターです。
読者はAIに明るくない一般職のビジネスパーソンで、Excelやメール作成・議事録など日々の作業に追われています。
1000万PVを達成した編集プロデューサーの基準で、深く・具体的に・実用的に書いてください。

テーマ：{title}
メインキーワード：{keyword}

【絶対要件 — 守らないと差し戻し】
1. 文字数：本文 12,000〜18,000 文字（5,000字程度の薄い記事は2026年Google Helpful Content Updateで殺されます。深さで勝負）。HTMLタグや図解の数値部分は文字数にカウントしない
2. 必須構成（順番通り全て含めること）：
   a) **ヒーローイラスト枠**（記事冒頭・本文より前）：以下の <section> ブロックを必ず最初に配置
      <section class="article-hero-visual">
        <div class="hero-text">
          <span class="hero-badge">[ツール名や記事タイプを大文字英語で。例: CHATGPT / 2026 EDITION]</span>
          <h2>[インパクトある2行のキャッチコピー。<br/>で改行]</h2>
          <p>[サブテキスト。記事で得られる成果を80字程度]</p>
        </div>
        <div class="hero-icon" aria-hidden="true">[テーマに合う絵文字1〜2個。例: 🤖 / 📝 / 🔍]</div>
      </section>
   b) リード文（400字）：具体的な業務シーン1つを描写、AIで何分→何分に短縮できるかを数値で示す
   c) **Mermaid図解①**（リード文直後・必須）：以下のテンプレで「従来 vs AI導入後」のフロー比較
      <div class="mermaid-wrapper">
        <div class="mermaid">
flowchart TB
    subgraph BEFORE["❌ 導入前（時間がかかる）"]
        direction LR
        A1[ステップ1] --> A2[ステップ2] --> A3[ステップ3] --> A4[時間消費]
    end
    subgraph AFTER["✅ 導入後（時短）"]
        direction LR
        B1[ステップ1] --> B2[ステップ2] --> B3[ステップ3] --> B4[時短完了]
    end
    BEFORE -.乗り換え.-> AFTER
    style BEFORE fill:#fef2f2,stroke:#dc2626
    style AFTER fill:#f0fdf4,stroke:#16a34a
        </div>
        <div class="diagram-caption">📊 図1：従来 vs ツール導入後のワークフロー比較</div>
      </div>
   d) H2「目次」：<ol> で各H2へのアンカーリンク
   e) H2「○○とは？事務職目線で3行要約」（id="about"）：3段落、合計600字
   f) H2「2026年5月時点のプラン徹底解説」（id="plans"）：800字＋価格比較表（Free/個人有料/法人プラン全て解説、円換算目安付き）
   g) H2「事務職の業務で○○が活躍する10シーン＋実プロンプト」（id="scenes"）：H3で10シーン、各シーン本文400字＋実プロンプト1つ（<pre><code>で）。合計約5,000字
   h) H2「効果測定：3ヶ月で何時間短縮できるか」（id="roi"）：比較表（業務×従来時間×短縮後×月間削減）＋800字解説
   i) **Chart.js棒グラフ**（効果測定表の直後・必須）：以下のテンプレで業務別の月間時間を可視化
      <div class="chart-container">
        <div class="chart-title">📊 図2：業務別の月間時間（分） — 従来 vs ツール導入後</div>
        <canvas id="roiChart" role="img" aria-label="業務別時間削減グラフ"></canvas>
      </div>
      <script>
        (function() {{
          if (typeof Chart === 'undefined') return;
          var ctx = document.getElementById('roiChart');
          if (!ctx) return;
          new Chart(ctx, {{
            type: 'bar',
            data: {{
              labels: ['業務1','業務2','業務3','業務4','業務5','業務6','業務7'],
              datasets: [
                {{ label: '従来の月間時間（分）', data: [/*7つの数値*/], backgroundColor: 'rgba(220, 38, 38, 0.65)', borderColor: '#dc2626', borderWidth: 1 }},
                {{ label: '導入後（分）', data: [/*7つの数値*/], backgroundColor: 'rgba(22, 163, 74, 0.65)', borderColor: '#16a34a', borderWidth: 1 }}
              ]
            }},
            options: {{
              responsive: true, maintainAspectRatio: false,
              plugins: {{ legend: {{ position: 'top', labels: {{ font: {{ size: 12 }} }} }} }},
              scales: {{ x: {{ ticks: {{ font: {{ size: 11 }} }} }}, y: {{ beginAtZero: true, title: {{ display: true, text: '月間時間（分）' }}, ticks: {{ font: {{ size: 11 }} }} }} }}
            }}
          }});
        }})();
      </script>
      ※ labels と data の中身は「効果測定」表のデータと完全に一致させる
   j) H2「他AIツールとの比較表」（id="compare"）：最低5ツール×7項目のHTML <table>＋500字解説
   k) **Mermaid図解②**（導入7ステップ見出しの直後・必須）：以下のテンプレで7ステップを横並びフロー化
      <div class="mermaid-wrapper">
        <div class="mermaid">
flowchart LR
    S1([🌐 STEP1<br/>内容]) --> S2([📧 STEP2<br/>内容])
    S2 --> S3([STEP3])
    S3 --> S4([STEP4])
    S4 --> S5([STEP5])
    S5 --> S6([STEP6])
    S6 --> S7([STEP7])
    style S1 fill:#dbeafe,stroke:#3B82F6
    style S2 fill:#dbeafe,stroke:#3B82F6
    style S3 fill:#dbeafe,stroke:#3B82F6
    style S4 fill:#fef3c7,stroke:#f59e0b
    style S5 fill:#fef3c7,stroke:#f59e0b
    style S6 fill:#fef3c7,stroke:#f59e0b
    style S7 fill:#d1fae5,stroke:#16a34a
        </div>
        <div class="diagram-caption">📊 図3：導入7ステップの流れ</div>
      </div>
   l) H2「導入7ステップ【スクショ前提】」（id="steps"）：各ステップ200字＋「ここがつまずきポイント」を1行（合計1,500字）
   m) H2「本音メリット・デメリット」（id="pros-cons"）：メリット4つ＋デメリット4つ、各H3で200字
   n) H2「事務職がやりがちな失敗例5つ」（id="fails"）：各H3で200字、合計1,000字
   o) H2「セキュリティ・情報管理の徹底ルール」（id="security"）：7ルール箇条書き＋万一の対応フロー（合計700字）
   p) H2「事務職タイプ別おすすめ活用パターン」（id="types"）：受付/経理/人事/営業事務/企画の5タイプ、各200字
   q) H2「まとめ」（id="summary"）：400字、判断軸を明示し、内部リンクを以下から3つ以上挿入：
      /articles/chatgpt-jimu-complete-guide.html / /articles/claude-vs-chatgpt-office.html / /articles/perplexity-ai-usage.html / /articles/notion-ai-jimu-complete-guide.html / /compare/jimu-ai-tools.html / /tools/ai-tool-finder.html

3. ASPリンク {{ASP_LINK_1}}〜{{ASP_LINK_3}} を3箇所配置（料金プラン直後・実プロンプト中盤・導入7ステップ直後）

4. HTML構造：h2/h3/p/ul/ol/li/table/thead/tbody/tr/th/td/strong/em/a/code/pre/div/span/section/canvas/script のみ使用
   表は <table class="compare-table"> を使用
   ※ div/span/section/canvas/scriptは「ヒーロー枠」「Mermaid図」「Chart.jsグラフ」のためにのみ使用、本文の段落分割では使わない

5. E-E-A-T配慮（必須）：
   - 「2026年5月時点で著者が業務利用」「3ヶ月運用した結果」など時期と状況を入れる
   - 数値は具体的に（「月10時間→月3時間」「20分→5分」など）
   - 「公式情報は変動」「最終確認日：2026年5月17日」を明記
   - 断定（必ず/絶対/100%）は禁止 → 「〜できます」「〜が期待できます」
   - YMYL警告：税務/法務/医療系の話題は「専門家確認前提」を必ず付ける

6. NGワード：「革命的」「神ツール」「完全攻略」「100%」「全員に」「誰でも稼げる」など誇大表現は全面禁止

7. 比較表は2026年5月時点で実在する以下ツール名・実価格を使用：
   - ChatGPT Plus（GPT-5.5）$20 / ChatGPT Pro（GPT-5.5 Pro）$100 ※GPT-5.5は2026年4月23日に全有料プランへ展開済み
   - Claude Pro（Sonnet 4.6）$20 / Claude Max（Opus 4.7）$100
   - Gemini Advanced（Gemini 3.1 Pro）約2,900円
   - Microsoft Copilot Pro 約3,200円 / M365 Copilot Business $18/seat（年払）
   - Notion AI / Perplexity Pro $20 / NotebookLM

8. 実プロンプトの書き方（各シーン末尾に <pre><code>で配置）：
   - 役割設定（あなたは○○の専門家です）
   - 入力データのフォーマット
   - 出力構成（番号付きで具体的）
   - 条件・制約（文字数・トーン・NG項目）

【出力形式】
- 上記HTMLのみ。前置きの説明文や ```html フェンスは絶対に出力しない
- 「以下が記事です」「お役に立てれば幸いです」等のメタ発言禁止

それでは、上記要件をすべて満たす12,000〜18,000字の高品質記事を書いてください。
"""


def generate_article_body(client: anthropic.Anthropic, topic: dict) -> str:
    """Claude APIで AI業務効率化カテゴリ向けの下書き本文を生成"""
    import re

    prompt = AI_PROMPT.format(title=topic["title"], keyword=topic["keyword"])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=32000,  # 12,000〜18,000字を確保するため大幅に余裕を持たせる（日本語1字 ≒ 1〜2トークン）
        messages=[{"role": "user", "content": prompt}]
    )

    body = message.content[0].text

    # Markdownコードフェンスを除去
    body = re.sub(r'```(?:html)?\n?', '', body)
    body = re.sub(r'\n?```', '', body)

    # ASPリンクプレースホルダーの処理
    # ASP未契約時はリンクを「公式サイト未掲載：編集者が手動で追記」のコメントに置換し、ダミーURL流出を防ぐ
    def replace_asp_link(match):
        num = match.group(1)
        link_url = get_asp_link(topic["slug"], num)
        if not link_url:
            return (
                f'<!-- TODO: ASP_LINK_{num} を手動で挿入してください（affiliate_links.json） -->'
            )
        return (
            f'<a class="btn-amazon" href="{link_url}" '
            f'target="_blank" rel="nofollow noopener sponsored">🔗 公式サイトで詳細を確認する</a>'
        )
    body = re.sub(r'\{ASP_LINK_(\w+)\}', replace_asp_link, body)

    return body


def get_asp_link(slug: str, num: str):
    """affiliate_links.json から実URLを返す。未設定なら None（ダミーURLは絶対に返さない）"""
    links_file = Path("affiliate_links.json")
    if not links_file.exists():
        return None
    try:
        links = json.loads(links_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    entry = links.get(slug, {})
    url = entry.get(num)
    if not url or "XXXX" in url or "YYYY" in url:
        # プレースホルダーやダミーURLは公開しない
        return None
    return url


def get_next_topic() -> tuple:
    """未生成テーマからランダムに1件選び、新しい状態を返す（AI 1軸のみ）"""
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    generated_slugs = set(state.get("generated_slugs", []))
    # articles/ と drafts/ の両方を既生成として扱う
    for d in (Path("articles"), DRAFTS_DIR):
        if d.exists():
            generated_slugs |= {f.stem for f in d.glob("*.html")}

    remaining = [t for t in TOPICS_AI if t["slug"] not in generated_slugs]
    if not remaining:
        remaining = TOPICS_AI  # 全消化後はリセット

    topic = random.choice(remaining)
    new_state = {
        **state,
        "generated_slugs": sorted(generated_slugs | {topic["slug"]}),
        "last_generated_at": datetime.now().isoformat(),
    }
    return topic, new_state


def save_generation_state(state: dict):
    """生成成功後に状態ファイルを更新"""
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def save_draft(topic: dict, body: str) -> Path:
    """下書きHTMLを drafts/ に保存する（articles/ には書き込まない）"""
    DRAFTS_DIR.mkdir(exist_ok=True)

    description = (
        f"{topic['keyword']}を事務・営業・企画職目線で実践解説。"
        f"使い方・料金・比較・失敗例まで網羅した実務向けガイド。"
    )

    html = ARTICLE_HTML_TEMPLATE.format(
        title=topic["title"],
        description=description,
        tag=topic["tag"],
        emoji=topic["emoji"],
        slug=topic["slug"],
        date=datetime.now().strftime("%Y年%m月%d日"),
        body=body,
    )

    output_path = DRAFTS_DIR / f"{topic['slug']}.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"📄 下書きを保存しました: {output_path}")
    print(f"   公開手順: drafts/{topic['slug']}.html を編集し articles/ へ移動")
    return output_path


def find_topic_by_slug(slug: str) -> dict:
    for t in TOPICS_AI:
        if t["slug"] == slug:
            return t
    raise ValueError(f"スラッグ '{slug}' に該当するテーマが TOPICS_AI に見つかりません")


def main():
    parser = argparse.ArgumentParser(description="AI×シゴト | マネゴリラボ 下書き自動生成")
    parser.add_argument("--slug", help="生成するテーマのslugを指定（省略時は未生成テーマからランダム）")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("環境変数 ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    print("📝 テーマを選定中...")
    if args.slug:
        topic = find_topic_by_slug(args.slug)
        new_state = None
    else:
        topic, new_state = get_next_topic()
    print(f"📌 テーマ: {topic['title']}")

    print("✍️  Claude APIで下書きを生成中...（約30〜60秒）")
    body = generate_article_body(client, topic)

    save_draft(topic, body)
    if new_state:
        save_generation_state(new_state)

    print("🎉 完了しました（公開前に必ず人間レビュー＆実体験追記を行ってください）")


if __name__ == "__main__":
    main()
