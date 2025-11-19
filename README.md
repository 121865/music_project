# nschool — music_phase4

說明
-
此專案包含 `music_phase4.py`，用來處理 `Spotify_Youtube.csv` 的資料清理、補值、分群、以及多份圖表的產生。程式會把圖檔儲存在資料夾 `information`，並在執行結束時以多個獨立視窗同時顯示這些圖表（在終端按 Enter 關閉視窗與結束程式）。

主要功能
-
- 缺失值檢查與補值（Likes、Stream 等欄位）
- Valence（情緒）分箱並比較 Spotify / YouTube 的人氣趨勢
- 平衡抽樣（按情緒）比較平台人氣
- K-Means 分群與 PCA 投影視覺化
- 平台別分群比較與熱圖
- 各式圖表自動儲存到 `information` 資料夾
- 最後將每張圖以獨立視窗同時顯示，等待使用者在終端按 Enter 關閉

檔案位置
-
- 程式: `C:\Users\cj6ru8cl6\Desktop\nschool\music_phase4.py`
- 輸入 CSV (預設): `C:\Users\cj6ru8cl6\Desktop\nschool\Spotify_Youtube.csv`
- 圖片輸出資料夾: `C:\Users\cj6ru8cl6\Desktop\nschool\information`
- 依賴清單（如有）: `C:\Users\cj6ru8cl6\Desktop\nschool\requirements.txt`

先決條件
-
- Python 3.10+（專案在你的環境使用 Python 3.13 測試過）
- 建議使用虛擬環境（venv）在專案目錄下

快速安裝（PowerShell 範例）
-
在專案資料夾建立並啟用 venv（若尚未建立）:

```powershell
# 建立 venv（只需做一次）
C:\> cd 'C:\Users\cj6ru8cl6\Desktop\nschool'
C:\Users\cj6ru8cl6\Desktop\nschool> python -m venv .venv
# 啟用 venv
C:\Users\cj6ru8cl6\Desktop\nschool> .\.venv\Scripts\Activate.ps1
```

安裝依賴（若已有 `requirements.txt`）:

