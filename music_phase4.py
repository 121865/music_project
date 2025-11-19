import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
import seaborn as sns


# ==========================================
# music_phase4.py
# 主要用途：讀取 'Spotify_Youtube.csv'，做資料前處理、補值、分群(PCA+KMeans)、
# 與多張視覺化圖表產生（每張圖會儲存到 `information` 目錄，程式最後同時打開所有圖窗）。
# 這份檔案以函式化組織，重要的處理步驟皆有對應的 plot_*() 函式。
# 註解以中文說明主要行為與回傳值，方便維護與後續延伸。
# ==========================================


def summarize_missing(df, title="缺失值統計", max_rows=30):
    """
    列印資料框的缺失值數量（降序）。

    參數:
    - df: pandas.DataFrame
    - title: 印表標題字串
    - max_rows: 最多顯示多少個欄位（其餘以省略表示）
    回傳: None（印出結果供人工檢視）
    """
    print(f"\n▶ {title}")
    na = df.isna().sum()
    na = na[na > 0].sort_values(ascending=False)
    if na.empty:
        print("  ✅ 無缺失值")
    else:
        print(na.head(max_rows).to_string())
        if len(na) > max_rows:
            print(f"  ... 另有 {len(na) - max_rows} 欄省略")


def minmax(s: pd.Series) -> pd.Series:
    """
    簡單的 min-max 正規化函式，將序列縮放到 0–1 範圍。
    若序列全為常數或全為 NaN，則回傳值為 0 向量以避免除以零。
    """
    s = pd.to_numeric(s, errors="coerce")
    mn, mx = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(mn) or pd.isna(mx) or mn == mx:
        return pd.Series(np.zeros(len(s), dtype=float), index=s.index)
    return (s - mn) / (mx - mn)


def mood_category(v):
    """
    將 Valence（0–1）分為三個情緒類別：Sad, Neutral, Happy。
    回傳對應的字串標籤或 NaN（若輸入為 NaN）。
    """
    if pd.isna(v):
        return np.nan
    elif v < 0.33:
        return 'Sad / Negative'
    elif v < 0.66:
        return 'Neutral / Moderate'
    else:
        return 'Happy / Positive'


def balanced_sample_per_mood(d: pd.DataFrame, mood_col: str, n: int, value_cols, seed: int = 42):
    """
    對 d 依 mood_col 分組，每組最多取 n 筆樣本。
    value_cols 可為字串或字串列表；會一併保留。
    使用「隨機排序 + groupby().head(n)」，避免 apply 棄用警告。
    """
    # 支援傳入單一欄位或多欄位的情況
    if isinstance(value_cols, str):
        keep_cols = [mood_col, value_cols]
    else:
        keep_cols = [mood_col] + list(value_cols)

    # 使用 numpy 的 RNG 產生隨機排序欄位，避免直接用 sample() 在分群上導致不穩定
    rng = np.random.default_rng(seed)
    out = d[keep_cols].copy()
    out["__rand"] = rng.random(len(out))
    out = (
        out.sort_values("__rand")
           .groupby(mood_col, group_keys=False)
           .head(n)
           .drop(columns="__rand")
    )
    return out


