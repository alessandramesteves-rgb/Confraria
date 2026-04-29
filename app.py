import re
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("adega_balacobaco.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Adega Balacobaco",
    page_icon="🍷",
    layout="wide",
)

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS encontros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            titulo TEXT NOT NULL,
            tema TEXT,
            anfitrioes TEXT,
            local TEXT,
            observacoes TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vinhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encontro_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
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
            paladar TEXT,
            foto_rotulo TEXT,
            FOREIGN KEY(encontro_id) REFERENCES encontros(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vinho_id INTEGER NOT NULL,
            confrade TEXT NOT NULL,
            nota REAL NOT NULL,
            repetiria TEXT,
            foi_balacobaco TEXT,
            comentario TEXT,
            FOREIGN KEY(vinho_id) REFERENCES vinhos(id)
        )
        """
    )

    # Compatibilidade com bancos já criados em versões anteriores
    novas_colunas_encontros = {
        "tema": "TEXT",
    }

    cur.execute("PRAGMA table_info(encontros)")
    colunas_encontros = [col[1] for col in cur.fetchall()]
    for coluna, tipo_coluna in novas_colunas_encontros.items():
        if coluna not in colunas_encontros:
            cur.execute(f"ALTER TABLE encontros ADD COLUMN {coluna} {tipo_coluna}")

    novas_colunas_vinhos = {
        "produtor": "TEXT",
        "tipo": "TEXT",
        "classificacao": "TEXT",
        "teor_alcoolico": "TEXT",
        "temperatura_servico": "TEXT",
        "harmonizacao": "TEXT",
        "visual": "TEXT",
        "aroma": "TEXT",
        "paladar": "TEXT",
        "foto_rotulo": "TEXT",
    }

    cur.execute("PRAGMA table_info(vinhos)")
    colunas_vinhos = [col[1] for col in cur.fetchall()]
    for coluna, tipo_coluna in novas_colunas_vinhos.items():
        if coluna not in colunas_vinhos:
            cur.execute(f"ALTER TABLE vinhos ADD COLUMN {coluna} {tipo_coluna}")

    novas_colunas_avaliacoes = {
        "repetiria": "TEXT",
        "foi_balacobaco": "TEXT",
    }

    cur.execute("PRAGMA table_info(avaliacoes)")
    colunas_avaliacoes = [col[1] for col in cur.fetchall()]
    for coluna, tipo_coluna in novas_colunas_avaliacoes.items():
        if coluna not in colunas_avaliacoes:
            cur.execute(f"ALTER TABLE avaliacoes ADD COLUMN {coluna} {tipo_coluna}")

    conn.commit()
    conn.close()


def roman_to_int(roman):
    valores = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    anterior = 0

    for letra in reversed(str(roman).upper()):
        valor = valores.get(letra, 0)
        if valor < anterior:
            total -= valor
        else:
            total += valor
            anterior = valor

    return total


def ordem_encontro(titulo):
    titulo = str(titulo)

    # Novo padrão: 1°, 2°, 10°...
    match_num = re.match(r"^\s*(\d+)[°º]?\s+Encontro", titulo, re.IGNORECASE)
    if match_num:
        return int(match_num.group(1))

    # Compatibilidade com romano
    match_romano = re.match(r"^\s*([IVXLCDM]+)\s+Encontro", titulo, re.IGNORECASE)
    if match_romano:
        return roman_to_int(match_romano.group(1))

    return 0


def ordenar_encontros(df):
    if df.empty:
        return df

    df = df.copy()
    df["ordem"] = df["titulo"].apply(ordem_encontro)
    return df.sort_values(["ordem", "id"], ascending=[False, False])


def proximo_numero_encontro():
    encontros = query_df("SELECT titulo FROM encontros")
    if encontros.empty:
        return 1

    maior = encontros["titulo"].apply(ordem_encontro).max()
    if pd.isna(maior) or int(maior) == 0:
        return 1

    return int(maior) + 1


def titulo_sugerido_encontro():
    numero = proximo_numero_encontro()
    return f"{numero}° Encontro Balacobaco"


init_db()

# -----------------------------
# Visual Confraria
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fff8ef 0%, #f6e6d8 42%, #ecd2bf 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #5b0f2e 0%, #2f0718 100%);
    }

    [data-testid="stSidebar"] * {
        color: #fff7ed !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #5b0f2e;
        letter-spacing: -0.02em;
    }

    .hero-card {
        background: linear-gradient(135deg, #5b0f2e 0%, #8a2048 60%, #b9873d 100%);
        color: #fff7ed;
        padding: 2rem;
        border-radius: 30px;
        box-shadow: 0 14px 34px rgba(91, 15, 46, 0.26);
        margin-bottom: 1.5rem;
    }

    .hero-card h1 {
        color: #fff7ed;
        margin-bottom: 0.25rem;
        font-size: 2.4rem;
    }

    .hero-card p {
        color: #fff1d6;
        font-size: 1.08rem;
        margin-bottom: 0;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.80);
        padding: 1rem;
        border-radius: 22px;
        border: 1px solid rgba(91,15,46,0.10);
        box-shadow: 0 8px 24px rgba(91,15,46,0.08);
    }

    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.76);
        border-radius: 24px;
        border: 1px solid rgba(91,15,46,0.10);
        box-shadow: 0 8px 24px rgba(91,15,46,0.08);
        padding: 0.8rem;
    }

    .stButton button {
        background: linear-gradient(135deg, #6b1233 0%, #9b2752 100%);
        color: white;
        border-radius: 14px;
        border: none;
        padding: 0.65rem 1.1rem;
        font-weight: 700;
    }

    .stButton button:hover {
        border: none;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Login simples
# -----------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "admin" not in st.session_state:
    st.session_state.admin = False

if not st.session_state.usuario:
    st.markdown(
        """
        <div class="hero-card">
            <h1>🍷 Adega Balacobaco</h1>
            <p>Entre com seu nome para acessar o catálogo da confraria.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nome = st.text_input("Seu nome")
    senha_admin = st.text_input("Senha de admin (somente para administração)", type="password")

    if st.button("Entrar"):
        if nome.strip():
            st.session_state.usuario = nome.strip()
            st.session_state.admin = nome.strip() == "Alessandra" and senha_admin == "balacobaco"
            st.rerun()
        else:
            st.warning("Informe seu nome.")

    st.stop()

