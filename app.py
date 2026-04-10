import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Propostas - Frei Galvão", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO GERAR PDF ---
def gerar_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "PROPOSTA DE COMPRA - FREI GALVÃO", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DADOS DO CLIENTE", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Nome: {d['nome'].upper()}", ln=True)
    pdf.cell(0, 8, f"CPF: {d['cpf']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DETALHES DO IMÓVEL", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Unidade: {d['unidade']}", ln=True)
    pdf.cell(0, 8, f"Valor Total: R$ {d['valor']:,.2f}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "CONDIÇÕES DE PAGAMENTO", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Ato (1%): R$ {d['ato']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Intermediação (5,3%): R$ {d['intermed']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Entrada Total: R$ {(d['ato']+d['intermed']):,.2f}", ln=True)
    pdf.cell(0, 8, f"Parcelamento: 36 parcelas de R$ {d['p36']:,.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    msg = "Saldo devedor após 36 meses sujeito a financiamento próprio (0,7% a.m + IPCA) ou quitação."
    pdf.multi_cell(0, 5, msg)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Vendas", "Admin"])

if aba == "Admin":
    st.header("⚙️ Painel Admin")
    if st.text_input("Senha", type="password") == "admin123":
        arquivo = st.file_uploader("Suba a planilha Frei Galvão", type=['xlsx'])
        if arquivo:
            # Pula as 11 linhas de cabeçalho (conforme o arquivo que você mandou)
            df = pd.read_excel(arquivo, skiprows=11)
            # Remove colunas vazias
            df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
            
            st.session_state['loteamentos']["Frei Galvão"] = df
            st.success("Tabela carregada!")
            st.dataframe(df.head())

else:
    st.header("📝 Gerar Proposta")
    if "Frei Galvão" in st.session_state['loteamentos']:
        df = st.session_state['loteamentos']["Frei Galvão"]
        
        # Filtra apenas linhas que tem nome de lote (evita subtitulos de quadra)
        lotes_validos = df[df['DESCRIÇÃO'].str.contains('LOTE', na=False)]
        
        unidade = st.selectbox("Selecione o Lote", lotes_validos['DESCRIÇÃO'].unique())
        dados = lotes_validos[lotes_validos['DESCRIÇÃO'] == unidade].iloc[0]
        
        # Extração de valores (ajustado para os nomes das colunas da sua tabela)
        v_total = float(dados['VALOR TOTAL'])
        v_36x = float(dados['36 parcelas'])
        v_ato = v_total * 0.01
        v_inter = v_total * 0.053
        
        col1, col2 = st.columns(2)
        col1.metric("Valor Total", f"R$ {v_total:,.2f}")
        col2.metric("36x de", f"R$ {v_36x:,.2f}")
        
        st.write(f"**Entrada:** Ato (R$ {v_ato:,.2f}) + Intermediação (R$ {v_inter:,.2f})")
        
        nome = st.text_input("Nome do Cliente")
        cpf = st.text_input("CPF")
        
        if st.button("Gerar PDF"):
            if nome and cpf:
                pdf_bytes = gerar_pdf({'nome':nome, 'cpf':cpf, 'unidade':unidade, 'valor':v_total, 'ato':v_ato, 'intermed':v_inter, 'p36':v_36x})
                st.download_button("📥 Baixar PDF", pdf_bytes, f"Proposta_{unidade}.pdf")
    else:
        st.info("O Admin precisa subir a planilha no painel ao lado.")