import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- FUNÇÃO DE LIMPEZA TOTAL ---
def limpar_e_converter(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    # Remove R$, pontos de milhar e troca vírgula por ponto
    texto = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto)
    except:
        return 0.0

# --- CLASSE PDF ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 10, 'F')
        self.set_font('Arial', 'B', 12)
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
    pdf.seccao("DETALHES DO IMÓVEL")
    pdf.campo("UNIDADE", d['unidade'], 190, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 190, True)
    pdf.ln(2)
    pdf.seccao("PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(190, 8, f"ENTRADA TOTAL ACORDADA: R$ {d['v_entrada_total']:,.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
if 'db' not in st.session_state: st.session_state['db'] = None

menu = st.sidebar.radio("Navegação", ["Corretor", "Admin"])

if menu == "Admin":
    st.header("⚙️ Configurações")
    if st.text_input("Senha", type="password") == "admin123":
        up = st.file_uploader("Tabela Excel", type=['xlsx'])
        if up:
            # Lendo a tabela e limpando nomes de colunas
            df_raw = pd.read_excel(up, skiprows=11)
            df_raw.columns = [str(c).strip() for c in df_raw.columns]
            st.session_state['db'] = df_raw
            st.success("Tabela carregada!")
else:
    st.header("📝 Gerador de Propostas")
    if st.session_state['db'] is None:
        st.info("Aguardando tabela...")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        dados_linha = lotes[lotes[col_lote] == u].iloc[0]

        # --- CÁLCULO MATEMÁTICO REAL ---
        # Buscando colunas por nome exato
        val_negocio = limpar_e_converter(dados_linha.get("Valor Negócio", 0))
        val_intermed = limpar_e_converter(dados_linha.get("Intermediação", 0))
        val_ent_imovel = limpar_e_converter(dados_linha.get("Entrada Imóvel", 0))
        
        # A SOMA QUE DEVE DAR 8550.68 NO LOTE 6
        entrada_sugerida = val_intermed + val_ent_imovel

        with st.form("form_final_v10"):
            st.write(f"### Unidade Selecionada: {u}")
            nome = st.text_input("Nome do Cliente")
            cpf = st.text_input("CPF")
            
            st.divider()
            # Entrada Total (Campo editável, mas inicia com a soma correta)
            entrada_cliente = st.number_input("Valor da Entrada Total (Soma da Tabela)", value=entrada_sugerida, key=f"v_ent_{u}")
            parcelas = st.slider("Dividir o Saldo Restante em:", 1, 4, 1)

            # Lógica do Ato e Saldo
            valor_ato = val_negocio * 0.003
            saldo_a_parcelar = entrada_cliente - valor_ato
            valor_parcela = saldo_a_parcelar / parcelas if saldo_a_parcelar > 0 else 0

            # --- CONFERÊNCIA VISUAL ---
            st.write("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Intermediação", f"R$ {val_intermed:,.2f}")
            c2.metric("Entrada Imóvel", f"R$ {val_ent_imovel:,.2f}")
            c3.metric("SOMA TOTAL", f"R$ {entrada_cliente:,.2f}")

            st.warning(f"**PLANO:** Ato de R$ {valor_ato:,.2f} + {parcelas}x de R$ {valor_parcela:,.2f}")

            if st.form_submit_button("GERAR PROPOSTA"):
                txt_pag = (
                    f"A entrada total de R$ {entrada_cliente:,.2f} será paga conforme abaixo:\n"
                    f"- 1x de R$ {valor_ato:,.2f} (ATO/SINAL - 0,30% do valor do negócio).\n"
                    f"- {parcelas}x de R$ {valor_parcela:,.2f} mensais (Saldo restante da entrada)."
                )
                
                info = {
                    'nome': nome, 'cpf': cpf, 'unidade': u,
                    'v_negocio': val_negocio, 'v_entrada_total': entrada_cliente,
                    'txt_pagamento': txt_pag
                }
                st.session_state['pdf'] = gerar_pdf(info)
                st.success("✅ Proposta Gerada!")

        if 'pdf' in st.session_state:
            with open(st.session_state['pdf'], "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=st.session_state['pdf'], use_container_width=True)