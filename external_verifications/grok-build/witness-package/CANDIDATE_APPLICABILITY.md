# Candidate Outcome Contract Applicability

Status: ADOPTED — STAGE 1 TECHNICAL SCOPE
対象作業領域・Candidate管理識別子: WT-WF-CANDIDATE-20261126-01
正式Candidate ID/name（package identity）: 未決定
採用承認者: Repository maintainer本人
採用・受理日: 2026-11-27
採用承認記録: OWNER-LOCAL-STAGE1-APPROVAL-20261127（後続決定追記）
候補適用revisionの識別・承認方法: 下記の基点commit＋変更前ハッシュで固定された4ファイル構成に対する本人の明示承認

## 1. 効力

本記録は、固定参照したOutcome Contractの意味論を変更せず、
Humanが承認した候補revisionに対する適用範囲を定める正式採用記録である。

効力は候補へのOutcome Contract適用範囲とStage 1技術規則に限定する。
承認根拠は上記Human Decision記録と、Repository maintainer本人が確認した
Grok BuildのStage 1独立技術レビュー（ACCEPTABLE、修正必須0件）である。
同本人はStage 1の技術的完了も承認した。Piは記録補助者であり承認者ではない。

承認対象は基点commit 319c6dcb92c5152225076b99a465436ba55924b3に対する
以下の変更前SHA-256で固定された未コミット4ファイル構成である。
パスはexternal_verifications/grok-build/witness-package/からの相対表記。

| ファイル | 承認対象の変更前SHA-256 |
|---|---|
| WITNESS_PACKAGE_VERSION.md | e20a2f586fbacc42329173ce2e9a63d8a65c57382dc7a073a536bc0cc476c4e6 |
| README.md | 74ae128ab779347a55772d0e33d4c7d768e8288588ed3bdd9eb6bb3bacc754f3 |
| LIFECYCLE_CLARIFICATION.md | 9d4473d29cdc72d5f9e43ae6f5f3bc6663f67a91d1a3dcc502f3494690811b62 |
| CANDIDATE_APPLICABILITY.md | 140c9ec3c7393a4b0a6eb940a59f5640f555b4a2929c2218ae839eb32e6da14f |

上表のApplicabilityハッシュは採用時の変更前内容を識別する。
本状態更新後の新ハッシュはHuman Decisionの後続追記に別記し、混同しない。
以下に保持する提案経緯・個別判断時点の記述は過去の文脈として読む。
今回の採用は新しいpackage version、tag、runtime compliance、READY、releaseを意味しない。
採用後も、ソース編集、テスト、build、validator実行、commit、
正式Source評価、Independent Witness、releaseの許可を兼ねない。

作業領域名を正式Candidate ID、package version、tagに自動昇格させない。
本記録の作成・採用だけではruntime complianceを確立しない。

## 2. Outcome Contractの固定参照

Repository:
https://github.com/chrono-vector/weaver-forge.git

基点commit:
319c6dcb92c5152225076b99a465436ba55924b3

Repository-relative path:
external_verifications/grok-build/witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json

Git object参照:
319c6dcb92c5152225076b99a465436ba55924b3:external_verifications/grok-build/witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json

Git blob object ID:
bf96fd320c92fd16fb688cc16869d7612df1a8ee

Git blob bytes:
17634 bytes、LF

Git blob SHA-256:
7e059f7a9ec8de17342c26adc7846861068ccb1132566caaae0365298b03f909

契約内部の識別値:
- contract_version: 1.0.0-phase3b
- contract_phase: 3B
- base_commit: 24a329c5fca4f9ee2ec974509ea589ecb402f876
- contract_status: CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING
- contract_scope: future rc5 remediation向けのOutcome語彙、
  producer ownership、result tuple、no-inference、no-overwrite。
  現在のruntime complianceを主張しない。

契約内部のbase_commitは契約の歴史的文脈であり、
今回の作業基点または候補revisionではない。

照合上の注意:
現在のworktreeコピーはCRLF、18105 bytesであり、そのSHA-256は
dbd0a32ce7096e298ea2f6a055b982fa8fce0b0799c6fb9586e14b268d1c7445。
CRLFをLFに変換した内容は指定Git blobと一致する。
固定参照の内容ハッシュにはGit blobの値を用い、
worktree bytesとGit blob bytesの完全一致を主張しない。
本記録は改行変換や契約ファイルの編集を許可しない。

## 3. 候補適用範囲

採用提案:
固定Contractの以下の規範的要求を、
承認された候補のhost/container/validatorの関連動作に適用する。
host-preliminaryおよびfinal-submissionの関係する処理を対象とし、
各mode固有の構造条件は別途指定するschemaに従う。

