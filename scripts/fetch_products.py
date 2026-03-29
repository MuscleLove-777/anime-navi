"""
DMM/FANZAアフィリエイトAPIから商品データを取得するモジュール
アニメ特化マルチジャンル対応版
ジャンルごとにservice/floorを切り替えてAPIを叩く
"""

import time
import random
import requests
from typing import Optional
from config import Config, GENRES


# ジャンルごとの関連キーワード（タイトル・ジャンルフィルタリング用）
GENRE_KEYWORDS = {
    "anime": ["アニメ", "OVA", "エロアニメ", "アニメーション", "声優", "2Dアニメ", "原作", "コミック原作", "ゲーム原作", "シリーズ"],
    "doujin_cg": ["CG集", "イラスト", "AI", "画像集", "CG", "フルカラー", "高画質", "立ち絵", "差分", "描き下ろし"],
    "doujin_manga": ["同人誌", "漫画", "マンガ", "コミック", "成人向け", "薄い本", "二次創作", "オリジナル", "フルカラー", "描き下ろし"],
    "doujin_voice": ["ASMR", "ボイス", "音声", "バイノーラル", "耳かき", "囁き", "催眠", "シチュエーション", "ドラマCD", "CV"],
    "doujin_game": ["同人ゲーム", "RPG", "アクション", "ノベル", "シミュレーション", "ドット絵", "ゲーム", "プレイ", "エンディング", "攻略"],
    "pcgame": ["美少女ゲーム", "エロゲ", "ノベルゲーム", "ギャルゲ", "アドベンチャー", "シミュレーション", "RPG", "Windows", "DL版", "パッケージ"],
    "comic": ["コミック", "漫画", "エロ漫画", "成人向け", "アダルトコミック", "単行本", "連載", "読み切り", "フルカラー", "オリジナル"],
    "ntr_anime": ["NTR", "寝取られ", "アニメ", "OVA", "人妻", "不倫", "浮気", "堕ち", "催眠", "洗脳"],
    "tentacle": ["触手", "異種姦", "モンスター", "魔物", "クリーチャー", "異種", "怪物", "拘束", "産卵", "侵食"],
    "isekai": ["異世界", "ファンタジー", "転生", "魔法", "冒険", "勇者", "魔王", "エルフ", "ハーレム", "チート"],
    "school": ["学園", "制服", "学校", "教室", "部活", "放課後", "先生", "生徒", "青春", "恋愛"],
    "bl": ["BL", "ボーイズラブ", "男の娘", "ショタ", "男子", "男×男", "腐", "イケメン", "美少年", "やおい"],
}


