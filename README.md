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
**實作流程與結果（依執行順序）**

1. 讀取資料與型別轉換
	- 使用 `pandas.read_csv()` 讀入 CSV，並對 `Likes`、`Views`、`Stream`、`Valence` 等欄位做 `pd.to_numeric(..., errors='coerce')`。
	- 範例輸出（缺失值檢查）會列印各欄缺失數量，範例：

```
▶ 前置處理後缺失值
Description         876
Stream              576
Comments            569
Likes               541
Url_youtube         470
...
```

2. Likes / Stream 補值（`impute_likes_and_stream`）
	- Likes：以現有 `Likes/Views` 比率估算缺失 `Likes`（只含 Views>0）。
	- Stream：計算每位 `Artist` 的 `Stream/Views` 中位數，優先用藝人中位數補值；若無則用全域中位數。
	- 範例輸出（補值統計）：

```
估計的 like_view_ratio = 0.012249
→ 依比例補 Likes 筆數：71
全域 Stream/Views 中位比例 = 3.158846
→ 依藝人比例補 Stream 筆數：555
```

3. 數值變換與正規化
	- 對人氣欄位使用 `np.log1p()`（產生 `log_Stream`、`log_Views`）以減少長尾影響。
	- 對平台內比較使用 Min–Max 正規化（`minmax()`），產生 `norm_Stream`、`norm_Views`（0–1）。

4. Valence 分箱與趨勢圖
	- 將 `Valence` 分為 10 箱，計算每箱平均人氣並繪製趨勢圖（Spotify / YouTube / 交叉比較）。

5. 平衡抽樣（情緒層級）與情緒比較圖
	- 使用 `balanced_sample_per_mood()` 在每個情緒類別（Sad / Neutral / Happy）中各抽樣最多 `target_n` 筆（範例 `target_n=2500`），以避免樣本不均造成偏誤。
	- 範例抽樣分佈輸出：

```
Spotify 抽樣分佈：
Happy / Positive      2500
Neutral / Moderate    2500
Sad / Negative        2500

YouTube 抽樣分佈：
Neutral / Moderate    2500
Happy / Positive      2500
Sad / Negative        2500
```

6. 分群分析（Elbow、K-Means、PCA）
	- 對音訊特徵做標準化（Z-score），以 `KMeans`（預設 k=4）分群並使用 PCA(2) 做視覺化投影。
	- 程式會產生 Elbow 圖幫助判斷群數，並列印每群平均特徵與群內平均人氣（log scale）。
	- 範例 PCA 輸出（整體）：

```
PCA explained variance ratio (overall): [0.30616254 0.1490607 ]
PCA loadings (components):
 PC1:
	Danceability: 0.4015
	Energy: 0.5030
	...
```

7. 平台別分群比較
	- 對 Spotify / YouTube 各自進行補值（median）、標準化、分群與 PCA，產生各平台的 heatmap 與 PCA 投影圖。
	- 範例群內人氣（log scale）輸出：

```
🎧 Spotify 各群平均人氣 (log1p Stream)：
0    19.045
1    18.774
2    18.305
3    18.673

📺 YouTube 各群平均人氣 (log1p Views)：
0    18.542
1    18.144
2    16.284
3    18.333
```

8. 特徵與人氣相關性分析
	- 計算每個音訊特徵與平台人氣（Stream / Views）之 Pearson 相關係數，並用長條圖 / 熱圖呈現。
	- 範例輸出（部分）：

```
🎯 音樂特徵與人氣的相關性比較：
						Spotify (Stream Corr)  YouTube (Views Corr)
Danceability                     -0.000                 0.089
Energy                            0.003                 0.068
...
```

9. 圖檔輸出與顯示
	- 所有圖檔會儲存在 `information` 資料夾（程式會自動建立），檔名前綴含順序編號，例如 `01_spotify_valence_trend.png`。
	- 程式最後會以獨立 matplotlib 視窗同時開啟所有已儲存的 PNG，並在終端等待使用者按 Enter 後關閉視窗。

以上順序即為 `music_phase4.py` 的主要執行流程；上面範例輸出來源於一次實際執行，實際數值會因 CSV 內容不同而改變。
**程式內容（資料處理方法）**

使用 `pandas.read_csv()` 讀入 `Spotify_Youtube.csv`，對下列流程做處理：