usuario_admin = st.session_state.get("admin", False)

st.sidebar.write(f"👤 {st.session_state.usuario}")

if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.session_state.admin = False
    st.rerun()

opcoes_menu = [
    "Dashboard",
    "Novo encontro",
    "Cadastrar vinho",
    "Avaliar vinho",
    "Catálogo",
    "Rankings",
]

if usuario_admin:
    opcoes_menu.append("Backup & Dados")

menu = st.sidebar.radio("Menu", opcoes_menu)

# Ao entrar no Dashboard, mostra apenas a lista dos encontros.
# A lista de vinhos só aparece depois de clicar em "Ver vinhos".
if "ultimo_menu" not in st.session_state:
    st.session_state.ultimo_menu = None

if menu == "Dashboard" and st.session_state.ultimo_menu != "Dashboard":
    st.session_state.dashboard_encontro_id = None

st.session_state.ultimo_menu = menu

st.markdown(
    """
    <div class="hero-card">
        <h1>🍷 Adega Balacobaco</h1>
        <p>Catálogo dos vinhos, encontros, fichas técnicas e avaliações da confraria.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Dashboard
# -----------------------------
if menu == "Dashboard":
    encontros = ordenar_encontros(query_df("SELECT * FROM encontros"))
    vinhos = query_df("SELECT * FROM vinhos")
    avaliacoes = query_df("SELECT * FROM avaliacoes")

    encontro_atual_ordem = int(encontros["ordem"].max()) if not encontros.empty else None

    col1, col2, col3 = st.columns(3)
    col1.metric("Encontros", len(encontros))
    col2.metric("Vinhos degustados", len(vinhos))
    col3.metric("Avaliações", len(avaliacoes))

    st.subheader("Encontros")

    if encontros.empty:
        st.info("Nenhum encontro cadastrado ainda.")
    else:
        if "dashboard_encontro_id" not in st.session_state:
            st.session_state.dashboard_encontro_id = None

        if "editar_encontro_id" not in st.session_state:
            st.session_state.editar_encontro_id = None

        todos_encontros = ordenar_encontros(
            query_df("SELECT id, data, titulo FROM encontros")
        )
        todos_encontros["label"] = todos_encontros["data"] + " - " + todos_encontros["titulo"]

        for _, row in encontros.iterrows():
            with st.container(border=True):
                col_info, col_btns = st.columns([4, 2])

                with col_info:
                    badge_atual = (
                        " <span style='background:#b9873d;color:white;padding:4px 10px;border-radius:999px;font-size:0.8rem;'>Atual</span>"
                        if int(row.get("ordem", 0)) == encontro_atual_ordem and encontro_atual_ordem > 0
                        else ""
                    )
                    st.markdown(f"### {row['titulo']}{badge_atual}", unsafe_allow_html=True)

                    if "tema" in row and pd.notna(row["tema"]) and str(row["tema"]).strip():
                        st.markdown(
                            f"<span style='color:#8a2048;font-size:1.18rem;font-style:italic;font-weight:500;'>"
                            f"{row['tema']}</span>",
                            unsafe_allow_html=True
                        )

                    st.write(f"**Data:** {row['data']}")
                    st.write(f"**Anfitriões:** {row['anfitrioes'] if row['anfitrioes'] else '-'}")
                    st.write(f"**Local:** {row['local'] if row['local'] else '-'}")

                with col_btns:
                    col_v, col_e = st.columns(2)

                    with col_v:
                        if st.button("Ver vinhos", key=f"ver_vinhos_{row['id']}"):
                            if st.session_state.dashboard_encontro_id == int(row["id"]):
                                st.session_state.dashboard_encontro_id = None
                            else:
                                st.session_state.dashboard_encontro_id = int(row["id"])

                    with col_e:
                        if st.button("Editar", key=f"editar_encontro_{row['id']}"):
                            if st.session_state.editar_encontro_id == int(row["id"]):
                                st.session_state.editar_encontro_id = None
                            else:
                                st.session_state.editar_encontro_id = int(row["id"])

            # Edição do encontro logo abaixo do evento selecionado
            if st.session_state.editar_encontro_id == int(row["id"]):
                with st.container(border=True):
                    st.markdown("#### ✏️ Editar encontro")

                    with st.form(f"form_editar_encontro_{row['id']}"):
                        titulo_edit = st.text_input("Título", value=row["titulo"])
                        tema_edit = st.text_input("Tema", value=row["tema"] if "tema" in row and pd.notna(row["tema"]) else "")
                        data_edit = st.text_input("Data", value=row["data"])
                        anfitrioes_edit = st.text_input("Anfitriões", value=row["anfitrioes"] or "")
                        local_edit = st.text_input("Local", value=row["local"] or "")
                        obs_edit = st.text_area("Observações", value=row["observacoes"] or "")

                        salvar = st.form_submit_button("Salvar alterações")

                    if salvar:
                        execute(
                            """
                            UPDATE encontros
                            SET titulo = ?, tema = ?, data = ?, anfitrioes = ?, local = ?, observacoes = ?
                            WHERE id = ?
                            """,
                            (
                                titulo_edit,
                                tema_edit,
                                data_edit,
                                anfitrioes_edit,
                                local_edit,
                                obs_edit,
                                int(row["id"]),
                            ),
                        )
                        st.success("Encontro atualizado com sucesso.")
                        st.session_state.editar_encontro_id = None
                        st.rerun()

            # Lista de vinhos logo abaixo do evento selecionado
            if st.session_state.dashboard_encontro_id == int(row["id"]):
                vinhos_do_dia = query_df(
                    """
                    SELECT
                        v.id,
                        v.encontro_id,
                        v.nome,
                        v.uva,
                        v.pais,
                        v.regiao,
                        v.safra,
                        v.tipo
                    FROM vinhos v
                    WHERE v.encontro_id = ?
                    ORDER BY v.nome
                    """,
                    (int(row["id"]),),
                )

                with st.container(border=True):
                    st.markdown("#### Vinhos degustados")

                    if vinhos_do_dia.empty:
                        st.info("Ainda não há vinhos cadastrados para este encontro.")
                    else:
                        for _, vinho in vinhos_do_dia.iterrows():
                            with st.expander(f"🍷 {vinho['nome']}"):
                                with st.form(f"editar_vinho_dashboard_{vinho['id']}"):
                                    nome_edit = st.text_input("Nome", value=vinho["nome"])
                                    uva_edit = st.text_input("Uva", value=vinho["uva"] or "")
                                    pais_edit = st.text_input("País", value=vinho["pais"] or "")
                                    regiao_edit = st.text_input("Região", value=vinho["regiao"] or "")
                                    safra_edit = st.text_input("Safra", value=vinho["safra"] or "")
                                    tipo_edit = st.text_input("Tipo", value=vinho["tipo"] or "")

                                    st.markdown("### Mover para outro encontro")
                                    encontro_atual_label = todos_encontros.loc[
                                        todos_encontros["id"] == vinho["encontro_id"], "label"
                                    ].iloc[0]

                                    novo_encontro_label = st.selectbox(
                                        "Novo encontro",
                                        todos_encontros["label"],
                                        index=todos_encontros["label"].tolist().index(encontro_atual_label),
                                        key=f"mover_vinho_{vinho['id']}",
                                    )

                                    novo_encontro_id = int(
                                        todos_encontros.loc[
                                            todos_encontros["label"] == novo_encontro_label, "id"
                                        ].iloc[0]
                                    )

                                    confirmar_exclusao = st.checkbox(
                                        "Confirmar exclusão deste vinho",
                                        key=f"confirmar_exclusao_vinho_{vinho['id']}",
                                    )

                                    col_salvar, col_excluir = st.columns(2)
                                    salvar = col_salvar.form_submit_button("Salvar alterações")
                                    excluir = col_excluir.form_submit_button("🗑️ Excluir vinho")

                                if salvar:
                                    execute(
                                        """
                                        UPDATE vinhos
                                        SET encontro_id = ?, nome = ?, uva = ?, pais = ?, regiao = ?, safra = ?, tipo = ?
                                        WHERE id = ?
                                        """,
                                        (
                                            novo_encontro_id,
                                            nome_edit,
                                            uva_edit,
                                            pais_edit,
                                            regiao_edit,
                                            safra_edit,
                                            tipo_edit,
                                            int(vinho["id"]),
                                        ),
                                    )
                                    st.success("Vinho atualizado com sucesso.")
                                    st.rerun()

                                if excluir:
                                    if confirmar_exclusao:
                                        execute("DELETE FROM avaliacoes WHERE vinho_id = ?", (int(vinho["id"]),))
                                        execute("DELETE FROM vinhos WHERE id = ?", (int(vinho["id"]),))
                                        st.success("Vinho excluído com sucesso.")
                                        st.rerun()
                                    else:
                                        st.warning("Marque a confirmação antes de excluir o vinho.")

# -----------------------------
# Novo encontro
# -----------------------------
elif menu == "Novo encontro":
    st.subheader("Novo encontro")

    titulo_sugerido = titulo_sugerido_encontro()

    with st.form("form_encontro"):
        data_encontro = st.date_input("Data", value=date.today())
        titulo = st.text_input("Título do encontro", value=titulo_sugerido)
        tema = st.text_input("Tema / subtítulo", placeholder="Ex.: Noite Italiana, Vinhos Portugueses, Harmonização com Massas")
        anfitrioes = st.text_input("Anfitriões", placeholder="Ex.: Alê & Ale")
        local = st.text_input("Local")
        observacoes = st.text_area("Observações")
        submit = st.form_submit_button("Salvar encontro")

    if submit:
        if not titulo:
            st.error("Informe o título do encontro.")
        else:
            execute(
                """
                INSERT INTO encontros (data, titulo, tema, anfitrioes, local, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(data_encontro), titulo, tema, anfitrioes, local, observacoes),
            )
            st.success("Encontro salvo com sucesso.")

