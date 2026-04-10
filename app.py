import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Frei Galvão", layout="wide")

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = {}

# --- FUNÇÃO PARA GERAR O PDF ---
def gerar_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "PROPOSTA DE COMPRA - RESIDENCIAL FREI GALVÃO", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. DADOS DO CLIENTE", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Nome: {d['nome'].upper()}", ln=True)
    pdf.cell(0, 8, f"CPF: {d['cpf']}", ln=True)
    
    pdf.ln(5)
    
    # Dados do Imóvel
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DETALHES DO IMÓVEL", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Unidade: {d['unidade']}", ln=True)
    pdf.cell(0, 8, f"Valor Total: R$ {d['valor']:,.2f}", ln=True)
    
    pdf.ln(5)
    
    # Condições
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. CONDIÇÕES DE PAGAMENTO", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Ato (1%): R$ {d['ato']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Intermediação (5,3%): R$ {d['intermed']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Entrada Total: R$ {(d['ato'] + d['intermed']):,.2f}", ln=True)
    pdf.cell(0, 8, f"Parcelamento: 36 parcelas de R$ {d['p36']:,.2f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    obs = ("Nota: O saldo devedor após as 36 parcelas poderá ser quitado ou financiado "
           "diretamente com o empreendedor (0,7% a.m. + IPCA).")
    pdf.multi_cell(0, 5, obs)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("Menu de Gestão")
aba = st.sidebar.radio("Navegação", ["Corretor (Vendas)", "Moderador (Admin)"])

# --- ABA ADMIN ---
if aba == "Moderador (Admin)":
    st.header("⚙️ Painel do Administrador")
    senha = st.text_input("Senha de Acesso", type="password")
    
    if senha == "admin123":
        nome_empreendimento = st.text_input("Nome do Empreendimento", value="Frei Galvão")
        arquivo = st.file_uploader("Suba a planilha Excel", type=['xlsx'])
        
        if arquivo:
            try:
                # Lógica para saltar o cabeçalho do Frei Galvão (11 linhas)
                df = pd.read_excel(arquivo, skiprows=11)
                
                # Limpa colunas e linhas totalmente vazias
                df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                
                # Resetar os nomes das colunas para garantir que espaços não quebrem o código
                df.columns = [str(c).strip() for c in df.columns]
                
                st.session_state['loteamentos'][nome_empreendimento] = df
                st.success(f"Tabela '{nome_empreendimento}' carregada com sucesso!")
                st.dataframe(df.head())
            except Exception as e:
                st.error(f"Erro ao ler ficheiro: {e}")

# --- ABA CORRETOR ---
else:
    st.header("📝 Gerador de Propostas")
    
    if not st.session_state['loteamentos']:
        st.info("Aguardando que o Administrador carregue a tabela no painel Admin.")
    else:
        lote_ref = st.selectbox("Selecione o Empreendimento", list(st.session_state['loteamentos'].keys()))
        tabela = st.session_state['loteamentos'][lote_ref]
        
        # Identificação por posição para evitar KeyError
        # 0=Descrição, 2=Valor Total, 7=36 parcelas (ajustado conforme o teu ficheiro)
        cols = tabela.columns.tolist()
        
        # Filtra apenas linhas que contêm a palavra "LOTE" na primeira coluna
        tabela[cols[0]] = tabela[cols[0]].astype(str)
        lotes_validos = tabela[tabela[cols[0]].str.contains('LOTE', case=False, na=False)]
        
        if not lotes_validos.empty:
            unidade = st.selectbox("Selecione a Unidade", lotes_validos[cols[0]].unique())
            dados_linha = lotes_validos[lotes_validos[cols[0]] == unidade].iloc[0]
            
            # Conversão de valores
            try:
                v_total = float(dados_linha[cols[2]])
                v_36x = float(dados_linha[cols[7]])
            except:
                st.error("Erro ao converter valores numéricos. Verifique a planilha.")
                v_total, v_36x = 0.0, 0.0
                
            v_ato = v_total * 0.01
            v_inter = v_total * 0.053
            
            c1, c2 = st.columns(2)
            c1.metric("Valor do Imóvel", f"R$ {v_total:,.2f}")
            c2.metric("Valor 36x", f"R$ {v_36x:,.2f}")
            
            st.divider()
            nome_cli = st.text_input("Nome do Cliente")
            cpf_cli = st.text_input("CPF do Cliente")
            
            if st.button("🚀 Gerar PDF"):
                if nome_cli and cpf_cli:
                    info_pdf = {
                        'nome': nome_cli, 'cpf': cpf_cli, 'unidade': unidade,
                        'valor': v_total, 'ato': v_ato, 'intermed': v_inter, 'p36': v_36x
                    }
                    pdf_out = gerar_pdf(info_pdf)
                    st.download_button("📥 Baixar Proposta", pdf_out, f"Proposta_{unidade}.pdf")
                else:
                    st.error("Preencha o Nome e o CPF.")
        else:
            st.warning("Não foram encontrados lotes válidos na primeira coluna da tabela.")