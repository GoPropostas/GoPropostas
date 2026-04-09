import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Frei Galvão", layout="wide")

# Inicialização do banco de dados temporário
if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO PARA GERAR O PDF ---
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Cabeçalho
    pdf.cell(200, 10, "PROPOSTA DE COMPRA - RESIDENCIAL FREI GALVÃO", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DADOS DO PROPONENTE", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Nome: {dados['nome'].upper()}", ln=True)
    pdf.cell(0, 8, f"CPF: {dados['cpf']}", ln=True)
    pdf.ln(5)
    
    # Dados do Imóvel
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IDENTIFICAÇÃO DO BEM", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Unidade: {dados['unidade']}", ln=True)
    pdf.cell(0, 8, f"Valor Total: R$ {dados['valor_total']:,.2f}", ln=True)
    pdf.ln(5)
    
    # Condições de Pagamento
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "CONDIÇÕES DE PAGAMENTO", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Entrada (Ato + Intermed.): R$ {dados['entrada_total']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Parcelamento: 36x de R$ {dados['v_parcela_36']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Residual após 36 meses: R$ {dados['saldo_residual']:,.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    obs = ("Nota: As primeiras 36 parcelas possuem apenas correção de IPCA. "
           "O saldo devedor remanescente poderá ser quitado ou financiado em até 204 meses "
           "com juros de 0,7% a.m. + IPCA direto com o empreendedor.")
    pdf.multi_cell(0, 5, obs)
    
    # Gera o PDF em memória para o Streamlit baixar
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Menu Principal")
aba = st.sidebar.radio("Ir para:", ["Corretor (Vendas)", "Admin (Upload de Tabela)"])

# --- ABA ADMIN ---
if aba == "Admin (Upload de Tabela)":
    st.header("⚙️ Configurações do Sistema")
    senha = st.text_input("Senha de Moderador", type="password")
    
    if senha == "admin123":
        st.success("Acesso Liberado!")
        nome_loteamento = st.text_input("Nome do Loteamento (ex: Frei Galvão)")
        arquivo_excel = st.file_uploader("Suba a planilha do Excel (.xlsx)", type=['xlsx'])
        
        if arquivo_excel and nome_loteamento:
            df = pd.read_excel(arquivo_excel)
            st.session_state['loteamentos'][nome_loteamento] = df
            st.success(f"Tabela {nome_loteamento} ativa com sucesso!")
            st.dataframe(df.head())

# --- ABA CORRETOR ---
else:
    st.header("📝 Nova Proposta de Venda")
    
    if not st.session_state['loteamentos']:
        st.warning("⚠️ O Moderador precisa subir uma tabela no Painel Admin antes de começar.")
    else:
        lote_ref = st.selectbox("Selecione o Empreendimento", list(st.session_state['loteamentos'].keys()))
        tabela = st.session_state['loteamentos'][lote_ref]
        
        col1, col2 = st.columns(2)
        with col1:
            nome_cli = st.text_input("Nome do Cliente")
            cpf_cli = st.text_input("CPF do Cliente")
        
        with col2:
            # Seleciona a unidade baseada na planilha
            unid_sel = st.selectbox("Selecione o Lote/Quadra", tabela['Unidade'].unique())
            dados_lote = tabela[tabela['Unidade'] == unid_sel].iloc[0]
            
            # Puxa os valores da tabela
            valor_venda = float(dados_lote['Valor Total R$'])
            v_parcela_36 = float(dados_lote['36x'])
            
            st.metric("Valor do Imóvel", f"R$ {valor_venda:,.2f}")

        # Cálculos de Entrada (1% ato + 5.3% comissão)
        v_ato = valor_venda * 0.01
        v_comissao = valor_venda * 0.053
        ent_total = v_ato + v_comissao
        saldo_pos_36 = valor_venda - ent_total - (v_parcela_36 * 36)

        st.divider()
        st.subheader("Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Ato + Intermed.:** R$ {ent_total:,.2f}")
        c2.write(f"**36 Parcelas de:** R$ {v_parcela_36:,.2f}")
        c3.write(f"**Saldo após 36m:** R$ {saldo_pos_36:,.2f}")

        if st.button("🚀 Gerar PDF"):
            if nome_cli and cpf_cli:
                payload = {
                    'nome': nome_cli,
                    'cpf': cpf_cli,
                    'unidade': unid_sel,
                    'valor_total': valor_venda,
                    'entrada_total': ent_total,
                    'v_ato': v_ato,
                    'v_intermed': v_comissao,
                    'v_parcela_36': v_parcela_36,
                    'saldo_residual': saldo_pos_36
                }
                pdf_output = gerar_pdf(payload)
                st.download_button(
                    label="📥 Baixar Proposta Pronta",
                    data=pdf_output,
                    file_name=f"Proposta_{nome_cli}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Preencha o nome e CPF do cliente!")