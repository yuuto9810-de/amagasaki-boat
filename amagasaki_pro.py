import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- ページ基本設定 ---
st.set_page_config(
    page_title="尼崎ボートGANRIKI",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 500px; padding-top: 1rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    .highlight-box { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #1f77b4; background-color: #f0f2f6; }
    </style>
""", unsafe_allow_html=True)

# 💡【ガチ修正】開催日に柔軟に対応する日付ロジック
# 基本は今日、もし取得に失敗したら「直近の開催データ」を自動的に追従させます
today = datetime.date.today()
date_url = today.strftime("%Y%m%d")
date_str = today.strftime("%Y年%m月%d日")

st.title("🎯 尼崎特化型 リアルタイム予測 GANRIKI")
st.caption("【プロ仕様】公式リアルタイムデータ完全連動システム")
st.markdown("---")

# --- 🛰️ 公式スクレイピング処理 (超強力クローラー仕様) ---
def fetch_html_with_retry(url, headers):
    """公式HPが重くても3回まで執念でリトライする関数"""
    for _ in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200 and "is-boatColor" in res.text:
                return res.text
        except:
            pass
    return None

@st.cache_data(ttl=10) # リアルタイム性を最優先にするためキャッシュを10秒に
def get_boatrace_official_data(race_num, target_date):
    jcd = "09" # 尼崎
    
    program_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_num}&jcd={jcd}&hd={target_date}"
    before_url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race_num}&jcd={jcd}&hd={target_date}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    
    racer_list = []
    weather = {"風向": "データ調整中", "風速": 0, "波高": 0}
    
    html_p = fetch_html_with_retry(program_url, headers)
    html_b = fetch_html_with_retry(before_url, headers)
    
    if not html_p:
        # 💡データが取れなかった場合、前日のデータを試す（夜間や早朝対策）
        alt_date = (datetime.datetime.strptime(target_date, "%Y%m%d") - datetime.timedelta(days=1)).strftime("%Y%m%d")
        program_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_num}&jcd={jcd}&hd={alt_date}"
        before_url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race_num}&jcd={jcd}&hd={alt_date}"
        html_p = fetch_html_with_retry(program_url, headers)
        html_b = fetch_html_with_retry(before_url, headers)
        if html_p:
            st.sidebar.info(f"💡 本日のレース時間外のため、直近({alt_date})のデータを表示しています。")
    
    if html_p:
        soup_p = BeautifulSoup(html_p, "html.parser")
        soup_b = BeautifulSoup(html_b, "html.parser") if html_b else None
        
        # --- 気象データの抽出 ---
        if soup_b:
            weather_box = soup_b.find("div", class_="weather1")
            if weather_box:
                txt = weather_box.get_text().replace("\n", "").replace(" ", "")
                w_speed = re.search(r"風速(\d+)m", txt)
                w_wave = re.search(r"波高(\d+)cm", txt)
                weather["風速"] = int(w_speed.group(1)) if w_speed else 0
                weather["波高"] = int(w_wave.group(1)) if w_wave else 0
                
                if "追い風" in txt: weather["風向"] = "追い風"
                elif "向かい風" in txt: weather["風向"] = "向かい風"
                elif "左横風" in txt: weather["風向"] = "左横風"
                elif "右横風" in txt: weather["風向"] = "右横風"
                else: weather["風向"] = "風平"

        # --- 6艇分のデータ抽出 ---
        tables = soup_p.find_all("tbody", class_=re.compile(r"is-boatColor"))
        
        for b in range(1, 7):
            name = f"取得中..."
            cls = "ーー"
            motor = 0.0
            ex_time = 6.75
            tilt = -0.5
            
            for t in tables:
                if f"is-boatColor{b}" in t.get("class", []):
                    name_tag = t.find("div", class_="is-name")
                    if name_tag and name_tag.find("a"):
                        name = name_tag.find("a").get_text().strip().replace(" ", "").replace("　", "")
                    class_tag = t.find("span", class_="is-class")
                    if class_tag:
                        cls = class_tag.get_text().strip()
                    
                    tds = t.find_all("td")
                    if len(tds) >= 10:
                        for td in tds:
                            td_txt = td.get_text().strip()
                            if "%" in td_txt:
                                try:
                                    motor = float(td_txt.replace("%", ""))
                                    break
                                except: pass
                    break

            if soup_b:
                b_tables = soup_b.find_all("tr")
                for row in b_tables:
                    tds = row.find_all("td")
                    if len(tds) >= 5 and tds[0].get_text().strip() == str(b):
                        try:
                            tilt = float(tds[2].get_text().strip())
                            ex_time = float(tds[4].get_text().strip())
                        except: pass
                        break
                        
            racer_list.append({
                "艇番": b,
                "選手名": name,
                "階級": cls,
                "展示タイム": ex_time,
                "チルト": tilt,
                "モーター2連率": motor
            })
        return pd.DataFrame(racer_list), weather
    else:
        # 完全にお手上げのときだけ出す最小限の仮枠
        return pd.DataFrame([{ "艇番": i, "選手名": "データ調整中", "階級": "A1", "展示タイム": 6.70, "チルト": -0.5, "モーター2連率": 40.0 } for i in range(1,7)]), weather

# --- UIレイアウト ---
race_num = st.selectbox("🔮 対象レースを選択", [i for i in range(1, 13)], index=0)

with st.spinner("🚀 BOATRACE公式HPから最新のリアルデータを同期中..."):
    df_racer, weather = get_boatrace_official_data(race_num, date_url)

# レースに登場するメイン選手名をヘッダーに表示して生存確認
top_player = df_racer.loc[df_racer["艇番"]==1, "選手名"].values[0]
st.subheader(f"📋 第 {race_num} レース 出走表・直前気配")

# 2. 直前気象情報の表示
st.markdown("### 🌤️ 直前気象ステータス")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="風向き", value=weather["風向"])
with col2:
    st.metric(label="風速", value=f"{weather.get('風速', 0)} m")
with col3:
    st.metric(label="波高", value=f"{weather.get('波高', 0)} cm")

# 3. 出走・直前展示データテーブル
st.dataframe(
    df_racer.set_index("艇番"),
    column_config={
        "選手名": st.column_config.TextColumn("選手名"),
        "展示タイム": st.column_config.NumberColumn("展示T", format="%.2f秒"),
        "モーター2連率": st.column_config.NumberColumn("モータ%", format="%.1f%%"),
    }
)

# --- 🧠 予測エンジン ---
st.markdown("---")
st.subheader("🏁 GANRIKI 展開予測・ガチ買い目")

in_edge_class = df_racer.loc[df_racer["艇番"]==1, "階級"].values[0]
in_edge_ex = df_racer.loc[df_racer["艇番"]==1, "展示タイム"].values[0]
min_ex_time = df_racer["展示タイム"].min()
best_ex_boats = df_racer[df_racer["展示タイム"] == min_ex_time]["艇番"].tolist()

base_in_escape_rate = 62.0 

if weather["風向"] == "向かい風":
    if weather.get('風速', 0) >= 6: base_in_escape_rate -= 18.5 
    elif weather.get('風速', 0) >= 3: base_in_escape_rate -= 5.0
elif weather["風向"] == "追い風":
    if weather.get('風速', 0) >= 5: base_in_escape_rate -= 12.0 
    else: base_in_escape_rate += 3.0 

if "A1" in in_edge_class: base_in_escape_rate += 15.0
elif "B" in in_edge_class: base_in_escape_rate -= 15.0

dangerous_out_boat = []
for idx, row in df_racer.iterrows():
    if row["艇番"] != 1 and (row["展示タイム"] <= in_edge_ex - 0.05):
        dangerous_out_boat.append(int(row["艇番"]))

if dangerous_out_boat:
    base_in_escape_rate -= 8.0 * len(dangerous_out_boat)

in_escape_rate = max(min(base_in_escape_rate, 95.0), 25.0)

st.write(f"**📊 1コース（{top_player}）の逃げ信頼度:**")
st.progress(int(in_escape_rate))
st.markdown(f"## 🎯 信頼度: `{in_escape_rate:.1f}%`")

st.markdown("### 💵 厳選フォーカス")
if top_player != "データ調整中":
    if in_escape_rate >= 65.0:
        st.markdown(f'<div class="highlight-box">📌 <b>【本命・イン逃げ濃厚】</b><br>1号艇 {top_player} 選手の機力・階級ともに上位。</div>', unsafe_allow_html=True)
        himo_boats = [2, 3, 4]
        for b in best_ex_boats:
            if b != 1 and b not in himo_boats: himo_boats.append(b)
        himo_str = ",".join(map(str, himo_boats[:3]))
        st.markdown("#### 🟢 3連単 本線")
        st.code(f"1 — {himo_str} — {himo_str}", language="text")
    else:
        st.markdown('<div class="highlight-box" style="border-left: 5px solid #ff4b4b;">⚠️ <b>【波乱含み・イン飛び警戒】</b><br>風向き、または外枠の展示タイムが強力です。</div>', unsafe_allow_html=True)
        target_boat = dangerous_out_boat[0] if dangerous_out_boat else 2
        st.markdown(f"#### 🔵 推奨穴フォーカス")
        st.code(f"{target_boat} — 1 — 流し\n{target_boat} — 3,4 — 流し", language="text")
else:
    st.info("※現在レース時間外か、尼崎での本日のレースが開催されていません。公式HPに当日の出走データが乗り次第、自動で買い目が生成されます。")
