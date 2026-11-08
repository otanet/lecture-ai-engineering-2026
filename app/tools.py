"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


# 第3回 宿題（実装）: 学習の記録を保存するツール
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_LOG_CHARS = 5000


def _safe_filename(title: str) -> str:
    """ファイル名に使えない文字を「_」に置き換え、長すぎる題名を切り詰める。"""
    cleaned = "".join("_" if c in '\\/:*?"<>|' or c.isspace() else c for c in title.strip())
    return cleaned[:40] or "untitled"


def save_learning_log(title: str, content: str) -> str:
    """学習の記録（学んだこと・疑問・次にやること）を、learning_log/ フォルダに Markdown で保存する。

    利用者が「今日学んだことを記録して」「この説明をメモに残して」のように、
    記録や保存をはっきり頼んだときだけ使う。頼まれていないのに使わない。
    title には記録の短い題名（例: "第3回 LoRAとQLoRA"）、content には保存する本文を入れる。
    保存してよいかの確認はプログラムが自動で行うので、確認の質問はせず、そのままこのツールを呼ぶこと。
    """
    if not content.strip():
        return "本文が空なので保存しませんでした。"
    if len(content) > MAX_LOG_CHARS:
        return f"本文が長すぎます（{len(content)}文字）。{MAX_LOG_CHARS}文字以内にまとめてください。"

    from datetime import datetime

    now = datetime.now()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{now:%Y%m%d-%H%M%S}_{_safe_filename(title)}.md"
    # "x" モード：同名のファイルがあれば上書きせずにエラーにする
    try:
        with open(path, "x", encoding="utf-8") as f:
            f.write(f"# {title.strip() or '無題'}\n\n- 保存日時: {now:%Y-%m-%d %H:%M:%S}\n\n{content.strip()}\n")
    except FileExistsError:
        return f"同じ名前のファイルがすでにあるため保存しませんでした: {path.name}"
    return f"保存しました: learning_log/{path.name}"