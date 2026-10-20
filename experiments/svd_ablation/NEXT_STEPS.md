# 核對後的下一步

舊版已完成 117 cases、23,400 筆 arm/repeat 結果，四份 CSV 的數值核對通過。
最後失敗點是來源雜湊檢查，並非某個 case 未完成。保留原始 CSV 與 metadata，
不要把 metadata 的 running 手動改成 complete。核對見 EXISTING_RUN_AUDIT.json
與 EXISTING_RUN_FINDINGS.md。這批可以保留作探索性結果；完整曲線與最終 ledger
hash 字典未保存，不能藉由本次核對補成完整的來源凍結驗證。

若只要初步回答 SVD 是否有幫助，現在已有小幅平均收益的證據，不必立即重跑。
若需要正式可重現版本，先 commit 凍結目前程式，再用剪枝新版跑到全新目錄。
以下指令由使用者自行執行；本次核對沒有啟動新的完整實驗，也沒有替使用者 commit。

在 repository 根目錄的 PowerShell：

```powershell
cd 'C:\Users\janet\Desktop\交換學生\machine translation\SAFE-EVAL\safe-eval'
$repo = (Get-Location).Path.Replace('\','/')
$branch = git -c "safe.directory=$repo" branch --show-current
if ($branch -ne 'experiment/svd-ablation') { throw '請先切到 experiment/svd-ablation' }

git -c "safe.directory=$repo" add -- experiments/svd_ablation
git -c "safe.directory=$repo" commit -m 'Add SVD ablation and audit dense-run results'
if ($LASTEXITCODE -ne 0) { throw '請先確認 commit 成功，再執行完整實驗' }

$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python experiments/svd_ablation/run_ablation.py --workers 2 --output experiments/svd_ablation/results_pruned_final
if ($LASTEXITCODE -ne 0) { throw '實驗尚未成功完成，請保留錯誤訊息' }

python experiments/svd_ablation/report.py --input experiments/svd_ablation/results_pruned_final --output experiments/svd_ablation/results_pruned_final/FINDINGS.md
if ($LASTEXITCODE -ne 0) { throw '結果報告核對失敗' }

git -c "safe.directory=$repo" add -- experiments/svd_ablation/results_pruned_final
git -c "safe.directory=$repo" commit -m 'Record completed pruned SVD ablation results'
```

若 results_pruned_final 已存在，換一個全新目錄名稱，同時修改 runner 與 report
的參數，不要覆寫舊結果。執行期間不要修改實驗程式。電腦睡眠時運算會暫停。
目前沒有背景實驗程序需要停止。
