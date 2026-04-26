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
# DB
# -----------------------------

def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS encontros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        titulo TEXT,
        anfitrioes TEXT,
        local TEXT
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
        produtor TEXT,
        tipo TEXT,
        classificacao TEXT,
        teor_alcoolico TEXT,
        temperatura_servico TEXT,
        harmonizacao TEXT,
        visual TEXT,
        aroma TEXT,
        paladar TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vinho_id INTEGER,
        confrade TEXT,
        nota REAL,
        comentario TEXT
    )
    """)

    conn.commit()
    conn.close()


def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


init_db()

# -----------------------------
# LOGIN
# -----------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    st.title("🍷 Adega Balacobaco")
    st.subheader("👤 Identifique-se")

    nome = st.text_input("Seu nome")

    if st.button("Entrar"):
        if nome:
            st.session_state.usuario = nome
            st.rerun()
        else:
            st.warning("Informe seu nome")

    st.stop()

# Sidebar
st.sidebar.write(f"👤 {st.session_state.usuario}")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.rerun()

# Controle de admin
ADMIN_NOME = "Alê"
usuario_admin = st.session_state.usuario == ADMIN_NOME

# -----------------------------
# MENU
# -----------------------------
opcoes_menu = ["Dashboard", "Novo encontro", "Cadastrar vinho", "Avaliar vinho", "Catálogo"]

if usuario_admin:
    opcoes_menu.append("Backup & Dados")

menu = st.sidebar.radio("Menu", opcoes_menu)

st.title("🍷 Adega Balacobaco")

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Dashboard":
    encontros = query_df("SELECT * FROM encontros ORDER BY data DESC")

    st.subheader("Encontros")
    for _, row in encontros.iterrows():
        st.write(f"**{row['titulo']}** - {row['data']}")

# -----------------------------
# NOVO ENCONTRO
# -----------------------------
elif menu == "Novo encontro":
    with st.form("novo_encontro"):
        data = st.date_input("Data", value=date.today())
        titulo = st.text_input("Título")
        anfitrioes = st.text_input("Anfitriões")
        local = st.text_input("Local")

        if st.form_submit_button("Salvar"):
            execute("INSERT INTO encontros (data, titulo, anfitrioes, local) VALUES (?, ?, ?, ?)",
                    (str(data), titulo, anfitrioes, local))
            st.success("Salvo")

# -----------------------------
# VINHO
# -----------------------------
elif menu == "Cadastrar vinho":
    encontros = query_df("SELECT id, titulo FROM encontros")

    with st.form("vinho"):
        encontro = st.selectbox("Encontro", encontros["titulo"])
        encontro_id = encontros[encontros["titulo"] == encontro]["id"].values[0]

        nome = st.text_input("Nome")
        uva = st.text_input("Uva")

        if st.form_submit_button("Salvar"):
            execute("INSERT INTO vinhos (encontro_id, nome, uva) VALUES (?, ?, ?)",
                    (encontro_id, nome, uva))
            st.success("Vinho salvo")

# -----------------------------
# AVALIAÇÃO
# -----------------------------
elif menu == "Avaliar vinho":
    vinhos = query_df("SELECT id, nome FROM vinhos")

    with st.form("avaliacao"):
        vinho = st.selectbox("Vinho", vinhos["nome"])
        vinho_id = vinhos[vinhos["nome"] == vinho]["id"].values[0]

        st.write(f"Avaliando como: **{st.session_state.usuario}**")

        nota = st.slider("Nota", 0.0, 10.0, 8.0)
        comentario = st.text_area("Comentário")

        if st.form_submit_button("Salvar"):
            execute("INSERT INTO avaliacoes (vinho_id, confrade, nota, comentario) VALUES (?, ?, ?, ?)",
                    (vinho_id, st.session_state.usuario, nota, comentario))
            st.success("Avaliação salva")

# -----------------------------
# CATÁLOGO
# -----------------------------
elif menu == "Catálogo":
    df = query_df("""
        SELECT v.nome, v.uva, AVG(a.nota) as nota
        FROM vinhos v
        LEFT JOIN avaliacoes a ON a.vinho_id = v.id
        GROUP BY v.id
    """)

    st.dataframe(df, width="stretch")

# -----------------------------
# BACKUP
# -----------------------------
elif menu == "Backup & Dados":
    if not usuario_admin:
        st.error("Acesso restrito")
        st.stop()

    st.subheader("💾 Backup dos dados")

    encontros = query_df("SELECT * FROM encontros")
    vinhos = query_df("SELECT * FROM vinhos")
    avaliacoes = query_df("SELECT * FROM avaliacoes")

    st.markdown("### Baixar dados individuais")

    st.download_button("⬇️ Baixar encontros", encontros.to_csv(index=False), "encontros.csv", "text/csv")
    st.download_button("⬇️ Baixar vinhos", vinhos.to_csv(index=False), "vinhos.csv", "text/csv")
    st.download_button("⬇️ Baixar avaliações", avaliacoes.to_csv(index=False), "avaliacoes.csv", "text/csv")

    st.markdown("---")
    st.markdown("### Backup completo")

    st.download_button(
        "⬇️ Baixar backup completo",
        pd.concat([
            encontros.assign(tipo="encontros"),
            vinhos.assign(tipo="vinhos"),
            avaliacoes.assign(tipo="avaliacoes")
        ]).to_csv(index=False),
        "backup_balacobaco.csv",
        "text/csv"
    )

    st.markdown("---")
    st.markdown("### ⚠️ Administração")

    confirmar = st.checkbox("Confirmar limpeza da base")

    if confirmar and st.button("🧹 Limpar base de dados"):
        execute("DELETE FROM avaliacoes")
        execute("DELETE FROM vinhos")
        execute("DELETE FROM encontros")
        st.success("Base limpa com sucesso")
