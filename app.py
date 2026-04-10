import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# --- CLASSE PARA GERAR O PDF COM O LAYOUT DA HOME BUY ---
class PropostaPDF(FPDF):
    def header(self):
        # Cabeçalho Azul
        self.set_fill_color(23, 55, 94) # Azul Home Buy
        self.rect(10, 10, 190, 10, 'F')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(190, 10, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(5)

    def seccao(self, titulo):
        self.set_fill_color(217, 217, 217) # Cinza Seção
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(190, 8, f" {titulo}", 0, 1, 'L', True)
        self.ln(2)

    def campo(self, label, valor, largura=0):
        self.set_font('Arial', 'B', 8)
        self.write(5, f"{label}: ")
        self.set_font('Arial', '', 9)
        self.write(5, f"{valor}  ")
        if largura == 1: self.ln(6)

# --- FUNÇÃO PARA CRIAR O PDF ---
def exportar_pdf(d):
    pdf = PropostaPDF()
    pdf.add_page()
    
    # 1. Proponente
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 1)
    pdf.campo("CPF/CNPJ", d['cpf'])
    pdf.campo("FONE CEL", d['fone'])
    pdf.campo("FONE FIXO", d['fone_fixo'], 1)
    pdf.campo("NACIONALIDADE", d['nac'])
    pdf.campo("PROFISSÃO", d['prof'])
    pdf.campo("REFERÊNCIA", d['fone_ref'], 1)
    pdf.campo("ESTADO CIVIL", d['est_civil'])
    pdf.campo("RENDA", d['renda'], 1)
    pdf.campo("E-MAIL", d['email'], 1)
    pdf.ln(5)

    # 2. Cônjuge
    pdf.seccao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 1)
    pdf.campo("CPF", d['ccpf'])
    pdf.campo("FONE", d['cfone'])
    pdf.campo("RENDA", d['crenda'], 1)
    pdf.ln(5)

    # 3. Imóvel
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 1)
    pdf.campo("UNIDADE", d['unidade'])
    pdf.campo("VALOR TOTAL", f"R$ {d['valor_venda']:,.2f}", 1)
    pdf.ln(5)

    # 4. Condições (Texto do seu PDF)
    pdf.seccao("CONDIÇÕES GERAIS E CLÁUSULA COMPROMISSÓRIA")
    pdf.set_font('Arial', '', 7)
    texto_legal = (
        "Todo litígio ou controvérsia decorrente deste instrumento será decidido por arbitragem, "
        "conforme a Lei 9.307/1996, administrada pela 2ª Corte de Conciliação e Arbitragem de Goiânia - Goiás."
    )
    pdf.multi_cell(190, 4, texto_legal)

    path = f"Proposta_{d['unidade']}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE STREAMLIT ---
st.title("Gerador Home Buy - Exportação PDF")

if 'db_precos' not in st.session_state:
    st.session_state['db_precos'] = None

# Sidebar Admin para subir a tabela
with st.sidebar:
    if st.text_input("Admin", type="password") == "admin123":
        arq = st.file_uploader("Suba a Tabela Excel", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['db_precos'] = df.dropna(how='all', axis=1)

# Formulário de Vendas
if st.session_state['db_precos'] is not None:
    df = st.session_state['db_precos']
    lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]
    
    with st.form("pdf_form"):
        unid = st.selectbox("Lote", lotes[df.columns[0]].unique())
        nome = st.text_input("Nome Completo")
        cpf = st.text_input("CPF")
        fone = st.text_input("Celular")
        renda = st.text_input("Renda")
        
        st.write("---")
        cnome = st.text_input("Nome Cônjuge")
        ccpf = st.text_input("CPF Cônjuge")
        
        if st.form_submit_button("GERAR PROPOSTA EM PDF"):
            dados_lote = lotes[lotes[df.columns[0]] == unid].iloc[0]
            v_venda = float(dados_lote[df.columns[2]])
            
            info = {
                'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': '',
                'nac': 'Brasileiro', 'prof': '', 'fone_ref': '', 'est_civil': 'Casado',
                'renda': renda, 'email': '',
                'cnome': cnome, 'ccpf': ccpf, 'cfone': '', 'crenda': '',
                'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': unid,
                'valor_venda': v_venda
            }
            
            path_pdf = exportar_pdf(info)
            st.session_state['pdf_path'] = path_pdf

    if 'pdf_path' in st.session_state:
        with open(st.session_state['pdf_path'], "rb") as f:
            st.download_button("📥 BAIXAR PROPOSTA EM PDF", f, file_name=st.session_state['pdf_path'])