def impute_likes_and_stream(df: pd.DataFrame) -> pd.DataFrame:
    """
    Likes：以 mean(likes/views) 估補（views>0，有限值）
    Stream：以每位 Artist 的 median(stream/views) 估補；無對應者用全域中位數
    """
    # 目標：盡量利用現有 Views、Artist 資訊，估算缺失的 Likes / Stream
    # 步驟：1) 將欄位轉數值 2) 計算 like/view 比率並補 Likes 3) 計算 artist-level stream/views 中位數並補 Stream
    for c in ["Likes", "Views", "Stream", "Valence"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Url_youtube" in df.columns:
        df["Url_youtube"] = df["Url_youtube"].astype("string")

    summarize_missing(df, "前置處理後缺失值")

    mask_ratio = df["Likes"].notna() & df["Views"].gt(0)
    tmp = df.loc[mask_ratio, ["Likes", "Views"]].copy()
    tmp["like_view_ratio"] = tmp["Likes"] / tmp["Views"]
    like_view_ratio = tmp.loc[np.isfinite(tmp["like_view_ratio"]), "like_view_ratio"].mean()

    print(f"\n估計的 like_view_ratio = {like_view_ratio:.6f}")
    cond_like = df["Likes"].isna() & df["Views"].gt(0)
    df.loc[cond_like, "Likes"] = df.loc[cond_like, "Views"] * like_view_ratio
    df["Likes"] = df["Likes"].round().astype("Int64")
    print(f"→ 依比例補 Likes 筆數：{int(cond_like.sum())}")

    g = df.loc[df["Stream"].notna() & df["Views"].gt(0), ["Artist", "Stream", "Views"]].copy()
    g["sv_ratio"] = g["Stream"] / g["Views"]
    sv = g.loc[np.isfinite(g["sv_ratio"]), ["Artist", "sv_ratio"]]
    artist_ratio = sv.groupby("Artist")["sv_ratio"].median()
    global_ratio = sv["sv_ratio"].median()
    print(f"全域 Stream/Views 中位比例 = {global_ratio:.6f}")

    cond_stream = df["Stream"].isna() & df["Views"].gt(0)
    to_fill = df.loc[cond_stream, ["Artist", "Views"]].copy()
    to_fill["ratio"] = to_fill["Artist"].map(artist_ratio).fillna(global_ratio)
    df.loc[cond_stream, "Stream"] = (to_fill["Views"] * to_fill["ratio"]).round()
    df["Stream"] = pd.to_numeric(df["Stream"], errors="coerce").astype("Int64")
    print(f"→ 依藝人比例補 Stream 筆數：{int(cond_stream.sum())}")

    summarize_missing(df, "補值後缺失值")
    return df


# 全域輸出設定（供各 plot 函式共用）
output_dir = r"C:\Users\cj6ru8cl6\Desktop\nschool\information"
os.makedirs(output_dir, exist_ok=True)
saved_images = []
_plot_counter = 0


def save_fig(name=None, dpi=150):
    """儲存目前的 matplotlib 圖表到 output_dir，並關閉當前 figure。
    name: 檔名 (可包含副檔名或不含)，會自動加上數字前綴避免覆寫。
    """
    global _plot_counter
    _plot_counter += 1
    if name is None:
        fname = f"{_plot_counter:02d}_plot.png"
    else:
        base = os.path.basename(name)
        fname = f"{_plot_counter:02d}_{base}"
    path = os.path.join(output_dir, fname)
    try:
        plt.tight_layout()
    except Exception:
        pass
    plt.savefig(path, dpi=dpi)
    saved_images.append(path)
    plt.close()
    return path

# ------------------------------------------
# 以下為多個圖表產生函式，皆採用 save_fig() 儲存檔案，
# 並以資料框或計算後的數值來繪圖。
# 每個函式內有較詳盡的程式流程註解，以利閱讀。
# ------------------------------------------


def plot_valence_trends(df: pd.DataFrame):
    """
    繪製 Valence（情緒）與平台人氣的趨勢圖：
    - 先計算 log1p 人氣、分箱 valence，並做平台內 minmax 正規化
    - 分別為 Spotify / YouTube 畫各自趨勢圖，最後畫交叉平台比較圖
    圖表會以 save_fig 儲存。
    """
    for c in ["Valence", "Stream", "Views"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["log_Stream"] = np.log1p(df.get("Stream"))
    df["log_Views"] = np.log1p(df.get("Views"))
    bins = np.linspace(0, 1, 11)
    labels = [f"{b:.1f}-{b+0.1:.1f}" for b in bins[:-1]]
    df["valence_group"] = pd.cut(df["Valence"], bins=bins, labels=labels, include_lowest=True)
    df["norm_Stream"] = minmax(df["log_Stream"])
    df["norm_Views"] = minmax(df["log_Views"])

    spotify_v_trend = df.groupby("valence_group", observed=True)["norm_Stream"].mean().reset_index()
    youtube_v_trend = df.groupby("valence_group", observed=True)["norm_Views"].mean().reset_index()

    plt.figure(figsize=(8, 4))
    plt.plot(spotify_v_trend["valence_group"], spotify_v_trend["norm_Stream"], marker="o", linewidth=2)
    plt.title("Spotify Popularity vs Valence (Normalized)")
    plt.xlabel("Valence (0–1, binned)")
    plt.ylabel("Average Popularity (0–1, normalized)")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    save_fig("01_spotify_valence_trend.png")

    plt.figure(figsize=(8, 4))
    plt.plot(youtube_v_trend["valence_group"], youtube_v_trend["norm_Views"], marker="o", linewidth=2)
    plt.title("YouTube Popularity vs Valence (Normalized)")
    plt.xlabel("Valence (0–1, binned)")
    plt.ylabel("Average Popularity (0–1, normalized)")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    save_fig("02_youtube_valence_trend.png")

    plt.figure(figsize=(8, 4))
    plt.plot(spotify_v_trend["valence_group"], spotify_v_trend["norm_Stream"], marker="o", label="Spotify")
    plt.plot(youtube_v_trend["valence_group"], youtube_v_trend["norm_Views"], marker="s", label="YouTube")
    plt.title("Cross-Platform Popularity vs Valence (Normalized)")
    plt.xlabel("Valence (0–1, binned)")
    plt.ylabel("Average Popularity (0–1, normalized)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    save_fig("03_crossplatform_valence_trend.png")


def plot_pop_by_mood(df: pd.DataFrame, target_n: int = 2500):
    """
    依 Valence 分類出的情緒（Sad/Neutral/Happy）做平衡抽樣後，
    比較 Spotify 與 YouTube 的平均人氣（以 log1p 減少極端值影響）。
    target_n 決定每個情緒每平台最多抽樣數。
    """
    df["Mood"] = df["Valence"].apply(mood_category)
    moods = ["Sad / Negative", "Neutral / Moderate", "Happy / Positive"]
    spotify_df = df.loc[df["log_Stream"].notna() & df["Mood"].notna(), ["Mood", "log_Stream"]].copy()
    youtube_df = df.loc[df["log_Views"].notna() & df["Mood"].notna(), ["Mood", "log_Views"]].copy()
    spotify_bal = balanced_sample_per_mood(spotify_df, "Mood", target_n, "log_Stream", seed=42)
    youtube_bal = balanced_sample_per_mood(youtube_df, "Mood", target_n, "log_Views", seed=42)
    print("\nSpotify 抽樣分佈："); print(spotify_bal["Mood"].value_counts().to_string())
    print("\nYouTube 抽樣分佈："); print(youtube_bal["Mood"].value_counts().to_string())
    spotify_bal_summary = spotify_bal.groupby("Mood")["log_Stream"].median().reindex(moods)
    youtube_bal_summary = youtube_bal.groupby("Mood")["log_Views"].median().reindex(moods)

    x = np.arange(len(moods)); width = 0.35
    plt.figure(figsize=(7, 4))
    plt.bar(x - width / 2, spotify_bal_summary.values, width, label="Spotify (balanced)")
    plt.bar(x + width / 2, youtube_bal_summary.values, width, label="YouTube (balanced)")
    plt.xticks(x, moods)
    plt.ylabel("Average Popularity (log scale)")
    plt.title(f"Cross-Platform Popularity by Mood (Balanced Sampling, n={target_n}/mood-platform)")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    save_fig("04_pop_by_mood.png")


def plot_clustering_overview(df: pd.DataFrame):
    """
    整體分群流程：
    - 選定音訊特徵，做中位數補值與 Z-score 標準化
    - 計算 Elbow 圖檢視 k 的選擇
    - 使用 KMeans 分群，並以 PCA(2) 投影做散佈視覺化
    - 列印每群平均音樂特徵與平均人氣
    """
    features = [
        "Danceability", "Energy", "Speechiness", "Acousticness",
        "Instrumentalness", "Liveness", "Valence", "Tempo"
    ]
    for c in features:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df_cluster = df[features + ["Artist", "Track", "Stream", "Views"]].dropna().copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster[features])

    inertia = []
    K_range = range(2, 9)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        km.fit(X_scaled)
        inertia.append(km.inertia_)

    plt.figure(figsize=(5, 3))
    plt.plot(list(K_range), inertia, marker="o")
    plt.title("Elbow Method for Optimal K")
    plt.xlabel("Number of Clusters (k)"); plt.ylabel("Inertia")
    plt.grid(True)
    save_fig("05_elbow_k.png")

    k = 4
    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    df_cluster["cluster"] = kmeans.fit_predict(X_scaled)
    pca = PCA(n_components=2)
    p2 = pca.fit_transform(X_scaled)
    df_cluster["pca1"] = p2[:, 0]; df_cluster["pca2"] = p2[:, 1]

    # 列印 PCA 診斷資訊：解釋變異比例與各特徵 loading（方便解釋 PC1 / PC2）
    try:
        print("\nPCA explained variance ratio (overall):", pca.explained_variance_ratio_)
        print("PCA loadings (components):")
        for i, comp in enumerate(pca.components_, start=1):
            print(f" PC{i}:")
            for fname, val in zip(features, comp):
                print(f"   {fname}: {val:.4f}")
    except Exception:
        pass

    plt.figure(figsize=(7, 5))
    for cid in sorted(df_cluster["cluster"].unique()):
        sub = df_cluster[df_cluster["cluster"] == cid]
        plt.scatter(sub["pca1"], sub["pca2"], s=12, alpha=0.6, label=f"cluster {cid}")
    plt.title("Song Clusters (PCA Projection)")
    plt.xlabel("PCA-1"); plt.ylabel("PCA-2")
    plt.legend(markerscale=2); plt.grid(True, alpha=0.3)
    save_fig("06_clusters_pca.png")

    cluster_features = df_cluster.groupby("cluster")[features].mean().round(3)
    print("\n各群平均音樂特徵：")
    print(cluster_features.to_string())
    cluster_pop = (df_cluster.groupby("cluster")[['Stream', 'Views']].mean().pipe(np.log1p).round(3))
    print("\n各群平均人氣 (log scale)：")
    print(cluster_pop.to_string())

    plt.figure(figsize=(7, 4))
    x = np.arange(k); width = 0.35
    plt.bar(x - width / 2, cluster_pop['Stream'].values, width, label="Spotify (Stream)")
    plt.bar(x + width / 2, cluster_pop['Views'].values, width, label="YouTube (Views)")
    plt.xticks(x, [f"C{cid}" for cid in range(k)])
    plt.ylabel("Average Popularity (log scale)")
    plt.title("Average Popularity by Cluster (log scale)")
    plt.legend(); plt.grid(axis="y", alpha=0.3)
    save_fig("07_avg_pop_by_cluster.png")


def plot_platform_specific_clusterings(df: pd.DataFrame):
    """
    對 Spotify 與 YouTube 分別做分群分析（以該平台有值的樣本為基礎）：
    - 以中位數補缺 + StandardScaler
    - 各平台分群後計算群內平均特徵並畫熱圖
    - 亦做 PCA 投影並畫分群散佈
    """
    features = [
        "Danceability", "Energy", "Speechiness", "Acousticness",
        "Instrumentalness", "Liveness", "Valence", "Tempo"
    ]
    for c in features:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    spotify_cluster = df[features + ["Stream"]].copy()
    spotify_cluster = spotify_cluster[spotify_cluster["Stream"].notna()]
    imp_sp = SimpleImputer(strategy="median")
    X_sp_filled = imp_sp.fit_transform(spotify_cluster[features])
    scaler_sp = StandardScaler()
    X_sp = scaler_sp.fit_transform(X_sp_filled)

    youtube_cluster = df[features + ["Views"]].copy()
    youtube_cluster = youtube_cluster[youtube_cluster["Views"].notna()]
    imp_yt = SimpleImputer(strategy="median")
    X_yt_filled = imp_yt.fit_transform(youtube_cluster[features])
    scaler_yt = StandardScaler()
    X_yt = scaler_yt.fit_transform(X_yt_filled)

    k = 4
    kmeans_sp = KMeans(n_clusters=k, random_state=42, n_init=10)
    spotify_cluster["cluster_sp"] = kmeans_sp.fit_predict(X_sp)
    kmeans_yt = KMeans(n_clusters=k, random_state=42, n_init=10)
    youtube_cluster["cluster_yt"] = kmeans_yt.fit_predict(X_yt)

    sp_features = (
        pd.DataFrame(X_sp_filled, columns=features, index=spotify_cluster.index)
          .assign(cluster_sp=spotify_cluster["cluster_sp"])
          .groupby("cluster_sp")[features].mean().round(3)
    )
    yt_features = (
        pd.DataFrame(X_yt_filled, columns=features, index=youtube_cluster.index)
          .assign(cluster_yt=youtube_cluster["cluster_yt"])
          .groupby("cluster_yt")[features].mean().round(3)
    )
    print("\n🎧 Spotify 各群平均特徵：")
    print(sp_features.to_string())
    print("\n📺 YouTube 各群平均特徵：")
    print(yt_features.to_string())
    sp_pop = spotify_cluster.groupby("cluster_sp")["Stream"].mean().pipe(np.log1p).round(3)
    yt_pop = youtube_cluster.groupby("cluster_yt")["Views"].mean().pipe(np.log1p).round(3)
    print("\n🎧 Spotify 各群平均人氣 (log1p Stream)：")
    print(sp_pop.to_string())
    print("\n📺 YouTube 各群平均人氣 (log1p Views)：")
    print(yt_pop.to_string())

    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    sns.heatmap(sp_features, cmap="YlGnBu", annot=True, fmt=".2f")
    plt.title("Spotify Cluster Feature Means")

    plt.subplot(1, 2, 2)
    sns.heatmap(yt_features, cmap="YlOrRd", annot=True, fmt=".2f")
    plt.title("YouTube Cluster Feature Means")
    save_fig("08_cluster_feature_heatmaps.png")

    pca_sp = PCA(n_components=2, random_state=42)
    pca_yt = PCA(n_components=2, random_state=42)
    sp_p2 = pca_sp.fit_transform(X_sp)
    yt_p2 = pca_yt.fit_transform(X_yt)
    spotify_cluster["pca1"], spotify_cluster["pca2"] = sp_p2[:, 0], sp_p2[:, 1]
    youtube_cluster["pca1"], youtube_cluster["pca2"] = yt_p2[:, 0], yt_p2[:, 1]
    # 列印平台別 PCA 診斷資訊
    try:
        print("\nSpotify PCA explained variance ratio:", pca_sp.explained_variance_ratio_)
        print("Spotify PCA loadings:")
        for i, comp in enumerate(pca_sp.components_, start=1):
            print(f" PC{i}:")
            for fname, val in zip(features, comp):
                print(f"   {fname}: {val:.4f}")
    except Exception:
        pass
    try:
        print("\nYouTube PCA explained variance ratio:", pca_yt.explained_variance_ratio_)
        print("YouTube PCA loadings:")
        for i, comp in enumerate(pca_yt.components_, start=1):
            print(f" PC{i}:")
            for fname, val in zip(features, comp):
                print(f"   {fname}: {val:.4f}")
    except Exception:
        pass
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    sns.scatterplot(data=spotify_cluster, x="pca1", y="pca2",
                    hue="cluster_sp", palette="Set2", s=15, alpha=0.6)
    plt.title("Spotify Clusters (PCA Projection)")
    plt.legend(title="Cluster", markerscale=2)

    plt.subplot(1, 2, 2)
    sns.scatterplot(data=youtube_cluster, x="pca1", y="pca2",
                    hue="cluster_yt", palette="Set1", s=15, alpha=0.6)
    plt.title("YouTube Clusters (PCA Projection)")
    plt.legend(title="Cluster", markerscale=2)
    save_fig("09_pca_platforms.png")


def plot_feature_correlations(df: pd.DataFrame):
    """
    計算特徵（features）與人氣（Stream / Views）之間的 Pearson 相關係數，
    並生成長條圖與熱圖以視覺化比較。
    """
    features = ["Danceability", "Energy", "Valence", "Tempo",
                 "Acousticness", "Instrumentalness", "Speechiness"]
    spotify_corr = df[features + ["Stream"]].corr()["Stream"].drop("Stream")
    youtube_corr = df[features + ["Views"]].corr()["Views"].drop("Views")
    corr_compare = pd.DataFrame({
        "Spotify (Stream Corr)": spotify_corr,
        "YouTube (Views Corr)": youtube_corr
    }).round(3)
    print("🎯 音樂特徵與人氣的相關性比較：")
    print(corr_compare)
    corr_compare.plot(kind="bar", figsize=(8, 4))
    plt.title("Feature–Popularity Correlation by Platform")
    plt.ylabel("Correlation (Pearson r)")
    plt.grid(axis="y", alpha=0.3)
    save_fig("10_feature_pop_corr.png")
    yt_corr = df[["Likes", "Comments"] + features].corr()
    sns.heatmap(yt_corr.loc[["Likes", "Comments"], features], annot=True, cmap="coolwarm")
    plt.title("YouTube Interaction vs Audio Features")
    save_fig("11_yt_interaction_vs_features.png")


def show_saved_images_nonblocking():
    # 每張圖各自開視窗並同時顯示（非匯集成一張圖）
    if saved_images:
        plt.ion()
        figs = []
        for img_path in saved_images:
            try:
                img = Image.open(img_path)
                fig = plt.figure(figsize=(6, 4))
                ax = fig.add_subplot(111)
                ax.imshow(img)
                ax.axis('off')
                ax.set_title(os.path.basename(img_path))
                figs.append(fig)
            except Exception:
                fig = plt.figure(figsize=(4, 3))
                fig.text(0.5, 0.5, 'Failed to load', ha='center')
                figs.append(fig)
        plt.show(block=False)
        try:
            input("所有圖表已開在獨立視窗。按 Enter 鍵以關閉所有視窗並結束程式...\n")
        except Exception:
            pass
        plt.close('all')


# main() 為程式主入口，負責讀取 CSV、呼叫各處理/繪圖函式，最後顯示已儲存的圖檔
def main(csv_path: str = r"C:\Users\cj6ru8cl6\Desktop\nschool\Spotify_Youtube.csv"):
    df = pd.read_csv(csv_path)
    df = impute_likes_and_stream(df)
    plot_valence_trends(df)
    plot_pop_by_mood(df)
    plot_clustering_overview(df)
    plot_platform_specific_clusterings(df)
    plot_feature_correlations(df)
    show_saved_images_nonblocking()


if __name__ == "__main__":
    # 確保 output 目錄存在（save_fig 依賴）
    os.makedirs(output_dir, exist_ok=True)
    main()

