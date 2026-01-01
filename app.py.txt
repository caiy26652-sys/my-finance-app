import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 設定頁面
st.set_page_config(page_title="個人理財助手", layout="wide")
st.title("💰 我的私人記帳 App")

# 模擬資料庫 (實際使用時可連結 CSV 或資料庫)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['日期', '類型', '分類', '金額', '帳戶'])

# --- 側邊欄：輸入資料 ---
st.sidebar.header("新增紀錄")
date = st.sidebar.date_input("日期", datetime.now())
t_type = st.sidebar.selectbox("類型", ["支出", "收入"])
category = st.sidebar.selectbox("分類", ["餐飲", "交通", "購物", "娛樂", "薪水", "其他"])
amount = st.sidebar.number_input("金額", min_value=0)
account = st.sidebar.selectbox("帳戶", ["現金", "銀行卡", "悠遊卡"])

if st.sidebar.button("提交紀錄"):
    new_entry = pd.DataFrame([[date, t_type, category, amount, account]], 
                             columns=['日期', '類型', '分類', '金額', '帳戶'])
    st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
    st.success("紀錄已儲存！")

# --- 主畫面：數據統計 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏦 帳戶餘額")
    # 計算邏輯
    df = st.session_state.data
    if not df.empty:
        income = df[df['類型'] == '收入'].groupby('帳戶')['金額'].sum()
        expense = df[df['類型'] == '支出'].groupby('帳戶')['金額'].sum()
        balance = income.add(-expense, fill_value=0)
        st.table(balance)
    else:
        st.write("目前尚無資料")

with col2:
    st.subheader("📅 今日支出統計")
    today = date # 依據選擇的日期
    today_df = df[(df['日期'] == today) & (df['類型'] == '支出')]
    if not today_df.empty:
        st.write(f"今日總花費：${today_df['金額'].sum()}")
        st.dataframe(today_df[['分類', '金額', '帳戶']])
    else:
        st.write("今天還沒花錢喔！")

# --- 每月趨勢圖 ---
st.divider()
st.subheader("📊 每月統計圖表")
if not df.empty:
    fig = px.pie(df[df['類型'] == '支出'], values='金額', names='分類', title="本月支出比例")
    st.plotly_chart(fig)