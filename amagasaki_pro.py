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
date_url = today.strftime("%y%m%d") # 例: "260602"
date_str = today.strftime("%Y年%m月%d日")

st.title("🎯 尼崎特化型 リアルタイム予測 GANRIKI")
st.subheader(f"📅 開催日: {date_str}")
st.caption("【完全自動・場識別対応】公式ZIP番組表データ完全連動モデル")
st.markdown("---")

# --- 🛰️ ZIP内の全ファイルを走査する完全版クローラー ---
@st.cache_data(ttl=1800)
def get_official_zip_text_all(target_date):
    """公式HPからZIPを落とし、中のテキストファイルをすべて結合して1つの巨大なテキストにする"""
    url = f"https://www.boatrace.jp/owpc/pc/extra/data/program/b{target_date}.zip"
    combined_text = ""
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        
        # ZIPファイルをメモリ上で展開
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            # ZIP内の全てのファイルをループで漏れなくチェックする
            for filename in z.namelist():
                if filename.endswith('.txt') or filename.startswith('b'):
                    with z.open(filename) as f:
                        # 各場のテキストをShift-JISでデコードして結合
                        combined_text += f.read().decode('cp932', errors='ignore') + "\n"
        return combined_text if combined_text else None
    except:
        return None

def parse_amagasaki_zip_perfect(raw_text, target_race):
    """結合テキストから尼崎(09#)を確実に狙い撃ちして、指定レースの6名を切り出す"""
    if not raw_text:
        return None
        
    lines = raw_text.split('\n')
    racer_list = []
    is_amagasaki = False
    race_found = False
    boat_count = 0
    
    for line in lines:
        clean_line = line.replace('\r', '')
        
        # 尼崎（場コード09#）のエリアが始まったか判定
        if "09#" in clean_line or ("尼崎" in clean_line and "番組表" in clean_line):
            is_amagasaki = True
            continue
            
        # 尼崎セクションの中にいる時だけ処理
        if is_amagasaki:
            # 他の競馬場・競艇場のコード（例: "10#"など）が来たら尼崎は終了
            if "#" in clean_line and "09#" not in clean_line:
                is_amagasaki = False
                break
                
            # 目的のレース（例: "11R" または " 1R"）の開始行を探す
            race_label = f"{target_race:2d}R" if target_race >= 10 else f" {target_race}R"
            if race_label in clean_line and "🎯" not in clean_line and "🔍" not in clean_line:
                race_found = True
                boat_count = 0
                racer_list = [] # 念のため初期化
                continue
                
            # 該当レースを見つけている最中の処理
            if race_found:
                # 別のレース番号（例：次のレースなど）のヘッダーが来たら解析終了
                if "R" in clean_line and race_label not in clean_line and len(clean_line) < 15:
                    race_found = False
                    break
                    
                # 1〜6号艇のデータ行を正規表現でガッチリキャッチ
                # 行の先頭が数字の1〜6で始まっている行を狙い撃ち
                match = re.match(r'^\s*([1-6])', clean_line)
                if match and boat_count < 6:
                    try:
                        boat_num = int(match.group(1))
                        
                        # 公式データの固定長レイアウトを正確にスライス
                        racer_name = clean_line[2:12].replace(" ", "").replace("　", "").strip()
                        racer_class = clean_line[12:15].strip()
                        
                        # モーター2連率の抽出（行の後半にある2連率の％数字を抽出）
                        motor_part = clean_line[25:38].strip()
                        motor_rate = 0.0
                        rate_match = re.search(r'(\d+\.\d+)', motor_part)
                        if rate_match:
                            motor_rate = float(rate_match.group(1))
                            
                        racer_list.append({
                            "艇番": boat_num,
                            "選手名": racer_name,
                            "階級": racer_class if racer_class in ["A1","A2","B1","B2"] else "B1",
                            "展示タイム": 6.70 + (boat_num * 0.01), # 直前調整用の初期値
                            "チルト": 0.0,
                            "モーター2連率": motor_rate
                        })
                        boat_count += 1
                    except:
                        pass

    if len(racer_list) == 6:
        return pd.DataFrame(racer_list)
    return None

# --- UI配置・処理実行 ---
race_num = st.selectbox("🔮 対象レースを選択", [i for i in range(1, 13)], index=0)

# 🚀 ZIPまるごと走査トリガー発動
full_text = get_official_zip_text_all(date_url)
df_racer = parse_amagasaki_zip_perfect(full_text, race_num)

# 万が一、朝が早すぎて公式ファイル自体がまだ無い場合やエラー時の最終バックアップ
if df_racer is None:
    st.error("公式番組表データの解析に失敗しました。本日、尼崎の開催がないか、公式HPのデータが更新中の可能性があります。")
    st.stop()

st.markdown("### 🛠️ 直前情報の微調整")
st.caption("公式ZIPから尼崎のテキストファイルを完全に特定し、自動復元に成功しました！")

col_w1, col_w2, col_ex = st.columns(3)
with col_w1:
    in_weather = st.selectbox("風向き", ["追い風", "向かい風", "左横風", "右横風"], index=0)
with col_w2:
    in_wind_speed = st.slider("風速 (m)", 0, 10, 2)
with col_ex:
    base_in_ex = float(df_racer.loc[df_racer["艇番"]==1, "展示タイム"].values[0])
    in_display_time = st.number_input("1号艇の展示タイム", value=base_in_ex, min_value=6.00, max_value=7.50, step=0.01, format="%.2f")

# リアルタイム入力された展示タイムを1号艇に上書き
df_racer.loc[df_racer["艇番"]==1, "展示タイム"] = in_display_time

st.markdown("---")
st.subheader(f"📋 第 {race_num} レース 出走表・直前気配")

# 出走表表示
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
