import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Home Buy - Portal de Propostas", layout="wide")

# --- VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]): return False
    return True

# --- CLASSE PDF (ESTILO OFICIAL HOME BUY) ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94) # Azul escuro institucional
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
    
    # 1. PROPONENTE
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
    
    # 2. CÔNJUGE
    pdf.ln(2)
    pdf.seccao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 190, True)
    pdf.campo("CPF/CNPJ", d['ccpf'], 95)
    pdf.campo("RENDA", f"R$ {d['crenda']}", 95, True)

    # 3. IMÓVEL
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.campo("INTERMEDIAÇÃO", f"R$ {d['v_intermed']:,.2f}", 95, True)
    pdf.campo("ENTRADA IMÓVEL", f"R$ {d['v_ent_imovel']:,.2f}", 95)
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['v_total_imovel']:,.2f}", 95, True)

    # 4. PAGAMENTO
    pdf.ln(2)
    pdf.seccao("CONDIÇÕES DE PAGAMENTO DA ENTRADA")
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(23, 55, 94)
    pdf.cell(190, 8, f"VALOR TOTAL DA ENTRADA: R$ {d['v_entrada_total']:,.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')

    pdf.ln(10)
    pdf.set_font('Arial', 'I', 7)
    pdf.multi_cell(190, 3, "Cláusula Compromissória: Todo litígio decorrente deste instrumento será decidido por arbitragem na 2ª Corte de Goiânia-GO (Lei 9.307/1996).")
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(190, 5, f"Goiânia, {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- LÓGICA DE INTERFACE ---
st.sidebar.image("https://homebuy.com.br/wp-content/uploads/2021/08/logo-home-buy.png", width=150) # Use o link da sua logo real
menu = st.sidebar.radio("Navegação", ["Área do Corretor", "Painel Admin"])

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
if 'db' not in st.session_state:
    st.session_state['db'] = None

# --- ÁREA ADMIN ---
if menu == "Painel Admin":
    st.header("⚙️ Configurações de Sistema")
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "admin123":
        st.success("Acesso Liberado")
        uploaded_file = st.file_uploader("Atualizar Tabela de Preços (Excel)", type=['xlsx'])
        if uploaded_file:
            st.session_state['db'] = pd.read_excel(uploaded_file, skiprows=11)
            st.info("Tabela carregada com sucesso!")
    elif senha != "":
        st.error("Senha Incorreta")

# --- ÁREA CORRETOR ---
else:
    st.header("📝 Gerador de Propostas - Home Buy")
    
    if st.session_state['db'] is None:
        st.warning("⚠️ O Administrador ainda não subiu a tabela de preços.")
    else:
        df = st.session_state['db']
        lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]
        
        with st.form("proposta_form"):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                u = st.selectbox("Selecione a Unidade", lotes[df.columns[0]].unique())
                
                # BUSCA VALORES DA TABELA
                dados = lotes[lotes[df.columns[0]] == u].iloc[0]
                v_negocio = float(dados[df.columns[2]])
                v_intermed = float(dados[df.columns[3]])
                v_ent_imovel = float(dados[df.columns[4]])
                entrada_sugerida = v_intermed + v_ent_imovel

            st.subheader("👤 Dados do Proponente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo")
            cpf = c2.text_input("CPF (somente números)")

            c3, c4, c5 = st.columns(3)
            fone = c3.text_input("Celular")
            f_fixo = c4.text_input("Telefone Fixo")
            f_ref = c5.text_input("Telefone Referência")

            c6, c7, c8 = st.columns(3)
            nac = c6.text_input("Nacionalidade", "Brasileiro")
            prof = c7.text_input("Profissão")
            est_civil = st.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
            
            c9, c10 = st.columns(2)
            renda = c9.text_input("Renda Mensal (R$)")
            email = c10.text_input("E-mail")

            st.subheader("👥 Dados do Cônjuge")
            cc1, cc2, cc3 = st.columns(3)
            cnome = cc1.text_input("Nome do Cônjuge")
            ccpf = cc2.text_input("CPF do Cônjuge")
            crenda = cc3.text_input("Renda do Cônjuge")

            st.subheader("💰 Plano Financeiro da Entrada")
            # Aqui calcula a entrada real baseada na soma das colunas
            v_entrada_input = st.number_input("Valor da Entrada Total (Intermediação + Entrada Imóvel)", value=float(entrada_sugerida))
            num_parc = st.slider("Parcelar o SALDO da entrada em quantas vezes?", 1, 4, 1)

            submit = st.form_submit_button("✨ GERAR PROPOSTA PROFISSIONAL")

            if submit:
                if not validar_cpf(cpf):
                    st.error("❌ CPF do Proponente inválido!")
                else:
                    # LÓGICA FINANCEIRA REQUERIDA
                    ato = v_negocio * 0.003
                    saldo = v_entrada_input - ato
                    v_parcela = saldo / num_parc if saldo > 0 else 0

                    txt_pag = (
                        f"O pagamento da entrada será realizado da seguinte forma:\n"
                        f"- ATO (0,30% sobre o valor do negócio): R$ {ato:,.2f}\n"
                        f"- SALDO DA ENTRADA: R$ {saldo:,.2f} parcelado em {num_parc}x de R$ {v_parcela:,.2f} mensais."
                    )

                    info_doc = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo, 'fone_ref': f_ref,
                        'nac': nac, 'prof': prof, 'est_civil': est_civil, 'renda': renda, 'email': email,
                        'cnome': cnome, 'ccpf': ccpf, 'crenda': crenda,
                        'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': u,
                        'v_negocio': v_negocio, 'v_intermed': v_intermed, 'v_ent_imovel': v_ent_imovel,
                        'v_total_imovel': v_negocio - v_intermed, 'v_entrada_total': v_entrada_input,
                        'txt_pagamento': txt_pag
                    }
                    
                    st.session_state['pdf_pronto'] = gerar_pdf_completo(info_doc)
                    st.success("✅ Documento gerado com sucesso!")

        if 'pdf_pronto' in st.session_state:
            with open(st.session_state['pdf_pronto'], "rb") as f:
                st.download_button("📥 BAIXAR PROPOSTA AGORA", f, file_name=st.session_state['pdf_pronto'], use_container_width=True)