```powershell
(.venv) C:\Users\cj6ru8cl6\Desktop\nschool> .\.venv\Scripts\python.exe -m pip install --upgrade pip
(.venv) C:\Users\cj6ru8cl6\Desktop\nschool> .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

若沒有 `requirements.txt`，可手動安裝主要套件：

```powershell
(.venv) C:\Users\cj6ru8cl6\Desktop\nschool> .\.venv\Scripts\python.exe -m pip install pandas matplotlib seaborn scikit-learn pillow
```

如何執行
-
在 PowerShell（已啟用 venv）執行：

```powershell
(.venv) C:\Users\cj6ru8cl6\Desktop\nschool> .\.venv\Scripts\python.exe C:\Users\cj6ru8cl6\Desktop\nschool\music_phase4.py
```

執行時行為
-
- 程式會讀取預設 CSV（如需改路徑，請編輯 `music_phase4.py` 內 `main()` 中的 `csv_path` 變數）。
- 產生的圖檔會被存放到 `information` 資料夾（若不存在會自動建立）。
- 每張圖都會以獨立的 matplotlib 視窗開啟（同時顯示），程式會在終端印出提示「按 Enter 鍵以關閉所有視窗並結束程式...」。按下 Enter 後所有視窗才會關閉。

重要函式（程式內）
-
- `impute_likes_and_stream(df)`：補值 Likes 與 Stream 欄位。
- `plot_valence_trends(df)`：Valence 與平台人氣趨勢圖。
- `plot_pop_by_mood(df)`：按情緒平衡抽樣並比較平台人氣。
- `plot_clustering_overview(df)`：Elbow、KMeans、PCA 等整體分群流程與圖表。
- `plot_platform_specific_clusterings(df)`：分別對 Spotify/YouTube 做分群並畫熱圖、PCA。
- `plot_feature_correlations(df)`：欄位與人氣的相關係數與熱圖。
- `save_fig(name)`：將目前圖表儲存到 `information`，並把路徑加入內部清單以供最後顯示。
- `show_saved_images_nonblocking()`：將已存的每張 PNG 以獨立視窗同時顯示，並等待 Enter 關閉視窗。

**程式內容（資料處理方法）**
- **讀取與型別轉換**：使用 `pandas.read_csv()` 讀入 `Spotify_Youtube.csv`，針對常用欄位（如 `Likes`、`Views`、`Stream`、`Valence` 等）用 `pd.to_numeric(..., errors='coerce')` 轉為數值型別，將無法轉為數字的值變為 `NaN`，方便後續補值。
- **補值策略（`impute_likes_and_stream`）**：
	- `Likes`：先計算現有資料中 `Likes/Views` 的平均比率（只含 Views>0），再用該比率乘以 `Views` 去估算缺失的 `Likes`。結果四捨五入並轉成整數類型（`Int64`）。
	- `Stream`：對有 `Stream` 與 `Views` 的資料計算 `Stream/Views`，以同一 `Artist` 的中位數比率填補該藝人的缺失；若該藝人沒有可用比率，則使用全域中位數。
	- 補值完會再次列出缺失欄位數量，並保留原始缺失較多（如 `Description`、`Url_youtube`）的狀況供判讀。
- **數值變換**：
	- 為了降低極端值的影響，對 `Stream`、`Views` 使用 `log1p`（即 `np.log1p`）產生 `log_Stream` 與 `log_Views`。
	- 以分箱（10 等分，0~1）對 `Valence` 做群組（`valence_group`），並計算每箱的平均人氣數值（先做平台內 Min–Max 正規化）。
- **正規化**：`minmax()` 對給定序列做 0–1 線性縮放（若 min==max 或全 NaN 則回傳 0 向量），用於平台內比較（`norm_Stream`, `norm_Views`）。
- **平衡抽樣**：`balanced_sample_per_mood()` 會對三個情緒類別（Sad / Neutral / Happy）分組，各組隨機抽樣最多 `n` 筆，確保比較時每種情緒在樣本數上平衡。
- **分群分析（K-Means）**：
	- 對選定的音訊特徵（`Danceability, Energy, Speechiness, Acousticness, Instrumentalness, Liveness, Valence, Tempo`）先以中位數補缺（僅在平台別分群），再做 `StandardScaler` Z-score 標準化，接著使用 K-Means（預設 k=4）進行分群。
	- 使用 PCA（2 成分）將高維特徵投影到 2D 作為視覺化（散佈圖），並計算每群的平均特徵與平均人氣（log 轉換）以比較群間差異。
- **相關性分析**：計算各音訊特徵與人氣（Spotify 的 `Stream`、YouTube 的 `Views`）的 Pearson 相關係數，並用長條圖與熱圖視覺化。

**欄位（Columns）說明**
- **Artist**: 曲目或單位所屬藝人名稱。
- **Track / Title**: 歌曲名稱或曲目標題。
- **Channel**: 上傳頻道（通常為 YouTube 頻道名）。
- **Url_youtube**: YouTube 影片連結。
- **Views**: YouTube 的觀看次數（代表平台人氣）。
- **Stream**: Spotify 的串流次數（代表平台人氣）。
- **Likes**: YouTube 的按讚數（互動指標）。
- **Comments**: YouTube 的留言數（互動指標）。
- **Valence**: 音樂情緒分數（通常 0–1，數值越高表示越愉悅/正向）。
- **Danceability**: 舞曲性（0–1），表示可舞動程度。
- **Energy**: 能量（0–1），表示強度與活動度。
- **Speechiness**: 語音性比例（0–1），值越高代表語音/朗讀元素較多。
- **Acousticness**: 原音比例（0–1），值越高表示越偏原聲音色。
- **Instrumentalness**: 器樂化程度（0–1），高值表示較少人聲。
- **Liveness**: 現場感（0–1），高值通常代表錄音中包含現場表演特徵。
- **Tempo**: 節拍（BPM，數值）。
- **Duration_ms**: 曲長（毫秒）。
- **Key**: 調性（數值編碼），若有提供的話。
- **Loudness**: 音量（dB），通常為負值。
- **Licensed**, **official_video**: 版權或官方影片標記（若資料中有）。

**程式內重要參數與行為**
- `target_n`：平衡抽樣大小（程式預設 2500，表示每平台、每情緒最多抽 2500 筆）。
- `k`：K-Means 預設分群數（程式裡多處預設為 4，可改成先跑 Elbow 再選 k）。
- 圖檔儲存檔名：存於 `information`，檔名前有數字前綴以避免覆寫（例如 `01_spotify_valence_trend.png`）。

若要我把這段說明整合回 `README.md` 的特定位置或把欄位定義改成對應你手頭 CSV 的實際欄位名稱（若不同），我可以依你的檔案精確調整。 

可自訂的地方
-
- 若要變更輸入 CSV 路徑，可打開 `music_phase4.py`，在 `main()` 的 `csv_path` 參數修改預設值。
- 若要變更輸出資料夾，修改 `output_dir` 的值（程式頂部附近）。
- 若不希望程式寫入 PNG（僅在 memory 顯示），可改造 `save_fig()` 與 `show_saved_images_nonblocking()`，我可以協助修改。
- 若要自動 commit 或上傳圖檔，請告訴我你的 git 工作流程，我可以幫你加入範例指令。

疑難排解
-
- 出現 `ModuleNotFoundError`：請確認已啟用虛擬環境，並執行安裝命令（參見上方安裝步驟）。
- 圖片無法顯示：Windows 下請確認 matplotlib 的後端可開視窗（一般預設可用），若在遠端或 headless 環境會失敗。

聯絡/下一步
-
需要我幫你：
- 把 `requirements.txt` 加入 repo 並 commit（我可代為產生 commit）。
- 讓程式支援 CLI 參數（直接傳入 CSV 路徑）。
- 取消中間 PNG 檔改為直接 subplot 顯示以節省磁碟空間。

---
檔案已建立於 `C:\Users\cj6ru8cl6\Desktop\nschool\README.md`。

