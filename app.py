import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Propostas - Loteamentos", layout="wide")

# Inicializa o armazenamento na sessão para não perder os dados ao navegar
if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO PARA GERAR O PDF ---
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "PROPOSTA DE COMPRA E VENDA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. DADOS DO CLIENTE", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Nome: {dados['nome'].upper()}", ln=True)
    pdf.cell(0, 8, f"CPF: {dados['cpf']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DADOS DO IMÓVEL", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Loteamento: {dados['loteamento']}", ln=True)
    pdf.cell(0, 8, f"Unidade: {dados['unidade']}", ln=True)
    pdf.cell(0, 8, f"Valor Total: R$ {dados['valor_total']:,.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    obs = "Esta proposta está sujeita a análise de crédito e disponibilidade de estoque."
    pdf.multi_cell(0, 10, obs)
    
    return pdf.output(dest='S').encode('latin-1')

# --- MENU LATERAL ---
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Selecione o acesso:", ["Corretor (Vendas)", "Moderador (Admin)"])

# --- MÓDULO MODERADOR (ADMIN) ---
if aba == "Moderador (Admin)":
    st.header("⚙️ Painel de Controle")
    senha = st.text_input("Digite a senha de administrador", type="password")
    
    if senha == "admin123":
        st.success("Acesso autorizado.")
        nome_empreendimento = st.text_input("Nome do Loteamento (Ex: Residencial Frei Galvão)")
        arquivo_excel = st.file_uploader("Suba a planilha de lotes (Excel)", type=['xlsx'])
        
        if arquivo_excel and nome_empreendimento:
            try:
                # Lê o excel tentando pular linhas vazias automagicamente
                df = pd.read_excel(arquivo_excel)
                
                # LIMPEZA: Remove colunas e linhas totalmente vazias
                df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
                
                # Se os nomes das colunas forem "Unnamed", tenta usar a primeira linha de dados como cabeçalho
                if "Unnamed" in str(df.columns):
                    df.columns = df.iloc[0]
                    df = df[1:]
                
                # Resetar o índice
                df = df.reset_index(drop=True)
                
                st.session_state['loteamentos'][nome_empreendimento] = df
                st.success(f"Tabela '{nome_empreendimento}' carregada com sucesso!")
                
                st.write("### Prévia da Tabela Carregada:")
                st.dataframe(df.head(10))
                
            except Exception as e:
                st.error(f"Erro ao processar o Excel: {e}")

# --- MÓDULO CORRETOR (VENDAS) ---
else:
    st.header("📝 Gerador de Propostas")
    
    if not st.session_state['loteamentos']:
        st.warning("Nenhuma tabela disponível. O Moderador precisa subir os dados no Painel Admin.")
    else:
        # Seleção do Loteamento
        loteamento_sel = st.selectbox("Escolha o Loteamento", list(st.session_state['loteamentos'].keys()))
        tabela_ativa = st.session_state['loteamentos'][loteamento_sel]
        
        # Identificação automática das colunas por posição (mais seguro que por nome)
        cols = tabela_ativa.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            # Coluna 0 geralmente é a Unidade/Lote
            unidade_escolhida = st.selectbox("Selecione o Lote/Unidade", tabela_ativa[cols[0]].unique())
            dados_lote = tabela_ativa[tabela_ativa[cols[0]] == unidade_escolhida].iloc[0]
            
        with col2:
            # Tenta encontrar o valor. Se não souber o nome da coluna, mostra tudo que achou
            st.info(f"Unidade selecionada: {unidade_escolhida}")
            # Aqui você pode ajustar o índice conforme sua planilha (ex: cols[1] para preço)
            try:
                valor_total = float(str(dados_lote[cols[1]]).replace('R$', '').replace('.', '').replace(',', '.'))
                st.metric("Preço de Tabela", f"R$ {valor_total:,.2f}")
            except:
                st.warning("Não foi possível calcular o valor automaticamente. Confira a tabela abaixo.")
                valor_total = 0.0

        st.write("---")
        st.subheader("Dados do Cliente")
        c1, c2 = st.columns(2)
        with c1:
            nome_cli = st.text_input("Nome Completo")
        with c2:
            cpf_cli = st.text_input("CPF")

        if st.button("✅ Gerar e Baixar Proposta"):
            if nome_cli and cpf_cli:
                pdf_info = {
                    'nome': nome_cli,
                    'cpf': cpf_cli,
                    'loteamento': loteamento_sel,
                    'unidade': unidade_escolhida,
                    'valor_total': valor_total
                }
                pdf_final = gerar_pdf(pdf_info)
                st.download_button(
                    label="📥 Clique aqui para Baixar PDF",
                    data=pdf_final,
                    file_name=f"Proposta_{unidade_escolhida}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Por favor, preencha o Nome e o CPF do cliente.")

        # Mostra os detalhes técnicos para o corretor conferir
        with st.expander("Ver detalhes completos da unidade"):
            st.write(dados_lote.to_dict())