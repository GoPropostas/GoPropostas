import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

class HomeBuyPDF(FPDF):
    def header(self):
        # Título Azul Superior
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 8, 'F')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(190, 8, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(2)

    def criar_seccao(self, titulo):
        self.set_fill_color(217, 217, 217)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 9)
        self.cell(190, 6, f" {titulo}", 0, 1, 'L', True)
        self.ln(1)

    def desenhar_campo(self, label, valor, largura, nova_linha=False):
        self.set_font('Arial', 'B', 8)
        self.cell(largura * 0.35, 6, f"{label}: ", 0, 0)
        self.set_font('Arial', '', 9)
        # Linha inferior para simular o campo de preenchimento
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.65, 6, f"{valor}", 0, 0)
        self.line(x, y + 5, x + (largura * 0.65), y + 5)
        if nova_linha:
            self.ln(7)

def gerar_pdf_identico(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. PROPONENTE
    pdf.criar_seccao("PROPONENTE/EMPRESA")
    pdf.desenhar_campo("NOME", d['nome'], 190, True)
    
    col_w = 190 / 3
    pdf.desenhar_campo("CNPJ/CPF Nº", d['cpf'], col_w)
    pdf.desenhar_campo("FONE CEL", d['fone'], col_w)
    pdf.desenhar_campo("FONE FIXO", d['fone_fixo'], col_w, True)
    
    pdf.desenhar_campo("NACIONALIDADE", d['nac'], col_w)
    pdf.desenhar_campo("PROFISSÃO", d['prof'], col_w)
    pdf.desenhar_campo("FONE REF", d['fone_ref'], col_w, True)
    
    pdf.desenhar_campo("ESTADO CIVIL", d['est_civil'], 120)
    pdf.desenhar_campo("RENDA", f"R$ {d['renda']}", 70, True)
    pdf.desenhar_campo("E-MAIL", d['email'], 190, True)
    pdf.ln(3)

    # 2. CÔNJUGE
    pdf.criar_seccao("CÔNJUGE / 2º PROPONENTE / REPRESENTANTE")
    pdf.desenhar_campo("NOME", d['cnome'], 190, True)
    
    pdf.desenhar_campo("CNPJ/CPF Nº", d['ccpf'], col_w)
    pdf.desenhar_campo("FONE CEL", d['cfone'], col_w)
    pdf.desenhar_campo("FONE", d['cfone_fixo'], col_w, True)
    
    pdf.desenhar_campo("NACIONALIDADE", d['cnac'], col_w)
    pdf.desenhar_campo("PROFISSÃO", d['cprof'], col_w)
    pdf.desenhar_campo("FONE REF", d['cfone_ref'], col_w, True)
    
    pdf.desenhar_campo("ESTADO CIVIL", d['cestado'], 120)
    pdf.desenhar_campo("RENDA", f"R$ {d['crenda']}", 70, True)
    pdf.ln(3)

    # 3. IMÓVEL E VALORES
    pdf.criar_seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.desenhar_campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.desenhar_campo("UNIDADE", d['unidade'], 60, True)
    
    pdf.desenhar_campo("VALOR TOTAL NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.desenhar_campo("VALOR COMISSÃO", f"R$ {d['v_comissao']:,.2f}", 95, True)
    pdf.desenhar_campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total']:,.2f}", 190, True)
    pdf.ln(5)

    # 4. TEXTO LEGAL (IGUAL AO PDF ORIGINAL)
    pdf.set_font('Arial', '', 7)
    texto_legal = (
        "Cláusula Compromissória: Todo litigio ou controvérsia originário ou decorrente deste instrumento será definitivamente decidido por arbitragem, "
        "conforme a Lei 9.307/1996. A arbitragem será administrada pela 2ª Corte de Conciliação e Arbitragem de Goiânia - Goiás, situada na Avenida Fuad José Sebba, "
        "nº 1.193, Jardim Goiás, Goiânia, Goiás. O proponente declara estar ciente de que seus dados serão tratados conforme a LGPD (Lei 13.709/2018)."
    )
    pdf.multi_cell(190, 4, texto_legal)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE STREAMLIT ---
st.title("Gerador Home Buy - PDF Fiel ao Original")

if 'db' not in st.session_state: st.session_state['db'] = None

with st.sidebar:
    st.header("Painel Admin")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Subir Tabela de Preços", type=['xlsx'])
        if arq:
            st.session_state['db'] = pd.read_excel(arq, skiprows=11).dropna(how='all', axis=1)

if st.session_state['db'] is not None:
    df = st.session_state['db']
    lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]

    with st.form("form_fiel"):
        unid = st.selectbox("Selecione a Unidade", lotes[df.columns[0]].unique())
        
        st.subheader("Dados do Proponente")
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome Completo")
        cpf = c2.text_input("CPF")
        fone = c3.text_input("Celular")
        
        c4, c5, c6 = st.columns(3)
        nac = c4.text_input("Nacionalidade", "Brasileiro")
        prof = c5.text_input("Profissão")
        f_fixo = c6.text_input("Fone Fixo")
        
        c7, c8, c9 = st.columns(3)
        est = st.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
        renda = c8.text_input("Renda Mensal")
        email = c9.text_input("E-mail")

        st.subheader("Dados do Cônjuge")
        cc1, cc2, cc3 = st.columns(3)
        cnome = cc1.text_input("Nome Cônjuge")
        ccpf = cc2.text_input("CPF Cônjuge")
        crenda = cc3.text_input("Renda Cônjuge")

        if st.form_submit_button("GERAR PROPOSTA EM PDF"):
            dados_lote = lotes[lotes[df.columns[0]] == unid].iloc[0]
            v_venda = float(dados_lote[df.columns[2]])
            
            info = {
                'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo, 'nac': nac, 'prof': prof,
                'fone_ref': 'Ver Anexo', 'est_civil': est, 'renda': renda, 'email': email,
                'cnome': cnome, 'ccpf': ccpf, 'cfone': '', 'cfone_fixo': '', 'cnac': 'Brasileiro', 
                'cprof': '', 'cfone_ref': '', 'cestado': 'Casado', 'crenda': crenda,
                'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': unid,
                'v_negocio': v_venda, 'v_comissao': v_venda * 0.053, 'v_total': v_venda
            }
            st.session_state['pdf_final'] = gerar_pdf_identico(info)

    if 'pdf_final' in st.session_state:
        with open(st.session_state['pdf_final'], "rb") as f:
            st.download_button("📥 BAIXAR PDF OFICIAL", f, file_name=st.session_state['pdf_final'])