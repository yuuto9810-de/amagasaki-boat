import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="尼崎GANRIKI 3連単特化", page_icon="🎯", layout="wide")

st.title("🎯 GANRIKI 3連単・ガチ勝負")

# --- 1. 自動取得：気象情報のシミュレーション ---
# 尼崎のリアルタイム風向・風速を取得する想定
weather = {"風向": "追い風", "風速": 2.0} 
st.info(f"🛰️ 現在の尼崎気象：{weather['風向']} {weather['風速']}m")

# --- 2. 手動入力：選手データ ---
st.subheader("📋 選手データ入力（スクショを見ながら入力）")
# 階級・モーター性能はスクショの値をここに入力
data = {
    "艇番": [1, 2, 3, 4, 5, 6],
    "階級": ["B1", "B1", "A2", "B1", "A2", "A2"],
    "モーター": [27.7, 33.3, 27.5, 35.7, 31.0, 30.0]
}
df = pd.DataFrame(data)
edited_df = st.data_editor(df, hide_index=True)

# --- 3. 解析ロジック ---
if st.button("🚀 3連単を算出"):
    # スコア計算
    class_pts = {"A1": 30, "A2": 20, "B1": 10, "B2": 0}
    edited_df["S"] = edited_df["階級"].map(class_pts) + (edited_df["モーター"] * 0.5)
    
    # 風速による補正
    if weather["風向"] == "追い風" and weather["風速"] <= 3.0:
        edited_df.loc[edited_df["艇番"]==1, "S"] += 15
    
    res = edited_df.sort_values("S", ascending=False).reset_index(drop=True)
    t1, t2, t3 = int(res.loc[0, "艇番"]), int(res.loc[1, "艇番"]), int(res.loc[2, "艇番"])
    
    # 理由生成
    def get_reason(n1, n2, n3, is_main):
        if is_main:
            return f"{n1}号艇が階級・モーター性能で上位であり、{weather['風向']}の条件下でインの信頼度が高い。{n2}号艇が実力で追走。"
        else:
            return f"{n3}号艇の気配が良く、{n2}号艇の攻めを活かして展開が向く中穴パターン。"

    st.markdown("---")
    
    # 本線
    st.subheader("✅ 本線（可能性重視）")
    st.metric("3連単", f"{t1}-{t2}-{t3}")
    st.write(f"**理由**: {get_reason(t1, t2, t3, True)}")
    
    # 中穴
    st.subheader("⚡ 中穴（配当狙い）")
    st.metric("3連単", f"{t1}-{t3}-{t2}")
    st.write(f"**理由**: {get_reason(t1, t3, t2, False)}")
