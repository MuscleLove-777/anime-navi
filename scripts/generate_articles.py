"""
商品データからHugo用のMarkdown記事を自動生成するモジュール
アニメ特化版（アニメエロナビ）
テンプレートのバリエーションを用意し、重複コンテンツを回避する
"""

import os
import re
import random
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from config import Config, GENRES


# ============================================================
# 記事テンプレート群（バリエーションで重複コンテンツを回避）
# ============================================================

ARTICLE_TEMPLATES = [
    # テンプレートA: ストレート紹介型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## {{ hook_title }}

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### 作品情報

| 項目 | 内容 |
|------|------|
{% if price %}| 価格 | {{ price }} |
{% endif %}{% if maker %}| サークル/メーカー | {{ maker }} |
{% endif %}{% if author %}| 著者 | {{ author }} |
{% endif %}{% if series %}| シリーズ | {{ series }} |
{% endif %}{% if actresses %}| 声優/出演 | {{ actresses }} |
{% endif %}

{{ body_text }}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ eronavi_link }}

{{ related_section }}
"""),

    # テンプレートB: レビュー風型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

## この作品の見どころ

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

{{ body_text }}

{% if maker %}
> **{{ maker }}**からリリースされたこの作品は、{{ category_name }}ファンなら見逃せない一本です。
{% endif %}

{% if author %}
> 著者：**{{ author }}** による{{ category_name }}作品。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ eronavi_link }}

{{ related_section }}
"""),

    # テンプレートC: ピックアップ型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## 本日の{{ category_name }}ピックアップ

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### この作品をおすすめする理由

{{ body_text }}

{% if price %}
**価格: {{ price }}** --- コスパも申し分なし！
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ eronavi_link }}

{{ related_section }}
"""),

    # テンプレートD: Q&A型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["{{ category }}"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### Q. どんな作品？

{{ body_text }}

### Q. 価格は？

{% if price %}{{ price }}で楽しめます。{% else %}詳細はリンク先でご確認ください。{% endif %}

{% if maker %}
### Q. どこのサークル/メーカー？

{{ maker }}の作品です。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ eronavi_link }}

{{ related_section }}
"""),
]


# ============================================================
# ジャンル別テキストバリエーション（アニメ特化）
# ============================================================

INTRO_VARIATIONS = [
    "これは見逃せない...！**「{title}」**は{genre_text}好きにはたまらない作品です。",
    "{genre_text}好きにはたまらない...！**「{title}」**、絶対ハマる作品が来ました。",
    "{genre_text}で興奮したいならコレ！**「{title}」**がマジでおすすめ。",
    "話題沸騰中の**「{title}」**をピックアップ。{genre_text}のド直球作品です。",
    "**「{title}」**が気になってる人、正解です。{genre_text}ジャンルの中でもガチで抜ける作品。",
    "本日の厳選{category_name}は**「{title}」**。「神作品」と話題に。",
    "新着から見つけた掘り出し物！**「{title}」**、{genre_text}がたっぷり詰まった作品です。",
    "サンプルだけでも興奮必至！**「{title}」**は{genre_text}の最高傑作かも。",
    "今週一番シコれる{category_name}作品はコレ。**「{title}」**、見逃すな！",
    "MuscleLoveが厳選！**「{title}」**は{genre_text}好きなら見逃せない作品です。",
    "MuscleLove編集部おすすめの**「{title}」**。{genre_text}ジャンルで今一番アツい作品。",
    "MuscleLoveイチオシ！**「{title}」**、{genre_text}好きを唸らせる最高の作品が来ました。",
    "二次元アダルトの新定番！**「{title}」**は{genre_text}ファン必見です。",
    "FANZAで大人気の**「{title}」**。{genre_text}ジャンルで高評価連発中！",
]

