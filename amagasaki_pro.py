import streamlit as st
import pandas as pd

st.set_page_config(page_title="尼崎GANRIKI", page_icon="🎯", layout="wide")
st.title("🎯 尼崎特化 GANRIKI 予測エンジン")

# アップロード機能
uploaded_file = st.file_uploader("出走表のスクショをここに貼ってください", type=["jpg", "png", "jpeg"])

# 初期データ
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "艇番": [1, 2, 3, 4, 5, 6], 
        "選手名": [""]*6, 
        "階級": ["B1"]*6, 
        "モーター率": [30.0]*6
    })

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 出走データ入力")
    st.session_state.df = st.data_editor(st.session_state.df, hide_index=True)

with col2:
    st.subheader("🏁 GANRIKI 予測")
    if st.button("予測実行"):
        df = st.session_state.df
        
        # --- 🚀 ここで計算ロジックを回します ---
        # 1号艇の強さを階級とモーターから算出
        in_power = 0
        if "A1" in df.loc[0, "階級"]: in_power += 30
        elif "A2" in df.loc[0, "階級"]: in_power += 20
        in_power += (df.loc[0, "モーター率"] - 30) * 0.5
        
        # 予測ロジック
        st.write(f"1号艇の総合パワー値: {in_power:.1f}")
        
        if in_power > 25:
            st.success(f"【本命】1 - 23 - 2345")
            st.caption("1号艇のランク・モーターが共に高水準。軸で狙える構成です。")
        elif in_power > 15:
            st.write(f"【混戦】1 - 3 - 245 / 3 - 1 - 245")
            st.caption("インは強いが、3コースの攻めが届く可能性あり。")
        else:
            st.error(f"【穴】3 - 4 - 全 / 4 - 3 - 全")
            st.caption("インが弱いため、中枠からの展開狙い。")
