import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- CLASSE DE GERAÇÃO DO PDF (RECRIAÇÃO DO MODELO HOME BUY) ---
class HomeBuyPDF(FPDF):
    def header(self):
        # Cabeçalho com o título azul conforme o PDF original
        self.set_fill_color(23, 55, 94) # Azul Marinho Home Buy
        self.rect(10, 10, 190, 8, 'F')
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(190, 8, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(2)

    def seccao(self, titulo):
        self.set_fill_color(217, 217, 217) # Cinza claro das seções
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 8)
        self.cell(190, 6, f" {titulo}", 0, 1, 'L', True)
        self.ln(1)

    def campo(self, label, valor, largura, nova_linha=False):
        self.set_font('Arial', 'B', 7)
        self.cell(largura * 0.4, 5, f"{label}:", 0, 0)
        self.set_font('Arial', '', 8)
        self.cell(largura * 0.6, 5, f"{valor}", 'B', 0)
        if nova_linha: self.ln(6)

# --- FUNÇÃO PARA CONSTRUIR O DOCUMENTO ---
def gerar_pdf_oficial(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 1. PROPONENTE
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CNPJ/CPF Nº", d['cpf'], 60)
    pdf.campo("FONE CEL", d['fone'], 60)
    pdf.campo("FONE FIXO", d['fone_fixo'], 70, True)
    pdf.campo("NACIONALIDADE", d['nac'], 60)
    pdf.campo("PROFISSÃO", d['prof'], 60)
    pdf.campo("FONE REF", d['fone_ref'], 70, True)
    pdf.campo("ESTADO CIVIL", d['est_civil'], 120)
    pdf.campo("RENDA", d['renda'], 70, True)
    pdf.campo("E-MAIL", d['email'], 190, True)
    pdf.ln(2)

    # 2. CÔNJUGE
    pdf.seccao("CÔNJUGE / 2º PROPONENTE / REPRESENTANTE")
    pdf.campo("NOME", d['cnome'], 190, True)
    pdf.campo("CNPJ/CPF Nº", d['ccpf'], 60)
    pdf.campo("FONE CEL", d['cfone'], 60)
    pdf.campo("FONE", d['cfone_fixo'], 70, True)
    pdf.campo("NACIONALIDADE", d['cnac'], 60)
    pdf.campo("PROFISSÃO", d['cprof'], 60)
    pdf.campo("FONE REF", d['cfone_ref'], 70, True)
    pdf.campo("ESTADO CIVIL", d['cest'], 120)
    pdf.campo("RENDA", d['crenda'], 70, True)
    pdf.ln(2)

    # 3. IMÓVEL
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR TOTAL NEGÓCIO", f"R$ {d['v_total']:,.2f}", 95)
    pdf.campo("VALOR COMISSÃO", f"R$ {d['v_comissao']:,.2f}", 95, True)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total']:,.2f}", 190, True)
    pdf.ln(2)

    # 4. CONDIÇÕES LEGAIS (CONFORME O PDF ENVIADO)
    pdf.seccao("CLÁUSULA COMPROMISSÓRIA E OBSERVAÇÕES")
    pdf.set_font('Arial', '', 6)
    texto_legal = (
        "Todo litígio ou controvérsia originário ou decorrente deste instrumento será definitivamente decidido por arbitragem, "
        "conforme a Lei 9.307/1996. A arbitragem será administrada pela 2ª Corte de Conciliação e Arbitragem de Goiânia - Goiás, "
        "situada na Avenida Fuad José Sebba, nº 1.193, Jardim Goiás, Goiânia, Goiás. "
        "O proponente declara estar ciente de que seus dados serão tratados conforme a LGPD (Lei 13.709/2018)."
    )
    pdf.multi_cell(190, 3, texto_legal)
    
    pdf.ln(10)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE STREAMLIT ---
st.title("Gerador Home Buy - PDF Idêntico")

if 'db' not in st.session_state: st.session_state['db'] = None

with st.sidebar:
    if st.text_input("Senha Admin", type="password") == "admin123":
        arq = st.file_uploader("Tabela Frei Galvão", type=['xlsx'])
        if arq:
            st.session_state['db'] = pd.read_excel(arq, skiprows=11).dropna(how='all', axis=1)

if st.session_state['db'] is not None:
    df = st.session_state['db']
    lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]

    with st.form("form_vendas"):
        u = st.selectbox("Unidade", lotes[df.columns[0]].unique())
        
        st.subheader("Dados Proponente")
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome")
        cpf = c2.text_input("CPF")
        fone = c3.text_input("Celular")
        
        c4, c5, c6 = st.columns(3)
        nac = c4.text_input("Nacionalidade", "Brasileiro")
        prof = c5.text_input("Profissão")
        renda = c6.text_input("Renda")
        
        c7, c8 = st.columns(2)
        est = c7.selectbox("Estado Civil", ["Solteiro", "Casado", "União Estável", "Divorciado"])
        email = c8.text_input("E-mail")

        st.subheader("Dados Cônjuge")
        cc1, cc2 = st.columns(2)
        cnome = cc1.text_input("Nome Cônjuge")
        ccpf = cc2.text_input("CPF Cônjuge")

        if st.form_submit_button("GERAR PDF"):
            dados_lote = lotes[lotes[df.columns[0]] == u].iloc[0]
            v_venda = float(dados_lote[df.columns[2]])
            
            info = {
                'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': '', 'nac': nac, 'prof': prof,
                'fone_ref': '', 'est_civil': est, 'renda': renda, 'email': email,
                'cnome': cnome, 'ccpf': ccpf, 'cfone': '', 'cfone_fixo': '', 'cnac': '', 'cprof': '',
                'cfone_ref': '', 'cest': '', 'crenda': '',
                'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                'v_total': v_venda, 'v_comissao': v_venda * 0.053
            }
            st.session_state['pdf_path'] = gerar_pdf_oficial(info)

    if 'pdf_path' in st.session_state:
        with open(st.session_state['pdf_path'], "rb") as f:
            st.download_button("📥 Baixar Proposta PDF", f, file_name=st.session_state['pdf_path'])