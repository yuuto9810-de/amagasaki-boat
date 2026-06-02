import streamlit as st
import pandas as pd

# --- ページ基本設定 ---
st.set_page_config(
    page_title="尼崎ボートGANRIKI",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# スマホで見やすいようにデザインを最適化
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 500px; padding-top: 1rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    .highlight-box { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #1f77b4; background-color: #f0f2f6; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 尼崎特化型 予測エンジン GANRIKI")
st.caption("【実戦カスタム仕様】目の前のリアルデータ完全一致システム")
st.markdown("---")

# --- 📥 直前・出走情報の入力エリア ---
st.subheader("📋 本日の出走・直前気配を入力")
st.caption("公式HPの出走表や直前情報を見ながら、サクッと入力してください。")

# レース番号
race_num = st.selectbox("🔮 対象レース", [f"第 {i} レース" for i in range(1, 13)], index=0)

# 水面状況
st.markdown("##### 🌤️ 水面コンディション")
col_w1, col_w2 = st.columns(2)
with col_w1:
    in_weather = st.selectbox("風向き", ["追い風", "向かい風", "左横風", "右横風"], index=0)
with col_w2:
    in_wind_speed = st.slider("風速 (m)", 0, 10, 2)

st.markdown("##### 🚤 6艇の選手・直前情報")

racer_data = []
# 1〜6号艇の入力エリアをループで作成
for b in range(1, 7):
    with st.expander(f"枠番 {b} 号艇", expanded=(b==1)): # 1号艇だけ最初から開いておく
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            # 2回目以降の入力が楽になるよう、デフォルトは「選手B」のようにしておきます
            p_name = st.text_input(f"選手名 ({b}号艇)", value=f"選手 {b}", key=f"name_{b}")
        with c2:
            p_class = st.selectbox(f"階級", ["A1", "A2", "B1", "B2"], index=0 if b in [1, 4] else 2, key=f"class_{b}")
        with c3:
            p_motor = st.number_input(f"モーター2連率", min_value=0.0, max_value=100.0, value=40.0 if b==1 else 35.0, step=0.1, key=f"motor_{b}")
            
        c4, c5 = st.columns(2)
        with c4:
            p_ex = st.number_input(f"展示タイム", min_value=6.00, max_value=7.50, value=6.70, step=0.01, format="%.2f", key=f"ex_{b}")
        with c5:
            p_tilt = st.selectbox(f"チルト", [-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0], index=0, key=f"tilt_{b}")
            
    racer_data.append({
        "艇番": b,
        "選手名": p_name,
        "階級": p_class,
        "展示タイム": p_ex,
        "チルト": p_tilt,
        "モーター2連率": p_motor
    })

df_racer = pd.DataFrame(racer_data)

# --- 🧠 GANRIKI 予測エンジン ---
st.markdown("---")
st.subheader(f"🏁 {race_num} 展開予測・ガチ買い目")

top_player = df_racer.loc[df_racer["艇番"]==1, "選手名"].values[0]
in_edge_class = df_racer.loc[df_racer["艇番"]==1, "階級"].values[0]
in_edge_ex = df_racer.loc[df_racer["艇番"]==1, "展示タイム"].values[0]

min_ex_time = df_racer["展示タイム"].min()
best_ex_boats = df_racer[df_racer["展示タイム"] == min_ex_time]["艇番"].tolist()

# 尼崎イン逃げ基本値
base_in_escape_rate = 62.0 

# 風による影響の計算
if in_weather == "向かい風":
    if in_wind_speed >= 6: base_in_escape_rate -= 18.5 
    elif in_wind_speed >= 3: base_in_escape_rate -= 5.0
elif in_weather == "追い風":
    if in_wind_speed >= 5: base_in_escape_rate -= 12.0 
    else: base_in_escape_rate += 3.0 

# 1号艇の階級による影響
if "A1" in in_edge_class: base_in_escape_rate += 15.0
elif "B" in in_edge_class: base_in_escape_rate -= 15.0

# 1号艇より展示タイムが強烈に良い（まくりリスク）外枠のあぶり出し
dangerous_out_boat = []
for idx, row in df_racer.iterrows():
    if row["艇番"] != 1 and (row["展示タイム"] <= in_edge_ex - 0.05):
        dangerous_out_boat.append(int(row["艇番"]))

if dangerous_out_boat:
    base_in_escape_rate -= 8.0 * len(dangerous_out_boat)

in_escape_rate = max(min(base_in_escape_rate, 95.0), 25.0)

# 結果表示
st.write(f"**📊 1コース（{top_player}）の逃げ信頼度:**")
st.progress(int(in_escape_rate))
st.markdown(f"## 🎯 信頼度: `{in_escape_rate:.1f}%`")

st.markdown("### 💵 厳選フォーカス")
if in_escape_rate >= 65.0:
    st.markdown(f'<div class="highlight-box">📌 <b>【本命・イン逃げ濃厚】</b><br>1号艇 {top_player} 選手の条件が非常に良く、信頼できる水面コンディションです。</div>', unsafe_allow_html=True)
    # 相手候補（2, 3, 4番に展示トップを絡める）
    himo_boats = [2, 3, 4]
    for b in best_ex_boats:
        if b != 1 and b not in himo_boats: himo_boats.append(b)
    himo_str = ",".join(map(str, himo_boats[:3]))
    st.markdown("#### 🟢 3連単 本線")
    st.code(f"1 — {himo_str} — {himo_str}", language="text")
else:
    st.markdown('<div class="highlight-box" style="border-left: 5px solid #ff4b4b;">⚠️ <b>【波乱含み・イン飛び警戒】</b><br>風・階級・展示タイムのいずれかに不安要素があります。穴目を推奨します。</div>', unsafe_allow_html=True)
    target_boat = dangerous_out_boat[0] if dangerous_out_boat else 2
    st.markdown(f"#### 🔵 推奨穴フォーカス")
    st.code(f"{target_boat} — 1 — 流し\n{target_boat} — 3,4 — 流し", language="text")

# 入力されたデータの確認用テーブル
st.markdown("---")
st.caption("🔍 現在の入力データ一覧")
st.dataframe(df_racer.set_index("艇番"))
