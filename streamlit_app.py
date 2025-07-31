import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# --- File Setup ---
DATA_FILE = 'data/transactions.csv'
os.makedirs('data', exist_ok=True)

# --- Load Data Safely ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.dropna(subset=["Date"])
        return df
    else:
        return pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])

# --- Save Data ---
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- Page Setup ---
st.set_page_config(page_title="💰 Budget Tracker", layout="centered")
st.title("💰 Personal Budget Tracker")

df = load_data()

# --- Add Transaction ---
st.subheader("➕ Add New Transaction")
with st.form("add_form"):
    col1, col2 = st.columns(2)
    amount = col1.number_input("Amount (₹)", min_value=0.0)
    type_ = col2.selectbox("Type", ["Income", "Expense"])
    category = st.text_input("Category")
    date = st.date_input("Date", value=datetime.today())
    submitted = st.form_submit_button("Add")
    if submitted:
        new_row = pd.DataFrame([[pd.to_datetime(date), type_, amount, category]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.success("✅ Transaction Added!")
        st.experimental_rerun()

# --- Clean Date Column ---
df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
df = df.dropna(subset=["Date"])

# --- Summary Metrics ---
st.subheader("📊 Summary")
total_income = df[df["Type"] == "Income"]["Amount"].sum()
total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Income", f"₹{total_income:.2f}")
col2.metric("Expenses", f"₹{total_expense:.2f}")
col3.metric("Balance", f"₹{balance:.2f}")

# --- Today's Transactions ---
st.subheader("📅 Today's Transactions")
today = pd.to_datetime(datetime.today().date())
df_today = df[df["Date"].dt.normalize() == today]

today_income = df_today[df_today["Type"] == "Income"]["Amount"].sum()
today_expense = df_today[df_today["Type"] == "Expense"]["Amount"].sum()
today_balance = today_income - today_expense
new_transactions_today = len(df_today)

col1, col2, col3 = st.columns(3)
col1.metric("Today's Income", f"₹{today_income:.2f}")
col2.metric("Today's Expense", f"₹{today_expense:.2f}")
col3.metric("Net Today", f"₹{today_balance:.2f}")

st.metric("🆕 New Transactions Today", new_transactions_today)

# --- Monthly Budget Limit ---
st.subheader("🎯 Monthly Budget Limit")
limit = st.number_input("Monthly Expense Limit (₹)", min_value=0.0, value=5000.0)

df["Month"] = df["Date"].dt.to_period("M").astype(str)
current_month = datetime.today().strftime('%Y-%m')

monthly_expense = df[(df["Type"] == "Expense") & (df["Month"] == current_month)]["Amount"].sum()
if monthly_expense > limit:
    st.error(f"⚠ Over Budget! ₹{monthly_expense:.2f} spent of ₹{limit}")
else:
    st.success(f"✅ Within Budget: ₹{monthly_expense:.2f} of ₹{limit}")

# --- Transaction Table ---
st.subheader("📋 All Transactions")
if not df.empty:
    df = df.sort_values(by="Date", ascending=False)
    df_display = df.reset_index(drop=True)
    st.dataframe(df_display)

    # --- Edit/Delete Transaction ---
    st.subheader("✏ Edit or 🗑 Delete a Transaction")
    index_to_edit = st.number_input("Row number to edit/delete (starts at 0)", min_value=0, max_value=len(df_display)-1)
    row = df_display.loc[index_to_edit]

    with st.form("edit_form"):
        new_amount = st.number_input("Edit Amount", value=float(row["Amount"]))
        new_type = st.selectbox("Edit Type", ["Income", "Expense"], index=0 if row["Type"] == "Income" else 1)
        new_category = st.text_input("Edit Category", value=row["Category"])
        new_date = st.date_input("Edit Date", value=row["Date"].date())

        col1, col2 = st.columns(2)
        update = col1.form_submit_button("✅ Update Transaction")
        delete = col2.form_submit_button("🗑 Delete Transaction")

        if update:
            df.loc[df_display.index[index_to_edit], "Amount"] = new_amount
            df.loc[df_display.index[index_to_edit], "Type"] = new_type
            df.loc[df_display.index[index_to_edit], "Category"] = new_category
            df.loc[df_display.index[index_to_edit], "Date"] = pd.to_datetime(new_date)
            save_data(df)
            st.success("✅ Transaction updated successfully!")
            st.experimental_rerun()

        if delete:
            df = df.drop(df_display.index[index_to_edit])
            save_data(df)
            st.success("🗑 Transaction deleted successfully!")
            st.experimental_rerun()
else:
    st.info("No transactions yet.")

# --- Monthly Income vs Expenses Chart ---
st.subheader("📈 Monthly Income vs Expenses")
if not df.empty:
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    monthly_summary = df.groupby(["Month", "Type"])["Amount"].sum().unstack().fillna(0)
    st.bar_chart(monthly_summary)

# --- Expense Distribution Pie Chart ---
st.subheader("📊 Expense Breakdown by Category")
expense_by_category = df[df["Type"] == "Expense"].groupby("Category")["Amount"].sum()
if not expense_by_category.empty:
    fig, ax = plt.subplots()
    ax.pie(
        expense_by_category,
        labels=expense_by_category.index,
        autopct='%1.1f%%',
        startangle=90
    )
    ax.set_title("Expense Distribution")
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("No expense data to show pie chart.")
