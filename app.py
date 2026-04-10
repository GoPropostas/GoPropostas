import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador Home Buy - Oficial", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- CLASSE PARA DESENHAR O PDF IGUAL AO MODELO ---
class HomeBuyPDF(FPDF):
    def header(self):
        # Cabeçalho da Proposta
        self.set_fill_color(240, 240, 240)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "PROPOSTA DE COMPRA DE LOTEAMENTO", 1, 1, 'C', 1)
        self.ln(2)

    def secao(self, titulo):
        self.set_fill_color(220, 220, 220)
        self.set_font("Arial", 'B', 9)
        self.cell(0, 6, titulo, 1, 1, 'L', 1)

    def campo(self, label, valor, largura, ln=0):
        self.set_font("Arial", 'B', 8)
        self.cell(largura * 0.3, 7, f" {label}:", 1, 0, 'L')
        self.set_font("Arial", size=9)
        self.cell(largura * 0.7, 7, f" {valor}", 1, ln, 'L')

# --- FUNÇÃO DE GERAÇÃO ---
def gerar_proposta_completa(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    # 1. PROPONENTE
    pdf.secao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 130)
    pdf.campo("CPF/CNPJ", d['cpf'], 60, ln=1)
    pdf.campo("NAC.", d['nacionalidade'], 60)
    pdf.campo("PROFISSÃO", d['profissao'], 70)
    pdf.campo("EST. CIVIL", d['est_civil'], 60, ln=1)
    pdf.campo("E-MAIL", d['email'], 190, ln=1)
    pdf.ln(2)

    # 2. CÔNJUGE / 2º PROPONENTE
    pdf.secao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['c_nome'], 130)
    pdf.campo("CPF/CNPJ", d['c_cpf'], 60, ln=1)
    pdf.campo("NAC.", d['c_nac'], 60)
    pdf.campo("PROFISSÃO", d['c_prof'], 70)
    pdf.campo("EST. CIVIL", d['c_est'], 60, ln=1)
    pdf.ln(2)

    # 3. IMÓVEL
    pdf.secao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("EMPREEND.", d['loteamento'], 110)
    pdf.campo("UNIDADE", d['unidade'], 80, ln=1)
    pdf.ln(2)

    # 4. CONDIÇÕES
    pdf.secao("CONDIÇÕES DE PAGAMENTO")
    pdf.campo("VALOR TOTAL", f"R$ {d['valor']:,.2f}", 95)
    pdf.campo("ATO (1%)", f"R$ {d['ato']:,.2f}", 95, ln=1)
    pdf.campo("INTERMED.", f"R$ {d['intermed']:,.2f}", 95)
    pdf.campo("36 PARCELAS", f"R$ {d['p36']:,.2f}", 95, ln=1)
    pdf.ln(4)

    # 5. CLÁUSULAS (Exatamente como no seu modelo)
    pdf.set_font("Arial", size=7)
    clausulas = (
        "O PROPONENTE autoriza a consulta de dados cadastrais. A proposta não garante reserva sem assinatura. "
        "Saldo devedor corrigido por IPCA + 0,7% a.m. Todo litígio será decidido por arbitragem na 2ª Corte de Goiânia-GO."
    )
    pdf.multi_cell(0, 4, clausulas, 1)
    
    pdf.ln(10)
    pdf.cell(95, 10, "__________________________", 0, 0, 'C')
    pdf.cell(95, 10, "__________________________", 0, 1, 'C')
    pdf.cell(95, 5, "Assinatura Proponente", 0, 0, 'C')
    pdf.cell(95, 5, "Home Buy Negócios Imobiliários", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Gerar Proposta", "Admin (Upload)"])

if aba == "Admin (Upload)":
    st.header("⚙️ Configuração")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Suba a planilha Frei Galvão", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos']["Frei Galvão"] = df.dropna(how='all', axis=1)
            st.success("Tabela Ativa!")

else:
    st.header("📝 Proposta Home Buy")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        cols = df.columns.tolist()
        lotes = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        # FORMULÁRIO DIVIDIDO
        with st.form("proposta_form"):
            st.subheader("1. Imóvel")
            unid = st.selectbox("Unidade", lotes[cols[0]].unique())
            dados_lote = lotes[lotes[cols[0]] == unid].iloc[0]
            
            st.subheader("2. Proponente Principal")
            c1, c2 = st.columns(2)
            n_cli = c1.text_input("Nome/Razão Social")
            cpf_cli = c2.text_input("CPF/CNPJ")
            c3, c4, c5 = st.columns(3)
            nac = c3.text_input("Nacionalidade", "Brasileiro")
            prof = c4.text_input("Profissão")
            est = c5.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
            email_cli = st.text_input("E-mail")

            st.subheader("3. Cônjuge / 2º Proponente")
            cc1, cc2 = st.columns(2)
            cnome = cc1.text_input("Nome Cônjuge")
            ccpf = cc2.text_input("CPF Cônjuge")
            cc3, cc4 = st.columns(2)
            cnac = cc3.text_input("Nacionalidade Cônjuge", "Brasileiro")
            cprof = cc4.text_input("Profissão Cônjuge")

            if st.form_submit_button("Gerar Proposta"):
                v_tot = float(dados_lote[cols[2]])
                v_p36 = float(dados_lote[cols[7]])
                
                info = {
                    'nome': n_cli, 'cpf': cpf_cli, 'nacionalidade': nac, 'profissao': prof, 'est_civil': est, 'email': email_cli,
                    'c_nome': cnome, 'c_cpf': ccpf, 'c_nac': cnac, 'c_prof': cprof, 'c_est': "Mesmo",
                    'unidade': unid, 'valor': v_tot, 'ato': v_tot*0.01, 'intermed': v_tot*0.053, 'p36': v_p36,
                    'loteamento': "Residencial Frei Galvão"
                }
                
                pdf_res = gerar_proposta_completa(info)
                st.download_button("📥 Baixar Proposta PDF", pdf_res, f"Proposta_{unid}.pdf")
    else:
        st.info("Suba a planilha no Admin.")