BODY_VARIATIONS = [
    "作画クオリティが高く、キャラデザも魅力的。エロシーンの演出も素晴らしく、抜きどころ満載の作品です。",
    "序盤からテンション高めの展開で、一気に引き込まれます。興奮が止まらない濃厚なシーンは、何度もリピートしたくなるクオリティ。",
    "とにかくシチュエーションが最高。エロさが際立つ演出で、見応え抜群。サンプルでその片鱗を確認してみてください。",
    "完成度が高く、ジャンルの魅力が全開。展開のバリエーションも豊富で飽きることなく最後まで楽しめます。リピート確定レベル。",
    "イラスト・作画のクオリティが高く、表情やシチュエーションの描写がしっかりしています。コレクションとしても満足度の高い一本。",
    "このジャンルが好きなら間違いなく刺さる作品。演出・構図・興奮度、すべてが高水準でまとまっています。",
    "抜けるかどうかで言えば、間違いなく抜ける。ドキドキ感と、ここぞという場面のねっとり感のバランスが絶妙です。",
    "声優の演技が最高で、没入感がハンパない。エロシーンとストーリーのバランスも良く、何度でも楽しめる作品。",
    "ドット絵やCGの美しさに目を奪われます。細部までこだわった描写は、クリエイターの本気を感じさせます。",
]

HOOK_TITLES = [
    "今夜のオカズはコレで決まり",
    "必見の抜けるおすすめ作品",
    "見逃し厳禁！興奮度MAXの注目作",
    "本日のシコネタはこちら",
    "ガチで抜ける厳選ピックアップ",
    "サンプルを今すぐチェック",
    "興奮度MAXの注目作品",
    "話題の二次元エロ作品を紹介",
    "MuscleLoveのイチオシ作品",
    "MuscleLove厳選！今日のおすすめ",
    "MuscleLoveが選ぶ注目作品",
    "二次元アダルトの新定番",
]


def generate_articles(
    products: list[dict],
    output_dir: str = "",
    genre: str = "",
) -> list[str]:
    """
    商品データからHugo用Markdown記事を生成する
    """
    if not output_dir:
        output_dir = Config.CONTENT_DIR

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generated_files = []

    for i, product in enumerate(products):
        try:
            filepath = _generate_single_article(product, output_dir, i, genre)
            if filepath:
                generated_files.append(filepath)
                print(f"[生成] {Path(filepath).name}")
        except Exception as e:
            print(f"[エラー] 記事生成に失敗: {product.get('title', '不明')} - {e}")

    print(f"\n[完了] {len(generated_files)}件の記事を生成しました → {output_dir}")
    return generated_files


