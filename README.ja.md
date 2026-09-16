# Astraeus

Astraが設計・委譲判断・統合・受け入れを担う、軽量なCodex CLI Pluginです。
必要な仕事だけをネイティブSubAgentへ委譲し、重要な変更を別コンテキストでレビューします。

小さな仕事はRootだけで完了します。実装担当が通常の検証も担当し、親は必要な統合確認を行います。
デザインセンス・視覚的な完成度の判断はAstraを優先します。実装を委譲しても、見た目が重要なら
Astraが実際の画面・画像を確認します。モデル・人数・検索回数を機械的に固定しません。

## 導入と全プロジェクトでの有効化

Codex CLIのPlugin・SubAgent対応版、Python 3.11以上、既存のCodexログインが必要です。
検証したCLIは0.153.4。構造化返信の検証にはuvまたはjsonschemaを使います。

checkoutのルートから実行します。

```sh
codex plugin marketplace add /absolute/path/to/astraeus
codex plugin add astraeus@astraeus
python3 plugins/astraeus/scripts/astraeus.py activation enable
python3 plugins/astraeus/scripts/astraeus.py activation enable --apply
```

`--apply`なしは変更内容のプレビューです。有効化は `$CODEX_HOME/AGENTS.md`
（既定 `~/.codex/AGENTS.md`）に短い管理ブロックを追記します。既存の指示は保持し、変更時には
バックアップを作ります。**新しいCodexセッションを開始し、Astraを選択**してください。
その後はどのプロジェクトでも通常の依頼で自律運用します。

これは指示による運用です。毎回の起動を強制するHookではありません。`AGENTS.override.md`、
上位の指示、プロジェクトの指示、Plugin無効化、ホストの指示省略などの影響を受けます。
RootのモデルをPluginが勝手に切り替えることもありません。

GitHubにソースがpushされた後は `codex plugin marketplace add See2et/astraeus --ref main`
からも導入できます。Privateの場合はGitアクセス権が必要です。空のリモートからは導入できません。
ローカルcheckoutとGit取得元を同じmarketplace名で重複登録しないでください。

## 利用と判断基準

明示的には `$astraeus:orchestrate`、レビューだけなら `$astraeus:review` を使えます。

| 選択候補 | 判断の目安 |
| --- | --- |
| Luna | 狭く明確で、容易に検証できる作業 |
| Terra | 複数箇所の理解や適度な判断を伴う、範囲の明確な作業 |
| Sol | 難しい依存関係・曖昧さ・失敗時の影響が大きい作業 |
| 別コンテキストのAstra | 深い推論、設計、デザイン・視覚品質の独立レビュー |
| RootのAstra | 引き継ぎ負担が大きい作業、設計判断、密結合な統合、最終受け入れ |

これは実測性能表ではなく判断指針です。最安モデルを必ず試す手順にはしません。
effortは別に判断し、実行環境が対応する値だけを指定します。指定値・ホストで観測した値・不明を
区別し、子Agentの自己申告をモデル確認の証拠にはしません。

重要な動作変更、互換性、データ、権限、インストール、複数部分にまたがる変更は独立レビューが必要です。
任意改善は完了を妨げません。レビュアーは編集しません。上限は**初回＋再レビュー1回の計2回**で、
失敗・不正な返信・中断も回数に含めます。未解決・証拠不足は未完了です。
モデルをユーザーが固定していなければ、Astraは理由を示して選び直せます。

## 設定と返信形式

設定なしで使えます。必要なプロジェクトだけ `astraeus.example.toml` を `astraeus.toml` にコピーします。
モデル制限、追加レビュー対象パス、回数上限の1回への引き下げ、保証の厳格性を設定できます。不明なキーはエラーです。

```sh
python3 plugins/astraeus/scripts/astraeus.py doctor --config astraeus.example.toml
```

通常は `reported`：ネイティブSubAgent＋編集禁止等の指示＋返答検証です。
権限やSchemaを技術的に強制できない点はプロンプトに明示します。`strict`ではホスト由来の
モデル・effort・read-only sandboxの証拠がなければ止めます。別モデルやAPI課金への黙った切替はしません。

探索・外部調査・実装・レビューにJSON Schemaを用意しています。レビュー以外は、利益が小さければ
短い通常返信で構いません。Schemaが指定するのは成果物であり、内部の思考手順ではありません。
具体的な検証コマンドは[Contract仕様](plugins/astraeus/references/contracts.md)と[英語README](README.md#result-contracts)にあります。

レビュー結果の検証は `--accept` で合格条件まで確認できます。指定しない場合、終了コード0は
「形式が正しい」という意味だけです。根拠の真偽・確認範囲・独立性・回数遵守はRootが確認します。

## 開発内容の再反映

ローカルcheckout、Git取得済みmarketplace、インストール済みキャッシュ、実行中セッションは別です。

```sh
# ローカルcheckoutが導入元の場合。まずプレビュー。
python3 plugins/astraeus/scripts/astraeus.py plugin refresh --repo .
python3 plugins/astraeus/scripts/astraeus.py plugin refresh --repo . --apply

# Gitが導入元の場合。
codex plugin marketplace upgrade astraeus
codex plugin add astraeus@astraeus
```

ローカルrefreshは導入元を確認し、manifestのバージョンに開発用suffixを付けて公式addを実行します。
別checkoutやGit取得元を誤って置き換えません。開発用suffixはリリース前に除いてください。
再導入に失敗するとsuffixは残ります。エラー原因を解決して再実行します。
成功後は新しいセッションを開始してください。実行中スレッドのhot reloadは保証しません。

破損したローカル導入を対象限定で再作成する場合は `plugin reset --repo . --apply` を使います。
Astraeusの公式remove/addだけを行い、キャッシュ全体は削除しません。

## 撤去

```sh
python3 plugins/astraeus/scripts/astraeus.py activation disable --apply
codex plugin remove astraeus@astraeus
codex plugin marketplace remove astraeus
```

既存の個人設定・認証・履歴・他Plugin・checkoutは保持します。指示ブロックが手編集されていたら
自動削除を止めます。バックアップは個人の指示を含み得るので公開せず、不要になったら手動で削除してください。

## 検証

```sh
uv sync --locked
uv run python -m unittest discover -s tests -v
python3 tests/smoke_plugin.py
```

Pluginの実機テストは一時的な `CODEX_HOME` 内で行い、モデルや認証情報を使用しません。
実際のSubAgent試験、確認済み事項と未検証事項は[検証記録](docs/verification.md)に分けて記載します。
コスト報告は補助機能で、API単価をPro枠の実測節約とは呼びません。

MIT / [出典](NOTICE.md)。公開用に新規実装し、個人Skillsや私的なリポジトリは同梱していません。