対象実装:
- scripts/run_witness_narrow_build.sh
- scripts/container_narrow_build.sh
- scripts/validate_witness_evidence.py
- 上記が生成・消費する関連Outcome/result tuple/evidence

適用対象はHumanが明示承認した候補revisionに限る。
基点の子孫であること、同じworktreeに存在すること、
同じファイル名であることだけでは適用承認を継承しない。

Contractに残るfuture rc5、Phase、実装予定の記述を変更しない。
候補への要求の採用は本記録とその承認によって明示し、
既存Contractが元から今回の候補に適用済みだったとは扱わない。

## 4. 採用する規範的要求

以下の参照は固定JSON内のJSON Pointerを示す。
要約ではなく、参照した要求本文を意味論の正本とする。

| 固定参照 | 候補が満たすべき要求 |
|---|---|
| /terminal_outcomes | 定義済み5種類のterminal outcomeと、それぞれのcargo・artifact・producer・tuple条件を維持する。 |
| /nonterminal_sentinels | 列挙されたsentinelをterminal outcomeとして受理しない。 |
| /producer_ownership | container、host、validator、shared identityの所有責任を維持する。 |
| /consumer_rules | missing/empty/duplicate/malformed/unsupportedをfail closedとし、矛盾を正規化して受理しない。 |
| /authoritative_result_tuple | 必須15フィールドの意味・所有者・許容値・成功条件を維持する。 |
| /overwrite_rules | 有効なcontainer outcomeを後続host失敗等で置換しない。失敗は所定の別結果で表現する。 |
| /inference_rules | outcomeを二次情報から推論・補完しない。欠落をINFRASTRUCTURE_FAILUREへ置換して構造を整えることも禁止する。 |
| /success_eligibility | 全要求の充足を必要とする。CARGO_SUCCEEDED_ARTIFACT_PRESENT単独でPASSやhost exit 0を認めない。 |
| /failure_rules | failure-only outcomeはPASS不適格とし、欠落・不正outcomeを成功へ補修しない。 |

terminal outcome:
- BUILD_NOT_STARTED
- CARGO_FAILED
- CARGO_SUCCEEDED_ARTIFACT_MISSING
- CARGO_SUCCEEDED_ARTIFACT_PRESENT
- INFRASTRUCTURE_FAILURE

INFRASTRUCTURE_FAILUREでは失敗owner/stageを明示する。
cargo_startedを一律NOにせず、既に生成されたcontainer事実を保持する。

必須result tuple:
schema_version、run_id、container_outcome、container_exit_code、
cargo_started、cargo_exit_code、artifact_present、
artifact_identity_complete、static_inspection_complete、
host_infrastructure_status、host_source_integrity_status、
post_build_integrity_status、evidence_completeness_status、
validator_status、machine_verdict_ceiling。

schema_version等のContract上の概念と、実際のevidence key・ファイルへの
対応はStage 2でtraceする。名称の類似だけで同一視しない。

## 5. 優先関係と役割分離

一律の「新しい文書がすべてに優先」という関係は設けない。

1. Human承認記録:
   候補revision、作業許可、適用範囲、責任者を決定する。
   実装許可と契約意味論の変更許可は別である。

2. 固定Outcome Contract:
   採用されたOutcome要求の意味論を規定する。
   本記録は許容outcome、ownership、成功条件を緩和・追加しない。

3. 本記録:
   候補への適用範囲と歴史的statusとの区別だけを規定する。
   Contract原本やRC8の判定を上書きしない。

4. Active schema/loader:
   schemas/canonical_schema_register_rc6.json、
   内部version rc6.5を継続利用する案とする。
   scripts/schema_register_loader.pyの明示選択に従い、
   evidence内容からactive authorityを選ばない。
   register version、evidence_schema_version=1、候補versionは別体系である。

5. Manifest:
   PACKAGE_FILE_MANIFEST.txtはpackageファイルinventory、
   WITNESS_PACKAGE_MANIFEST.mdはevidence要求等の文書、
   EVIDENCE_MANIFEST.sha256はrun evidenceのhash inventoryとして区別する。
   mode別構造条件は承認済みactive schemaと整合させる。
   文書や実装との不一致を黙示的な上書きで解消しない。

6. 実装・VALIDATOR.md・tests:
   要求への適合を実装・説明・検証する対象であり、
   現在の動作やtest PASSを理由にContract要求を再定義しない。

7. README・VERSION・LIFECYCLE・管理index:
   候補入口、identity、歴史的文脈、参照案内を担当する。
   これらの説明だけでContract applicabilityを変更しない。

