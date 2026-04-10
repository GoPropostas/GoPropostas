import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]): return False
    return True

# --- CLASSE PDF ESTILO HOME BUY ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 8, 'F')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(190, 8, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(2)

    def seccao(self, titulo):
        self.set_fill_color(217, 217, 217)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 9)
        self.cell(190, 6, f" {titulo}", 0, 1, 'L', True)
        self.ln(1)

    def campo(self, label, valor, largura, nova_linha=False):
        self.set_font('Arial', 'B', 8)
        self.cell(largura * 0.35, 6, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.65, 6, str(valor), 0, 0)
        self.line(x, y + 5, x + (largura * 0.65) - 2, y + 5)
        if nova_linha: self.ln(7)

def gerar_pdf_proposta(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    # 1. PROPONENTE
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CNPJ/CPF Nº", d['cpf'], 65)
    pdf.campo("FONE CEL", d['fone'], 60)
    pdf.campo("FONE FIXO", d['fone_fixo'], 65, True)
    pdf.campo("NACIONALIDADE", d['nac'], 65)
    pdf.campo("PROFISSÃO", d['prof'], 60)
    pdf.campo("FONE REF", d['fone_ref'], 65, True)
    pdf.campo("ESTADO CIVIL", d['est_civil'], 125)
    pdf.campo("RENDA", f"R$ {d['renda']}", 65, True)
    pdf.campo("E-MAIL", d['email'], 190, True)
    
    # 2. CÔNJUGE
    pdf.ln(2)
    pdf.seccao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 190, True)
    pdf.campo("CNPJ/CPF Nº", d['ccpf'], 65)
    pdf.campo("FONE CEL", d['cfone'], 60)
    pdf.campo("RENDA", f"R$ {d['crenda']}", 65, True)

    # 3. IMÓVEL
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR TOTAL NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("VALOR INTERMEDIAÇÃO", f"R$ {d['v_intermed']:,.2f}", 95, True)
    pdf.campo("VALOR ENTRADA IMÓVEL", f"R$ {d['v_ent_imovel']:,.2f}", 95)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total_imovel']:,.2f}", 95, True)

    # 4. PAGAMENTO DA ENTRADA
    pdf.ln(2)
    pdf.seccao("FORMA DE PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(190, 8, f"VALOR DA ENTRADA TOTAL (SOMA): R$ {d['v_entrada_total']:,.2f}", 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
st.title("Home Buy - Gerador de Propostas")

if 'db' not in st.session_state: st.session_state['db'] = None

with st.sidebar:
    if st.text_input("Senha Admin", type="password") == "admin123":
        arq = st.file_uploader("Subir Tabela", type=['xlsx'])
        if arq: 
            # Lendo a tabela e forçando a identificação correta das colunas
            st.session_state['db'] = pd.read_excel(arq, skiprows=11)

if st.session_state['db'] is not None:
    df = st.session_state['db']
    # Identifica as colunas dinamicamente para evitar erro de posição
    col_lote = df.columns[0]
    col_negocio = df.columns[2]
    col_intermed = df.columns[3]
    col_entrada_imovel = df.columns[4]

    lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

    with st.form("form_final"):
        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        
        # BUSCA DOS VALORES
        dados = lotes[lotes[col_lote] == u].iloc[0]
        v_neg = float(dados[col_negocio])
        v_int = float(dados[col_intermed])
        v_ent_imov = float(dados[col_entrada_imovel])
        
        # AQUI ESTÁ A SOMA QUE VOCÊ PEDIU
        entrada_total_soma = v_int + v_ent_imov

        st.subheader("Dados do Cliente")
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        cpf = c2.text_input("CPF")
        
        c3, c4, c5 = st.columns(3)
        fone = c3.text_input("Celular")
        f_fixo = c4.text_input("Fixo")
        f_ref = c5.text_input("Referência")

        st.subheader("Pagamento")
        # Valor da entrada total preenchido automaticamente pela soma
        v_ent_user = st.number_input("Entrada Total (Intermediação + Entrada Imóvel)", value=entrada_total_soma)
        parc = st.selectbox("Parcelar saldo em:", [1, 2, 3, 4])

        if st.form_submit_button("GERAR PROPOSTA"):
            if not validar_cpf(cpf):
                st.error("CPF Inválido!")
            else:
                ato = v_neg * 0.003
                saldo = v_ent_user - ato
                v_parc = saldo / parc if saldo > 0 else 0

                txt = (f"PAGAMENTO:\n- ATO (0,30%): R$ {ato:,.2f}\n"
                       f"- SALDO DA ENTRADA: {parc}x de R$ {v_parc:,.2f}")

                info = {
                    'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo, 'fone_ref': f_ref,
                    'nac': 'Brasileiro', 'prof': '', 'est_civil': 'Solteiro', 'renda': '0,00', 'email': '',
                    'cnome': '', 'ccpf': '', 'crenda': '',
                    'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                    'v_negocio': v_neg, 'v_intermed': v_int, 'v_ent_imovel': v_ent_imov,
                    'v_total_imovel': v_neg - v_int, 'v_entrada_total': v_ent_user,
                    'txt_pagamento': txt
                }
                st.session_state['file'] = gerar_pdf_proposta(info)
                st.success("✅ PDF Gerado!")

    if 'file' in st.session_state:
        with open(st.session_state['file'], "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name=st.session_state['file'])