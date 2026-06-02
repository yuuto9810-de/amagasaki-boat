import streamlit as st
import pandas as pd

st.set_page_config(page_title="尼崎GANRIKI", page_icon="🎯", layout="wide")
st.title("🎯 尼崎特化 GANRIKI 解析エンジン")

# スクショ確認用の表示エリア（アップロードした画像を表示するだけ）
uploaded_file = st.file_uploader("出走表のスクショをここに貼ってください（確認用）", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="入力元データ")

# データ入力エリア（ここを埋めるのが最速です）
st.subheader("📋 階級とモーター勝率を入力")
df = pd.DataFrame({
    "艇番": [1, 2, 3, 4, 5, 6],
    "階級": ["B1", "B1", "A2", "B1", "A2", "A2"],
    "モーター": [27.7, 33.3, 27.5, 35.7, 31.0, 30.0]
})
edited_df = st.data_editor(df, hide_index=True)

# 予測エンジン（階級・モーター性能をスコア化）
if st.button("🚀 厳密解析を実行"):
    # スコア計算式: 階級ポイント(A1:3, A2:2, B1:1) + モーター率の偏差値
    def get_score(row):
        class_pts = {"A1": 3, "A2": 2, "B1": 1, "B2": 0}
        return class_pts.get(row["階級"], 0) * 10 + (row["モーター"] - 30)
    
    edited_df["スコア"] = edited_df.apply(get_score, axis=1)
    
    st.subheader("🎯 解析結果")
    st.table(edited_df.sort_values("スコア", ascending=False))
    
    # 買い目ロジック（スコア差で判定）
    top = edited_df.loc[edited_df["スコア"].idxmax()]
    st.write(f"最高スコア: {top['艇番']}号艇 ({top['スコア']:.1f}pt)")
