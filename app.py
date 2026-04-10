import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- FUNÇÃO DE LIMPEZA DE DADOS ---
def para_float(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    texto = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto)
    except:
        return 0.0

# --- CLASSE PDF ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 10, 'F')
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(190, 10, 'PROPOSTA DE COMPRA - HOME BUY', 0, 1, 'C')
        self.ln(5)

    def seccao(self, titulo):
        self.set_fill_color(240, 240, 240)
        self.set_text_color(23, 55, 94)
        self.set_font('Arial', 'B', 10)
        self.cell(190, 7, f" {titulo}", 0, 1, 'L', True)
        self.ln(2)

    def campo(self, label, valor, largura, nova_linha=False):
        self.set_font('Arial', 'B', 8)
        self.cell(largura * 0.35, 6, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.65, 6, str(valor), 0, 0)
        self.line(x, y + 5, x + (largura * 0.65) - 2, y + 5)
        if nova_linha: self.ln(8)

def gerar_pdf(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    pdf.seccao("DADOS DO CLIENTE")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CPF", d['cpf'], 95, True)
    
    pdf.ln(2)
    pdf.seccao("DADOS DO IMÓVEL")
    pdf.campo("UNIDADE", d['unidade'], 190, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95, True)
    
    pdf.ln(2)
    pdf.seccao("PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(190, 8, f"VALOR TOTAL DISPONIBILIZADO: R$ {d['v_entrada_total']:,.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')
    
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
if 'db' not in st.session_state: st.session_state['db'] = None

st.sidebar.title("Menu")
menu = st.sidebar.radio("Navegação", ["Corretor", "Admin"])

if menu == "Admin":
    st.header("⚙️ Admin")
    if st.text_input("Senha", type="password") == "admin123":
        up = st.file_uploader("Subir Tabela Excel", type=['xlsx'])
        if up:
            df_admin = pd.read_excel(up, skiprows=11)
            df_admin.columns = [str(c).strip() for c in df_admin.columns]
            st.session_state['db'] = df_admin
            st.success("Tabela carregada!")
else:
    st.header("📝 Gerar Proposta")
    if st.session_state['db'] is None:
        st.info("Aguardando tabela do Admin...")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        dados = lotes[lotes[col_lote] == u].iloc[0]

        # --- VALORES DA PLANILHA ---
        v_negocio = para_float(dados.get("Valor Negócio", 0))
        v_intermed = para_float(dados.get("Intermediação", 0))
        v_ent_imov = para_float(dados.get("Entrada Imóvel", 0))
        soma_sugerida = v_intermed + v_ent_imov

        with st.form("form_venda_v4"):
            nome = st.text_input("Nome do Cliente")
            cpf = st.text_input("CPF")
            
            st.divider()
            st.subheader("💰 Plano de Entrada")
            
            # CAMPO ONDE VOCÊ COLOCA O VALOR QUE O CLIENTE QUER DAR
            v_entrada_cliente = st.number_input("Quanto o cliente dará de entrada total?", value=soma_sugerida)
            qtd_parc = st.slider("Parcelar o SALDO RESTANTE em:", 1, 4, 1)

            # --- LÓGICA DE CÁLCULO ---
            ato_obrigatorio = v_negocio * 0.003
            saldo_apos_ato = v_entrada_cliente - ato_obrigatorio
            valor_da_parcela = saldo_apos_ato / qtd_parc if saldo_apos_ato > 0 else 0

            # --- PAINEL DE CONFERÊNCIA EM TEMPO REAL ---
            st.write("### 🔍 Resumo dos Cálculos")
            col_calc1, col_calc2 = st.columns(2)
            col_calc1.metric("Ato (Retirado da Entrada)", f"R$ {ato_obrigatorio:,.2f}")
            col_calc2.metric("Saldo para Parcelar", f"R$ {saldo_apos_ato:,.2f}")
            
            st.info(f"O plano será: 1x de R$ {ato_obrigatorio:,.2f} (Ato) + {qtd_parc}x de R$ {valor_da_parcela:,.2f} (Parcelas)")

            if st.form_submit_button("🚀 GERAR PROPOSTA"):
                txt_pag = (
                    f"A entrada total de R$ {v_entrada_cliente:,.2f} será paga da seguinte forma:\n"
                    f"- 1ª Parcela (ATO/SINAL): R$ {ato_obrigatorio:,.2f} (correspondente a 0,30% do valor do negócio).\n"
                    f"- SALDO RESTANTE: R$ {saldo_apos_ato:,.2f} dividido em {qtd_parc} parcelas de R$ {valor_da_parcela:,.2f} mensais."
                )

                info_pdf = {
                    'nome': nome, 'cpf': cpf, 'unidade': u,
                    'v_negocio': v_negocio, 'v_entrada_total': v_entrada_cliente,
                    'txt_pagamento': txt_pag
                }
                
                st.session_state['pdf_link'] = gerar_pdf(info_pdf)
                st.success("✅ Proposta Gerada!")

        if 'pdf_link' in st.session_state:
            with open(st.session_state['pdf_link'], "rb") as f:
                st.download_button("📥 Baixar Proposta em PDF", f, file_name=st.session_state['pdf_link'], use_container_width=True)