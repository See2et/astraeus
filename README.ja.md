# Astraeus

GPT-6.1 SolのRootが設計・委譲判断・統合・最終受け入れを担う、軽量なCodex CLI Pluginです。
必要な仕事だけをネイティブSubAgentへ委譲し、重要な変更を別コンテキストでレビューします。
レビューでReject相当の`changes_required`が出た場合だけ、別の採否Agentが要件の根拠・具体的な影響・修正の妥当性を判断します。
PassはRootが結果と現在の対象を確認して受け入れます。
採用した指摘だけを実装担当へ戻し、Rootが最終受け入れを行います。

小さな仕事はRootだけで完了します。実装担当が通常の検証も担当し、親は必要な統合確認を行います。
デザインセンス・視覚的な完成度の判断はAstraを優先します。実装を委譲しても、見た目が重要なら
Astraが実際の画面・画像を確認します。モデル・人数・検索回数を機械的に固定しません。
通常の作業はGPTを優先します。ユーザーが明示的に希望した場合だけ、デザイン設計と直接関連する
UI実装をClaude Codeの`--bg`へ委譲できます。その他の実装、独立レビュー、採否判断、統合はGPTに
残します。「見た目を改善して」という依頼だけではClaudeを起動しません。
連携方法は[Claude委譲仕様](plugins/astraeus/references/claude-design.md)にあります。

重複作業を減らすため、目的・範囲・制約・完了条件が委譲できる程度に明確になったら、Rootの
調査を止めます。範囲が明確な仕事の調査・実装・通常の検証・修正は同じ担当者が継続します。
独立した仕事には原則として新規コンテキストで必要なファイル・決定事項・制約だけを渡し、
履歴の継承は必要な場合に限定します。Rootは差分・検証結果・未解決事項を確認し、統合変更、
検証失敗、証拠不足、具体的な懸念がある範囲だけ再調査・再検証します。
独立レビューは要件・変更で壊れ得る動作・検証不足に集中し、必要なら依存先まで確認します。
無関係な改善探しや設計のやり直しは依頼しません。レビューの必須条件は維持します。
これらは重複を抑える運用方針であり、Pro利用枠の削減率を保証するものではありません。

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
バックアップを作ります。**新しいCodexセッションを開始し、GPT-6.1 Sol（`gpt-6.1-sol`）を選択**してください。
その後はどのプロジェクトでも通常の依頼で自律運用します。

これは指示による運用です。毎回の起動を強制するHookではありません。`AGENTS.override.md`、
上位の指示、プロジェクトの指示、Plugin無効化、ホストの指示省略などの影響を受けます。
RootのモデルをPluginが勝手に切り替えることもありません。
GPT-6.1 Solがホストに表示されない場合は未適用と明示し、GPT-5.6 Solで代用しません。
必要ならクライアント更新後、新しいセッションで指定モデルを選択します。

GitHubにソースがpushされた後は `codex plugin marketplace add See2et/astraeus --ref main`
からも導入できます。Privateの場合はGitアクセス権が必要です。空のリモートからは導入できません。
ローカルcheckoutとGit取得元を同じmarketplace名で重複登録しないでください。

## 利用と判断基準

明示的には `$astraeus:orchestrate`、レビューだけなら `$astraeus:review` を使えます。

| 選択候補 | 判断の目安 |
| --- | --- |
| GPT-5.6 Luna | 狭く明確で、容易に検証できる作業 |
| GPT-5.6 Terra | 複数箇所の理解や適度な判断を伴う、範囲の明確な作業 |
| GPT-5.6 Sol | 難しい依存関係・曖昧さ・失敗時の影響が大きい作業 |
| 別コンテキストのGPT-6 Astra | 深い推論、設計、デザイン・視覚品質の独立レビュー |
| RootのGPT-6.1 Sol | 引き継ぎ負担が大きい作業、設計判断、密結合な統合、最終受け入れ |

GPT-6 Lunaは既定の候補から外します。GPT-5.6 Lunaは狭い作業用に残します。
SolのRootは視覚評価をAstraへ委譲し、その実物確認の証拠を使って最終受け入れを判断します。

これは実測性能表ではなく判断指針です。最安モデルを必ず試す手順にはしません。
effortは別に判断し、実行環境が対応する値だけを指定します。指定値・ホストで観測した値・不明を
区別し、子Agentの自己申告をモデル確認の証拠にはしません。

