import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from datetime import datetime
from tabulate import tabulate
import concurrent.futures
import webbrowser

# ======== データ取得する直近試合数を設定 ========
while True:
    try:
        MAX_GAMES = int(input("何試合分を集計しますか？（1〜100）→ "))
        if 1 <= MAX_GAMES <= 100:
            break
        else:
            print("1以上100以下の数字を入力してください！")
    except ValueError:
        print("整数を入力してください！")

# ======== ベースURL ========
base_url = "https://baseball.yahoo.co.jp"
schedule_url = f"{base_url}/npb/teams/4/schedule"

# ======== 終了試合URL取得関数 ========
def get_finished_game_urls(soup):
    game_urls = []
    for link in soup.find_all("a"):
        href = link.get("href", "")
        if "/game/" in href and "index" in href and "試合終了" in link.text:
            if href.startswith("http"):
                stats_url = href.replace("/index", "/stats")
            else:
                stats_url = base_url + href.replace("/index", "/stats")
            game_urls.append(stats_url)
    return game_urls

# ======== 月をさかのぼって試合URLを集める（前年には突入しない） ========
game_links = []
today = datetime.today()
current_month = today.month

loops = 0

while len(game_links) < MAX_GAMES:
    if loops == 0:
        target_url = schedule_url
        target_month = current_month
    else:
        target_month = current_month - loops
        if target_month < 1:
            break  # 今年の1月より前には行かない

    if loops != 0:
        month_text = f"{target_month}月"
        response = requests.get(schedule_url)
        soup = BeautifulSoup(response.text, "html.parser")
        month_link = None
        for link in soup.find_all("a"):
            if link.text.strip() == month_text and "/schedule" in link.get("href", ""):
                month_link = link["href"]
                break

        if month_link:
            target_url = base_url + month_link
        else:
            break

    response = requests.get(target_url)
    soup = BeautifulSoup(response.text, "html.parser")
    urls = get_finished_game_urls(soup)
    game_links += urls

    loops += 1

# ======== 最新順に並べて MAX_GAMES に切り詰め ========
game_links = sorted(list(set(game_links)), reverse=True)
game_links = game_links[:MAX_GAMES]

# ======== 並列取得関数 ========
def get_game_data(url):
    res = requests.get(url)
    html = res.text
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag else "タイトル不明"
    title = title.split(" - ")[0]
    dfs = pd.read_html(StringIO(html))

    if "中日" in dfs[2].to_string():
        dragons_df = dfs[1]
        print(f"{url} → {title} テーブル1から取得！")
    elif "中日" in dfs[3].to_string():
        dragons_df = dfs[4]
        print(f"{url} → {title} テーブル4から取得！")
    else:
        print(f"スキップ: {url} は中日ドラゴンズの試合ではありません。")
        return None

    if "選手" in dragons_df.columns and "選手名" not in dragons_df.columns:
        dragons_df = dragons_df.rename(columns={"選手": "選手名"})

    cols = [c for c in ["選手名", "打数", "安打", "打点", "三振", "四球", "死球", "犠打"] if c in dragons_df.columns]
    if len(cols) < 5:
        print(f"列不足: {url}")
        return None

    dragons_df = dragons_df[cols].fillna(0)
    for col in cols[1:]:
        dragons_df[col] = pd.to_numeric(dragons_df[col], errors="coerce").fillna(0)

    return dragons_df

# ======== 並列で取得 ========
all_games_df = pd.DataFrame()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(get_game_data, game_links))

dfs_valid = [df for df in results if df is not None]
if dfs_valid:
    all_games_df = pd.concat(dfs_valid, ignore_index=True)

# 実際に集計できた試合数を取得
collected_games = len([r for r in results if r is not None])

# ======== 集計 ========
if all_games_df.empty:
    print("\n有効な試合データがありません！")
    exit()

grouped = all_games_df.groupby("選手名").sum().reset_index()
grouped = grouped[grouped["選手名"] != "合計"]
grouped["選手名"] = grouped["選手名"].str.replace(r"\s+\d+$", "", regex=True)
grouped = grouped[
    ~(
        (grouped["打数"] == 0) & (grouped["四球"] == 0) &
        (grouped["死球"] == 0) & (grouped["犠打"] == 0)
    )
]

grouped["打率"] = grouped["安打"] / grouped["打数"]
grouped["出塁率"] = (grouped["安打"] + grouped["四球"] + grouped["死球"]) / (
    grouped["打数"] + grouped["四球"] + grouped["死球"] + grouped["犠打"]
)

grouped["打率"] = grouped["打率"].fillna(0.0).apply(lambda x: f"{x:.3f}")
grouped["出塁率"] = grouped["出塁率"].fillna(0.0).apply(lambda x: f"{x:.3f}")

grouped = grouped[["選手名", "打数", "安打", "打点", "打率", "出塁率", "三振", "犠打", "四球", "死球"]]
grouped = grouped.sort_values(by="安打", ascending=False)

print(tabulate(grouped.head(100), headers='keys', tablefmt='github', showindex=False))

# ======== HTMLに出力して Chromeで開く（実際の件数を反映） ========
html_table = grouped.head(100).to_html(index=False, border=1)

html_output = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>中日ドラゴンズ 集計結果</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    padding: 20px;
  }}
  table {{
    border-collapse: collapse;
    width: auto;
    max-width: 100%;
  }}
  th, td {{
    border: 1px solid #aaa;
    padding: 8px 12px;
    text-align: right;
    white-space: nowrap;
  }}
  th {{
    background-color: #f2f2f2;
  }}
  td:first-child {{
    text-align: left;
  }}
</style>
</head>
<body>
<h1>中日ドラゴンズ 集計結果（最新 {collected_games} 試合）</h1>
{html_table}
</body>
</html>
"""

with open("result.html", "w", encoding="utf-8") as f:
    f.write(html_output)

webbrowser.open("result.html")
