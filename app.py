import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador de Propostas - Frei Galvão", layout="wide")

# Inicialização do banco de dados na sessão
if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO PARA GERAR O PDF ---
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(200, 10, "PROPOSTA DE COMPRA - RESIDENCIAL", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Proponente
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "1. DADOS DO PROPONENTE", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 8, f"Nome: {dados['nome'].upper()}", ln=True)
    pdf.cell(0, 8, f"CPF: {dados['cpf']}", ln=True)
    
    pdf.ln(5)
    
    # Dados do Imóvel
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "2. IDENTIFICAÇÃO DO BEM", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 8, f"Empreendimento: {dados['loteamento']}", ln=True)
    pdf.cell(0, 8, f"Unidade: {dados['unidade']}", ln=True)
    pdf.cell(0, 8, f"Valor do Imóvel: R$ {dados['valor_total']:,.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("helvetica", 'I', 9)
    pdf.multi_cell(0, 5, "Esta proposta é válida por 48 horas e está sujeita a confirmação de disponibilidade e análise de crédito.")
    
    return pdf.output().encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Sistema de Vendas")
aba = st.sidebar.radio("Navegação", ["Corretor (Vendas)", "Moderador (Admin)"])

# --- ABA ADMIN (UPLOAD) ---
if aba == "Moderador (Admin)":
    st.header("⚙️ Configuração de Tabelas")
    senha = st.text_input("Senha de Acesso", type="password")
    
    if senha == "admin123":
        nome_lote = st.text_input("Nome do Empreendimento (ex: Frei Galvão)")
        arquivo_excel = st.file_uploader("Suba a tabela Excel", type=['xlsx'])
        
        if arquivo_excel and nome_lote:
            try:
                # PASSO 1: Lê o Excel bruto para descobrir onde a tabela começa
                df_raw = pd.read_excel(arquivo_excel, header=None)
                
                # PASSO 2: Localiza a linha que contém palavras-chave (ignora o logo/CNPJ no topo)
                linha_cabecalho = 0
                for i, row in df_raw.iterrows():
                    # Se a linha contiver "Unidade", "Lote" ou "Quadra", assumimos que é o cabeçalho
                    if row.astype(str).str.contains('Unidade|Lote|Quadra|Descrição', case=False).any():
                        linha_cabecalho = i
                        break
                
                # PASSO 3: Recarrega o Excel pulando as linhas inúteis
                df = pd.read_excel(arquivo_excel, skiprows=linha_cabecalho)
                
                # LIMPEZA: Remove colunas "Unnamed" geradas por células vazias/mescladas
                df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed|^nan')]
                df = df.dropna(how='all', axis=0) # Remove linhas totalmente vazias
                
                st.session_state['loteamentos'][nome_lote] = df
                st.success(f"Tabela '{nome_lote}' carregada com sucesso!")
                
                st.write("### Prévia dos dados detectados:")
                st.dataframe(df.head(10))
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                st.info("Dica: Tente remover células mescladas no topo do seu Excel antes de subir.")

# --- ABA CORRETOR (VENDAS) ---
else:
    st.header("📝 Nova Proposta de Venda")
    
    if not st.session_state['loteamentos']:
        st.info("Aguardando o Moderador subir a tabela no Painel Admin.")
    else:
        lote_sel = st.selectbox("Selecione o Empreendimento", list(st.session_state['loteamentos'].keys()))
        tabela = st.session_state['loteamentos'][lote_sel]
        
        # Identifica as colunas dinamicamente
        colunas = tabela.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            # Assume que a primeira coluna é a identificação da unidade
            unidade = st.selectbox("Selecione a Unidade", tabela[colunas[0]].unique())
            dados_unidade = tabela[tabela[colunas[0]] == unidade].iloc[0]
            
        with col2:
            st.markdown(f"**Detalhes da Unidade:** {unidade}")
            # Tenta encontrar um valor numérico na segunda ou terceira coluna
            try:
                # Limpa R$, pontos e vírgulas para converter em número
                raw_val = str(dados_unidade[colunas[1]])
                valor_limpo = raw_val.replace('R$', '').replace('.', '').replace(',', '.')
                valor_final = float(valor_limpo)
                st.metric("Valor do Lote", f"R$ {valor_final:,.2f}")
            except:
                valor_final = 0.0
                st.warning("Não foi possível extrair o preço automático.")

        st.divider()
        nome_cli = st.text_input("Nome do Cliente")
        cpf_cli = st.text_input("CPF do Cliente")

        if st.button("🚀 Gerar Proposta em PDF"):
            if nome_cli and cpf_cli:
                dados_pdf = {
                    'nome': nome_cli,
                    'cpf': cpf_cli,
                    'loteamento': lote_sel,
                    'unidade': unidade,
                    'valor_total': valor_final
                }
                pdf_bytes = gerar_pdf(dados_pdf)
                st.download_button(
                    label="📥 Baixar Arquivo PDF",
                    data=pdf_bytes,
                    file_name=f"Proposta_{unidade}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Preencha todos os campos do cliente.")
        
        with st.expander("Ver todos os dados desta unidade"):
            st.write(dados_unidade.to_dict())