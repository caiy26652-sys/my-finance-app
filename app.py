import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# 頁面基本設定
st.set_page_config(page_title="雲端記帳本", layout="wide")
st.title("💰 我的私人記帳 App (雲端同步版)")

# 1. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 讀取資料 (請確認你的試算表下方標籤名稱是 "工作表1")
try:
    df = conn.read(worksheet="工作表1", ttl=5)
    # 確保金額是數字格式
    if not df.empty:
        df['金額'] = pd.to_numeric(df['金額'], errors='coerce')
except Exception as e:
    st.error(f"連線失敗，請檢查 Secrets 或表格名稱：{e}")
    df = pd.DataFrame(columns=['日期', '類型', '分類', '金額', '帳戶'])

# --- 側邊欄：新增紀錄 ---
st.sidebar.header("📝 記一筆")
date = st.sidebar.date_input("日期", datetime.now())
t_type = st.sidebar.selectbox("交易類型", ["支出", "收入"])
category = st.sidebar.selectbox("分類", ["餐飲", "交通", "購物", "娛樂", "薪水", "其他"])
amount = st.sidebar.number_input("金額", min_value=0, step=1)
account = st.sidebar.selectbox("支付帳戶", ["現金", "銀行卡", "悠遊卡"])

if st.sidebar.button("確認儲存"):
    new_row = pd.DataFrame([{
        "日期": str(date),
        "類型": t_type,
        "分類": category,
        "金額": amount,
        "帳戶": account
    }])
    # 合併新舊資料
    updated_df = pd.concat([df, new_row], ignore_index=True)
    # 同步回 Google Sheets
    conn.update(worksheet="工作表1", data=updated_df)
    st.sidebar.success("✅ 已儲存至 Google 雲端！")
    st.rerun()

# --- 主畫面：儀表板 ---
if not df.empty:
    # A. 帳戶餘額統計
    st.subheader("🏦 帳戶即時餘額")
    income_total = df[df['類型'] == '收入'].groupby('帳戶')['金額'].sum()
    expense_total = df[df['類型'] == '支出'].groupby('帳戶')['金額'].sum()
    balance = income_total.add(-expense_total, fill_value=0)
    
    # 用橫向小卡片顯示餘額
    cols = st.columns(len(balance) if len(balance) > 0 else 1)
    for i, (acc, bal) in enumerate(balance.items()):
        cols[i].metric(acc, f"${int(bal)}")

    st.divider()

    # B. 今日支出與明細
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader(f"📅 {date} 支出統計")
        today_data = df[(df['日期'] == str(date)) & (df['類型'] == '支出')]
        if not today_data.empty:
            st.write(f"今日總花費：**${int(today_data['金額'].sum())}**")
            st.dataframe(today_data[['分類', '金額', '帳戶']], use_container_width=True)
        else:
            st.info("今天還沒記帳喔！")

    # C. 每月分類統計圖
    with col_right:
        st.subheader("📊 本月支出佔比")
        month_str = str(date)[:7] # 取得 YYYY-MM
        month_df = df[(df['日期'].str.contains(month_str)) & (df['類型'] == '支出')]
        if not month_df.empty:
            fig = px.pie(month_df, values='金額', names='分類', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("本月尚無支出數據")

    # D. 全部歷史紀錄
    st.divider()
    with st.expander("🔍 查看完整歷史紀錄"):
        st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True)
else:
    st.warning("📭 雲端表格目前是空的，請從左側開始輸入第一筆資料！")