def fetch_products(
    keyword: str = "",
    hits: int = Config.DEFAULT_HITS,
    service: str = "",
    floor: str = "",
    sort: str = Config.DEFAULT_SORT,
    genre: str = "",
) -> list[dict]:
    """
    DMM Affiliate API v3から商品一覧を取得する

    Args:
        keyword: 検索キーワード
        hits: 取得件数（最大100）
        service: サービス種別（digital, doujin, pcgame, ebook, mono等）
        floor: フロアID（anime, digital_doujin, digital_pcgame, comic等）
        sort: ソート順（date, rank, price等）
        genre: ジャンルキー（anime, doujin_cg, pcgame等）

    Returns:
        商品情報の辞書リスト
    """
    if not Config.validate():
        return []

    # ジャンルからservice/floorを決定（引数での指定を優先）
    genre_info = GENRES.get(genre, {}) if genre else {}
    if not service:
        service = genre_info.get("service", Config.DEFAULT_SERVICE)
    if not floor:
        floor = genre_info.get("floor", Config.DEFAULT_FLOOR)

    # キーワード未指定時はジャンルからランダムに選択
    if not keyword:
        if genre and genre in GENRES:
            keyword = random.choice(GENRES[genre]["keywords"])
        else:
            # ランダムなジャンルから選択
            random_genre = random.choice(list(GENRES.values()))
            keyword = random.choice(random_genre["keywords"])

    # APIリクエストパラメータの構築
    params = {
        "api_id": Config.API_ID,
        "affiliate_id": Config.AFFILIATE_ID,
        "site": "FANZA",
        "service": service,
        "hits": min(hits, 100),
        "sort": sort,
        "keyword": keyword,
        "output": "json",
    }

    if floor:
        params["floor"] = floor

    print(f"[取得中] キーワード「{keyword}」(service={service}, floor={floor}) で{hits}件の商品を検索...")

    try:
        response = requests.get(Config.API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("[エラー] APIリクエストがタイムアウトしました")
        return []
    except requests.exceptions.ConnectionError:
        print("[エラー] APIサーバーに接続できません")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[エラー] APIがHTTPエラーを返しました: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[エラー] リクエスト中に予期せぬエラーが発生: {e}")
        return []

    try:
        data = response.json()
    except ValueError:
        print("[エラー] APIレスポンスのJSONパースに失敗しました")
        return []

    result = data.get("result", {})
    status = result.get("status", 0)
    if status != 200:
        message = result.get("message", "不明なエラー")
        print(f"[エラー] API応答エラー: {message}")
        return []

    items = result.get("items", [])
    if not items:
        print(f"[情報] キーワード「{keyword}」に該当する商品が見つかりませんでした")
        return []

    # フィルタリング用キーワードを決定
    relevant_kws = GENRE_KEYWORDS.get(genre, []) if genre else []

    products = []
    for item in items:
        product = _parse_item(item)
        if product:
            if relevant_kws:
                if _is_relevant(product, keyword, relevant_kws):
                    products.append(product)
                else:
                    print(f"[除外] 関連度低: {product['title'][:40]}...")
            else:
                products.append(product)

    print(f"[完了] {len(products)}件の関連商品データを取得しました")
    return products


def _is_relevant(product: dict, keyword: str, relevant_keywords: list[str]) -> bool:
    """
    商品がテーマに関連するかチェックする
    """
    title = product.get("title", "").lower()
    genres = " ".join(product.get("genres", [])).lower()
    check_text = f"{title} {genres}"

    if keyword.lower() in check_text:
        return True

    for kw in relevant_keywords:
        if kw.lower() in check_text:
            return True

    return False


def _build_affiliate_url(item: dict, affiliate_id: str) -> str:
    """商品のアフィリエイトURLを構築する"""
    # FANZAのアフィリエイトURLをそのまま使う
    affiliate_url = item.get("affiliateURL", "")
    if affiliate_url:
        return affiliate_url

    content_id = item.get("content_id", "")
    direct_url = item.get("URL", "")

    if direct_url:
        separator = "&" if "?" in direct_url else "?"
        return f"{direct_url}{separator}af_id={affiliate_id}"

    return ""


def _parse_item(item: dict) -> Optional[dict]:
    """APIレスポンスの1商品をパースして整形する"""
    try:
        image_url = ""
        image_data = item.get("imageURL", {})
        if image_data:
            image_url = image_data.get("large", image_data.get("small", ""))

        prices = item.get("prices", {})
        price = ""
        if prices:
            price_info = prices.get("price", prices.get("deliveries", {}).get("delivery", [{}]))
            if isinstance(price_info, str):
                price = price_info
            elif isinstance(price_info, list) and price_info:
                price = price_info[0].get("price", "")

        genres = []
        item_info = item.get("iteminfo", {})
        if item_info:
            genre_list = item_info.get("genre", [])
            genres = [g.get("name", "") for g in genre_list if g.get("name")]

        # アニメ系は女優→声優/サークルなど
        actresses = []
        if item_info:
            actress_list = item_info.get("actress", [])
            actresses = [a.get("name", "") for a in actress_list if a.get("name")]

        # サークル/ブランド情報（同人系で重要）
        circle = ""
        if item_info:
            maker_list = item_info.get("maker", [])
            if maker_list:
                circle = maker_list[0].get("name", "")

        # 著者情報（コミック系）
        author = ""
        if item_info:
            author_list = item_info.get("author", [])
            if author_list:
                author = author_list[0].get("name", "")

        sample_images = []
        sample_image_data = item.get("sampleImageURL", {})
        if sample_image_data:
            sample_l = sample_image_data.get("sample_l", {})
            if sample_l:
                sample_images = sample_l.get("image", [])
            else:
                sample_s = sample_image_data.get("sample_s", {})
                if sample_s:
                    small_images = sample_s.get("image", [])
                    import re as _re
                    for img in small_images:
                        large_img = _re.sub(r'(\w+)-(\d+\.jpg)$', r'\1jp-\2', img)
                        sample_images.append(large_img)

        sample_movie_url = ""
        sample_movie_data = item.get("sampleMovieURL", {})
        if sample_movie_data:
            size_560 = sample_movie_data.get("size_560_360", "")
            if size_560:
                sample_movie_url = size_560

        return {
            "title": item.get("title", "タイトル不明"),
            "description": item.get("title", ""),
            "image_url": image_url,
            "affiliate_url": _build_affiliate_url(item, Config.AFFILIATE_ID),
            "price": price,
            "date": item.get("date", ""),
            "content_id": item.get("content_id", ""),
            "product_id": item.get("product_id", ""),
            "genres": genres,
            "actresses": actresses,
            "maker": circle,
            "author": author,
            "series": item_info.get("series", [{}])[0].get("name", "") if item_info.get("series") else "",
            "sample_images": sample_images,
            "sample_movie_url": sample_movie_url,
        }
    except (KeyError, IndexError, TypeError) as e:
        print(f"[警告] 商品データのパースに失敗しました: {e}")
        return None


def fetch_multiple_keywords(
    keywords: Optional[list[str]] = None,
    hits_per_keyword: int = 3,
    genre: str = "",
) -> list[dict]:
    """複数キーワードで商品を一括取得する"""
    if keywords is None:
        if genre and genre in GENRES:
            keywords = GENRES[genre]["keywords"]
        else:
            keywords = []
            for g in GENRES.values():
                keywords.extend(g["keywords"])

    all_products = []
    seen_ids = set()

    for kw in keywords:
        products = fetch_products(keyword=kw, hits=hits_per_keyword, genre=genre)
        for p in products:
            pid = p.get("content_id", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(p)
        time.sleep(1)

    print(f"[合計] {len(all_products)}件のユニークな商品を取得しました")
    return all_products


if __name__ == "__main__":
    products = fetch_products(keyword="アニメ", hits=3, genre="anime")
    for p in products:
        print(f"  - {p['title']} ({p['price']})")