# -----------------------------
# Cadastrar vinho
# -----------------------------
elif menu == "Cadastrar vinho":
    st.subheader("Cadastrar vinho degustado")

    encontros = ordenar_encontros(query_df("SELECT id, data, titulo FROM encontros"))

    if encontros.empty:
        st.warning("Cadastre um encontro primeiro.")
    else:
        encontros["label"] = encontros["data"] + " - " + encontros["titulo"]

        with st.form("form_vinho"):
            encontro_label = st.selectbox("Encontro", encontros["label"])
            encontro_id = int(
                encontros.loc[encontros["label"] == encontro_label, "id"].iloc[0]
            )

            nome = st.text_input("Nome do vinho")
            uva = st.text_input("Uva", placeholder="Ex.: Malbec, Cabernet Sauvignon, Chardonnay")
            pais = st.text_input("País")
            regiao = st.text_input("Região")
            safra = st.text_input("Safra")
            produtor = st.text_input("Produtor")
            tipo = st.text_input("Tipo", placeholder="Ex.: Tinto, Branco, Rosé, Espumante")
            classificacao = st.text_input("Classificação", placeholder="Ex.: Seco, Meio seco, Suave")
            teor_alcoolico = st.text_input("Teor alcoólico", placeholder="Ex.: 14%")
            temperatura_servico = st.text_input("Temperatura de serviço", placeholder="Ex.: 16 a 18°C")
            harmonizacao = st.text_area("Harmonização", placeholder="Ex.: Carnes, massas, queijos curados")

            st.markdown("### Características sensoriais")
            visual = st.text_area("Visual", placeholder="Ex.: Rubi profundo, reflexos violáceos")
            aroma = st.text_area("Aroma", placeholder="Ex.: Frutas negras, especiarias, notas florais")
            paladar = st.text_area("Paladar", placeholder="Ex.: Encorpado, taninos macios, final persistente")

            foto = st.file_uploader("Foto do rótulo", type=["png", "jpg", "jpeg"])

            submit = st.form_submit_button("Salvar vinho")

        if submit:
            if not nome:
                st.error("Informe o nome do vinho.")
            else:
                foto_path = None

                if foto:
                    foto_path = str(UPLOAD_DIR / foto.name)
                    with open(foto_path, "wb") as f:
                        f.write(foto.getbuffer())

                execute(
                    """
                    INSERT INTO vinhos
                    (
                        encontro_id, nome, uva, pais, regiao, safra, produtor,
                        tipo, classificacao, teor_alcoolico, temperatura_servico,
                        harmonizacao, visual, aroma, paladar, foto_rotulo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        encontro_id,
                        nome,
                        uva,
                        pais,
                        regiao,
                        safra,
                        produtor,
                        tipo,
                        classificacao,
                        teor_alcoolico,
                        temperatura_servico,
                        harmonizacao,
                        visual,
                        aroma,
                        paladar,
                        foto_path,
                    ),
                )
                st.success("Vinho salvo com sucesso.")

# -----------------------------
# Avaliar vinho
# -----------------------------
elif menu == "Avaliar vinho":
    st.subheader("Avaliação dos confrades")

    vinhos = query_df(
        """
        SELECT v.id, v.nome, e.data, e.titulo
        FROM vinhos v
        JOIN encontros e ON e.id = v.encontro_id
        ORDER BY e.id DESC, v.nome
        """
    )

    if vinhos.empty:
        st.warning("Cadastre um vinho primeiro.")
    else:
        vinhos["label"] = (
            vinhos["data"] + " - " + vinhos["titulo"] + " | " + vinhos["nome"]
        )

        with st.form("form_avaliacao"):
            vinho_label = st.selectbox("Vinho", vinhos["label"])
            vinho_id = int(vinhos.loc[vinhos["label"] == vinho_label, "id"].iloc[0])

            st.write(f"Avaliando como: **{st.session_state.usuario}**")

            nota = st.slider("Nota", 0.0, 10.0, 8.0, 0.5)
            repetiria = st.radio("Repetiria?", ["Sim", "Talvez", "Não"], horizontal=True)
            foi_balacobaco = st.radio("Foi Balacobaco?", ["Sim", "Muito", "Épico"], horizontal=True)
            comentario = st.text_area("Comentário")

            submit = st.form_submit_button("Salvar avaliação")

        if submit:
            execute(
                """
                INSERT INTO avaliacoes
                (vinho_id, confrade, nota, repetiria, foi_balacobaco, comentario)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    vinho_id,
                    st.session_state.usuario,
                    nota,
                    repetiria,
                    foi_balacobaco,
                    comentario,
                ),
            )
            st.success("Avaliação salva com sucesso.")

