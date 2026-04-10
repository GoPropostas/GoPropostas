import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador Home Buy", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- CLASSE PARA DESENHAR O PDF IGUAL AO MODELO EXCEL ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(240, 240, 240)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "PROPOSTA DE COMPRA DE LOTEAMENTO", 1, 1, 'C', 1)
        self.ln(2)

    def secao(self, titulo):
        self.set_fill_color(220, 220, 220)
        self.set_font("Arial", 'B', 9)
        self.cell(0, 6, f" {titulo}", 1, 1, 'L', 1)

    def campo(self, label, valor, largura, ln=0):
        self.set_font("Arial", 'B', 8)
        self.cell(largura * 0.3, 7, f" {label}:", 1, 0, 'L')
        self.set_font("Arial", size=9)
        self.cell(largura * 0.7, 7, f" {valor}", 1, ln, 'L')

def gerar_proposta_completa(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    # 1. PROPONENTE
    pdf.secao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 130)
    pdf.campo("CPF/CNPJ", d['cpf'], 60, ln=1)
    pdf.campo("NAC.", d['nacionalidade'], 50)
    pdf.campo("PROFISSÃO", d['profissao'], 70)
    pdf.campo("EST. CIVIL", d['est_civil'], 70, ln=1)
    pdf.campo("E-MAIL", d['email'], 120)
    pdf.campo("FONE", d['fone'], 70, ln=1)
    
    # 2. ENDEREÇO
    pdf.ln(2)
    pdf.secao("ENDEREÇO DO PROPONENTE")
    pdf.campo("LOGRADOURO", d['rua'], 130)
    pdf.campo("Nº", d['num'], 60, ln=1)
    pdf.campo("BAIRRO", d['bairro'], 70)
    pdf.campo("CIDADE", d['cidade'], 70)
    pdf.campo("UF", d['uf'], 50, ln=1)
    
    # 3. CÔNJUGE
    pdf.ln(2)
    pdf.secao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['c_nome'], 130)
    pdf.campo("CPF", d['c_cpf'], 60, ln=1)
    
    # 4. IMÓVEL E VALORES
    pdf.ln(2)
    pdf.secao("CARACTERIZAÇÃO DO IMÓVEL E CONDIÇÕES")
    pdf.campo("EMPREEND.", d['loteamento'], 110)
    pdf.campo("UNIDADE", d['unidade'], 80, ln=1)
    pdf.campo("VALOR TOTAL", f"R$ {d['valor']:,.2f}", 95)
    pdf.campo("ATO (1%)", f"R$ {d['ato']:,.2f}", 95, ln=1)
    pdf.campo("INTERMED.", f"R$ {d['intermed']:,.2f}", 95)
    pdf.campo("36 PARC.", f"R$ {d['p36']:,.2f}", 95, ln=1)

    # 5. RODAPÉ LEGAL
    pdf.ln(5)
    pdf.set_font("Arial", size=7)
    pdf.multi_cell(0, 4, "Cláusula Compromissória: Todo litígio será decidido por arbitragem na 2ª Corte de Conciliação de Goiânia-GO. A proposta não garante reserva sem assinatura e pagamento do ato.", 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Gerar Proposta", "Admin"])

if aba == "Admin":
    st.header("⚙️ Painel Admin")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Suba a planilha", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos']["Frei Galvão"] = df.dropna(how='all', axis=1)
            st.success("Tabela Ativa!")
else:
    st.header("📝 Formulário Home Buy")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        cols = df.columns.tolist()
        lotes = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        # Variável para controlar se o PDF está pronto
        if 'pdf_pronto' not in st.session_state:
            st.session_state.pdf_pronto = None

        with st.form("proposta_home_buy"):
            st.subheader("Dados do Imóvel")
            unid = st.selectbox("Selecione o Lote", lotes[cols[0]].unique())
            
            st.subheader("Dados do Proponente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo")
            cpf = c2.text_input("CPF/CNPJ")
            
            c3, c4, c5 = st.columns(3)
            nac = c3.text_input("Nacionalidade", "Brasileiro")
            prof = c4.text_input("Profissão")
            est = c5.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
            
            st.subheader("Endereço")
            end_c1, end_c2 = st.columns([3, 1])
            rua = end_c1.text_input("Rua/Av")
            num = end_c2.text_input("Nº")
            
            st.subheader("Cônjuge (Se houver)")
            cnome = st.text_input("Nome do Cônjuge")
            ccpf = st.text_input("CPF do Cônjuge")

            submit = st.form_submit_button("Preparar Proposta")
            
            if submit:
                dados_lote = lotes[lotes[cols[0]] == unid].iloc[0]
                v_tot = float(dados_lote[cols[2]])
                
                info = {
                    'nome': nome, 'cpf': cpf, 'nacionalidade': nac, 'profissao': prof, 'est_civil': est,
                    'email': "", 'fone': "", 'rua': rua, 'num': num, 'bairro': "", 'cidade': "", 'uf': "",
                    'c_nome': cnome, 'c_cpf': ccpf, 'unidade': unid, 'valor': v_tot,
                    'ato': v_tot*0.01, 'intermed': v_tot*0.053, 'p36': float(dados_lote[cols[7]]),
                    'loteamento': "Residencial Frei Galvão"
                }
                st.session_state.pdf_pronto = gerar_proposta_completa(info)
                st.session_state.unid_ref = unid

        # BOTÃO DE DOWNLOAD FORA DO FORMULÁRIO
        if st.session_state.pdf_pronto:
            st.success("✅ Proposta preparada com sucesso!")
            st.download_button(
                label="📥 BAIXAR PROPOSTA AGORA",
                data=st.session_state.pdf_pronto,
                file_name=f"Proposta_{st.session_state.unid_ref}.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Suba a planilha no Admin.")