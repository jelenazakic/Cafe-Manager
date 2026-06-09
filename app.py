
import streamlit as st
import sqlite3
import pandas as pd

DB = "cafe.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        item TEXT,
        quantity REAL,
        unit TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        product TEXT,
        quantity REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Cafe Manager", layout="wide")
st.title("☕ Cafe Manager")

tab1, tab2, tab3 = st.tabs(["📦 Nabavke", "🍺 Prodaja", "📊 Dashboard"])

with tab1:
    st.subheader("Unos nabavke")

    with st.form("purchase_form"):
        date = st.date_input("Datum")
        item = st.text_input("Artikal")
        quantity = st.number_input("Količina", min_value=0.0)
        unit = st.selectbox("Jedinica", ["kg", "l", "kom"])

        submit = st.form_submit_button("Sačuvaj")

        if submit:
            conn = sqlite3.connect(DB)
            conn.execute(
                "INSERT INTO purchases(date,item,quantity,unit) VALUES(?,?,?,?)",
                (str(date), item, quantity, unit)
            )
            conn.commit()
            conn.close()
            st.success("Nabavka sačuvana.")

with tab2:
    st.subheader("Unos prodaje")

    with st.form("sales_form"):
        date = st.date_input("Datum prodaje")
        product = st.text_input("Piće")
        quantity = st.number_input("Prodata količina", min_value=0.0)

        submit = st.form_submit_button("Sačuvaj prodaju")

        if submit:
            conn = sqlite3.connect(DB)
            conn.execute(
                "INSERT INTO sales(date,product,quantity) VALUES(?,?,?)",
                (str(date), product, quantity)
            )
            conn.commit()
            conn.close()
            st.success("Prodaja sačuvana.")

with tab3:
    st.subheader("Dashboard")

    conn = sqlite3.connect(DB)

    purchases = pd.read_sql("SELECT * FROM purchases", conn)
    sales = pd.read_sql("SELECT * FROM sales", conn)

    conn.close()

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Nabavke")
        st.dataframe(purchases, use_container_width=True)

    with col2:
        st.write("### Prodaja")
        st.dataframe(sales, use_container_width=True)

    if not sales.empty:
        summary = (
            sales.groupby("product")["quantity"]
            .sum()
            .sort_values(ascending=False)
        )

        st.write("### Najprodavanija pića")
        st.bar_chart(summary)
