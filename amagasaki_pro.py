import streamlit as st
import pandas as pd

st.set_page_config(page_title="尼崎GANRIKI", page_icon="🎯", layout="wide")
st.title("🎯 GANRIKI 3連単・ガチ勝負")

# 自動取得（ダミー）
weather = {"風向": "追い風", "風速": 2.0} 
st.info(f"🛰️ 現在の尼崎：{weather['風向']} {weather['風速']}m")

# データ初期化（エラー回避のため、すべての列をここで定義）
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "艇番": [1, 2, 3, 4, 5, 6],
        "階級": ["B1"]*6,
        "モーター": [30.0]*6,
        "ボート": [30.0]*6,
        "1着": [False]*6,
        "2着": [False]*6,
        "3着": [False]*6
    })

# 階級の選択UI
st.subheader("📋 選手データ入力")
cols = st.columns(6)
for i in range(6):
    st.session_state.df.at[i, "階級"] = cols[i].selectbox(f"{i+1}号艇", ["A1", "A2", "B1", "B2"], key=f"c{i}", index=2)

# 数値入力（全列を明示的に指定してエラーを回避）
st.session_state.df = st.data_editor(
    st.session_state.df, 
    hide_index=True,
    column_config={
        "階級": st.column_config.TextColumn(disabled=True), # セレクトボックスで選ぶので入力不可に
        "艇番": st.column_config.NumberColumn(disabled=True)
    }
)

if st.button("🚀 3連単を算出"):
    df = st.session_state.df
    # スコア計算
    class_pts = {"A1": 40, "A2": 30, "B1": 20, "B2": 10}
    df["S"] = (
        df["階級"].map(class_pts) + 
        (df["モーター"] * 0.4) + 
        (df["ボート"] * 0.4)
    )
    
    # 風補正
    if weather["風向"] == "追い風" and weather["風速"] <= 3.0:
        df.loc[df["艇番"]==1, "S"] += 10
        
    res = df.sort_values("S", ascending=False).reset_index(drop=True)
    t1, t2, t3, t4 = int(res.loc[0, "艇番"]), int(res.loc[1, "艇番"]), int(res.loc[2, "艇番"]), int(res.loc[3, "艇番"])
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.subheader("✅ 本線"); c1.metric("3連単", f"{t1}-{t2}-{t3}"); c1.write("指数トップ。鉄板。")
    c2.subheader("⚡ 中穴"); c2.metric("3連単", f"{t1}-{t3}-{t2}"); c2.write("機力重視の差しパターン。")
    c3.subheader("🌋 大穴"); c3.metric("3連単", f"{t2}-{t1}-{t4}"); c3.write("イン遅れ想定の逆転劇。")
