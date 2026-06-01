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

today = datetime.date.today()
date_url = today.strftime("%Y%m%d")
date_str = today.strftime("%Y年%m月%d日")

st.title("🎯 尼崎特化型 リアルタイム予測 GANRIKI")
st.subheader(f"📅 開催日: {date_str}")
st.caption("【プロ仕様】公式リアルタイムデータ完全連動システム")
st.markdown("---")

# --- 🛰️ 公式スクレイピング処理 ---
@st.cache_data(ttl=30)  # 直前情報なのでキャッシュは30秒
def get_boatrace_official_data(race_num):
    # 尼崎の場コードは「09」
    jcd = "09"
    
    # 1. 出走表（選手名・階級・モーター）の取得
    program_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_num}&jcd={jcd}&hd={date_url}"
    # 2. 直前情報（展示タイム・チルト・気象）の取得
    before_url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race_num}&jcd={jcd}&hd={date_url}"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # 配列の初期化
    racer_list = []
    weather = {"風向": "無風", "風速": 0, "波高": 0}
    
    try:
        # 出走表の解析
        res_p = requests.get(program_url, headers=headers, timeout=5)
        soup_p = BeautifulSoup(res_p.text, "html.parser")
        
        # 直前情報の解析
        res_b = requests.get(before_url, headers=headers, timeout=5)
        soup_b = BeautifulSoup(res_b.text, "html.parser")
        
        # --- 気象データの抽出 ---
        weather_box = soup_b.find("div", class_="weather1")
        if weather_box:
            txt = weather_box.get_text()
            # 風速、波高を正規表現で抽出
            w_speed = re.search(r"風速\s*(\d+)m", txt)
            w_wave = re.search(r"波高\s*(\d+)cm", txt)
            weather["风速"] = int(w_speed.group(1)) if w_speed else 0
            weather["波高"] = int(w_wave.group(1)) if w_wave else 0
            
            if "追い風" in txt: weather["風向"] = "追い風"
            elif "向かい風" in txt: weather["風向"] = "向かい風"
            elif "左横風" in txt: weather["風向"] = "左横風"
            elif "右横風" in txt: weather["風向"] = "右横風"

        # --- 6艇分のデータ抽出 ---
        for b in range(1, 7):
            # 選手名と階級の取得（出走表から）
            # 公式のHTML構造に合わせてクラス名等から抽出
            name = f"レーサー{b}"
            cls = "B1"
            motor = 30.0
            
            p_body = soup_p.find_all("tbody", class_=f"is-boatColor{b}")
            if p_body:
                name_tag = p_body[0].find("div", class_="is-name")
                if name_tag:
                    name = name_tag.find("a").get_text().replace(" ", "").replace("　", "")
                class_tag = p_body[0].find("span", class_="is-class")
                if class_tag:
                    cls = class_tag.get_text()
                # モーター2連率
                motor_tags = p_body[0].find_all("td")
                if len(motor_tags) > 7:
                    motor_txt = motor_tags[7].get_text()
                    try: motor = float(motor_txt)
                    except: pass

            # 展示タイムとチルトの取得（直前情報から）
            ex_time = 6.75
            tilt = -0.5
            b_rows = soup_b.find_all("tr")
            # 展示タイムテーブルの解析
            for row in b_rows:
                tds = row.find_all("td")
                if len(tds) >= 4 and tds[0].get_text() == str(b):
                    try:
                        ex_time = float(tds[4].get_text())
                        tilt = float(tds[2].get_text())
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
    except Exception as e:
        # 万が一公式がメンテナンス中やエラー時のためのフォールバック
        st.error("公式HPからのデータ取得に失敗しました。開催時間外か、メンテ中の可能性があります。")
        return pd.DataFrame([{ "艇番": i, "選手名": f"取得失敗({i})", "階級": "B1", "展示タイム": 6.70, "チルト": -0.5, "モーター2連率": 30.0 } for i in range(1,7)]), weather

# --- UIレイアウト ---
race_num = st.selectbox("🔮 対象レースを選択", [i for i in range(1, 13)], index=0)

with st.spinner("🚀 BOATRACE公式HPからリアルタイム直前データを取得中..."):
    df_racer, weather = get_boatrace_official_data(race_num)

# 2. 直前気象情報の表示
st.markdown("### 🌤️ 直前気象ステータス")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="風向き", value=weather["風向"])
with col2:
    st.metric(label="風速", value=f"{weather.get('風速', 0)} m", delta="強風注意" if weather.get('風速', 0)>=6 else None, delta_color="inverse")
with col3:
    st.metric(label="波高", value=f"{weather.get('波高', 0)} cm")

# 3. 出走・直前展示データテーブル
st.markdown("### 📋 本日の出走表・直前展示")
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

if in_edge_class == "A1": base_in_escape_rate += 15.0
elif "B" in in_edge_class: base_in_escape_rate -= 15.0

dangerous_out_boat = []
for idx, row in df_racer.iterrows():
    if row["艇番"] != 1 and (row["展示タイム"] <= in_edge_ex - 0.05):
        dangerous_out_boat.append(int(row["艇番"]))

if dangerous_out_boat:
    base_in_escape_rate -= 8.0 * len(dangerous_out_boat)

in_escape_rate = max(min(base_in_escape_rate, 95.0), 25.0)

st.write(f"**📊 1コース（{df_racer.loc[df_racer['艇番']==1, '選手名'].values[0]}）の逃げ信頼度:**")
st.progress(int(in_escape_rate))
st.markdown(f"## 🎯 信頼度: `{in_escape_rate:.1f}%`")

st.markdown("### 💵 厳選フォーカス")
if in_escape_rate >= 65.0:
    st.markdown('<div class="highlight-box">📌 <b>【本命・イン逃げ濃厚】</b><br>尼崎のセオリー通りの水面。1号艇の機力・階級ともに上位。</div>', unsafe_allow_html=True)
    himo_boats = [2, 3, 4]
    for b in best_ex_boats:
        if b != 1 and b not in himo_boats: himo_boats.append(b)
    himo_str = ",".join(map(str, himo_boats[:3]))
    st.markdown("#### 🟢 3連単 本線")
    st.code(f"1 — {himo_str} — {himo_str}", language="text")
else:
    st.markdown('<div class="highlight-box" style="border-left: 5px solid #ff4b4b;">⚠️ <b>【波乱含み・イン飛び警戒】</b><br>風向き、または外枠の展示タイムが強烈。波乱展開。</div>', unsafe_allow_html=True)
    target_boat = dangerous_out_boat[0] if dangerous_out_boat else 2
    st.markdown(f"#### 🔵 推奨穴フォーカス")
    st.code(f"{target_boat} — 1 — 流し\n{target_boat} — 3,4 — 流し", language="text")