重要な動作変更、互換性、データ、権限、インストール、複数部分にまたがる変更は独立レビューが必要です。
任意改善は完了を妨げません。レビュアーは編集しません。レビュー・採否Agentの累計呼び出し回数に固定上限はありません。
失敗・不正な返信・中断は必要に応じて再試行し、修正や新しい証拠に応じて再レビューします。未解決・証拠不足は未完了です。
`changes_required`の完了レビューにだけ採否Agentを1回呼び出します。
Passでは採否Agentを呼び出しません。任意の改善提案も採否判断の理由にはしません。証拠不足や`inconclusive`は未完了として扱います。再帰的なレビュー・採否の議論は行いません。
モデルをユーザーが固定していなければ、Rootは理由を示して選び直せます。

## 設定と返信形式

設定なしで使えます。必要なプロジェクトだけ `astraeus.example.toml` を `astraeus.toml` にコピーします。
モデル制限、追加レビュー対象パス、保証の厳格性を設定できます。旧`review_limit`設定は廃止したため、既存設定から削除してください。不明なキーはエラーです。

```sh
python3 plugins/astraeus/scripts/astraeus.py doctor --config astraeus.example.toml
```

通常は `reported`：ネイティブSubAgent＋編集禁止等の指示＋返答検証です。
権限やSchemaを技術的に強制できない点はプロンプトに明示します。`strict`ではホスト由来の
モデル・effort・read-only sandboxの証拠がなければ止めます。別モデルやAPI課金への黙った切替はしません。

探索・外部調査・実装・レビュー・採否にJSON Schemaを用意しています。レビューと採否以外は、利益が小さければ
短い通常返信で構いません。Schemaが指定するのは成果物であり、内部の思考手順ではありません。
Claudeのバックグラウンド連携では、回収用の最終成果だけimplementation JSONを必須にします。
会話全体のJSON化や生成時のSchema強制は求めず、`-p`への自動切替もしません。
具体的な検証コマンドは[Contract仕様](plugins/astraeus/references/contracts.md)と[英語README](README.md#result-contracts)にあります。

採否結果の検証は `--kind adjudication --review-result <元レビューJSON> --accept` で受け入れ条件まで確認できます。
Passは `--kind review --accept` で直接検証できます。`strict`ではレビューAgentのホスト証拠を`--receipt`で渡します。
レビューv1は引き続き読めます。`changes_required`と`inconclusive`をレビュー単独で受け入れることはできません。指定しない場合、終了コード0は
「形式が正しい」という意味だけです。根拠の真偽・確認範囲・独立性はRootが確認します。
採否結果は元レビューの内容ハッシュと対象コードに紐づけ、指摘の漏れ・重複・古い結果を拒否します。
`strict`の採否検証では、採否Agentの`--receipt`とレビューAgentの`--review-receipt`が必要です。

## 要件・テストの扱い

製品の目的と対象範囲はユーザーが決めます。Rootは依頼と根拠から目的・受け入れ条件・対象外・
守る契約を整理し、明確な依頼に追加承認や恒久的な仕様書を求めません。
実装担当が変更領域の既存挙動とテストを確認し、実装・通常検証まで継続します。

既存コード・テストは現在の挙動を示しますが、それだけで維持すべき仕様とは判断しません。
テスト追加には守る要件・具体的なリスクと検証不足を、変更・削除には仕様の廃止または保証の移し先を示します。
テスト件数を目標にせず、通すためだけのassertion緩和も行いません。未文書化でも実利用者や公開契約、
保存データへの影響は確認し、理由が不明というだけで削除しません。毎回の全体棚卸しは不要です。

`$astraeus:adjudicate`は`changes_required`の場合にだけ呼び出し、各指摘を「修正／調査／不採用／人間による仕様判断」に分けます。
レビューの重大度やテストの存在だけで採用せず、既存の範囲内の修正は自律的に進めます。
未承認の製品仕様変更だけを、影響と選択肢をまとめてユーザーへ戻します。証拠不足は採否Agentでも免除できません。
詳しくは[要件とテストの方針](plugins/astraeus/references/requirements-and-tests.md)を参照してください。

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