- 讀取與型別轉換：針對數值欄位（例：`Likes`, `Views`, `Stream`, `Valence` 等）使用 `pd.to_numeric(..., errors='coerce')`，把不能轉為數值的值設為 `NaN`，以利統一補值處理。

- 補值策略（`impute_likes_and_stream`）：
	- `Likes`：在有 `Views` 的資料中計算 `Likes/Views` 的比率（排除 `Views == 0`），以該比率乘回 `Views` 去估算缺失的 `Likes`，最後四捨五入並轉成整數型別（`Int64`）。
	- `Stream`：對每位 `Artist` 計算 `Stream/Views` 的中位數比率，若該藝人有可用比率則以藝人中位數補值，否則用全域中位數作為後備。
	- 補值後會再列出缺失值統計，以便判讀哪些欄位仍缺資料（例如 `Description`、`Url_youtube` 可能仍大量缺失）。

- 數值變換與正規化：
	- 為降低長尾影響，對人氣相關欄位使用 `np.log1p()` 產生 `log_Stream` / `log_Views`（用於群內平均比較或點大小顯示）。
	- 對平台內比較使用 Min–Max 正規化（`minmax()`），輸出 `norm_Stream` / `norm_Views`，範圍 0–1，方便在同一張圖上比較平台差異。

- Valence 分箱與平衡抽樣：
	- 將 `Valence`（0–1）分成固定數量的箱（預設 10 箱），每箱計算平均人氣以觀察情緒與人氣間的趨勢。
	- `balanced_sample_per_mood()` 會在每個情緒類別（Sad / Neutral / Happy）內隨機抽樣最多 `n` 筆（預設 `target_n`），以避免某情緒樣本過少造成偏誤。

- 分群與降維：
	- 對選定音訊特徵（例：`Danceability, Energy, Speechiness, Acousticness, Instrumentalness, Liveness, Valence, Tempo`）先以中位數補缺，再做 `StandardScaler` 標準化。
	- 使用 K-Means（預設 `k=4`）分群；另提供 Elbow 圖協助選擇適當的 `k`。
	- 使用 PCA（2 成分）做視覺化投影；在散佈圖中以群編號上色、以人氣（log1p）為點大小以利解釋群體的人氣差異。

	**PCA 補充（PC1 / PC2 與如何列印 loading）**

	PC1 與 PC2 分別為第一與第二主成分，代表資料中變異量最多與次多的方向。若要在程式中直接觀察每個主成分的「解釋變異比例（explained variance ratio）」與原始特徵的 loading（各特徵對主成分的權重），可以在 PCA 計算後列印，例如：

	```python
	# 假設 X_scaled 為 StandardScaler() 處理後的特徵矩陣，features 為特徵名稱列表
	from sklearn.decomposition import PCA
	pca = PCA(n_components=2)
	X_pca = pca.fit_transform(X_scaled)
	print('PCA explained variance ratio:', pca.explained_variance_ratio_)
	print('PC loadings (components):')
	for i, comp in enumerate(pca.components_, start=1):
	    print(f'PC{i}:')
	    for fname, val in zip(features, comp):
	        print(f'  {fname}: {val:.4f}')
	```

	輸出會列出 PC1 / PC2 各自解釋的變異比例（例如 0.42, 0.18），以及每個原始特徵在 PC1/PC2 上的 loading（正/負與大小），方便把 PCA 投影圖解釋為「哪些特徵的組合造成了該方向的變異」。

**範例數值（PC1 / PC2）**

下列為最近一次執行程式時產生的 PCA 範例數值，僅作示例用途 — 實際數值會依資料而異。第一表為每個主成分的解釋變異比例，第二表為各特徵在 PC1 / PC2 的 loading（權重）。

PCA 解釋變異比例（Explained Variance Ratio）

| 成分 | Explained variance ratio |
|---:|:---:|
| PC1 | 0.3062 |
| PC2 | 0.1491 |

PCA 各特徵 Loading（示例，取至小數點第四位）

| 特徵 | PC1 | PC2 |
|---|---:|---:|
| Danceability | 0.4015 | 0.5381 |
| Energy | 0.5030 | -0.3290 |
| Speechiness | 0.1672 | 0.1992 |
| Acousticness | -0.4616 | 0.2821 |
| Instrumentalness | -0.3842 | -0.1008 |
| Liveness | 0.0861 | -0.4583 |
| Valence | 0.4157 | 0.2530 |
| Tempo | 0.1303 | -0.4457 |

