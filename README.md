# Simple Fluent Notepad

PySide6 と QFluentWidgets を使用したモダンなテキストエディタアプリケーションです。

## 特徴

- **行番号表示** - コード編集に便利な行番号エリア
- **現在行ハイライト** - カーソル位置の行を視覚的に強調
- **検索機能** - テキスト内検索（前方・後方対応）
- **ズーム機能** - 表示サイズの拡大・縮小
- **テーマ切り替え** - ライト/ダークモード対応
- **Fluent Design** - Windows 11 スタイルのモダンな UI

## スクリーンショット

（スクリーンショットをここに追加）

## 必要要件

- Python 3.8 以上
- PySide6
- PyQt-Fluent-Widgets

## インストール

```bash
pip install PySide6 PyQt-Fluent-Widgets
```

## 使い方

```bash
python main.py
```

## 機能一覧

| 機能 | ショートカット | 説明 |
|------|---------------|------|
| 新規作成 | `Ctrl+N` | 新しいファイルを作成 |
| 開く | `Ctrl+O` | ファイルを開く |
| 保存 | `Ctrl+S` | ファイルを保存 |
| 元に戻す | `Ctrl+Z` | 直前の操作を取り消し |
| やり直し | `Ctrl+Y` | 取り消した操作を再実行 |
| 検索 | `Ctrl+F` | 検索バーを表示 |

## 対応ファイル形式

- テキストファイル (*.txt)
- Python ファイル (*.py)
- その他すべてのテキストファイル

## プロジェクト構成

```
simple-fluent-notepad/
├── main.py          # メインアプリケーション
├── README.md        # このファイル
└── requirements.txt # 依存パッケージ
```

## requirements.txt

```
PySide6>=6.4.0
PyQt-Fluent-Widgets>=1.0.0
```

## ライセンス

MIT License

## 作者

天才技術集団
