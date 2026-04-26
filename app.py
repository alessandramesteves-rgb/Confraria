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

    # Compatibilidade com versões anteriores do banco
    novas_colunas_vinhos = {
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
    if st.button("Entrar"):
        if nome.strip():
            st.session_state.usuario = nome.strip()
            st.rerun()
        else:
            st.warning("Informe seu nome.")
    st.stop()

ADMIN_NOMES = ["Alê", "Ale", "Alessandra"]
usuario_admin = st.session_state.usuario in ADMIN_NOMES

st.sidebar.write(f"👤 {st.session_state.usuario}")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
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

# Ao entrar no Dashboard, mostra apenas a lista de encontros.
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
    encontros = query_df("SELECT * FROM encontros ORDER BY data DESC")
    vinhos = query_df("SELECT * FROM vinhos")
    avaliacoes = query_df("SELECT * FROM avaliacoes")

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

        for _, row in encontros.iterrows():
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"### {row['titulo']}")
                    st.write(f"**Data:** {row['data']}")
                    st.write(f"**Anfitriões:** {row['anfitrioes'] if row['anfitrioes'] else '-'}")
                    st.write(f"**Local:** {row['local'] if row['local'] else '-'}")
                with col_btn:
                    if st.button("Ver vinhos", key=f"ver_vinhos_{row['id']}"):
                        st.session_state.dashboard_encontro_id = int(row["id"])

        if st.session_state.dashboard_encontro_id:
            encontro_sel = encontros[encontros["id"] == st.session_state.dashboard_encontro_id].iloc[0]
            st.divider()
            st.subheader(f"Vinhos do encontro: {encontro_sel['titulo']}")
            vinhos_do_dia = query_df(
                """
                SELECT
                    v.nome,
                    v.uva,
                    v.pais,
                    v.regiao,
                    v.safra,
                    v.tipo,
                    ROUND(AVG(a.nota), 2) AS nota_media,
                    COUNT(a.id) AS qtd_avaliacoes
                FROM vinhos v
                LEFT JOIN avaliacoes a ON a.vinho_id = v.id
                WHERE v.encontro_id = ?
                GROUP BY v.id
                ORDER BY v.nome
                """,
                (st.session_state.dashboard_encontro_id,),
            )
            if vinhos_do_dia.empty:
                st.info("Ainda não há vinhos cadastrados para este encontro.")
            else:
                st.dataframe(vinhos_do_dia, width="stretch")

# -----------------------------
# Novo encontro
# -----------------------------
elif menu == "Novo encontro":
    st.subheader("Novo encontro")
    with st.form("form_encontro"):
        data_encontro = st.date_input("Data", value=date.today())
        titulo = st.text_input("Título do encontro", placeholder="Ex.: Noite Italiana")
        anfitrioes = st.text_input("Anfitriões", placeholder="Ex.: Alê & Ale")
        local = st.text_input("Local")
        observacoes = st.text_area("Observações")
        submit = st.form_submit_button("Salvar encontro")

    if submit:
        if not titulo:
            st.error("Informe o título do encontro.")
        else:
            execute(
                "INSERT INTO encontros (data, titulo, anfitrioes, local, observacoes) VALUES (?, ?, ?, ?, ?)",
                (str(data_encontro), titulo, anfitrioes, local, observacoes),
            )
            st.success("Encontro salvo com sucesso.")

# -----------------------------
# Cadastrar vinho
# -----------------------------
elif menu == "Cadastrar vinho":
    st.subheader("Cadastrar vinho degustado")
    encontros = query_df("SELECT id, data, titulo FROM encontros ORDER BY data DESC")

    if encontros.empty:
        st.warning("Cadastre um encontro primeiro.")
    else:
        encontros["label"] = encontros["data"] + " - " + encontros["titulo"]

        with st.form("form_vinho"):
            encontro_label = st.selectbox("Encontro", encontros["label"])
            encontro_id = int(encontros.loc[encontros["label"] == encontro_label, "id"].iloc[0])

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
                    (encontro_id, nome, uva, pais, regiao, safra, produtor, tipo, classificacao,
                     teor_alcoolico, temperatura_servico, harmonizacao, visual, aroma, paladar, foto_rotulo)
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
        ORDER BY e.data DESC, v.nome
        """
    )

    if vinhos.empty:
        st.warning("Cadastre um vinho primeiro.")
    else:
        vinhos["label"] = vinhos["data"] + " - " + vinhos["titulo"] + " | " + vinhos["nome"]
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
                INSERT INTO avaliacoes (vinho_id, confrade, nota, repetiria, foi_balacobaco, comentario)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (vinho_id, st.session_state.usuario, nota, repetiria, foi_balacobaco, comentario),
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
        ORDER BY e.data DESC, v.nome
        """
    )

    if df.empty:
        st.info("Nenhum vinho cadastrado ainda.")
    else:
        encontros_filtro = ["Todos"] + sorted(df["encontro"].dropna().unique().tolist())
        filtro_encontro = st.selectbox("Filtrar por encontro", encontros_filtro)
        busca = st.text_input("Buscar vinho, uva, país ou região")

        df_filtrado = df.copy()
        if filtro_encontro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["encontro"] == filtro_encontro]
        if busca:
            mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
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
                    st.write(f"**Uva:** {row['uva']} | **País/Região:** {row['pais']} / {row['regiao']}")
                    st.write(f"**Safra:** {row['safra']} | **Produtor:** {row['produtor']}")
                    st.write(f"**Tipo:** {row['tipo']} | **Classificação:** {row['classificacao']}")
                    st.write(f"**Teor alcoólico:** {row['teor_alcoolico']} | **Temperatura:** {row['temperatura_servico']}")
                    st.write(f"**Harmonização:** {row['harmonizacao']}")
                    st.write(f"**Visual:** {row['visual']}")
                    st.write(f"**Aroma:** {row['aroma']}")
                    st.write(f"**Paladar:** {row['paladar']}")
                    st.write(f"**Nota média:** {row['nota_media'] if pd.notna(row['nota_media']) else 'Sem avaliação'}")

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
                            st.success("Vinho atualizado com sucesso. Atualize a página para visualizar os dados revisados.")

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
        por_uva = ranking.groupby("uva", dropna=False)["nota_media"].mean().reset_index().sort_values("nota_media", ascending=False)
        st.bar_chart(por_uva, x="uva", y="nota_media")

        st.markdown("### Média por país")
        por_pais = ranking.groupby("pais", dropna=False)["nota_media"].mean().reset_index().sort_values("nota_media", ascending=False)
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
    st.download_button("⬇️ Baixar encontros", encontros.to_csv(index=False), "encontros.csv", "text/csv")
    st.download_button("⬇️ Baixar vinhos", vinhos.to_csv(index=False), "vinhos.csv", "text/csv")
    st.download_button("⬇️ Baixar avaliações", avaliacoes.to_csv(index=False), "avaliacoes.csv", "text/csv")

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
    st.download_button("⬇️ Baixar backup completo", backup.to_csv(index=False), "backup_balacobaco.csv", "text/csv")

    st.markdown("---")
    st.markdown("### ⚠️ Administração")
    confirmar = st.checkbox("Confirmar limpeza da base")
    if confirmar and st.button("🧹 Limpar base de dados"):
        execute("DELETE FROM avaliacoes")
        execute("DELETE FROM vinhos")
        execute("DELETE FROM encontros")
        st.success("Base limpa com sucesso.")
