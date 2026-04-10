import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Home Buy - Frei Galvão", layout="wide")

# Nome do seu arquivo modelo que deve estar no GitHub
ARQUIVO_MODELO = "PROPOSTA LOTEAMENTO HOME BUY (1).xlsx"

if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = None

# --- FUNÇÃO PARA ESCREVER NO EXCEL (CORRIGIDA PARA CÉLULAS MESCLADAS) ---
def preencher_proposta_excel(dados):
    wb = load_workbook(ARQUIVO_MODELO)
    ws = wb.active

    # MAPEAMENTO DE CÉLULAS (Ajuste aqui as coordenadas conforme seu Excel)
    # Proponente
    ws['B6'] = dados['nome']
    ws['B7'] = dados['cpf']
    ws['H7'] = dados['fone']
    ws['B8'] = dados['nac']
    ws['H8'] = dados['prof']
    ws['B9'] = dados['est_civil']
    ws['B10'] = dados['email']
    
    # Cônjuge
    ws['B13'] = dados['cnome']
    ws['B14'] = dados['ccpf']
    
    # Imóvel e Valores
    ws['C21'] = "RESIDENCIAL FREI GALVÃO"
    ws['I21'] = dados['unidade']
    ws['C22'] = dados['rua']
    ws['C24'] = dados['valor_total']
    ws['C25'] = dados['ato']
    ws['I25'] = dados['comissao']

    output_path = f"Proposta_Gerada_{dados['unidade']}.xlsx"
    wb.save(output_path)
    return output_path

# --- INTERFACE ---
st.sidebar.title("Menu")
aba = st.sidebar.radio("Ir para:", ["Corretor (Vendas)", "Admin (Tabela)"])

# --- ABA ADMIN ---
if aba == "Admin (Tabela)":
    st.header("⚙️ Configuração do Sistema")
    senha = st.text_input("Senha de Acesso", type="password")
    if senha == "admin123":
        arq = st.file_uploader("Suba a tabela de preços (Excel do Frei Galvão)", type=['xlsx'])
        if arq:
            # Pula as 11 linhas iniciais como no Frei Galvão original
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos'] = df.dropna(how='all', axis=1)
            st.success("Tabela de preços carregada e integrada!")

# --- ABA CORRETOR ---
else:
    st.header("📝 Gerar Proposta no Modelo Original")
    
    if st.session_state['loteamentos'] is None:
        st.info("O administrador precisa carregar a tabela de preços na aba Admin.")
    elif not os.path.exists(ARQUIVO_MODELO):
        st.error(f"Arquivo '{ARQUIVO_MODELO}' não encontrado no servidor. Suba o modelo .xlsx para o GitHub.")
    else:
        df_precos = st.session_state['loteamentos']
        cols = df_precos.columns.tolist()
        
        # Filtra apenas linhas que são LOTES
        lotes_validos = df_precos[df_precos[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]
        
        with st.form("proposta_oficial"):
            st.subheader("1. Seleção do Imóvel")
            unidade_sel = st.selectbox("Escolha a Unidade", lotes_validos[cols[0]].unique())
            
            # Busca valores automaticamente
            dados_lote = lotes_validos[lotes_validos[cols[0]] == unidade_sel].iloc[0]
            valor_venda = float(dados_lote[cols[2]])
            valor_p36 = float(dados_lote[cols[7]])
            
            st.write(f"**Valor Total:** R$ {valor_venda:,.2f} | **Ato (1%):** R$ {valor_venda*0.01:,.2f}")

            st.subheader("2. Dados do Cliente")
            c1, c2 = st.columns(2)
            nome_cli = c1.text_input("Nome Completo")
            cpf_cli = c2.text_input("CPF/CNPJ")
            
            c3, c4 = st.columns(2)
            nac_cli = c3.text_input("Nacionalidade", "Brasileiro")
            prof_cli = c4.text_input("Profissão")
            
            email_cli = st.text_input("E-mail")
            fone_cli = st.text_input("Telefone")
            est_civil = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "União Estável"])

            st.subheader("3. Cônjuge (Se houver)")
            cnome = st.text_input("Nome do Cônjuge")
            ccpf = st.text_input("CPF do Cônjuge")

            if st.form_submit_button("Gerar Proposta Excel"):
                if not nome_cli or not cpf_cli:
                    st.error("Preencha o Nome e CPF do cliente.")
                else:
                    dados_finais = {
                        'nome': nome_cli, 'cpf': cpf_cli, 'fone': fone_cli,
                        'nac': nac_cli, 'prof': prof_cli, 'est_civil': est_civil,
                        'email': email_cli, 'cnome': cnome, 'ccpf': ccpf,
                        'unidade': unidade_sel, 'rua': "Residencial Frei Galvão",
                        'valor_total': valor_venda, 'ato': valor_venda * 0.01,
                        'comissao': valor_venda * 0.053, 'p36': valor_p36
                    }
                    
                    try:
                        caminho_arquivo = preencher_proposta_excel(dados_finais)
                        with open(caminho_arquivo, "rb") as f:
                            st.success("✅ Proposta preparada com sucesso!")
                            st.download_button(
                                label="📥 Baixar Proposta Preenchida",
                                data=f,
                                file_name=f"Proposta_{unidade_sel}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")