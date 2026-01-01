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

# 2. 讀取資料 (直接從 Secrets 抓網址，請確認試算表分頁名稱是否為 "工作表1")
# 修改 app.py 這一段
try:
    df = conn.read(worksheet="工作表1", ttl=5)
    if not df.empty:
        df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0)
except Exception as e:
    # 這裡會印出真正的錯誤原因
    st.error(f"發生錯誤了！原因：{e}")
    st.stop() # 讓程式停在這裡

# --- 側邊欄：輸入介面 ---
st.sidebar.header("📝 新增收支紀錄")
date = st.sidebar.date_input("選擇日期", datetime.now())
t_type = st.sidebar.selectbox("交易類型", ["支出", "收入"])
category = st.sidebar.selectbox("分類", ["餐飲", "交通", "購物", "娛樂", "薪水", "居家", "其他"])
amount = st.sidebar.number_input("輸入金額", min_value=0, step=1)
account = st.sidebar.selectbox("支付帳戶", ["現金", "銀行卡", "悠遊卡", "信用卡"])

if st.sidebar.button("確認儲存並同步"):
    # 建立新的一列資料
    new_row = pd.DataFrame([{
        "日期": str(date),
        "類型": t_type,
        "分類": category,
        "金額": amount,
        "帳戶": account
    }])
    
    # 合併新資料並寫回雲端
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="工作表1", data=updated_df)
    
    st.sidebar.success("✅ 資料已成功寫入 Google 表格！")
    st.rerun()

# --- 主畫面：數據儀表板 ---
if not df.empty:
    # A. 帳戶餘額統計
    st.subheader("🏦 帳戶即時餘額")
    income_sum = df[df['類型'] == '收入'].groupby('帳戶')['金額'].sum()
    expense_sum = df[df['類型'] == '支出'].groupby('帳戶')['金額'].sum()
    balance = income_sum.add(-expense_sum, fill_value=0)
    
    # 顯示各個帳戶餘額卡片
    cols = st.columns(len(balance) if len(balance) > 0 else 1)
    for i, (acc, bal) in enumerate(balance.items()):
        cols[i].metric(acc, f"${int(bal)}")

    st.divider()

    # B. 今日摘要與圖表
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader(f"📅 {date} 消費清單")
        today_df = df[(df['日期'] == str(date)) & (df['類型'] == '支出')]
        if not today_df.empty:
            st.write(f"今日總支出：**${int(today_df['金額'].sum())}**")
            st.table(today_df[['分類', '金額', '帳戶']])
        else:
            st.info("今天還沒有支出紀錄喔。")

    with col_right:
        st.subheader("📊 本月支出分佈")
        # 抓取本月份的資料 (YYYY-MM)
        current_month = str(date)[:7]
        month_df = df[(df['日期'].str.contains(current_month)) & (df['類型'] == '支出')]
        
        if not month_df.empty:
            fig = px.pie(month_df, values='金額', names='分類', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("本月目前還沒有支出數據。")

    # C. 查看原始資料
    with st.expander("🔍 查看所有歷史明細"):
        st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True)

else:
    st.warning("📭 雲端表格內目前沒有資料。請先從左側側邊欄輸入第一筆交易！")

