import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador Home Buy Oficial", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- CLASSE PARA DESIGN IDÊNTICO AO PDF HOME BUY ---
class HomeBuyPDF(FPDF):
    def header(self):
        # Cabeçalho Azul Escuro (RGB exato da Home Buy)
        self.set_fill_color(23, 55, 94) 
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", 'B', 14)
        self.cell(0, 12, "PROPOSTA DE COMPRA DE LOTEAMENTO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def secao(self, titulo):
        # Faixa de Título de Seção (Cinza claro)
        self.set_fill_color(217, 217, 217)
        self.set_font("Arial", 'B', 9)
        self.cell(0, 7, f" {titulo}", 1, 1, 'L', 1)

    def campo(self, label, valor, largura, ln=0):
        # Desenha o rótulo em negrito e o valor
        self.set_font("Arial", 'B', 7)
        self.cell(largura * 0.35, 7, f" {label}:", 1, 0, 'L')
        self.set_font("Arial", size=9)
        self.cell(largura * 0.65, 7, f" {str(valor)}", 1, ln, 'L')

def gerar_pdf_fiel(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    
    # 1. PROPONENTE
    pdf.secao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 130)
    pdf.campo("CPF/CNPJ", d['cpf'], 60, ln=1)
    
    pdf.campo("NACIONALIDADE", d['nac'], 65)
    pdf.campo("PROFISSÃO", d['prof'], 65)
    pdf.campo("ESTADO CIVIL", d['est'], 60, ln=1)
    
    pdf.campo("E-MAIL", d['email'], 120)
    pdf.campo("CELULAR", d['fone'], 70, ln=1)
    pdf.ln(2)

    # 2. CÔNJUGE (Aqui estava o erro - corrigido)
    pdf.secao("CÔNJUGE / 2º PROPONENTE / REPRESENTANTE")
    pdf.campo("NOME", d['cnome'], 130)
    pdf.campo("CPF", d['ccpf'], 60, ln=1)
    pdf.campo("NACIONALIDADE", d['cnac'], 65)
    pdf.campo("PROFISSÃO", d['cprof'], 65)
    pdf.campo("CELULAR", d['cfone'], 60, ln=1) # Corrigido para bater com o dicionário
    pdf.ln(2)

    # 3. ENDEREÇO
    pdf.secao("ENDEREÇO DE CORRESPONDÊNCIA")
    pdf.campo("LOGRADOURO", d['rua'], 140)
    pdf.campo("Nº", d['num'], 50, ln=1)
    pdf.campo("BAIRRO", d['bairro'], 65)
    pdf.campo("CIDADE", d['cidade'], 95)
    pdf.campo("UF", d['uf'], 30, ln=1)
    pdf.ln(2)

    # 4. IMÓVEL E CONDIÇÕES
    pdf.secao("CARACTERIZAÇÃO DO IMÓVEL E CONDIÇÕES")
    pdf.campo("EMPREENDIMENTO", d['loteamento'], 130)
    pdf.campo("UNIDADE", d['unidade'], 60, ln=1)
    
    pdf.campo("VALOR TOTAL IMÓVEL", f"R$ {d['valor']:,.2f}", 95)
    pdf.campo("ATO (1%)", f"R$ {d['ato']:,.2f}", 95, ln=1)
    
    pdf.campo("INTERMEDIAÇÃO (5,3%)", f"R$ {d['intermed']:,.2f}", 95)
    pdf.campo("36 PARCELAS", f"R$ {d['p36']:,.2f}", 95, ln=1)
    
    # 5. CLÁUSULA COMPROMISSÓRIA (Exata do seu PDF)
    pdf.ln(4)
    pdf.set_font("Arial", size=7)
    texto_hb = (
        "Cláusula Compromissória: Todo litígio ou controvérsia originário ou decorrente deste instrumento será definitivamente decidido por arbitragem, "
        "conforme a Lei 9.307/1996. A arbitragem será administrada pela 2ª Corte de Conciliação e Arbitragem de Goiânia - Goiás, situada na "
        "Avenida Fuad José Sebba, nº 1.193, Jardim Goiás, Goiânia, Goiás, eleita pelas partes e indicada nesta Cláusula.\n\n"
        "Neste ato, a Home Buy Negócios Imobiliários LTDA informa que utilizará os dados pessoais do(s) proponente(s) para ações de marketing "
        "e execução do contrato de compra e venda, de acordo com a Lei 13.709/2018 (LGPD)."
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
    st.header("⚙️ Configuração")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Upload Planilha Frei Galvão", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos']["Frei Galvão"] = df.dropna(how='all', axis=1)
            st.success("Tabela Carregada!")
else:
    st.header("📝 Formulário Home Buy")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        cols = df.columns.tolist()
        lotes = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

        with st.form("form_vendas"):
            st.subheader("1. Lote")
            unid = st.selectbox("Unidade", lotes[cols[0]].unique())
            
            st.subheader("2. Proponente Principal")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome/Razão Social")
            cpf = c2.text_input("CPF/CNPJ")
            c3, c4, c5 = st.columns(3)
            nac = c3.text_input("Nacionalidade", "Brasileiro")
            prof = c4.text_input("Profissão")
            est = st.selectbox("Estado Civil", ["Solteiro", "Casado", "Divorciado", "União Estável"])
            email = st.text_input("E-mail")
            fone = st.text_input("Celular")

            st.subheader("3. Cônjuge / 2º Proponente")
            cc1, cc2 = st.columns(2)
            cnome = cc1.text_input("Nome Cônjuge")
            ccpf = cc2.text_input("CPF Cônjuge")
            cc3, cc4, cc5 = st.columns(3)
            cnac = cc3.text_input("Nacionalidade Cônjuge", "Brasileiro")
            cprof = cc4.text_input("Profissão Cônjuge")
            cfone = cc5.text_input("Celular Cônjuge") # Campo adicionado para evitar o erro

            st.subheader("4. Endereço")
            e1, e2 = st.columns([3, 1])
            rua = e1.text_input("Logradouro (Rua/Av)")
            num = e2.text_input("Nº")
            e3, e4, e5 = st.columns([2, 2, 1])
            bairro = e3.text_input("Bairro")
            cidade = e4.text_input("Cidade")
            uf = e5.text_input("UF", "GO")

            if st.form_submit_button("Gerar PDF Idêntico"):
                dados_lote = lotes[lotes[cols[0]] == unid].iloc[0]
                v_tot = float(dados_lote[cols[2]])
                
                info = {
                    'nome': nome, 'cpf': cpf, 'nac': nac, 'prof': prof, 'est': est, 'email': email, 'fone': fone,
                    'cnome': cnome, 'ccpf': ccpf, 'cnac': cnac, 'cprof': cprof, 'cfone': cfone,
                    'rua': rua, 'num': num, 'bairro': bairro, 'cidade': cidade, 'uf': uf,
                    'unidade': unid, 'valor': v_tot, 'ato': v_tot*0.01, 
                    'intermed': v_tot*0.053, 'p36': float(dados_lote[cols[7]]),
                    'loteamento': "Residencial Frei Galvão"
                }
                st.session_state.pdf_data = gerar_pdf_fiel(info)
                st.session_state.u_ref = unid

        if st.session_state.pdf_data:
            st.download_button("📥 BAIXAR PROPOSTA (PDF OFICIAL)", st.session_state.pdf_data, f"Proposta_{st.session_state.u_ref}.pdf")
    else:
        st.info("Suba a planilha no Admin primeiro.")