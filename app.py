import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# 設定
st.set_page_config(page_title="雲端記帳本", layout="wide")
st.title("💰 永久存檔版記帳 App")

# 這裡請貼上你剛剛複製的 Google 表格網址
SHEET_URL = "在此處貼上你的Google表格網址"

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料
try:
    df = conn.read(spreadsheet=SHEET_URL)
except:
    df = pd.DataFrame(columns=['日期', '類型', '分類', '金額', '帳戶'])

# --- 側邊欄輸入 ---
st.sidebar.header("新增紀錄")
date = st.sidebar.date_input("日期", datetime.now())
t_type = st.sidebar.selectbox("類型", ["支出", "收入"])
category = st.sidebar.selectbox("分類", ["餐飲", "交通", "購物", "娛樂", "薪水", "其他"])
amount = st.sidebar.number_input("金額", min_value=0)
account = st.sidebar.selectbox("帳戶", ["現金", "銀行卡", "悠遊卡"])

if st.sidebar.button("儲存到雲端"):
    new_row = pd.DataFrame([{
        "日期": str(date),
        "類型": t_type,
        "分類": category,
        "金額": amount,
        "帳戶": account
    }])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    # 寫回 Google Sheets
    conn.update(spreadsheet=SHEET_URL, data=updated_df)
    st.sidebar.success("已成功同步到 Google 表格！")
    st.rerun()

# --- 報表顯示 ---
if not df.empty:
    # 這裡放你之前的統計圖表邏輯...
    st.subheader("📊 本月支出分析")
    fig = px.pie(df[df['類型'] == '支出'], values='金額', names='分類')
    st.plotly_chart(fig)
    st.dataframe(df)
else:
    st.info("目前雲端表格沒有數據，請開始記帳！")
