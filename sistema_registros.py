import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Cadastro de Leads - ible Macaé",
    page_icon="📋",
    layout="wide"
)

# --- CONEXÃO COM O BANCO DE DADOS NA NUVEM (SUPABASE) ---
def conectar_bd():
    return psycopg2.connect(
        host=st.secrets.get("postgres", {}).get("host", "aws-1-us-east-1.pooler.supabase.com"),
        database=st.secrets.get("postgres", {}).get("database", "postgres"),
        user=st.secrets.get("postgres", {}).get("user", "postgres.wnzmjdsbxkoqsvgvkkbg"),
        password=st.secrets.get("postgres", {}).get("password", "MarcioJamilleMel"),
        port=st.secrets.get("postgres", {}).get("port", "5432")
    )

# --- INICIALIZAÇÃO DAS TABELAS ---
def criar_tabelas():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Tabela Principal de Registros (Leads)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY,
            data VARCHAR(20),
            responsavel VARCHAR(250),
            aluno VARCHAR(250),
            idade VARCHAR(50),
            curso VARCHAR(100),
            horario VARCHAR(100),
            telefone VARCHAR(50),
            whatsapp INTEGER,
            situacao VARCHAR(50),
            observacao TEXT,
            matricula VARCHAR(50),
            parcela VARCHAR(50)
        );
    """)
    
    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(100) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL
        );
    """)
    
    # Adiciona usuário padrão (admin / admin) se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s);", ("admin", "admin"))
    
    conn.commit()
    cursor.close()
    conn.close()

try:
    criar_tabelas()
except Exception as e:
    st.error(f"Erro ao conectar ao Banco de Dados na nuvem: {e}")

# --- CONTROLE DE SESSÃO / LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario_atual' not in st.session_state:
    st.session_state['usuario_atual'] = ""

def realizar_login(user, pwd):
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios WHERE usuario = %s AND senha = %s;", (user, pwd))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res:
            st.session_state['autenticado'] = True
            st.session_state['usuario_atual'] = res[0]
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")

# --- TELA DE LOGIN ---
if not st.session_state['autenticado']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>Cadastro de Leads</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #555;'>ible - Unidade Macaé</h3>", unsafe_allow_html=True)
        st.write("")
        
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("ENTRAR", use_container_width=True)
            
            if btn_entrar:
                realizar_login(usuario_input, senha_input)
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"Usuário ativo: {st.session_state['usuario_atual']}")
if st.sidebar.button("Sair / Deslogar"):
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual'] = ""
    st.rerun()

st.title("📋 Cadastro de Leads")
st.markdown("---")

# --- FORMULÁRIO DE CADASTRO ---
st.subheader("Novo Registro")
with st.form("form_registro", clear_on_submit=True):
    col_d, col_r = st.columns([1, 3])
    with col_d:
        data_reg = st.text_input("DATA", value=datetime.now().strftime("%d/%m/%Y"))
    with col_r:
        responsavel = st.text_input("RESPONSÁVEL").upper()

    col_a, col_i, col_c = st.columns([2, 1, 1.5])
    with col_a:
        aluno = st.text_input("ALUNO (Obrigatório)").upper()
    with col_i:
        idade = st.text_input("IDADE").upper()
    with col_c:
        curso = st.selectbox("CURSO", ["INGLÊS", "INFORMÁTICA", "LIBRAS", "GESTÃO", "MMR"])

    col_h, col_t, col_w, col_s = st.columns([1.2, 1.5, 0.8, 1.5])
    with col_h:
        horario = st.text_input("HORÁRIO").upper()
    with col_t:
        telefone = st.text_input("TELEFONE")
    with col_w:
        whatsapp = st.checkbox("WHATSAPP")
    with col_s:
        situacao = st.selectbox("SITUAÇÃO", ["AGUARDANDO", "MATRICULADO", "DESISTENTE"])

    observacao = st.text_area("OBSERVAÇÃO").upper()

    col_m, col_p = st.columns([1, 1])
    with col_m:
        matricula = st.text_input("MATRÍCULA (R$)")
    with col_p:
        parcela = st.text_input("PARCELA (R$)")

    btn_salvar = st.form_submit_button("SALVAR REGISTRO")

    if btn_salvar:
        if not aluno.strip():
            st.warning("O campo ALUNO é obrigatório!")
        else:
            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO registros (data, responsavel, aluno, idade, curso, horario, telefone, whatsapp, situacao, observacao, matricula, parcela)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (data_reg, responsavel, aluno, idade, curso, horario, telefone, 1 if whatsapp else 0, situacao, observacao, matricula, parcela))
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"Lead '{aluno}' cadastrado com sucesso no banco de dados!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar registro: {e}")

st.markdown("---")

# --- CONSULTA E FILTROS COMBINADOS ---
st.subheader("🔍 Consultar e Filtrar Registros")

col_b1, col_b2, col_b3 = st.columns([2, 1.5, 1.5])
with col_b1:
    busca_nome = st.text_input("Buscar por Nome do Aluno").upper()
with col_b2:
    filtro_curso = st.selectbox("Filtrar por Curso", ["TODOS OS CURSOS", "INGLÊS", "INFORMÁTICA", "LIBRAS", "GESTÃO", "MMR"])
with col_b3:
    filtro_situacao = st.selectbox("Filtrar por Situação", ["TODAS AS SITUAÇÕES", "AGUARDANDO", "MATRICULADO", "DESISTENTE"])

# Leitura e exibição dos dados salvos no Supabase
try:
    conn = conectar_bd()
    query = "SELECT id, data, responsavel, aluno, idade, curso, horario, telefone, situacao, matricula, parcela, observacao FROM registros WHERE 1=1"
    params = []

    if busca_nome:
        query += " AND aluno LIKE %s"
        params.append(f"%{busca_nome}%")
    if filtro_curso != "TODOS OS CURSOS":
        query += " AND curso = %s"
        params.append(filtro_curso)
    if filtro_situacao != "TODAS AS SITUAÇÕES":
        query += " AND situacao = %s"
        params.append(filtro_situacao)

    query += " ORDER BY id DESC;"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Download da tabela em Excel (.csv)
        csv_data = df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📥 Exportar Registros para Excel (.csv)",
            data=csv_data,
            file_name=f"relatorio_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum registro encontrado.")
except Exception as e:
    st.error(f"Erro ao consultar registros: {e}")