# -----------------------------
# Catálogo
# -----------------------------
elif menu == "Catálogo":
    st.subheader("Catálogo de vinhos")

    df = query_df(
        """
        SELECT
            v.id,
            v.encontro_id,
            e.data,
            e.titulo AS encontro,
            e.tema AS tema_encontro,
            v.nome,
            v.uva,
            v.pais,
            v.regiao,
            v.safra,
            v.produtor,
            v.tipo,
            v.classificacao,
            v.teor_alcoolico,
            v.temperatura_servico,
            v.harmonizacao,
            v.visual,
            v.aroma,
            v.paladar,
            ROUND(AVG(a.nota), 2) AS nota_media,
            COUNT(a.id) AS qtd_avaliacoes,
            v.foto_rotulo
        FROM vinhos v
        JOIN encontros e ON e.id = v.encontro_id
        LEFT JOIN avaliacoes a ON a.vinho_id = v.id
        GROUP BY v.id
        ORDER BY e.id DESC, v.nome
        """
    )

    if df.empty:
        st.info("Nenhum vinho cadastrado ainda.")
    else:
        df["ordem"] = df["encontro"].apply(ordem_encontro)

        encontros_filtro = ["Todos"] + (
            df.sort_values(["ordem", "encontro_id"], ascending=[False, False])["encontro"]
            .dropna()
            .drop_duplicates()
            .tolist()
        )

        filtro_encontro = st.selectbox("Filtrar por encontro", encontros_filtro)
        busca = st.text_input("Buscar vinho, uva, país ou região")

        df_filtrado = df.copy()

        if filtro_encontro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["encontro"] == filtro_encontro]

        if busca:
            mask = df_filtrado.apply(
                lambda row: row.astype(str).str.contains(busca, case=False).any(),
                axis=1,
            )
            df_filtrado = df_filtrado[mask]

        for _, row in df_filtrado.iterrows():
            with st.container(border=True):
                col_img, col_info = st.columns([1, 3])

                with col_img:
                    if row["foto_rotulo"] and Path(row["foto_rotulo"]).exists():
                        st.image(row["foto_rotulo"], width=160)
                    else:
                        st.write("🍷")

                with col_info:
                    st.markdown(f"### {row['nome']}")
                    st.write(f"**Encontro:** {row['data']} - {row['encontro']}")
                    if "tema_encontro" in row and row["tema_encontro"]:
                        st.write(f"**Tema:** {row['tema_encontro']}")
                    st.write(f"**Uva:** {row['uva']} | **País/Região:** {row['pais']} / {row['regiao']}")
                    st.write(f"**Safra:** {row['safra']} | **Produtor:** {row['produtor']}")
                    st.write(f"**Tipo:** {row['tipo']} | **Classificação:** {row['classificacao']}")
                    st.write(f"**Teor alcoólico:** {row['teor_alcoolico']} | **Temperatura:** {row['temperatura_servico']}")
                    st.write(f"**Harmonização:** {row['harmonizacao']}")
                    st.write(f"**Visual:** {row['visual']}")
                    st.write(f"**Aroma:** {row['aroma']}")
                    st.write(f"**Paladar:** {row['paladar']}")
                    st.write(
                        f"**Nota média:** {row['nota_media'] if pd.notna(row['nota_media']) else 'Sem avaliação'}"
                    )

                    with st.expander("Editar ficha técnica e características"):
                        with st.form(f"editar_vinho_{row['id']}"):
                            nome_edit = st.text_input("Nome do vinho", value=row["nome"] or "")
                            uva_edit = st.text_input("Uva", value=row["uva"] or "")
                            pais_edit = st.text_input("País", value=row["pais"] or "")
                            regiao_edit = st.text_input("Região", value=row["regiao"] or "")
                            safra_edit = st.text_input("Safra", value=row["safra"] or "")
                            produtor_edit = st.text_input("Produtor", value=row["produtor"] or "")
                            tipo_edit = st.text_input("Tipo", value=row["tipo"] or "")
                            classificacao_edit = st.text_input("Classificação", value=row["classificacao"] or "")
                            teor_edit = st.text_input("Teor alcoólico", value=row["teor_alcoolico"] or "")
                            temperatura_edit = st.text_input("Temperatura de serviço", value=row["temperatura_servico"] or "")
                            harmonizacao_edit = st.text_area("Harmonização", value=row["harmonizacao"] or "")
                            visual_edit = st.text_area("Visual", value=row["visual"] or "")
                            aroma_edit = st.text_area("Aroma", value=row["aroma"] or "")
                            paladar_edit = st.text_area("Paladar", value=row["paladar"] or "")

                            salvar_edit = st.form_submit_button("Salvar alterações")

                        if salvar_edit:
                            execute(
                                """
                                UPDATE vinhos
                                SET nome = ?, uva = ?, pais = ?, regiao = ?, safra = ?, produtor = ?,
                                    tipo = ?, classificacao = ?, teor_alcoolico = ?, temperatura_servico = ?,
                                    harmonizacao = ?, visual = ?, aroma = ?, paladar = ?
                                WHERE id = ?
                                """,
                                (
                                    nome_edit,
                                    uva_edit,
                                    pais_edit,
                                    regiao_edit,
                                    safra_edit,
                                    produtor_edit,
                                    tipo_edit,
                                    classificacao_edit,
                                    teor_edit,
                                    temperatura_edit,
                                    harmonizacao_edit,
                                    visual_edit,
                                    aroma_edit,
                                    paladar_edit,
                                    int(row["id"]),
                                ),
                            )
                            st.success("Vinho atualizado com sucesso.")
                            st.rerun()

