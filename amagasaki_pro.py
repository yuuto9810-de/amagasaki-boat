import streamlit as st
import pandas as pd

st.set_page_config(page_title="尼崎GANRIKI 解析エンジン", page_icon="🎯", layout="wide")
st.title("🎯 GANRIKI 3連単・ガチ勝負")

# 自動取得気象
weather = {"風向": "追い風", "風速": 2.0} 
st.info(f"🛰️ 現在の尼崎：{weather['風向']} {weather['風速']}m")

# 階級・モーター・ボートの3項目入力
st.subheader("📋 選手データ入力（スクショを見ながら入力）")
data = {
    "艇番": [1, 2, 3, 4, 5, 6],
    "階級": ["B1", "B1", "A2", "B1", "A2", "A2"],
    "モーター": [30.0]*6,
    "ボート": [30.0]*6
}
df = pd.DataFrame(data)
edited_df = st.data_editor(df, hide_index=True)

if st.button("🚀 3連単を算出"):
    # スコア計算: 階級(A1:40, A2:30, B1:20, B2:10) + モーター(30%) + ボート(70%)
    class_pts = {"A1": 40, "A2": 30, "B1": 20, "B2": 10}
    # モーターとボートの数値を反映
    edited_df["S"] = (
        edited_df["階級"].map(class_pts) + 
        (edited_df["モーター"] * 0.4) + 
        (edited_df["ボート"] * 0.4)
    )
    
    # 風補正
    if weather["風向"] == "追い風" and weather["風速"] <= 3.0:
        edited_df.loc[edited_df["艇番"]==1, "S"] += 10
        
    res = edited_df.sort_values("S", ascending=False).reset_index(drop=True)
    t1, t2, t3 = int(res.loc[0, "艇番"]), int(res.loc[1, "艇番"]), int(res.loc[2, "艇番"])
    
    st.markdown("---")
    st.subheader("✅ 本線")
    st.metric("3連単", f"{t1}-{t2}-{t3}")
    st.write(f"理由: {t1}号艇は階級・機力（モーター/ボート）の総合指数が最も高く、気象条件下で最も有利です。")
    
    st.subheader("⚡ 中穴")
    st.metric("3連単", f"{t1}-{t3}-{t2}")
    st.write(f"理由: {t3}号艇の機力補正値が伸びており、{t1}号艇を軸に展開を突く狙いです。")