候補文書の入口はwitness-package/README.mdとする案であり、
annotated tagによる実行時package identityとは区別する。
本記録はversion/tag対応表や実行時解決規則を変更しない。

## 6. 歴史的statusと既知違反

固定Contractの以下の値は原本に保持する。

- /contract_status:
  CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING
- /success_eligibility/implementation_status:
  contract_only_host_gating_not_yet_implemented
- /known_implementation_violations:
  下記2件ともUNRESOLVED_IMPLEMENTATION_VIOLATION、acceptable=false

| 違反ID | 原本の関連箇所・予定 | 候補における扱い |
|---|---|---|
| VALIDATOR_DETERMINE_OUTCOME_INFERENCE | /inference_rules/known_current_violation、determine_outcome、later_validator_slice | 対応義務を保持。候補での解消は未検証。 |
| HOST_OVERWRITES_CONTAINER_BUILD_EXIT_CODE | /overwrite_rules/known_current_violation、enforce_post_docker_source_integrity_boundary、Phase 3D | 対応義務を保持。候補での解消は未検証。 |

原本の実装状況の記述は、その固定記録の歴史的statusである。
それを削除・更新せず、候補の実装状況を別の証拠で示す。
既存修正やtestの存在から候補全体のcomplianceを推論しない。

/later_remediation_slicesと/blocker_status_noteは歴史的計画・状態を保持し、
今回のStage番号や新たなclosure条件へ自動変換しない。

候補runtime compliance: 未検証。
候補の適用除外: 本案では設けない。
本記録に記載されていない要求を黙示的に免除しない。

## 7. RC8・歴史版の除外境界

本記録はRC8およびRC1〜RC7の固定版へ遡及適用しない。
歴史的fixture/evidenceを使用しても、その歴史版を候補へ再分類しない。

RC8固定値:
- tag: grok-build-witness-v1.0.0-rc8
- annotated tag object: 8113d952d3b127d32e138dbf804141f5d1dfb26f
- peeled commit: 1de4b4d9523711418390f8331c95988523ef4481
- tree: 87b40d8a32ca536a4cdba0eee474f6171c62f6bb

タグ、原本、archive、bundle、sidecar、fixture、証拠を変更しない。

GOV-004のRC8最終判定NOT READY、
F-01〜F-04/B-01〜B-03のOPENを変更しない。
Independent Witness未承認、C-014 NOT_STARTED、RC9未承認を維持する。
別Source Weaver auditの実施・未実施を本記録から断定しない。

## 8. 配置・参照・証拠の境界

本記録は候補packageのルートに置くcandidate-native applicability正本。
一般管理indexや説明資料の複製を正本としない。

新規作成、README等からのリンク、候補package inventoryへの収載は、
それぞれ許可範囲を確認して実施する。
manifestへの収載が未反映の段階をpackage完成状態と表示しない。

本記録をrunのEVIDENCE_DIRへ投入しない。
closed evidence inventoryへの追加を暗黙に許可しない。
候補証拠の保存先・作成権限は別途承認する。

## 9. 停止条件

次の場合は適合・受入を宣言せず、影響する作業を停止してHumanへ戻す。

- 固定commit/path/blob/hashを確認できない。
- 候補revision、正式識別、承認範囲が不明または不一致。
- Contract内部、またはContract/schema/docs/implementation間で要求が競合する。
- ownership、tuple、mode、manifest適用を推測しなければ実装できない。
- 既知違反を証拠なしに解消済み・非適用とする必要が生じる。
- 意味論の変更や適用除外が必要になる。
- RC8固定資産、歴史版、dirty checkoutに影響する。
- 未承認ファイル・証拠出力・実行操作が必要になる。

適用除外が必要な場合は、対象条項、理由、対象revision、
影響、承認権限を特定した別の明示判断を要する。
技術的に実装しにくいことやtest失敗は免除理由としない。
意味論を変更するものはapplicabilityだけでは処理しない。

## 10. Stage境界と未決定事項

Stage 1で確定する事項:
- 本記録の正本配置・効力・採用承認。
- 正式Candidate識別と対象revisionの結び付け。
- 固定Contract、採用条項、対象component/mode。
- schema/manifest/validatorとの役割分離。
- 例外なしの原則、歴史的statusとの分離、停止条件。
- 未解消の解釈問題と、その判断主体。

明示的な解釈確認が必要な点:
Contractの/producer_ownershipはvalidator_statusをvalidator所有とする一方、
/overwrite_rules/required_future_representation/
host_owned_fields_on_failureにはvalidator_status=FAILEDも含まれる。
本記録はこの差を黙示的に解消せず、最終writer・host失敗通知との関係を
Humanが指定する技術判断主体へ確認する。
回答がContract意味論の変更を必要とする場合は別手続とし、
影響する実装を開始しない。