# -----------------------------
# Rankings
# -----------------------------
elif menu == "Rankings":
    st.subheader("Rankings Balacobaco")

    ranking = query_df(
        """
        SELECT
            v.nome,
            v.uva,
            v.pais,
            v.safra,
            e.titulo AS encontro,
            ROUND(AVG(a.nota), 2) AS nota_media,
            COUNT(a.id) AS qtd_avaliacoes
        FROM vinhos v
        JOIN encontros e ON e.id = v.encontro_id
        JOIN avaliacoes a ON a.vinho_id = v.id
        GROUP BY v.id
        HAVING COUNT(a.id) > 0
        ORDER BY nota_media DESC, qtd_avaliacoes DESC
        """
    )

    if ranking.empty:
        st.info("Ainda não há avaliações suficientes para ranking.")
    else:
        st.markdown("### Top vinhos")
        st.dataframe(ranking, width="stretch")

        st.markdown("### Média por uva")
        por_uva = (
            ranking.groupby("uva", dropna=False)["nota_media"]
            .mean()
            .reset_index()
            .sort_values("nota_media", ascending=False)
        )
        st.bar_chart(por_uva, x="uva", y="nota_media")

        st.markdown("### Média por país")
        por_pais = (
            ranking.groupby("pais", dropna=False)["nota_media"]
            .mean()
            .reset_index()
            .sort_values("nota_media", ascending=False)
        )
        st.bar_chart(por_pais, x="pais", y="nota_media")

