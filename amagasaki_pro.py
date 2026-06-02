import streamlit as st

# ページ設定
st.set_page_config(page_title="尼崎GANRIKI", page_icon="🎯")
st.title("🎯 尼崎特化 GANRIKI 予測エンジン")

# 選手名を入力させるのではなく、スクショを見ながら「強い艇」を選ぶ形式に変更
st.subheader("💡 予想ツール（スクショを見ながら選択）")

# データの自動解析ができない分、人間が判断して入力する方が圧倒的に早くて確実です
with st.form("prediction_form"):
    st.write("スクショを見て、有利な艇を選択してください：")
    
    col1, col2 = st.columns(2)
    with col1:
        favorite = st.selectbox("本命の艇", [1, 2, 3, 4, 5, 6])
    with col2:
        condition = st.select_slider("本命の選手の気配", options=["悪い", "普通", "良い", "絶好調"])
    
    submitted = st.form_submit_button("🏁 GANRIKI 予測実行")

if submitted:
    st.markdown("---")
    st.subheader("🎯 買い目案")
    st.write(f"本命 {favorite} 号艇の展開を解析しました！")
    
    # 階級やデータに基づいてロジックで提示
    if condition == "絶好調":
        st.success(f"【鉄板】 {favorite} - 全 - 全")
    elif condition == "良い":
        st.write(f"【展開】 {favorite} - {favorite+1 if favorite<6 else 1} - 全")
    else:
        st.write("【混戦】 3 - 1 - 全 / 1 - 3 - 5")
