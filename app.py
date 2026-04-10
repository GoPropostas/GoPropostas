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

# --- FUNÇÃO PARA LIMPAR NÚMEROS DO EXCEL ---
def converter_para_float(valor):
    try:
        if isinstance(valor, str):
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(valor)
    except:
        return 0.0

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

# --- NAVEGAÇÃO ---
st.sidebar.title("Home Buy")
menu = st.sidebar.radio("Navegação", ["Área do Corretor", "Painel Admin"])

if 'db' not in st.session_state:
    st.session_state['db'] = None

# --- PAINEL ADMIN ---
if menu == "Painel Admin":
    st.header("⚙️ Painel do Administrador")
    senha = st.text_input("Senha", type="password")
    if senha == "admin123":
        uploaded_file = st.file_uploader("Subir Tabela (xlsx)", type=['xlsx'])
        if uploaded_file:
            df_temp = pd.read_excel(uploaded_file, skiprows=11)
            # Limpa espaços nos nomes das colunas
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            st.session_state['db'] = df_temp
            st.success("Tabela carregada!")
            st.write("Colunas detectadas:", list(df_temp.columns))

# --- ÁREA DO CORRETOR ---
else:
    st.header("📝 Gerador de Propostas")
    
    if st.session_state['db'] is None:
        st.warning("⚠️ Suba a tabela no Painel Admin primeiro.")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]
        
        with st.form("form_venda_oficial"):
            u = st.selectbox("Unidade", lotes[col_lote].unique())
            
            # Puxa os dados da linha selecionada
            linha = lotes[lotes[col_lote] == u].iloc[0]
            
            # CONVERSÃO SEGURA (Garante que a soma funcione mesmo com texto no Excel)
            v_negocio = converter_para_float(linha.get("Valor Negócio", 0))
            v_intermed = converter_para_float(linha.get("Intermediação", 0))
            v_ent_imovel = converter_para_float(linha.get("Entrada Imóvel", 0))
            
            # A SOMA QUE VOCÊ SOLICITOU
            soma_entrada = v_intermed + v_ent_imovel

            st.subheader("👤 Dados do Cliente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome")
            cpf = c2.text_input("CPF")
            
            st.subheader("💰 Condições")
            # Exibe a soma calculada automaticamente
            v_entrada_input = st.number_input("Entrada Total (Intermediação + Entrada Imóvel)", value=soma_entrada)
            parc = st.slider("Parcelar saldo em:", 1, 4, 1)

            # Botão de envio DENTRO do formulário
            enviar = st.form_submit_button("🚀 GERAR PROPOSTA")

            if enviar:
                if not validar_cpf(cpf):
                    st.error("CPF Inválido")
                else:
                    # Regra de 0,30% sobre o VALOR NEGÓCIO
                    ato = v_negocio * 0.003
                    saldo = v_entrada_input - ato
                    v_parc = saldo / parc if saldo > 0 else 0

                    st.write(f"Conferência: Ato R$ {ato:,.2f} | Saldo R$ {saldo:,.2f}")
                    st.success("PDF Gerado com Sucesso!")
                    # (Aqui entraria a chamada da função gerar_pdf_completo como nos códigos anteriores)