def _generate_single_article(
    product: dict,
    output_dir: str,
    index: int,
    genre: str = "",
) -> str:
    """1商品分の記事を生成する"""
    title = product.get("title", "タイトル不明")
    image_url = product.get("image_url", "")
    affiliate_url = product.get("affiliate_url", "")
    price = product.get("price", "")
    genres = product.get("genres", [])
    actresses = ", ".join(product.get("actresses", []))
    maker = product.get("maker", "")
    author = product.get("author", "")
    series = product.get("series", "")
    sample_images = product.get("sample_images", [])
    sample_movie_url = product.get("sample_movie_url", "")

    # カテゴリ名の取得
    genre_info = GENRES.get(genre, {}) if genre else {}
    category_name = genre_info.get("label", "おすすめ")
    category_slug = genre_info.get("category", "recommended")

    # 日付の整形
    article_date = _format_date()

    # スラッグの生成
    slug = _make_slug(product.get("content_id", ""), index)

    # ファイル名
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    # 既存ファイルがあればスキップ
    if os.path.exists(filepath):
        print(f"[スキップ] 既に存在: {filename}")
        return ""

    # タグの生成
    tag_list = genres[:5] if genres else [category_name]
    tags = ", ".join(f'"{t}"' for t in tag_list)

    # ジャンルテキスト（導入文用）
    genre_text = "・".join(genres[:3]) if genres else category_name

    # テンプレート変数の準備
    intro_text = random.choice(INTRO_VARIATIONS).format(
        title=_truncate(title, 40),
        genre_text=genre_text,
        category_name=category_name,
    )
    body_text = random.choice(BODY_VARIATIONS)
    hook_title = random.choice(HOOK_TITLES)
    meta_description = _build_meta_description(title, genre_text, category_name)

    # 各セクション生成
    cta_section = _build_cta(affiliate_url, title)
    sample_gallery = _build_sample_gallery(sample_images, category_name)
    sample_movie = _build_sample_movie(sample_movie_url)
    sns_section = _build_sns_section()
    footer_brand = _build_footer_brand()
    related_section = _build_related_section(category_name)
    eronavi_link = _build_eronavi_link()
    alt_text = _build_alt_text(title, genre_text, category_name)

    # ランダムにテンプレートを選択
    template = random.choice(ARTICLE_TEMPLATES)

    # レンダリング
    content = template.render(
        title=_truncate(title, 60),
        date=article_date,
        tags=tags,
        category=category_slug,
        category_name=category_name,
        meta_description=meta_description,
        hook_title=hook_title,
        intro_text=intro_text,
        image_url=image_url,
        body_text=body_text,
        price=price,
        maker=maker,
        author=author,
        series=series,
        actresses=actresses,
        alt_text=alt_text,
        cta_section=cta_section,
        sample_gallery=sample_gallery,
        sample_movie=sample_movie,
        sns_section=sns_section,
        footer_brand=footer_brand,
        related_section=related_section,
        eronavi_link=eronavi_link,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

    return filepath


def _format_date() -> str:
    """今日の日付をHugo用のISO形式で返す"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _make_slug(content_id: str, index: int) -> str:
    """URLスラッグを生成する"""
    if content_id:
        slug = re.sub(r"[^a-zA-Z0-9]", "-", content_id).strip("-").lower()
        if slug:
            return slug
    return f"product-{index:03d}"


def _build_meta_description(title: str, genre_text: str, category_name: str) -> str:
    """SEOキーワードを自然に含んだmeta descriptionを生成する"""
    desc_variations = [
        f"{title}のサンプル・レビュー。{genre_text}系作品を紹介。",
        f"{category_name}好き必見の「{title}」を徹底レビュー。{genre_text}好きにおすすめ。",
        f"興奮度MAX！{genre_text}作品「{title}」。サンプル付きで紹介。",
        f"{category_name}の注目作「{title}」。{genre_text}のシーンをサンプル付きで紹介。",
        f"FANZA{category_name}の人気作「{title}」。{genre_text}ファンなら見逃せない。",
    ]
    desc = random.choice(desc_variations)
    return _truncate(desc, 155)


def _truncate(text: str, max_len: int) -> str:
    """テキストを指定文字数で切り詰める"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _build_alt_text(title: str, genre_text: str, category_name: str) -> str:
    """SEO向けの具体的なalt属性テキストを生成する"""
    alt_variations = [
        f"{category_name}作品「{title}」のパッケージ画像",
        f"「{title}」{genre_text}系作品のサムネイル",
        f"興奮度MAXの「{title}」の作品画像",
    ]
    return _truncate(random.choice(alt_variations), 120)


def _build_cta(affiliate_url: str, title: str) -> str:
    """CTAボタンセクションを生成する"""
    if not affiliate_url:
        return ""

    cta_texts = [
        "サンプルを見る",
        "今すぐチェック",
        "この作品を見る",
        "FANZAで詳細を見る",
        "作品ページへGO",
    ]
    cta_text = random.choice(cta_texts)

    return f"""
<div style="text-align: center; margin: 2em 0;">
  <a href="{affiliate_url}" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 15px 40px; background: #e63946; color: #fff; text-decoration: none; border-radius: 8px; font-size: 1.1em; font-weight: bold;">
    {cta_text}
  </a>
  <p style="margin-top: 0.5em; font-size: 0.85em; color: #888;">※FANZAの作品ページに移動します</p>
</div>
"""


def _build_sample_gallery(sample_images: list[str], category_name: str = "") -> str:
    """サンプル画像ギャラリーを生成する"""
    if not sample_images:
        return ""

    images = sample_images[:6]
    label = category_name if category_name else "二次元アダルト"

    gallery_html = f"""
### サンプル画像

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 1em 0;">
"""
    for idx, img_url in enumerate(images, 1):
        gallery_html += f'  <a href="{img_url}" target="_blank" rel="nofollow"><img src="{img_url}" alt="{label}作品のサンプル画像{idx}" style="width: 100%; border-radius: 4px;" loading="lazy" /></a>\n'

    gallery_html += "</div>\n"
    return gallery_html


def _build_sample_movie(sample_movie_url: str) -> str:
    """サンプル動画の埋め込みセクションを生成する"""
    if not sample_movie_url:
        return ""

    return f"""
### サンプル動画を見る

<div style="width: 100%; max-width: 560px; margin: 1.5em auto;">
  <iframe src="{sample_movie_url}" width="560" height="360" frameborder="0" allowfullscreen
          style="width: 100%; height: auto; aspect-ratio: 560/360; border-radius: 8px;"></iframe>
</div>
"""


def _build_sns_section() -> str:
    """SNSリンクセクションを生成する"""
    return """
### MuscleLove

<div style="display: flex; gap: 16px; flex-wrap: wrap; margin: 1.5em 0;">
  <a href="https://www.patreon.com/c/MuscleLove" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #FF424D; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on Patreon
  </a>
  <a href="https://x.com/MuscleGirlLove7" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on X
  </a>
  <a href="https://linktr.ee/ILoveMyCats" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #43e660; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove Links
  </a>
</div>
"""


def _build_footer_brand() -> str:
    """フッターのブランド表示を生成する"""
    return """
<p style="text-align: center; margin: 2em 0 0.5em; font-size: 0.9em; color: #888;">Presented by <strong>MuscleLove</strong></p>
"""


def _build_eronavi_link() -> str:
    """実写版エロナビへの相互リンクを生成する"""
    return """
### 実写AV作品はこちら

<div style="margin: 1em 0; padding: 12px 20px; background: #1a1a2e; border: 1px solid #30363d; border-radius: 8px;">
  <a href="https://musclelove-777.github.io/eronavi/" target="_blank"
     style="color: #ff6b6b; text-decoration: none; font-weight: bold;">
    エロナビ（実写AV版） → NTR・熟女・VR・巨乳…全ジャンルの実写AV作品はこちら
  </a>
</div>
"""


def _build_related_section(current_genre: str = "") -> str:
    """他ジャンルへの内部リンクでSEOを強化"""
    genres = {
        "エロアニメ": "/anime-navi/categories/anime/",
        "同人CG": "/anime-navi/categories/doujincg/",
        "同人漫画": "/anime-navi/categories/doujinmanga/",
        "ASMR": "/anime-navi/categories/voice/",
        "同人ゲーム": "/anime-navi/categories/doujingame/",
        "エロゲ": "/anime-navi/categories/pcgame/",
        "コミック": "/anime-navi/categories/comic/",
        "NTRアニメ": "/anime-navi/categories/ntranime/",
        "触手": "/anime-navi/categories/tentacle/",
        "異世界": "/anime-navi/categories/isekai/",
        "学園": "/anime-navi/categories/school/",
        "BL": "/anime-navi/categories/bl/",
    }
    # 現在のジャンルを除外してランダム5つ選ぶ
    other = [(k, v) for k, v in genres.items() if k != current_genre]
    picks = random.sample(other, min(5, len(other)))

    links = " | ".join([f'[{name}の作品を見る]({url})' for name, url in picks])

    return f"""
### 他のジャンルも見る

{links}

[全カテゴリ一覧](/anime-navi/categories/) | [タグ一覧](/anime-navi/tags/)
"""


if __name__ == "__main__":
    test_products = [
        {
            "title": "テスト作品",
            "image_url": "https://example.com/image.jpg",
            "affiliate_url": "https://example.com/affiliate",
            "price": "1,980円",
            "date": "2026-03-29 10:00:00",
            "content_id": "test001",
            "product_id": "test001",
            "genres": ["テスト"],
            "actresses": ["テスト声優"],
            "maker": "テストサークル",
            "author": "",
            "series": "",
            "sample_images": [],
            "sample_movie_url": "",
        }
    ]
    files = generate_articles(test_products, genre="anime")
    for f in files:
        print(f"  生成: {f}")
