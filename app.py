import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Home Buy - Sistema de Propostas", layout="wide")

# --- VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]): return False
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
        self.set_text_color(50, 50, 50)
        self.cell(largura * 0.35, 6, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.65, 6, str(valor), 0, 0)
        self.line(x, y + 5, x + (largura * 0.65) - 2, y + 5)
        if nova_linha: self.ln(8)

def gerar_pdf_completo(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CPF/CNPJ", d['cpf'], 65)
    pdf.campo("CELULAR", d['fone'], 60)
    pdf.campo("FONE FIXO", d['fone_fixo'], 65, True)
    pdf.campo("NACIONALIDADE", d['nac'], 65)
    pdf.campo("PROFISSÃO", d['prof'], 60)
    pdf.campo("REFERÊNCIA", d['fone_ref'], 65, True)
    pdf.campo("ESTADO CIVIL", d['est_civil'], 95)
    pdf.campo("RENDA", f"R$ {d['renda']}", 95, True)
    pdf.campo("E-MAIL", d['email'], 190, True)
    
    pdf.ln(2)
    pdf.seccao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 190, True)
    pdf.campo("CPF/CNPJ", d['ccpf'], 95)
    pdf.campo("RENDA", f"R$ {d['crenda']}", 95, True)

    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("INTERMEDIAÇÃO", f"R$ {d['v_intermed']:,.2f}", 95, True)
    pdf.campo("ENTRADA IMÓVEL", f"R$ {d['v_ent_imovel']:,.2f}", 95)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total_imovel']:,.2f}", 95, True)

    pdf.ln(2)
    pdf.seccao("CONDIÇÕES DE PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(23, 55, 94)
    pdf.cell(190, 8, f"VALOR TOTAL DA ENTRADA: R$ {d['v_entrada_total']:,.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- NAVEGAÇÃO ---
st.sidebar.title("Menu")
menu = st.sidebar.radio("Ir para:", ["Área do Corretor", "Painel Admin"])

if 'db' not in st.session_state:
    st.session_state['db'] = None

# --- PAINEL ADMIN ---
if menu == "Painel Admin":
    st.header("⚙️ Painel do Administrador")
    senha = st.text_input("Senha", type="password")
    if senha == "admin123":
        uploaded_file = st.file_uploader("Subir Tabela (Excel)", type=['xlsx'])
        if uploaded_file:
            # Lendo e limpando nomes de colunas (removendo espaços extras)
            temp_df = pd.read_excel(uploaded_file, skiprows=11)
            temp_df.columns = [str(c).strip() for c in temp_df.columns] 
            st.session_state['db'] = temp_df
            st.success("Tabela carregada!")
            st.write("Colunas encontradas:", list(temp_df.columns))
    elif senha != "":
        st.error("Senha incorreta.")

# --- ÁREA DO CORRETOR ---
else:
    st.header("📝 Gerador de Propostas")
    
    if st.session_state['db'] is None:
        st.warning("⚠️ Por favor, suba a tabela no Painel Admin primeiro.")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]
        
        # O formulário deve envolver todos os inputs E o botão de submit
        with st.form("meu_formulario_proposta"):
            u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
            
            dados = lotes[lotes[col_lote] == u].iloc[0]
            
            # Busca segura de colunas
            v_negocio_val = float(dados.get("Valor Negócio", 0))
            v_intermed_val = float(dados.get("Intermediação", 0))
            v_ent_imovel_val = float(dados.get("Entrada Imóvel", 0))
            entrada_total_val = v_intermed_val + v_ent_imovel_val

            st.subheader("👤 Cliente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome")
            cpf = c2.text_input("CPF")
            
            c3, c4, c5 = st.columns(3)
            fone = c3.text_input("Celular")
            f_fixo = c4.text_input("Fixo")
            f_ref = c5.text_input("Referência")
            
            c6, c7, c8 = st.columns(3)
            nac = c6.text_input("Nacionalidade", "Brasileiro")
            prof = c7.text_input("Profissão")
            est_civil = c8.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
            
            c9, c10 = st.columns(2)
            renda = c9.text_input("Renda")
            email = c10.text_input("E-mail")

            st.subheader("👥 Cônjuge")
            cc1, cc2, cc3 = st.columns(3)
            cnome = cc1.text_input("Nome Cônjuge")
            ccpf = cc2.text_input("CPF Cônjuge")
            crenda = cc3.text_input("Renda Cônjuge")

            st.subheader("💰 Plano de Entrada")
            v_entrada_final = st.number_input("Valor da Entrada Total (Soma)", value=float(entrada_total_val))
            parcelas = st.slider("Parcelar saldo em (1 a 4x):", 1, 4, 1)

            # O BOTÃO DEVE ESTAR DENTRO DO BLOCO 'WITH ST.FORM'
            enviar = st.form_submit_button("🚀 GERAR PROPOSTA")

            if enviar:
                if not validar_cpf(cpf):
                    st.error("CPF Inválido")
                elif v_negocio_val == 0:
                    st.error("Erro: Valor do negócio não encontrado na planilha. Verifique o cabeçalho 'Valor Negócio'.")
                else:
                    ato_val = v_negocio_val * 0.003
                    saldo_val = v_entrada_final - ato_val
                    v_parc_val = saldo_val / parcelas if saldo_val > 0 else 0

                    txt_pag = (
                        f"Detalhamento:\n"
                        f"- Ato (0,30% sobre Valor Negócio): R$ {ato_val:,.2f}\n"
                        f"- Saldo da Entrada: {parcelas}x de R$ {v_parc_val:,.2f} mensais."
                    )

                    info = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo, 'fone_ref': f_ref,
                        'nac': nac, 'prof': prof, 'est_civil': est_civil, 'renda': renda, 'email': email,
                        'cnome': cnome, 'ccpf': ccpf, 'crenda': crenda,
                        'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                        'v_negocio': v_negocio_val, 'v_intermed': v_intermed_val, 
                        'v_ent_imovel': v_ent_imovel_val, 'v_total_imovel': v_negocio_val - v_intermed_val,
                        'v_entrada_total': v_entrada_final, 'txt_pagamento': txt_pag
                    }
                    
                    st.session_state['pdf_file'] = gerar_pdf_completo(info)
                    st.success("✅ Proposta gerada!")

        if 'pdf_file' in st.session_state:
            with open(st.session_state['pdf_file'], "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=st.session_state['pdf_file'], use_container_width=True)