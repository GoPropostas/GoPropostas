import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Home Buy - Portal de Propostas", layout="wide")

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
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    return True

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
    pdf.campo("INTERMEDIAÇÃO", f"R$ {d['v_intermed']:,.2f}", 95, True)
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

        # --- SELEÇÃO DE UNIDADE (FORA DO FORM PARA ATUALIZAR REAL-TIME) ---
        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        dados = lotes[lotes[col_lote] == u].iloc[0]

        # Pegando valores da coluna correta
        v_negocio = para_float(dados.get("Valor Negócio", 0))
        v_intermed = para_float(dados.get("Intermediação", 0))
        v_ent_imov = para_float(dados.get("Entrada Imóvel", 0))
        
        # SOMA DA ENTRADA
        soma_entrada_calculada = v_intermed + v_ent_imov

        # --- PAINEL DE CONFERÊNCIA VISUAL ---
        st.info(f"📍 **Unidade:** {u} | 💰 **Valor Negócio:** R$ {v_negocio:,.2f}")
        
        with st.form("form_venda"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Cliente")
            cpf = c2.text_input("CPF")
            fone = st.text_input("Telefone")

            st.subheader("💰 Plano Financeiro")
            col_ent1, col_ent2 = st.columns(2)
            
            # Valor da entrada pode ser editado, mas inicia com a soma correta
            v_entrada_final = col_ent1.number_input("Valor da Entrada Total", value=soma_entrada_calculada)
            parc = col_ent2.slider("Parcelar restante da entrada em:", 1, 4, 1)

            # Cálculos automáticos para conferência interna
            ato = v_negocio * 0.003
            restante_entrada = v_entrada_final - ato
            valor_parcela = restante_entrada / parc if restante_entrada > 0 else 0

            # --- CAMPO DE CONFERÊNCIA ANTES DE GERAR ---
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #17375e;">
                <h4 style="margin-top:0;">🔍 Conferência dos Valores:</h4>
                <b>• Valor Negócio:</b> R$ {v_negocio:,.2f}<br>
                <b>• Valor da Entrada (Soma):</b> R$ {v_entrada_final:,.2f}<br>
                <b>• Ato (0,30%):</b> R$ {ato:,.2f}<br>
                <b>• Restante para Parcelar:</b> R$ {restante_entrada:,.2f}<br>
                <b>• Parcelas:</b> {parc}x de R$ {valor_parcela:,.2f}
            </div>
            """, unsafe_allow_html=True)

            st.write("") # Espaçamento
            
            if st.form_submit_button("🚀 GERAR PROPOSTA NO PDF"):
                if not nome or not cpf:
                    st.error("Preencha o nome e CPF do cliente.")
                else:
                    txt = (f"O pagamento da entrada será realizado da seguinte forma:\n"
                           f"- ATO (0,30% sobre Valor Negócio): R$ {ato:,.2f}\n"
                           f"- RESTANTE DA ENTRADA: R$ {restante_entrada:,.2f} em {parc}x de R$ {valor_parcela:,.2f} mensais.")

                    info = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'unidade': u,
                        'v_negocio': v_negocio, 'v_intermed': v_intermed,
                        'v_entrada_total': v_entrada_final, 'txt_pagamento': txt
                    }
                    st.session_state['arq'] = gerar_pdf(info)
                    st.success("✅ PDF Gerado com os valores acima!")

        if 'arq' in st.session_state:
            with open(st.session_state['arq'], "rb") as f:
                st.download_button("📥 Baixar PDF Agora", f, file_name=st.session_state['arq'], use_container_width=True)