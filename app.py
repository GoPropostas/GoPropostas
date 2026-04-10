import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador Home Buy Oficial", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- CLASSE PARA O DESIGN IDÊNTICO AO EXCEL ---
class HomeBuyPDF(FPDF):
    def header(self):
        # Cor Azul Marinho (Cabeçalho)
        self.set_fill_color(23, 55, 94) 
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", 'B', 14)
        self.cell(0, 12, "PROPOSTA DE COMPRA DE LOTEAMENTO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def secao(self, titulo):
        # Cor Cinza (Subtítulos)
        self.set_fill_color(217, 217, 217)
        self.set_font("Arial", 'B', 9)
        self.cell(0, 7, f" {titulo}", 1, 1, 'L', 1)

    def campo(self, label, valor, largura, ln=0):
        self.set_font("Arial", 'B', 8)
        self.cell(largura * 0.3, 7, f" {label}:", 1, 0, 'L')
        self.set_font("Arial", size=9)
        self.cell(largura * 0.7, 7, f" {str(valor)}", 1, ln, 'L')

def gerar_pdf_identico(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    # 1. PROPONENTE
    pdf.secao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 130)
    pdf.campo("CPF/CNPJ", d['cpf'], 60, ln=1)
    pdf.campo("NACIONALIDADE", d['nac'], 65)
    pdf.campo("PROFISSÃO", d['prof'], 65)
    pdf.campo("ESTADO CIVIL", d['est'], 60, ln=1)
    pdf.campo("E-MAIL", d['email'], 130)
    pdf.campo("CELULAR", d['fone'], 60, ln=1)
    
    # 2. CÔNJUGE
    pdf.ln(2)
    pdf.secao("CÔNJUGE / 2º PROPONENTE")
    pdf.campo("NOME", d['cnome'], 130)
    pdf.campo("CPF", d['ccpf'], 60, ln=1)
    pdf.campo("NACIONALIDADE", d['cnac'], 65)
    pdf.campo("PROFISSÃO", d['cprof'], 65)
    pdf.campo("ESTADO CIVIL", d['cest'], 60, ln=1)

    # 3. ENDEREÇO
    pdf.ln(2)
    pdf.secao("ENDEREÇO")
    pdf.campo("LOGRADOURO", d['rua'], 130)
    pdf.campo("Nº", d['num'], 60, ln=1)
    pdf.campo("BAIRRO", d['bairro'], 65)
    pdf.campo("CIDADE", d['cidade'], 95)
    pdf.campo("UF", d['uf'], 30, ln=1)

    # 4. CARACTERIZAÇÃO DO IMÓVEL (VALORES)
    pdf.ln(2)
    pdf.secao("PROPRIETÁRIO / INCORPORADOR / CONDIÇÕES")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 110)
    pdf.campo("UNIDADE", d['unidade'], 80, ln=1)
    pdf.campo("VALOR TOTAL", f"R$ {d['valor']:,.2f}", 95)
    pdf.campo("ATO (1%)", f"R$ {d['ato']:,.2f}", 95, ln=1)
    pdf.campo("INTERMED.", f"R$ {d['intermed']:,.2f}", 95)
    pdf.campo("36 PARCELAS", f"R$ {d['p36']:,.2f}", 95, ln=1)

    # 5. CLÁUSULA COMPROMISSÓRIA (TEXTO INTEGRAL DO SEU EXCEL)
    pdf.ln(4)
    pdf.set_font("Arial", size=7)
    texto_hb = (
        "Cláusula Compromissória: Todo litígio ou controvérsia originário ou decorrente deste instrumento será definitivamente decidido por arbitragem, "
        "conforme a Lei 9.307/1996. A arbitragem será administrada pela 2° Corte de Conciliação e Arbitragem de Goiânia - Goiás, situada na "
        "Avenida Fuad José Sebba, n° 1.193, Jardim Goiás, Goiânia, Goiás, eleita pelas partes e indicada nesta Cláusula. "
        "A proposta assinada não garante reserva da unidade sem o pagamento do ato."
    )
    pdf.multi_cell(0, 4, texto_hb, 1)
    
    pdf.ln(12)
    pdf.cell(95, 10, "________________________________", 0, 0, 'C')
    pdf.cell(95, 10, "________________________________", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(95, 5, "Assinatura do Proponente", 0, 0, 'C')
    pdf.cell(95, 5, "Home Buy Negócios Imobiliários", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Gerar Proposta", "Admin"])

if aba == "Admin":
    st.header("⚙️ Painel de Controle")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Suba a planilha Frei Galvão", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos']["Frei Galvão"] = df.dropna(how='all', axis=1)
            st.success("Tabela Carregada!")

else:
    st.header("📝 Nova Proposta - Padrão Home Buy")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        cols = df.columns.tolist()
        lotes = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

        with st.form("form_oficial"):
            st.subheader("1. Imóvel e Dados Pessoais")
            c1, c2 = st.columns(2)
            unid = c1.selectbox("Unidade", lotes[cols[0]].unique())
            nome = c2.text_input("Nome/Razão Social")
            
            c3, c4, c5 = st.columns(3)
            cpf = c3.text_input("CPF/CNPJ")
            nac = c4.text_input("Nacionalidade", "Brasileiro")
            prof = c5.text_input("Profissão")
            
            c6, c7, c8 = st.columns(3)
            est = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "União Estável"])
            fone = st.text_input("Telefone Celular")
            email = st.text_input("E-mail")

            st.subheader("2. Cônjuge / 2º Proponente")
            cc1, cc2 = st.columns(2)
            cnome = cc1.text_input("Nome Cônjuge")
            ccpf = cc2.text_input("CPF Cônjuge")
            
            st.subheader("3. Endereço")
            e1, e2, e3 = st.columns([3, 1, 1])
            rua = e1.text_input("Logradouro")
            num = e2.text_input("Nº")
            uf = e3.text_input("UF", "GO")
            
            e4, e5 = st.columns(2)
            bairro = e4.text_input("Bairro")
            cidade = e5.text_input("Cidade")

            if st.form_submit_button("Gerar Proposta Idêntica"):
                dados_lote = lotes[lotes[cols[0]] == unid].iloc[0]
                v_tot = float(dados_lote[cols[2]])
                
                info = {
                    'nome': nome, 'cpf': cpf, 'nac': nac, 'prof': prof, 'est': est, 'fone': fone, 'email': email,
                    'cnome': cnome, 'ccpf': ccpf, 'cnac': "Brasileiro", 'cprof': "", 'cest': est,
                    'rua': rua, 'num': num, 'bairro': bairro, 'cidade': cidade, 'uf': uf,
                    'unidade': unid, 'valor': v_tot, 'ato': v_tot*0.01, 
                    'intermed': v_tot*0.053, 'p36': float(dados_lote[cols[7]]),
                    'loteamento': "Residencial Frei Galvão"
                }
                st.session_state.pdf_data = gerar_pdf_identico(info)
                st.session_state.u_ref = unid

        if st.session_state.pdf_data:
            st.download_button("📥 BAIXAR PDF (FORMATO OFICIAL)", st.session_state.pdf_data, f"Proposta_{st.session_state.u_ref}.pdf")
    else:
        st.info("Aguardando planilha no Admin.")