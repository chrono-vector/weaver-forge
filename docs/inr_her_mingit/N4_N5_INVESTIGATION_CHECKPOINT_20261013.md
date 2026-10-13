# N4/N5 Investigation Checkpoint — 2026-10-13

## 1. Status
PLAN_A_NONLAUNCH=SAVED（909ccce）
PLAN_B_NONLAUNCH=SAVED（1a2f7eec）
N4=OPEN
N5=OPEN
OPERATIONAL_MINGIT_PIN=UNRATIFIED
LAUNCH_IDENTITY=UNBOUND_AT_LAUNCH
SUPERVISOR_HALT_GUARANTEE=UNCHANGED
REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED
FULL_INR_READY=NO

本記録は調査チェックポイントであり、N4/N5の閉鎖、運用PIN批准、実行承認、正文変更ではない。

## 2. Distribution and source provenance
MinGit-2.56.0.2-64-bit.zip
Release asset 613673731
Distribution SHA-256:
da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be

上記は配布ZIPの批准値であり、運用PINではない。

Git for Windows source:
v2.56.0.windows.2
cc4dbf752a05efdc0e04e71fd3e8110d11bdd35c

公開workflow/cache/jobの調査結果はUCRT64/x86_64系統、RUNTIME_PREFIX、相対GIT_EXEC_PATH、ETC_GITCONFIGのソース定義との対応を支持する。ただし展開済みコンパイラコマンド、出荷バイナリの実値、runtime prefixの実動作は未確認。

## 3. MinGit etc/gitconfig static inspection
ZIP内のetc/gitconfigは557バイト。
include.pathが2件存在：
- C:/Program Files (x86)/Git/etc/gitconfig
- C:/Program Files/Git/etc/gitconfig

同じメンバ内にcredential.helper=manager、git-lfs filter、textconv=astextplainがある。当該メンバ内にincludeIfはない。

これは静的な設定記録であり、設定が実際に読み込まれたことやhelperが実行されたことの証明ではない。

## 4. Windows host observations
2026-10-13時点の限定観測：

C:/Program Files (x86)/Git/etc/gitconfig
- 対象ファイル不在

C:/Program Files/Git/etc/gitconfig
- 通常ファイルとして存在
- 401バイト
- include.pathなし
- includeIfなし
- credential.helperあり
- filter関連あり
- diff.*.textconvあり

設定値、資格情報、全文は保存していない。指定パス上で再解析点は検出されなかった。観測時点の結果に限る。

## 5. Git source call-path findings
固定3操作：
VERSION: --version
EXEC_PATH: --exec-path
CONFIG_SCOPES: config --list --show-scope -z

Gitソース上で、3操作とも初期化時にvery-early configを読む。

GIT_CONFIG_NOSYSTEM=1は通常のsystem設定読込を抑止するが、全設定源を無効化しない。

CONFIG_SCOPESはrepository discovery、local/worktree設定、GIT_CONFIG_COUNT、GIT_CONFIG_PARAMETERS等の環境注入経路を持つ。

CONFIG_SCOPESにはpager起動経路があり、stdoutのTTY判定に依存する。実際の子のstdoutがパイプとなることは未証明。

固定argvの通常ソース経路ではcredential helper、filter、textconv、hooksの直接実行呼出しは確認されなかった。ただしバイナリやホスト全体の非到達証明ではない。

Cursor調査をCodexが限定ACCEPT。ただしCodexはソースを独立再取得していない。

## 6. Deployment design gaps
EMPTY_GLOBAL_CONFIG：
- 専用空ファイルの要件のみ定義済み
- 実在する具体パスは未指定
- 作成・保護・実機確認は未実施

CWD：
- Controller所有の非リポジトリ作業ディレクトリという要件のみ
- 具体パス未指定
- repository discovery抑止未証明

11-key environment：
- キー集合、拒否規則、文字列提案は既存C-6/C-7およびPlan Aに存在
- 実配備の具体パス値は一部未指定
- 子プロセスへの適用は未実装・未実行

N4：
- IFEO、AppCert、AppInit、KnownDLLs、SxS、.local、DLL探索、CWD等は未閉鎖
- 既存EB-1の通常import調査は実ローダ解決の証明ではない

N5：
- ProgramData、prefix相対、fallback、include抑止、実際の設定読込、pager、environment bindingなどは未閉鎖

## 7. Paused work and next priority
N4/N5の個別調査を一時停止する。

既存のZIP、ソース、ビルドログ、2つのホスト設定パス、empty global、CWD、11キー環境を理由なく再調査しない。

次の優先作業はWeaver Forge全体の実用化計画を整理し、Windows起動器に依存せず利用できる既存機能、運用条件が残る機能、真の重大blockerを区別すること。

N4/N5の再開や運用安全保証の変更には、別途Human判断が必要。
