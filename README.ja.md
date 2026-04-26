[![mddiff](./assets/header.svg)](https://github.com/izag8216/mddiff)

# mddiff

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-3fb950?style=flat-square)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-3fb950?style=flat-square)](#)

Markdown差分ビューア -- セクション単位のセマンティック差分を表示するCLIツール。

従来の`diff`は行単位で比較するため、Markdown文書のセクション移動や段落の再構成が大量のノイズとして表示されます。**mddiff**はヘッダーでセクションを分割し、意味のある変更点だけをハイライトします。

## 主な機能

- **セクション単位の差分** -- ヘッダー(`#`, `##`, ...)で文書を分割し、セクション単位で比較
- **変更タイプの識別** -- 追加(緑)・削除(赤)・変更(黄)・移動(シアン)を区別
- **インラインdiff** -- 変更セクション内の行レベル差分を表示
- **Git連携** -- `git diff`の結果をMarkdownセクション単位で表示
- **サマリー出力** -- 変更統計のみを表示
- **Richターミナル** -- 色付きパネルで直感的に表示

## インストール

```bash
pip install mddiff
```

またはリポジトリから直接:

```bash
git clone https://github.com/izag8216/mddiff.git
cd mddiff
pip install -e .
```

## 使い方

### 基本的な使い方

```bash
# 二つのファイルを比較
mddiff old.md new.md

# サマリーのみ表示
mddiff old.md new.md --summary

# 特定セクションのみ表示
mddiff old.md new.md --section "## Installation"

# インラインdiff非表示
mddiff old.md new.md --no-inline

# 未変更セクションも表示
mddiff old.md new.md --unchanged
```

### Git連携

```bash
# 直前のコミットとの差分
mddiff --commit HEAD~1

# globパターンでファイルを絞り込み
mddiff --commit HEAD~1 --glob "docs/**/*.md"

# mainブランチとの差分
mddiff --commit main --summary
```

## 仕組み

1. **Parse** -- Markdownをヘッダーでセクションに分割
2. **Match** -- セクションキーでドキュメント間をマッチング
3. **Diff** -- 各セクションペアの類似度を計算し変更タイプを判定
4. **Render** -- Richで色付きパネルとして出力

### 変更タイプ

| アイコン | タイプ | 説明 |
|---------|--------|------|
| `+` | Added | 新しいセクションが追加された |
| `-` | Deleted | セクションが削除された |
| `~` | Modified | セクション内容が変更された |
| `<->` | Moved | セクションが移動した |
| ` ` | Unchanged | 変更なし |

## 動作環境

- Python >= 3.9
- rich >= 13.0

## ライセンス

MIT License -- 詳細は [LICENSE](LICENSE) をご覧ください。

## 関連プロジェクト

- [diff-so-fancy](https://github.com/so-fancy/diff-so-fancy) -- 行レベルの表示改善
- [delta](https://github.com/dandavison/delta) -- 汎用diffビューア
