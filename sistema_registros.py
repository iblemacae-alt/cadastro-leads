import os
import unicodedata
from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(100) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            data_hora VARCHAR(30) NOT NULL,
            usuario VARCHAR(100) NOT NULL,
            acao VARCHAR(100) NOT NULL,
            detalhes TEXT NOT NULL
        );
    """)
    
    cursor.execute("SELECT COUNT(*) FROM usuarios;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s);", ("admin", "admin"))
    
    conn.commit()
    cursor.close()
    conn.close()

try:
    criar_tabelas()
except Exception as e:
    st.error(f"Erro ao conectar ao Banco de Dados: {e}")

# --- FUNÇÕES AUXILIARES DE PADRONIZAÇÃO ---
def limpar_texto(texto):
    """Remove acentos e converte o texto para MAIÚSCULAS."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFD', str(texto))
    texto_sem_acento = "".join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.upper().strip()

def formatar_moeda(valor_str):
    """Formata qualquer valor numérico no padrão R$ 0,00."""
    if not valor_str:
        return ""
    texto = str(valor_str).replace("R$", "").strip()
    if not texto:
        return ""
    
    # Trata separadores decimais e de milhar
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
        
    try:
        val = float(texto)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        digits = "".join([c for c in texto if c.isdigit()])
        if not digits:
            return ""
        val = float(digits)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def registrar_historico(acao, detalhes):
    try:
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        usuario = st.session_state.get('usuario_atual', 'Sistema')
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historico (data_hora, usuario, acao, detalhes) VALUES (%s, %s, %s, %s);",
            (data_hora, usuario, limpar_texto(acao), limpar_texto(detalhes))
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

