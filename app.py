import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador Home Buy - Frei Galvão", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO PARA GERAR O PDF DETALHADO (MODELO HOME BUY) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(5)

def gerar_pdf_home_buy(d):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # --- SEÇÃO 1: PROPONENTE ---
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 7, "DADOS DO PROPONENTE", 1, 1, 'L', 1)
    pdf.cell(130, 7, f"Nome: {d['nome']}", 1)
    pdf.cell(60, 7, f"CPF/CNPJ: {d['cpf']}", 1, 1)
    pdf.cell(60, 7, f"Nacionalidade: {d['nacionalidade']}", 1)
    pdf.cell(70, 7, f"Profissao: {d['profissao']}", 1)
    pdf.cell(60, 7, f"Estado Civil: {d['estado_civil']}", 1, 1)
    pdf.cell(0, 7, f"Email: {d['email']}", 1, 1)
    
    # --- SEÇÃO 2: IMÓVEL E VALORES ---
    pdf.ln(5)
    pdf.cell(0, 7, "CARACTERIZAÇÃO DO IMÓVEL E CONDIÇÕES", 1, 1, 'L', 1)
    pdf.cell(100, 7, f"Empreendimento: {d['loteamento']}", 1)
    pdf.cell(90, 7, f"Unidade: {d['unidade']}", 1, 1)
    
    pdf.cell(60, 7, f"Valor Total: R$ {d['valor']:,.2f}", 1)
    pdf.cell(65, 7, f"Ato (1%): R$ {d['ato']:,.2f}", 1)
    pdf.cell(65, 7, f"Intermed. (5.3%): R$ {d['intermed']:,.2f}", 1, 1)
    
    pdf.cell(0, 7, f"Parcelamento: 36 parcelas mensais de R$ {d['p36']:,.2f}", 1, 1)
    
    # --- TEXTO LEGAL ---
    pdf.ln(5)
    pdf.set_font("Arial", size=8)
    clausula = ("O proponente declara ter conhecimento das condicoes de venda e que a presente proposta "
                "esta sujeita a analise de credito. O saldo devedor sera corrigido mensalmente pelo IPCA.")
    pdf.multi_cell(0, 5, clausula, 1)
    
    pdf.ln(10)
    pdf.cell(95, 10, "________________________________", 0, 0, 'C')
    pdf.cell(95, 10, "________________________________", 0, 1, 'C')
    pdf.cell(95, 5, "Assinatura do Proponente", 0, 0, 'C')
    pdf.cell(95, 5, "Home Buy Negocios Imobiliarios", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Vendas", "Admin"])

if aba == "Admin":
    st.header("⚙️ Painel Admin")
    if st.text_input("Senha", type="password") == "admin123":
        arquivo = st.file_uploader("Suba a planilha Frei Galvão", type=['xlsx'])
        if arquivo:
            df = pd.read_excel(arquivo, skiprows=11)
            df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
            st.session_state['loteamentos']["Frei Galvão"] = df
            st.success("Tabela carregada!")

else:
    st.header("📝 Formulário de Proposta - Home Buy")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        cols = df.columns.tolist()
        
        # Filtro de Lote
        lotes_validos = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]
        
        with st.expander("1. Seleção do Imóvel", expanded=True):
            unidade = st.selectbox("Selecione a Unidade", lotes_validos[cols[0]].unique())
            dados = lotes_validos[lotes_validos[cols[0]] == unidade].iloc[0]
            
            v_total = float(dados[cols[2]])
            v_36x = float(dados[cols[7]])
            v_ato = v_total * 0.01
            v_inter = v_total * 0.053
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Valor Total", f"R$ {v_total:,.2f}")
            c2.metric("Entrada (Ato+Inter)", f"R$ {(v_ato+v_inter):,.2f}")
            c3.metric("36x", f"R$ {v_36x:,.2f}")

        with st.expander("2. Dados do Proponente"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo / Razão Social")
            cpf = c2.text_input("CPF / CNPJ")
            
            c3, c4, c5 = st.columns(3)
            nacionalidade = c3.text_input("Nacionalidade", value="Brasileiro")
            profissao = c4.text_input("Profissão")
            estado_civil = c5.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
            
            email = st.text_input("E-mail")

        if st.button("🚀 Gerar Proposta Home Buy"):
            if nome and cpf:
                dados_completos = {
                    'nome': nome, 'cpf': cpf, 'nacionalidade': nacionalidade,
                    'profissao': profissao, 'estado_civil': estado_civil, 'email': email,
                    'unidade': unidade, 'valor': v_total, 'ato': v_ato, 
                    'intermed': v_inter, 'p36': v_36x, 'loteamento': 'Residencial Frei Galvão'
                }
                pdf_bytes = gerar_pdf_home_buy(dados_completos)
                st.download_button("📥 Baixar PDF Completo", pdf_bytes, f"Proposta_{unidade}.pdf")
            else:
                st.error("Preencha os campos obrigatórios (Nome e CPF).")
    else:
        st.info("O Admin precisa subir a planilha no painel ao lado.")