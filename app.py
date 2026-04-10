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

# --- CLASSE PDF (ESTILO HOME BUY) ---
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
    
    # PROPONENTE
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
    
    # CÔNJUGE
    pdf.ln(2)
    pdf.seccao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 190, True)
    pdf.campo("CNPJ/CPF Nº", d['ccpf'], 190, True)

    # IMÓVEL
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR TOTAL NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("VALOR COMISSÃO", f"R$ {d['v_comissao']:,.2f}", 95, True)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total']:,.2f}", 190, True)

    # PAGAMENTO
    pdf.ln(2)
    pdf.seccao("FORMA DE PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 9)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')

    # TEXTO LEGAL
    pdf.ln(5)
    pdf.set_font('Arial', '', 7)
    pdf.multi_cell(190, 3, "Cláusula Compromissória: Todo litígio decorrente deste instrumento será decidido por arbitragem na 2ª Corte de Goiânia - GO (Lei 9.307/1996).")
    
    pdf.ln(10)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    path = f"Proposta_{d['unidade']}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
st.title("Home Buy - Gerador de Propostas Oficial")

if 'db' not in st.session_state: st.session_state['db'] = None

with st.sidebar:
    if st.text_input("Senha Admin", type="password") == "admin123":
        arq = st.file_uploader("Subir Tabela Excel", type=['xlsx'])
        if arq: st.session_state['db'] = pd.read_excel(arq, skiprows=11)

if st.session_state['db'] is not None:
    df = st.session_state['db']
    lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]

    with st.form("vendas_form"):
        u = st.selectbox("Selecione a Unidade", lotes[df.columns[0]].unique())
        
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome do Cliente")
        cpf = c2.text_input("CPF (apenas números)")
        
        st.subheader("Simulação de Entrada")
        v_ent_cliente = st.number_input("Valor total que o cliente quer dar de entrada (R$)", min_value=0.0, step=100.0)
        num_parcelas = st.selectbox("Parcelar o restante da entrada (após o ato) em quantas vezes?", [1, 2, 3, 4])

        if st.form_submit_button("GERAR PROPOSTA EM PDF"):
            if not validar_cpf(cpf):
                st.error("CPF Inválido! Corrija para prosseguir.")
            else:
                # Dados da tabela
                dados_lote = lotes[lotes[df.columns[0]] == u].iloc[0]
                v_negocio = float(dados_lote[df.columns[2]])
                
                # CÁLCULOS
                ato_minimo = v_negocio * 0.003
                
                if v_ent_cliente < ato_minimo:
                    st.warning(f"O valor de entrada (R$ {v_ent_cliente:,.2f}) é menor que o Ato mínimo de 0,30% (R$ {ato_minimo:,.2f}).")
                    restante = 0
                    v_parcela = 0
                else:
                    restante = v_ent_cliente - ato_minimo
                    v_parcela = restante / num_parcelas

                txt_pag = (
                    f"FORMA DE PAGAMENTO DA ENTRADA:\n"
                    f"- ATO (0,30% do negócio): R$ {ato_minimo:,.2f}\n"
                    f"- SALDO DA ENTRADA: R$ {restante:,.2f} parcelado em {num_parcelas}x de R$ {v_parcela:,.2f} mensais.\n"
                    f"- TOTAL DA ENTRADA INFORMADA: R$ {v_ent_cliente:,.2f}"
                )

                info = {
                    'nome': nome, 'cpf': cpf, 'fone': '', 'fone_fixo': '', 'fone_ref': '',
                    'nac': 'Brasileiro', 'prof': '', 'est_civil': 'Solteiro', 'renda': '0,00', 'email': '',
                    'cnome': '', 'ccpf': '', 'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                    'v_negocio': v_negocio, 'v_comissao': v_negocio * 0.053, 'v_total': v_negocio,
                    'txt_pagamento': txt_pag
                }
                
                st.session_state['file'] = gerar_pdf_proposta(info)
                st.success("✅ Proposta Gerada!")

    if 'file' in st.session_state:
        with open(st.session_state['file'], "rb") as f:
            st.download_button("📥 Baixar Proposta PDF", f, file_name=st.session_state['file'])