import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- FUNÇÃO DE VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]): return False
    return True

# --- CLASSE PARA GERAR O PDF FIEL AO ORIGINAL ---
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
        self.cell(largura * 0.4, 6, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.6, 6, str(valor), 0, 0)
        self.line(x, y + 5, x + (largura * 0.6) - 2, y + 5)
        if nova_linha: self.ln(7)

def gerar_pdf_completo(d):
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
    pdf.campo("FONE", d['cfone_ref'], 65, True)
    pdf.campo("RENDA", f"R$ {d['crenda']}", 190, True)

    # 3. IMÓVEL
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR TOTAL NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("VALOR COMISSÃO", f"R$ {d['v_comissao']:,.2f}", 95, True)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_imovel']:,.2f}", 190, True)

    # 4. PAGAMENTO (Onde entra a lógica que você pediu)
    pdf.ln(2)
    pdf.seccao("FORMA DE PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', '', 8)
    pdf.multi_cell(190, 5, d['txt_pagamento'], 'B')

    # 5. TEXTO LEGAL
    pdf.ln(5)
    pdf.set_font('Arial', '', 7)
    pdf.multi_cell(190, 3, "Cláusula Compromissória: Todo litígio ou controvérsia decorrente deste instrumento será decidido por arbitragem na 2ª Corte de Goiânia - Goiás (Lei 9.307/1996).")
    
    pdf.ln(10)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

    path = f"Proposta_{d['unidade']}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
st.title("Gerador Home Buy - Oficial")

if 'db' not in st.session_state: st.session_state['db'] = None

with st.sidebar:
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Tabela Excel", type=['xlsx'])
        if arq: st.session_state['db'] = pd.read_excel(arq, skiprows=11)

if st.session_state['db'] is not None:
    df = st.session_state['db']
    lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]

    with st.form("form_vendas"):
        u = st.selectbox("Unidade", lotes[df.columns[0]].unique())
        
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Proponente")
        cpf = col2.text_input("CPF (Somente números)")
        
        col3, col4, col5 = st.columns(3)
        fone = col3.text_input("Celular")
        f_fixo = col4.text_input("Fone Fixo")
        f_ref = col5.text_input("Fone Referência")

        col6, col7 = st.columns(2)
        renda = col6.text_input("Renda Mensal")
        email = col7.text_input("E-mail")

        st.subheader("Forma de Pagamento da Entrada")
        tipo_pag = st.radio("Escolha a condição:", [
            "Entrada Total à Vista",
            "Entrada Total (Ato + 4x)",
            "Entrada Mínima (0,30% no Ato + Restante da entrada em 4x)"
        ])

        if st.form_submit_button("GERAR PROPOSTA PDF"):
            if not validar_cpf(cpf):
                st.error("❌ CPF Inválido! Verifique os números.")
            else:
                dados_lote = lotes[lotes[df.columns[0]] == u].iloc[0]
                v_venda = float(dados_lote[df.columns[2]])
                comissao = v_venda * 0.053
                v_imovel = v_venda - comissao
                entrada_total = v_venda * 0.10 # Exemplo de 10% de entrada

                # Lógica das Opções de Pagamento
                if "à Vista" in tipo_pag:
                    txt = f"Pagamento da entrada total (R$ {entrada_total:,.2f}) em uma única parcela à vista."
                elif "Ato + 4x" in tipo_pag:
                    valor_parc = entrada_total / 5
                    txt = f"Entrada total de R$ {entrada_total:,.2f} dividida em: Ato de R$ {valor_parc:,.2f} + 4 parcelas mensais de R$ {valor_parc:,.2f}."
                else:
                    minimo = v_venda * 0.003
                    restante = (entrada_total - minimo) / 4
                    txt = f"Entrada Mínima: R$ {minimo:,.2f} (0,30% do total) no ato + 4 parcelas de R$ {restante:,.2f}."

                info = {
                    'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo, 'fone_ref': f_ref,
                    'nac': 'Brasileiro', 'prof': '', 'est_civil': 'Solteiro', 'renda': renda, 'email': email,
                    'cnome': '', 'ccpf': '', 'cfone': '', 'cfone_ref': '', 'crenda': '',
                    'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                    'v_negocio': v_venda, 'v_comissao': comissao, 'v_imovel': v_imovel,
                    'txt_pagamento': txt
                }
                st.session_state['pdf'] = gerar_pdf_completo(info)
                st.success("✅ PDF Gerado com sucesso!")

    if 'pdf' in st.session_state:
        with open(st.session_state['pdf'], "rb") as f:
            st.download_button("📥 BAIXAR PROPOSTA OFICIAL", f, file_name=st.session_state['pdf'])