import re
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("adega_balacobaco.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Adega Balacobaco", page_icon="🍷", layout="wide")

# -----------------------------
# Banco de dados
# -----------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)


def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS encontros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        titulo TEXT,
        anfitrioes TEXT,
        local TEXT,
        observacoes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vinhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        encontro_id INTEGER,
        nome TEXT,
        uva TEXT,
        pais TEXT,
        regiao TEXT,
        safra TEXT,
        tipo TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# -----------------------------
# Funções
# -----------------------------
def roman_to_int(roman):
    valores = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0
    prev = 0
    for c in reversed(roman):
        v = valores.get(c,0)
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total


def ordem_encontro(titulo):
    match = re.match(r"^\s*([IVXLCDM]+)\s+Encontro", titulo)
    return roman_to_int(match.group(1)) if match else 0


# -----------------------------
# Dashboard
# -----------------------------
st.title("🍷 Confraria Balacobaco")

menu = st.sidebar.radio("Menu", ["Dashboard", "Novo encontro"])

if menu == "Dashboard":

    encontros = query_df("SELECT * FROM encontros")

    if not encontros.empty:
        encontros["ordem"] = encontros["titulo"].apply(ordem_encontro)
        encontros = encontros.sort_values(["ordem","id"], ascending=False)
        ordem_max = encontros["ordem"].max()
    else:
        ordem_max = None

    for _, row in encontros.iterrows():

        badge = " 🟡 Atual" if row["ordem"] == ordem_max else ""

        st.subheader(f"{row['titulo']}{badge}")
        st.write(row["data"])
        st.write(row["local"])

        col1, col2 = st.columns(2)

        if col1.button("Ver vinhos", key=f"v{row['id']}"):
            st.session_state["ver"] = row["id"]

        if col2.button("Editar", key=f"e{row['id']}"):
            st.session_state["edit"] = row["id"]

        # editar evento
        if st.session_state.get("edit") == row["id"]:
            with st.form(f"edit{row['id']}"):
                titulo = st.text_input("Título", value=row["titulo"])
                data = st.text_input("Data", value=row["data"])
                local = st.text_input("Local", value=row["local"])

                if st.form_submit_button("Salvar"):
                    execute("""
                    UPDATE encontros SET titulo=?, data=?, local=? WHERE id=?
                    """, (titulo, data, local, row["id"]))

                    st.session_state["edit"] = None
                    st.rerun()

        # vinhos
        if st.session_state.get("ver") == row["id"]:
            vinhos = query_df("SELECT * FROM vinhos WHERE encontro_id=?", (row["id"],))

            for _, v in vinhos.iterrows():
                st.write(f"🍷 {v['nome']} - {v['uva']}")


# -----------------------------
# Novo encontro
# -----------------------------
elif menu == "Novo encontro":

    with st.form("novo"):
        titulo = st.text_input("Título (ex: VIII Encontro Balacobaco)")
        data = st.text_input("Data")
        local = st.text_input("Local")

        if st.form_submit_button("Salvar"):
            execute("""
            INSERT INTO encontros (data, titulo, local)
            VALUES (?, ?, ?)
            """, (data, titulo, local))

            st.success("Salvo!")