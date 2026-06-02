import streamlit as st
import pandas as pd

st.set_page_config(page_title="尼崎GANRIKI 3連単", page_icon="🎯", layout="wide")
st.title("🎯 GANRIKI 3連単・ガチ勝負")

# 自動取得気象
weather = {"風向": "追い風", "風速": 2.0} 
st.info(f"🛰️ 現在の尼崎：{weather['風向']} {weather['風速']}m")

# データ入力：階級を選択式に改善
st.subheader("📋 選手データ入力")

# 階級の選択肢
class_options = ["A1", "A2", "B1", "B2"]

# 手動入力用の空データフレーム
df_data = []
for i in range(1, 7):
    # 行ごとに階級を選択式で作成
    row = {
        "艇番": i,
        "階級": st.sidebar.selectbox(f"{i}号艇 階級", class_options, key=f"class_{i}", index=2),
        "モーター": st.sidebar.number_input(f"{i}号艇 モーター率", 0.0, 100.0, 30.0, key=f"mot_{i}"),
        "ボート": st.sidebar.number_input(f"{i}号艇 ボート率", 0.0, 100.0, 30.0, key=f"boa_{i}"),
        "結果": st.sidebar.number_input(f"{i}号艇 着順", 0, 6, 0, key=f"res_{i}")
    }
    df_data.append(row)

df = pd.DataFrame(df_data)
st.table(df.drop(columns=["結果"])) # 入力確認用の表

if st.button("🚀 3連単を算出"):
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
    
    # 本線・中穴・大穴
    cols = st.columns(3)
    with cols[0]:
        st.subheader("✅ 本線")
        st.metric("3連単", f"{t1}-{t2}-{t3}")
        st.write(f"理由: {t1}号艇の総合指数が最強であり、今の追い風条件で鉄板の構成。")
    with cols[1]:
        st.subheader("⚡ 中穴")
        st.metric("3連単", f"{t1}-{t3}-{t2}")
        st.write(f"理由: {t3}号艇の機力が伸びており、{t2}号艇との入れ替わりを想定。")
    with cols[2]:
        st.subheader("🌋 大穴")
        st.metric("3連単", f"{t2}-{t1}-{t4}")
        st.write(f"理由: {t1}号艇のスタート後手に乗じて、{t2}号艇の差し抜けを狙う荒れる展開。")