### validator_status所有権の個別設計判断 — Stage 1採用方針

上記の解釈確認事項は判断前の論点として保持する。その論点に対し、
Repository maintainerの今回の指示に基づき、Grok Buildの読み取り専用
限定技術レビュー判定Aを次のStage 1技術設計方針として記録する。
この個別判断時点では、別のFormal Source判定、Candidate Applicability全体の
正式採用、既存Contractの変更、実装・テストの許可を意味しなかった。
当時の先頭状態はPROPOSED — NOT ADOPTEDであり、今回の正式採用は第1節に区別する。

1. validator_statusの規範上の所有者・書込主体はValidatorであり、Hostではない。
   関連参照: /producer_ownership/validator_owns。
2. HostはHost所有の失敗状態を記録し、validator_statusを直接作成・上書きしない。
   関連参照: /producer_ownership/host_owns、
   /consumer_rules/no_component_may_overwrite_foreign_owned_field。
3. Validatorが実行された場合、Hostの失敗状態を評価し、契約上の失敗条件に
   該当すればValidator自身がvalidator_status=FAILEDを記録する。
   関連参照: /authoritative_result_tuple、/success_eligibility、
   /overwrite_rules/required_future_representation。
4. Validatorが未実行の場合、Hostはvalidator_status=FAILEDを合成しない。
   必須フィールドの欠落は既存のfail-closed規則に従い、成功を認めない。
   関連参照: /consumer_rules/missing_required_tuple_members、
   /authoritative_result_tuple、
   /success_eligibility/single_false_missing_duplicate_malformed_or_sentinel_in_required_success_field_prevents_success。
5. 有効なcontainer outcomeを後続Host失敗によって上書きしない。
   関連参照: /overwrite_rules/host_may_replace_valid_container_outcome、
   /producer_ownership/host_may_replace_container_outcome。
6. /overwrite_rules/required_future_representation/host_owned_fields_on_failure/validator_status
   のFAILEDは、Hostに所有権を移す意味ではなく、Validator評価後に求められる
   失敗表現として解釈する。
7. 本方針は前記限定技術レビューに基づくStage 1の個別設計判断であり、
   Formal Source評価、READY、finding closure、Stage 1完了を宣言しない。

machine_verdict_ceilingのHost失敗時の具体的値は未決定とし、推測で決めない。
関連参照: /producer_ownership/validator_owns、/authoritative_result_tuple。
既知違反2件の候補での解消・runtime complianceは引き続き未検証であり、
本判断によって既存ContractのstatusやRC8の判定・OPEN状態を変更しない。

Stage 2へ延期できる事項:
- 要求→実装symbol→実際のevidence field→testの対応。
- host/container/validatorの具体的差分。
- 2件の既知違反と成功gatingの候補での検証。
- mode別inventory、manifest totality、failure pathの検証。
- 許可済み環境でのtestと証拠取得。

要求の採否、authority、適用scopeそのものはStage 2へ先送りしない。
具体的なpackage manifest/入口の実体整合は既存Stage 3計画に従う。

## 11. 根拠資料

Repository内:
- PROJECT_CHARTER.md §7–8
- RC8_FREEZE_BOUNDARY.md §7/9/10
- CURRENT_CONTRACT_INDEX.md §5、CONTRACT-IDX-017
- GOV-004_RC8_FORMAL_SOURCE_EVALUATION_CLOSURE_RECORD.md §3–8
- RC8_FINAL_CLOSEOUT_AND_FUTURE_PLANNING_PACKAGE.md
  Category 3、F-03/B-02のremediation boundary
- 固定参照したAUTHORITATIVE_OUTCOME_CONTRACT.json
- scripts/schema_register_loader.py
- schemas/canonical_schema_register_rc6.json
- WITNESS_PACKAGE_MANIFEST.mdのmode別manifest方針

外部承認・設計資料:
- OWNER-LOCAL-PHASE2-TECHNICAL-DESIGN-20261126
- OWNER-LOCAL-PHASE2-AUTHORIZATION-PROPOSAL-20261126
  （提案書であり承認記録ではない）
- 本記録の正式採用承認: 冒頭のHuman Decision記録の後続決定追記（2026-11-27）

Stage 1技術的完了はRepository maintainer本人の承認として第1節に記録する。
本記録は正式Source評価、READY、finding closure、Independent Witnessを宣言しない。
Stage 2の実装・テスト・commit・pushは別途の明示承認まで禁止する。