# -----------------------------
# Backup & Dados
# -----------------------------
elif menu == "Backup & Dados":
    if not usuario_admin:
        st.error("Acesso restrito.")
        st.stop()

    st.subheader("💾 Backup dos dados")

    encontros = query_df("SELECT * FROM encontros")
    vinhos = query_df("SELECT * FROM vinhos")
    avaliacoes = query_df("SELECT * FROM avaliacoes")

    st.markdown("### Baixar dados individuais")

    st.download_button(
        "⬇️ Baixar encontros",
        encontros.to_csv(index=False),
        "encontros.csv",
        "text/csv",
    )

    st.download_button(
        "⬇️ Baixar vinhos",
        vinhos.to_csv(index=False),
        "vinhos.csv",
        "text/csv",
    )

    st.download_button(
        "⬇️ Baixar avaliações",
        avaliacoes.to_csv(index=False),
        "avaliacoes.csv",
        "text/csv",
    )

    st.markdown("---")
    st.markdown("### Backup completo")

    backup = pd.concat(
        [
            encontros.assign(tipo_backup="encontros"),
            vinhos.assign(tipo_backup="vinhos"),
            avaliacoes.assign(tipo_backup="avaliacoes"),
        ],
        ignore_index=True,
        sort=False,
    )

    st.download_button(
        "⬇️ Baixar backup completo",
        backup.to_csv(index=False),
        "backup_balacobaco.csv",
        "text/csv",
    )

    st.markdown("---")
    st.markdown("### ⚠️ Administração")

    confirmar = st.checkbox("Confirmo que desejo limpar toda a base de dados")

    if confirmar and st.button("🧹 Limpar base de dados"):
        execute("DELETE FROM avaliacoes")
        execute("DELETE FROM vinhos")
        execute("DELETE FROM encontros")
        st.success("Base limpa com sucesso.")


    st.markdown("---")
    st.markdown("### 🔄 Restaurar backup completo")

    uploaded = st.file_uploader("Selecione o arquivo backup_balacobaco.csv", type=["csv"], key="upload_backup")

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)

            if "tipo_backup" not in df.columns:
                st.error("Arquivo inválido. Não contém coluna tipo_backup.")
            else:
                if st.button("Restaurar agora"):
                    # Limpa base
                    execute("DELETE FROM avaliacoes")
                    execute("DELETE FROM vinhos")
                    execute("DELETE FROM encontros")

                    # Encontros
                    encontros_df = df[df["tipo_backup"] == "encontros"].drop(columns=["tipo_backup"], errors="ignore")
                    if not encontros_df.empty:
                        for _, r in encontros_df.iterrows():
                            execute(
                                """
                                INSERT INTO encontros (id, data, titulo, tema, anfitrioes, local, observacoes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    int(r.get("id")),
                                    r.get("data"),
                                    r.get("titulo"),
                                    r.get("tema"),
                                    r.get("anfitrioes"),
                                    r.get("local"),
                                    r.get("observacoes"),
                                ),
                            )

                    # Vinhos
                    vinhos_df = df[df["tipo_backup"] == "vinhos"].drop(columns=["tipo_backup"], errors="ignore")
                    if not vinhos_df.empty:
                        for _, r in vinhos_df.iterrows():
                            execute(
                                """
                                INSERT INTO vinhos (id, encontro_id, nome, uva, pais, regiao, safra, produtor,
                                tipo, classificacao, teor_alcoolico, temperatura_servico, harmonizacao,
                                visual, aroma, paladar, foto_rotulo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    int(r.get("id")),
                                    int(r.get("encontro_id")),
                                    r.get("nome"),
                                    r.get("uva"),
                                    r.get("pais"),
                                    r.get("regiao"),
                                    r.get("safra"),
                                    r.get("produtor"),
                                    r.get("tipo"),
                                    r.get("classificacao"),
                                    r.get("teor_alcoolico"),
                                    r.get("temperatura_servico"),
                                    r.get("harmonizacao"),
                                    r.get("visual"),
                                    r.get("aroma"),
                                    r.get("paladar"),
                                    r.get("foto_rotulo"),
                                ),
                            )

                    # Avaliações
                    aval_df = df[df["tipo_backup"] == "avaliacoes"].drop(columns=["tipo_backup"], errors="ignore")
                    if not aval_df.empty:
                        for _, r in aval_df.iterrows():
                            execute(
                                """
                                INSERT INTO avaliacoes (id, vinho_id, confrade, nota, repetiria, foi_balacobaco, comentario)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    int(r.get("id")),
                                    int(r.get("vinho_id")),
                                    r.get("confrade"),
                                    float(r.get("nota")) if pd.notna(r.get("nota")) else None,
                                    r.get("repetiria"),
                                    r.get("foi_balacobaco"),
                                    r.get("comentario"),
                                ),
                            )

                    st.success("Backup restaurado com sucesso.")
        except Exception as e:
            st.error(f"Erro ao restaurar: {e}")
