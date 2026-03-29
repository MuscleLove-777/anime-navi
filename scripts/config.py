"""
設定管理モジュール
環境変数または.envファイルから設定を読み込む
アニメ特化アフィリエイトサイト「アニメエロナビ」用
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込む
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


# ジャンル定義（検索キーワード・カテゴリ名・service/floor）
GENRES = {
    "anime": {
        "keywords": ["アニメ", "OVA", "エロアニメ"],
        "category": "Anime",
        "label": "エロアニメ",
        "service": "digital",
        "floor": "anime",
    },
    "doujin_cg": {
        "keywords": ["CG集", "イラスト集", "AI CG"],
        "category": "DoujinCG",
        "label": "同人CG",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "doujin_manga": {
        "keywords": ["同人誌", "エロ漫画", "成人向け漫画"],
        "category": "DoujinManga",
        "label": "同人漫画",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "doujin_voice": {
        "keywords": ["ASMR", "ボイス", "音声作品"],
        "category": "Voice",
        "label": "ASMR",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "doujin_game": {
        "keywords": ["同人ゲーム", "RPG", "アクション"],
        "category": "DoujinGame",
        "label": "同人ゲーム",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "pcgame": {
        "keywords": ["美少女ゲーム", "エロゲ", "ノベルゲーム"],
        "category": "PCGame",
        "label": "エロゲ",
        "service": "pcgame",
        "floor": "digital_pcgame",
    },
    "comic": {
        "keywords": ["アダルトコミック", "エロ漫画", "成人向け"],
        "category": "Comic",
        "label": "コミック",
        "service": "ebook",
        "floor": "comic",
    },
    "ntr_anime": {
        "keywords": ["NTR アニメ", "寝取られ アニメ"],
        "category": "NTRAnime",
        "label": "NTRアニメ",
        "service": "digital",
        "floor": "anime",
    },
    "tentacle": {
        "keywords": ["触手", "異種姦", "モンスター"],
        "category": "Tentacle",
        "label": "触手",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "isekai": {
        "keywords": ["異世界", "ファンタジー", "転生"],
        "category": "Isekai",
        "label": "異世界",
        "service": "doujin",
        "floor": "digital_doujin",
    },
    "school": {
        "keywords": ["学園", "制服", "学園モノ"],
        "category": "School",
        "label": "学園",
        "service": "digital",
        "floor": "anime",
    },
    "bl": {
        "keywords": ["BL", "ボーイズラブ", "男の娘"],
        "category": "BL",
        "label": "BL",
        "service": "doujin",
        "floor": "digital_doujin_bl",
    },
}


class Config:
    """アプリケーション設定クラス"""

    # DMM API認証情報
    API_ID: str = os.getenv("API_ID", "")
    AFFILIATE_ID: str = os.getenv("AFFILIATE_ID", "")
    SITE_NAME: str = os.getenv("SITE_NAME", "anime-navi")

    # APIエンドポイント
    API_BASE_URL: str = "https://api.dmm.com/affiliate/v3/ItemList"

    # Hugo出力設定
    CONTENT_DIR: str = str(_project_root / "content" / "posts")

    # 記事生成のデフォルト設定
    DEFAULT_HITS: int = 5
    DEFAULT_SERVICE: str = "digital"
    DEFAULT_FLOOR: str = "anime"
    DEFAULT_SORT: str = "date"

    @classmethod
    def validate(cls) -> bool:
        """必須設定が存在するか検証する"""
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.AFFILIATE_ID:
            missing.append("AFFILIATE_ID")
        if missing:
            print(f"[エラー] 以下の環境変数が未設定です: {', '.join(missing)}")
            print("  .envファイルを作成するか、環境変数を設定してください。")
            return False
        return True
