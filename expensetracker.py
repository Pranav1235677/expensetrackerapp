import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path
import random
from faker import Faker
import altair as alt

# Ensure the 'data' directory exists
directory = Path("data")
directory.mkdir(parents=True, exist_ok=True)

# Generate sample CSV files (optional, for testing purposes)
def generate_sample_data():
    fake = Faker()
    categories = ['Food', 'Transportation', 'Bills', 'Groceries', 'Subscriptions', 'Others']
    payment_modes = ['Cash', 'Online']

    for month in range(1, 13):
        data = []
        for _ in range(500):  # Generate 500 transactions per month
            data.append({
                'Date': fake.date_this_year(),
                'Category': random.choice(categories),
                'Payment_Mode': random.choice(payment_modes),
                'Description': fake.sentence(),
                'Amount_Paid': round(random.uniform(10, 500), 2),
                'Cashback': round(random.uniform(0, 20), 2)
            })
        df = pd.DataFrame(data)
        file_path = directory / f"expenses_{month}.csv"
        df.to_csv(file_path, index=False)
    st.success("Sample data generated for all 12 months.")

# Function to create SQLite tables for expenses
def create_tables():
    conn = sqlite3.connect("data/expenses.db")
    for month in range(1, 13):
        table_name = f"Expenses_{month:02d}"
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                ID INTEGER PRIMARY KEY,
                Date TEXT,
                Category TEXT,
                Payment_Mode TEXT,
                Description TEXT,
                Amount_Paid REAL,
                Cashback REAL
            );
        """)
    conn.close()
    st.success("Tables created for all 12 months.")

# Function to insert data into SQLite tables from CSV files
def insert_data():
    conn = sqlite3.connect("data/expenses.db")
    for month in range(1, 13):
        file_path = directory / f"expenses_{month}.csv"
        if not file_path.exists():
            st.warning(f"File not found: {file_path.name}. Skipping...")
            continue
        data = pd.read_csv(file_path)
        table_name = f"Expenses_{month:02d}"
        data.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()
    st.success("Data inserted into all available monthly tables.")

# Function to show total spending by category
def show_total_spending():
    conn = sqlite3.connect("data/expenses.db")
    query = """
    SELECT Category, SUM(Amount_Paid) AS Total_Spent
    FROM (
        """ + " UNION ALL ".join([f"SELECT * FROM Expenses_{month:02d}" for month in range(1, 13)]) + """
    ) AS Combined
    GROUP BY Category
    ORDER BY Total_Spent DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    st.subheader("Total Spending by Category")
    st.dataframe(df)

    # Visualize spending using a bar chart
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("Category:N", sort='-y', axis=alt.Axis(labelAngle=-45)),
        y="Total_Spent:Q"
    )
    st.altair_chart(chart, use_container_width=True)

# Function for an interactive dashboard
def interactive_dashboard():
    conn = sqlite3.connect("data/expenses.db")

    # Filters
    category_filter = st.sidebar.multiselect("Select Categories", ['Food', 'Transportation', 'Bills', 'Groceries', 'Subscriptions', 'Others'])
    payment_mode_filter = st.sidebar.multiselect("Select Payment Modes", ['Cash', 'Online'])
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")

    query = f"""
    SELECT *
    FROM (
        """ + " UNION ALL ".join([f"SELECT * FROM Expenses_{month:02d}" for month in range(1, 13)]) + """
    ) AS Combined
    WHERE Date BETWEEN '{start_date}' AND '{end_date}'
    """

    if category_filter:
        query += f" AND Category IN ({', '.join(f'\'{cat}\'' for cat in category_filter)})"
    if payment_mode_filter:
        query += f" AND Payment_Mode IN ({', '.join(f'\'{mode}\'' for mode in payment_mode_filter)})"

    df = pd.read_sql_query(query, conn)
    conn.close()

    st.subheader("Filtered Expenses")
    st.dataframe(df)

    # Add a download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_expenses.csv",
        mime="text/csv"
    )

# Main Streamlit App
if "__name_ "== "__main__":
    st.title("Expense Tracker Application")

    # Sidebar for Navigation
    menu = ["Generate Sample Data", "Create Tables", "Insert Data", "View Spending", "Interactive Dashboard"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Generate Sample Data":
        st.subheader("Generate Sample Data for Testing")
        if st.button("Generate Data"):
            generate_sample_data()

    elif choice == "Create Tables":
        st.subheader("Create Tables for Monthly Expenses")
        if st.button("Create Tables"):
            create_tables()

    elif choice == "Insert Data":
        st.subheader("Insert Monthly Expense Data")
        if st.button("Insert Data"):
            insert_data()

    elif choice == "View Spending":
        st.subheader("View Total Spending by Category")
        show_total_spending()

    elif choice == "Interactive Dashboard":
        st.subheader("Explore and Analyze Expenses")
        interactive_dashboard()