（註：若程式以平台分別計算 PCA，亦會列印各平台對應的 explained variance 與 loadings；可參考程式輸出作更細節解讀。）

- 相關性分析：
	- 計算每個音訊特徵與平台人氣（Spotify 的 `Stream`、YouTube 的 `Views`）間的 Pearson 相關係數，並以長條圖與熱圖呈現正/負相關強度。

**欄位（Columns）說明**

- `Artist`：曲目或作品所屬藝人。
- `Track` / `Title`：歌曲標題。
- `Channel`：YouTube 上傳頻道名稱。
- `Url_youtube`：YouTube 影片連結。
- `Views`：YouTube 觀看次數（整數）。
- `Stream`：Spotify 串流次數（整數）。
- `Likes`：YouTube 按讚數（整數）。
- `Comments`：YouTube 留言數（整數）。
- `Valence`：情緒分數（通常 0–1，越高表示越正向/愉悅）。
- `Danceability`、`Energy`、`Speechiness`、`Acousticness`、`Instrumentalness`、`Liveness`：常見 0–1 音訊特徵，代表音色/編曲特性。
- `Tempo`：節拍（BPM）。
- `Duration_ms`：曲長（毫秒）。
- `Key`：調性編碼（若資料提供）。
- `Loudness`：平均響度（dB，通常為負值）。
- `Licensed`、`official_video`：布林或標記類欄位，代表版權或是否官方影片（若資料提供）。

**產出圖表解說（每張圖的 X / Y 軸與讀法）**

- Valence 趨勢圖（`valence` vs 平台人氣）：
	- X 軸：`Valence` 分箱（範圍 0.0–1.0，預設分 10 箱）或箱中點值。
	- Y 軸：平台內 Min–Max 正規化人氣（`norm_Stream` 或 `norm_Views`），範圍 0–1；較高值代表相對於該平台其他曲目的高人氣。
	- 讀法：比較相同 Valence 位置上 Spotify 與 YouTube 的曲線差異，可看情緒與平台人氣偏好。

- 情緒（Mood）比較長條圖（平衡抽樣後）：
	- X 軸：情緒類別（`Sad`、`Neutral`、`Happy`）。
	- Y 軸：平均 `log1p` 人氣（Spotify 用 `Stream`、YouTube 用 `Views`）；以 log1p 減少極端值影響。
	- 讀法：條形高度顯示情緒對平均人氣的影響，誤差線（若有）表示群內變異。

- Elbow 圖（選擇 K 的依據）：
	- X 軸：群數 `k`。
	- Y 軸：K-Means 的 Inertia（SSE，平方和誤差）。
	- 讀法：尋找 Inertia 明顯減緩（肘點）的 `k` 作為合理群數候選。

- PCA 散佈圖（群內分布）：
	- X 軸 / Y 軸：第一與第二主成分（`PC1`, `PC2`），單位為標準化後的主成分得分。
	- 顏色：KMeans 分群編號；點大小：以 `log1p(popularity)` 表示（如 `log1p(Stream)` 或 `log1p(Views)`），以視覺化群內人氣差異。
	- 讀法：觀察群之間在主要變異方向上的分離與群內人氣集中情形。

- 族群特徵熱圖（cluster × feature）：
	- X 軸：音訊特徵名稱（例如 `Danceability`, `Energy`, …）。
	- Y 軸：群編號（Cluster 0,1,2,…）。
	- 色彩值：該群在該特徵上的平均值（通常為 z-score 或標準化後的平均），便於比較不同特徵在各群中的相對高低。
	- 讀法：找出每個群的特徵型態（例如高 Energy、低 Acousticness 的群），並與該群人氣一起解釋。

- 相關性長條圖 / 熱圖（feature vs popularity）：
	- X 軸（長條圖）：音訊特徵名稱；Y 軸：Pearson 相關係數 r（介於 -1 到 1），代表該特徵與平台人氣的線性相關強度。
	- 熱圖則以顏色呈現同樣的相關係數矩陣（行：特徵，列：人氣指標如 `log1p(Stream)` / `log1p(Views)`）。
	- 讀法：正值表正相關（特徵越高人氣越高），負值則代表負相關；數值大小表示相關強度。

以上產出多數會註明所用的人氣度量（`norm_*` vs `log1p(*)`），圖檔名稱中也含有說明（例如 `*_valence_trend.png`, `*_pca_clusters.png` 等），可依檔名前綴快速對應圖表內容。