def gerar_html_relatorio(titulo, df):
    tabela_html = df.to_html(index=False, border=1, classes="tabela")
    usuario = st.session_state.get('usuario_atual', 'Sistema')
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
            h2 {{ color: #1a365d; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
            .info {{ font-size: 12px; color: #666; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; font-size: 12px; }}
            th {{ background-color: #f2f2f2; color: #1a365d; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h2>{titulo}</h2>
        <div class="info">Gerado por <strong>{usuario}</strong> em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</div>
        {tabela_html}
    </body>
    </html>
    """

# --- AUTENTICAÇÃO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario_atual' not in st.session_state:
    st.session_state['usuario_atual'] = ""

def realizar_login(user, pwd):
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios WHERE usuario = %s AND senha = %s;", (user.strip(), pwd.strip()))
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

if not st.session_state['autenticado']:
    col1, col2, col3 = st.columns([1.2, 1.6, 1.2])
    with col2:
        if os.path.exists("logo.png"):
            sub_col1, sub_col2, sub_col3 = st.columns([1, 2, 1])
            with sub_col2:
                st.image("logo.png", use_container_width=True)
        
        st.markdown("<h1 style='text-align: center;'>Cadastro de Leads</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #555;'>ible - Unidade Macaé</h3>", unsafe_allow_html=True)
        st.write("")
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                realizar_login(usuario_input, senha_input)
    st.stop()

# --- MENU LATERAL ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=150)

st.sidebar.title("📋 Menu do Sistema")
st.sidebar.info(f"Usuário ativo: **{st.session_state['usuario_atual']}**")

pagina = st.sidebar.radio(
    "Navegação",
    ["Cadastro e Consulta de Leads", "Editar / Excluir Registro", "Histórico de Operações", "Gerenciar Usuários"]
)

st.sidebar.markdown("---")
if st.sidebar.button("Sair / Deslogar", use_container_width=True):
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual'] = ""
    st.rerun()

# Listas padronizadas sem acento
CURSOS_OPCOES = ["INGLES", "INFORMATICA", "LIBRAS", "GESTAO", "MMR"]
SITUACAO_OPCOES = ["AGUARDANDO", "MATRICULADO", "DESISTENTE"]

# ==============================================================================
# PÁGINA 1: CADASTRO E CONSULTA DE LEADS
# ==============================================================================
if pagina == "Cadastro e Consulta de Leads":
    st.title("📋 Cadastro de Leads - ible Unidade Macaé")
    
    with st.expander("➕ Novo Registro", expanded=True):
        with st.form("form_novo_lead", clear_on_submit=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                data_reg = st.text_input("DATA", value=datetime.now().strftime("%d/%m/%Y"))
            with col2:
                responsavel = st.text_input("RESPONSAVEL")

            col3, col4, col5 = st.columns([2, 1, 1.5])
            with col3:
                aluno = st.text_input("ALUNO (Obrigatorio)")
            with col4:
                idade = st.text_input("IDADE")
            with col5:
                curso = st.selectbox("CURSO", CURSOS_OPCOES)

            col6, col7, col8, col9 = st.columns([1.2, 1.5, 0.8, 1.5])
            with col6:
                horario = st.text_input("HORARIO")
            with col7:
                telefone = st.text_input("TELEFONE (Max 11 digitos)", max_chars=11)
            with col8:
                st.write("")
                st.write("")
                whatsapp = st.checkbox("WHATSAPP")
            with col9:
                situacao = st.selectbox("SITUACAO", SITUACAO_OPCOES)

            observacao = st.text_area("OBSERVACAO", height=80)

            col10, col11 = st.columns(2)
            with col10:
                matricula = st.text_input("MATRICULA (Ex: 150)", placeholder="R$ 0,00")
            with col11:
                parcela = st.text_input("PARCELA (Ex: 220)", placeholder="R$ 0,00")

            st.caption("ℹ️ Todos os textos serão salvos automaticamente em MAIÚSCULAS e SEM ACENTOS. Valores formatados em R$ 0,00.")

            if st.form_submit_button("💾 SALVAR REGISTRO", type="primary"):
                if not aluno.strip():
                    st.warning("O campo ALUNO é obrigatório!")
                elif telefone and not telefone.isdigit():
                    st.warning("O campo TELEFONE deve conter apenas números!")
                else:
                    try:
                        aluno_limpo = limpar_texto(aluno)
                        mat_fmt = formatar_moeda(matricula)
                        par_fmt = formatar_moeda(parcela)
                        
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO registros (data, responsavel, aluno, idade, curso, horario, telefone, whatsapp, situacao, observacao, matricula, parcela)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            limpar_texto(data_reg), limpar_texto(responsavel), aluno_limpo, limpar_texto(idade),
                            limpar_texto(curso), limpar_texto(horario), telefone.strip(), 1 if whatsapp else 0,
                            limpar_texto(situacao), limpar_texto(observacao), mat_fmt, par_fmt
                        ))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        registrar_historico("CADASTRAR", f"Cadastrou o aluno '{aluno_limpo}' (Curso: {curso})")
                        st.success(f"Lead '{aluno_limpo}' salvo com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.subheader("🔍 Consultar e Filtrar Registros")

    col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1.5])
    with col_f1:
        busca_nome = limpar_texto(st.text_input("Buscar por Nome do Aluno"))
    with col_f2:
        filtro_curso = st.selectbox("Filtrar por Curso", ["TODOS OS CURSOS"] + CURSOS_OPCOES)
    with col_f3:
        filtro_situacao = st.selectbox("Filtrar por Situação", ["TODAS AS SITUACOES"] + SITUACAO_OPCOES)

    try:
        conn = conectar_bd()
        query = """
            SELECT id AS "ID", data AS "DATA", responsavel AS "RESPONSAVEL", aluno AS "ALUNO", 
                   idade AS "IDADE", curso AS "CURSO", horario AS "HORARIO", telefone AS "TELEFONE", 
                   CASE WHEN whatsapp = 1 THEN 'SIM' ELSE 'NAO' END AS "WHATSAPP",
                   situacao AS "SITUACAO", matricula AS "MATRICULA", parcela AS "PARCELA", observacao AS "OBSERVACAO"
            FROM registros WHERE 1=1
        """
        params = []
        if busca_nome:
            query += " AND aluno LIKE %s"
            params.append(f"%{busca_nome}%")
        if filtro_curso != "TODOS OS CURSOS":
            query += " AND curso = %s"
            params.append(filtro_curso)
        if filtro_situacao != "TODAS AS SITUACOES":
            query += " AND situacao = %s"
            params.append(filtro_situacao)

        query += " ORDER BY id DESC;"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            col_exp1, col_exp2, _ = st.columns([1.2, 1.2, 3])
            with col_exp1:
                csv_data = df.to_csv(index=False, sep=';').encode('utf-8-sig')
                st.download_button(
                    label="📥 Exportar Excel (.csv)",
                    data=csv_data,
                    file_name=f"leads_ible_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            with col_exp2:
                html_data = gerar_html_relatorio("Relatório de Cadastro de Leads - ible Macaé", df).encode('utf-8')
                st.download_button(
                    label="📄 Exportar Relatório (.html / PDF)",
                    data=html_data,
                    file_name=f"relatorio_leads_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        else:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
    except Exception as e:
        st.error(f"Erro ao carregar registros: {e}")

# ==============================================================================
# PÁGINA 2: EDITAR OU EXCLUIR REGISTRO
# ==============================================================================
elif pagina == "Editar / Excluir Registro":
    st.title("✏️ Editar ou Excluir Lead")
    
    try:
        conn = conectar_bd()
        df_lista = pd.read_sql_query("SELECT id, aluno, curso, situacao FROM registros ORDER BY id DESC;", conn)
        conn.close()

        if df_lista.empty:
            st.info("Não há registros cadastrados para editar.")
        else:
            opcoes = {f"ID {row['id']} - {row['aluno']} ({row['curso']} | {row['situacao']})": row['id'] for _, row in df_lista.iterrows()}
            escolha = st.selectbox("Selecione o registro que deseja alterar ou excluir:", list(opcoes.keys()))
            reg_id = opcoes[escolha]

            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registros WHERE id = %s;", (reg_id,))
            reg = cursor.fetchone()
            cursor.close()
            conn.close()

            if reg:
                curso_atual = limpar_texto(reg[5])
                idx_curso = CURSOS_OPCOES.index(curso_atual) if curso_atual in CURSOS_OPCOES else 0

                sit_atual = limpar_texto(reg[9])
                idx_sit = SITUACAO_OPCOES.index(sit_atual) if sit_atual in SITUACAO_OPCOES else 0

                with st.form("form_editar_lead"):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        ed_data = st.text_input("DATA", value=reg[1] or "")
                    with col2:
                        ed_resp = st.text_input("RESPONSAVEL", value=reg[2] or "")

                    col3, col4, col5 = st.columns([2, 1, 1.5])
                    with col3:
                        ed_aluno = st.text_input("ALUNO", value=reg[3] or "")
                    with col4:
                        ed_idade = st.text_input("IDADE", value=reg[4] or "")
                    with col5:
                        ed_curso = st.selectbox("CURSO", CURSOS_OPCOES, index=idx_curso)

                    col6, col7, col8, col9 = st.columns([1.2, 1.5, 0.8, 1.5])
                    with col6:
                        ed_horario = st.text_input("HORARIO", value=reg[6] or "")
                    with col7:
                        ed_tel = st.text_input("TELEFONE", value=reg[7] or "", max_chars=11)
                    with col8:
                        st.write("")
                        st.write("")
                        ed_wpp = st.checkbox("WHATSAPP", value=True if reg[8] == 1 else False)
                    with col9:
                        ed_sit = st.selectbox("SITUACAO", SITUACAO_OPCOES, index=idx_sit)

                    ed_obs = st.text_area("OBSERVACAO", value=reg[10] or "", height=80)

                    col10, col11 = st.columns(2)
                    with col10:
                        ed_mat = st.text_input("MATRICULA", value=reg[11] or "")
                    with col11:
                        ed_par = st.text_input("PARCELA", value=reg[12] or "")

                    if st.form_submit_button("✅ ATUALIZAR REGISTRO", type="primary"):
                        if not ed_aluno.strip():
                            st.warning("O campo ALUNO é obrigatório!")
                        else:
                            aluno_ed_limpo = limpar_texto(ed_aluno)
                            conn = conectar_bd()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE registros 
                                SET data=%s, responsavel=%s, aluno=%s, idade=%s, curso=%s, horario=%s, 
                                    telefone=%s, whatsapp=%s, situacao=%s, observacao=%s, matricula=%s, parcela=%s
                                WHERE id=%s;
                            """, (
                                limpar_texto(ed_data), limpar_texto(ed_resp), aluno_ed_limpo, limpar_texto(ed_idade),
                                limpar_texto(ed_curso), limpar_texto(ed_horario), ed_tel.strip(), 1 if ed_wpp else 0,
                                limpar_texto(ed_sit), limpar_texto(ed_obs), formatar_moeda(ed_mat), formatar_moeda(ed_par), reg_id
                            ))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            registrar_historico("ATUALIZAR", f"Atualizou o registro ID {reg_id} ('{aluno_ed_limpo}')")
                            st.success("Registro atualizado com sucesso!")
                            st.rerun()

                st.markdown("---")
                st.subheader("⚠️ Zona de Exclusão")
                if st.button(f"🗑️ Excluir definitivamente o registro ID {reg_id} ({reg[3]})"):
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM registros WHERE id = %s;", (reg_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    registrar_historico("EXCLUIR", f"Excluiu o registro ID {reg_id} ('{reg[3]}')")
                    st.success("Registro excluído!")
                    st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar edição: {e}")

# ==============================================================================
# PÁGINA 3: HISTÓRICO DE OPERAÇÕES
# ==============================================================================
elif pagina == "Histórico de Operações":
    st.title("🕒 Histórico de Ações dos Usuários")
    try:
        conn = conectar_bd()
        df_hist = pd.read_sql_query(
            'SELECT id AS "ID", data_hora AS "DATA/HORA", usuario AS "USUARIO", acao AS "ACAO", detalhes AS "DETALHES" FROM historico ORDER BY id DESC;',
            conn
        )
        conn.close()

        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            csv_hist = df_hist.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(
                label="📥 Exportar Histórico (.csv)",
                data=csv_hist,
                file_name=f"historico_ible_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma operação registrada no histórico ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

# ==============================================================================
# PÁGINA 4: GERENCIAR USUÁRIOS
# ==============================================================================
elif pagina == "Gerenciar Usuários":
    st.title("👥 Gerenciar Usuários de Acesso")

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.subheader("Cadastrar Novo Usuário")
        with st.form("form_novo_usuario", clear_on_submit=True):
            novo_u = st.text_input("Nome de Usuário")
            nova_s = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar Usuário", type="primary"):
                if not novo_u.strip() or not nova_s.strip():
                    st.warning("Preencha usuário e senha!")
                else:
                    try:
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s);", (novo_u.strip(), nova_s.strip()))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        registrar_historico("CRIAR USUARIO", f"Criou o usuario '{novo_u.strip()}'")
                        st.success(f"Usuário '{novo_u.strip()}' criado com sucesso!")
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("Esse nome de usuário já existe!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with col_u2:
        st.subheader("Usuários Cadastrados")
        try:
            conn = conectar_bd()
            df_users = pd.read_sql_query("SELECT id, usuario FROM usuarios ORDER BY id;", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            usuarios_removiveis = [u for u in df_users['usuario'].tolist() if u != "admin"]
            if usuarios_removiveis:
                user_del = st.selectbox("Selecionar usuário para remover", usuarios_removiveis)
                if st.button("Excluir Usuário Selecionado"):
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE usuario = %s;", (user_del,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    registrar_historico("EXCLUIR USUARIO", f"Excluiu o usuario '{user_del}'")
                    st.success(f"Usuário '{user_del}' removido!")
                    st.rerun()
        except Exception as e:
            st.error(f"Erro ao listar usuários: {e}")
