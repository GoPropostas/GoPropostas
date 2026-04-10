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

# --- VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    return len(cpf) == 11

# --- CLASSE PDF ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 10, 'F')
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(190, 10, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
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
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CPF", d['cpf'], 95)
    pdf.campo("FONE", d['fone'], 95, True)
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("UNIDADE", d['unidade'], 190, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.ln(2)
    pdf.seccao("CONDIÇÕES DE PAGAMENTO")
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(190, 8, f"TOTAL DA ENTRADA: R$ {d['v_entrada_total']:,.2f}", 0, 1)
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
        up = st.file_uploader("Subir Tabela", type=['xlsx'])
        if up:
            df_admin = pd.read_excel(up, skiprows=11)
            df_admin.columns = [str(c).strip() for c in df_admin.columns]
            st.session_state['db'] = df_admin
            st.success("Tabela carregada!")
else:
    st.header("📝 Gerar Proposta")
    if st.session_state['db'] is None:
        st.info("Aguardando tabela do Admin.")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        dados = lotes[lotes[col_lote] == u].iloc[0]

        # 1. PEGA OS VALORES DAS COLUNAS CORRETAS
        v_negocio = para_float(dados.get("Valor Negócio", 0))
        v_intermed = para_float(dados.get("Intermediação", 0))
        v_ent_imov = para_float(dados.get("Entrada Imóvel", 0))
        
        # 2. CALCULA A SOMA DA ENTRADA (Sempre atualiza quando muda o lote)
        soma_entrada_real = v_intermed + v_ent_imov

        with st.form("form_venda_v3"):
            st.subheader(f"📍 Unidade: {u}")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Cliente")
            cpf = c2.text_input("CPF")
            fone = st.text_input("Telefone")

            st.divider()
            st.subheader("💰 Plano Financeiro")
            
            # Campo de entrada total já inicia com a soma de (Intermed + Entrada Imóvel)
            v_entrada_total = st.number_input("Valor da Entrada Total (Confirmar)", value=soma_entrada_real, key=f"v_ent_{u}")
            parc = st.slider("Parcelar saldo da entrada em:", 1, 4, 1)

            # --- CÁLCULOS DE CONFERÊNCIA ---
            ato_calc = v_negocio * 0.003
            # O Saldo para parcelar usa o valor do campo "Entrada Total" menos o Ato
            saldo_para_parc = v_entrada_total - ato_calc
            valor_da_parc = saldo_para_parc / parc if saldo_para_parc > 0 else 0

            # --- PAINEL DE CONFERÊNCIA (NATIVO, SEM FAIXA BRANCA) ---
            st.write("---")
            st.write("### 🔍 Conferência de Valores")
            m1, m2, m3 = st.columns(3)
            m1.metric("Valor Negócio", f"R$ {v_negocio:,.2f}")
            m2.metric("Ato (0,30%)", f"R$ {ato_calc:,.2f}")
            m3.metric("Entrada Total", f"R$ {v_entrada_total:,.2f}")
            
            m4, m5 = st.columns(2)
            m4.metric("Saldo a Parcelar", f"R$ {saldo_para_parc:,.2f}")
            m5.metric("Valor da Parcela", f"R$ {valor_da_parc:,.2f}")
            st.write("---")

            if st.form_submit_button("🚀 GERAR PDF"):
                if not nome or not cpf:
                    st.error("Preencha os dados do cliente.")
                else:
                    detalhes_pag = (f"Pagamento da entrada:\n"
                                   f"- Ato (0,30% sobre negócio): R$ {ato_calc:,.2f}\n"
                                   f"- Saldo da entrada: R$ {saldo_para_parc:,.2f} em {parc}x de R$ {valor_da_parc:,.2f} mensais.")

                    info_pdf = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'unidade': u,
                        'v_negocio': v_negocio, 'v_intermed': v_intermed,
                        'v_entrada_total': v_entrada_total, 'txt_pagamento': detalhes_pag
                    }
                    st.session_state['pdf_gerado'] = gerar_pdf(info_pdf)
                    st.success("PDF Criado!")

        if 'pdf_gerado' in st.session_state:
            with open(st.session_state['pdf_gerado'], "rb") as f:
                st.download_button("📥 Baixar Proposta", f, file_name=st.session_state['pdf_gerado'])