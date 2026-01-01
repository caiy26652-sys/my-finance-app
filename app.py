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

# 2. 讀取資料 (ttl=5 代表每 5 秒快取更新一次)
try:
    # 注意：這裡的 worksheet 名稱必須跟你的 Google 表格分頁名字一模一樣
    df = conn.read(worksheet="工作表1", ttl=5)
    
    # 確保金額欄位是數字格式
    if not df.empty:
        df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0)
except Exception as e:
    # 僅顯示錯誤但不停止程式
    st.error(f"連線失敗，請檢查 Secrets 或表格名稱：{e}")
    df = pd.DataFrame(columns=['日期', '類型', '分類', '金額', '帳戶'])

# --- 側邊欄：輸入介面 ---
st.sidebar.header("📝 新增紀錄")
date = st.sidebar.date_input("日期", datetime.now())
t_type = st.sidebar.selectbox("類型", ["支出", "收入"])
category = st.sidebar.selectbox("分類", ["餐飲", "交通", "購物", "娛樂", "薪水", "居家", "其他"])
amount = st.sidebar.number_input("金額", min_value=0, step=1)
account = st.sidebar.selectbox("帳戶", ["現金", "銀行卡", "悠遊卡", "信用卡"])

if st.sidebar.button("確認儲存"):
    # 建立新紀錄
    new_row = pd.DataFrame([{
        "日期": str(date),
        "類型": t_type,
        "分類": category,
        "金額": amount,
        "帳戶": account
    }])
    
    # 合併新舊資料並同步回雲端
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="工作表1", data=updated_df)
    
    st.sidebar.success("✅ 已同步到 Google 表格！")
    # 儲存後自動刷新畫面
    st.rerun()

# --- 主畫面：報表與明細 ---
if not df.empty:
    # A. 簡易統計卡片
    st.subheader("📊 本月概況")
    month_str = str(date)[:7] # 取得本月 YYYY-MM
    month_df = df[(df['日期'].str.contains(month_str)) & (df['類型'] == '支出')]
    
    col1, col2 = st.columns(2)
    with col1:
        total_expense = month_df['金額'].sum()
        st.metric("本月總支出", f"${int(total_expense)}")
    
    # B. 支出圓餅圖
    st.divider()
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🍕 類別支出比例")
        if not month_df.empty:
            fig = px.pie(month_df, values='金額', names='分類', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("本月尚無支出數據")

    with col_right:
        st.subheader("📋 最近紀錄 (最前 10 筆)")
        st.dataframe(df.sort_values(by="日期", ascending=False).head(10), use_container_width=True)

    # C. 全部歷史清單
    with st.expander("🔍 查看完整歷史明細"):
        st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True)
else:
    st.info("👋 你好！目前雲端表格沒有資料，請從左側側邊欄輸入第一筆交易。")
