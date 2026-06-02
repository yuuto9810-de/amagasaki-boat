import streamlit as st
import pandas as pd
import requests
import datetime
import zipfile
import io
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
date_url = today.strftime("%y%m%d") # "260602"
date_str = today.strftime("%Y年%m月%d日")

st.title("🎯 尼崎特化型 リアルタイム予測 GANRIKI")
st.subheader(f"📅 開催日: {date_str}")
st.caption("【完全自動】スペース・文字ズレ完全克服最終モデル")
st.markdown("---")

# --- 🛰️ 公式ZIPダウンロード処理 ---
@st.cache_data(ttl=1800)
def get_official_dataset(target_date):
    """公式HPからZIPを落とし、中のファイルを確実に全結合してテキスト化する"""
    url = f"https://www.boatrace.jp/owpc/pc/extra/data/program/b{target_date}.zip"
    combined_text = ""
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            for filename in z.namelist():
                with z.open(filename) as f:
                    combined_text += f.read().decode('cp932', errors='ignore') + "\n"
        return combined_text
    except:
        return None

def parse_amagasaki_by_pattern(raw_text, target_race):
    """不規則な全角半角スペースを完全に無効化してデータをぶち抜く"""
    if not raw_text:
        return None
        
    lines = raw_text.split('\n')
    racer_list = []
    
    is_amagasaki = False
    current_race = None
    
    for line in lines:
        clean_line = line.replace('\r', '').strip()
        if not clean_line:
            continue
            
        # 尼崎セクション（09#）の検知
        if "09#" in clean_line:
            is_amagasaki = True
            continue
        # 別の場（10#など）が始まったら尼崎終了
        if is_amagasaki and "#" in clean_line and "09#" not in clean_line:
            is_amagasaki = False
            break
            
        if is_amagasaki:
            # レース番号（例: 11R や 1R）の検知
            race_match = re.search(r'^\s*(\d+)\s*R', clean_line)
            if race_match:
                current_race = int(race_match.group(1))
                continue
                
            if current_race != target_race:
                continue
                
            # 💡【最終解】全角・半角スペースがどれだけ暴れても、文字の「パターン」だけで狙い撃ち
            # 先頭が艇番(1-6) → 任意の空白 → 4桁の登録番号 → 空白 → 選手名 → 空白 → 階級(A1-B2)
            boat_match = re.search(r'^([1-6])\s*(\d{4})\s*([^\sA-B]+)\s*(A1|A2|B1|B2)', clean_line)
            if boat_match:
                try:
                    boat_num = int(boat_match.group(1))
                    racer_name = boat_match.group(3).replace(" ", "").replace("　", "").strip()
                    racer_class = boat_match.group(4)
                    
                    # モーター2連率（行の後半にある「数字.数字」を抽出）
                    rates = re.findall(r'(\d+\.\d+)', clean_line)
                    motor_rate = float(rates[-1]) if len(rates) >= 2 else 30.0
                    
                    if not any(r['艇番'] == boat_num for r in racer_list):
                        racer_list.append({
                            "艇番": boat_num,
                            "選手名": racer_name,
                            "階級": racer_class,
                            "展示タイム": 6.70 + (boat_num * 0.01), # 展示初期値
                            "チルト": 0.0,
                            "モーター2連率": motor_rate
                        })
                except:
                    pass

    if len(racer_list) == 6:
        return pd.DataFrame(racer_list).sort_values("艇番")
    return None

# --- UI配置・処理実行 ---
race_num = st.selectbox("🔮 対象レースを選択", [i for i in range(1, 13)], index=0)

full_text = get_official_dataset(date_url)
df_racer = parse_amagasaki_by_pattern(full_text, race_num)

if df_racer is None:
    st.error("【通信完了】公式データファイルの解析パターンが一致しません。本日、尼崎ボートは非開催（場外発売のみ）の可能性があります。開催スケジュールをご確認ください。")
    st.stop()

st.markdown("### 🛠️ 直前情報の微調整")
st.caption("全角スペースの壁を突破し、本日開催の【本物のデータ】の自動同期に成功しました！")

col_w1, col_w2, col_ex = st.columns(3)
with col_w1:
    in_weather = st.selectbox("風向き", ["追い風", "向かい風", "左横風", "右横風"], index=0)
with col_w2:
    in_wind_speed = st.slider("風速 (m)", 0, 10, 2)
with col_ex:
    base_in_ex = float(df_racer.loc[df_racer["艇番"]==1, "展示タイム"].values[0])
    in_display_time = st.number_input("1号艇の展示タイム", value=base_in_ex, min_value=6.00, max_value=7.50, step=0.01, format="%.2f")

df_racer.loc[df_racer["艇番"]==1, "展示タイム"] = in_display_time

st.markdown("---")
st.subheader(f"📋 第 {race_num} レース 出走表・直前気配")

# 出走表テーブル表示
st.dataframe(df_racer.set_index("艇番"))

# --- 🧠 GANRIKI 予測エンジン ---
st.markdown("---")
st.subheader("🏁 GANRIKI 展開予測・ガチ買い目")

top_player = df_racer.loc[df_racer["艇番"]==1, "選手名"].values[0]
in_edge_class = df_racer.loc[df_racer["艇番"]==1, "階級"].values[0]
in_edge_ex = df_racer.loc[df_racer["艇番"]==1, "展示タイム"].values[0]
min_ex_time = df_racer["展示タイム"].min()
best_ex_boats = df_racer[df_racer["展示タイム"] == min_ex_time]["艇番"].tolist()

base_in_escape_rate = 62.0 
if in_weather == "向かい風":
    if in_wind_speed >= 6: base_in_escape_rate -= 18.5 
    elif in_wind_speed >= 3: base_in_escape_rate -= 5.0
elif in_weather == "追い風":
    if in_wind_speed >= 5: base_in_escape_rate -= 12.0 
    else: base_in_escape_rate += 3.0 

if "A1" in in_edge_class: base_in_escape_rate += 15.0
elif "B" in in_edge_class: base_in_escape_rate -= 15.0

in_escape_rate = max(min(base_in_escape_rate, 95.0), 25.0)

st.write(f"**📊 1コース（{top_player}）の逃げ信頼度:**")
st.progress(int(in_escape_rate))
st.markdown(f"## 🎯 信頼度: `{in_escape_rate:.1f}%`")

st.markdown("### 💵 厳選フォーカス")
himo_boats = [2, 3, 4]
for b in best_ex_boats:
    if b != 1 and b not in himo_boats: himo_boats.append(b)
himo_str = ",".join(map(str, himo_boats[:3]))

st.code(f"1 — {himo_str} — {himo_str}", language="text")
