import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- FUNÇÃO DE LIMPEZA DE DADOS (CRUCIAL PARA A SOMA) ---
def para_float(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    # Remove R$, espaços e ajusta pontos/vírgulas
    texto = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto)
    except:
        return 0.0

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
    # Seções do PDF (Dados do proponente, imóvel e pagamento)
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CPF", d['cpf'], 95)
    pdf.campo("FONE", d['fone'], 95, True)
    
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("UNIDADE", d['unidade'], 190, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("INTERMEDIAÇÃO", f"R$ {d['v_intermed']:,.2f}", 95, True)
    
    pdf.ln(2)
    pdf.seccao("CONDIÇÕES DE PAGAMENTO")
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')
    
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
st.sidebar.title("Home Buy")
menu = st.sidebar.radio("Navegação", ["Corretor", "Admin"])

if 'db' not in st.session_state: st.session_state['db'] = None

if menu == "Admin":
    st.header("⚙️ Configurações")
    if st.text_input("Senha", type="password") == "admin123":
        up = st.file_uploader("Subir Tabela", type=['xlsx'])
        if up:
            df_admin = pd.read_excel(up, skiprows=11)
            # Limpa nomes de colunas para evitar erros de espaço
            df_admin.columns = [str(c).strip() for c in df_admin.columns]
            st.session_state['db'] = df_admin
            st.success("Tabela ativa!")
            st.write("Colunas lidas:", list(df_admin.columns))

else:
    st.header("📝 Gerar Proposta")
    if st.session_state['db'] is None:
        st.info("Aguardando tabela do Admin.")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

        with st.form("form_venda"):
            u = st.selectbox("Unidade", lotes[col_lote].unique())
            dados = lotes[lotes[col_lote] == u].iloc[0]

            # BUSCA PELO NOME EXATO DA COLUNA
            # Valor Negócio (conforme solicitado)
            v_negocio = para_float(dados.get("Valor Negócio", 0))
            v_intermed = para_float(dados.get("Intermediação", 0))
            v_ent_imov = para_float(dados.get("Entrada Imóvel", 0))
            
            soma_entrada = v_intermed + v_ent_imov

            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Cliente")
            cpf = c2.text_input("CPF")
            fone = st.text_input("Telefone")

            st.subheader("💰 Plano Financeiro")
            # Number input que reseta quando troca a unidade
            v_ent_final = st.number_input("Entrada Total (Intermediação + Entrada Imóvel)", value=soma_entrada, key=f"ent_{u}")
            parc = st.slider("Parcelar saldo em:", 1, 4, 1)

            if st.form_submit_button("GERAR PDF"):
                if not validar_cpf(cpf):
                    st.error("CPF inválido")
                else:
                    ato = v_negocio * 0.003
                    saldo = v_ent_final - ato
                    v_parc = saldo / parc if saldo > 0 else 0

                    txt = (f"ATO (0,30% de R$ {v_negocio:,.2f}): R$ {ato:,.2f}\n"
                           f"SALDO DA ENTRADA: {parc}x de R$ {v_parc:,.2f}")

                    info = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'unidade': u,
                        'v_negocio': v_negocio, 'v_intermed': v_intermed,
                        'v_ent_imovel': v_ent_imov, 'v_entrada_total': v_ent_final,
                        'txt_pagamento': txt
                    }
                    st.session_state['arq'] = gerar_pdf(info)
                    st.success("Proposta Criada!")

        if 'arq' in st.session_state:
            with open(st.session_state['arq'], "rb") as f:
                st.download_button("📥 Baixar Proposta", f, file_name=st.session_state['arq'])