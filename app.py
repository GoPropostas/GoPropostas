import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Home Buy - Gerador Oficial", layout="wide")

ARQUIVO_MODELO = "PROPOSTA LOTEAMENTO HOME BUY (1).xlsx"

# Inicialização do estado
if 'loteamentos' not in st.session_state:
    st.session_state['loteamentos'] = None
if 'arquivo_pronto' not in st.session_state:
    st.session_state['arquivo_pronto'] = None

# --- FUNÇÃO PARA ESCREVER EM CÉLULAS MESCLADAS ---
def safe_write(ws, cell_coord, value):
    cell = ws[cell_coord]
    if isinstance(cell, MergedCell):
        for range_ in ws.merged_cells.ranges:
            if cell_coord in range_:
                ws.cell(range_.min_row, range_.min_col).value = value
                break
    else:
        ws[cell_coord] = value

def preencher_proposta_excel(dados):
    wb = load_workbook(ARQUIVO_MODELO)
    ws = wb.active

    # Mapeamento conforme seu modelo original
    safe_write(ws, 'B5', dados['nome'])
    safe_write(ws, 'B6', dados['cpf'])
    safe_write(ws, 'I6', dados['fone'])
    safe_write(ws, 'B7', dados['nac'])
    safe_write(ws, 'I7', dados['prof'])
    safe_write(ws, 'B8', dados['est_civil'])
    safe_write(ws, 'B9', dados['email'])
    
    # Cônjuge
    safe_write(ws, 'B11', dados['cnome'])
    safe_write(ws, 'B12', dados['ccpf'])
    
    # Imóvel e Valores
    safe_write(ws, 'C19', "RESIDENCIAL FREI GALVÃO")
    safe_write(ws, 'I20', dados['unidade'])
    safe_write(ws, 'C23', dados['valor_total'])
    safe_write(ws, 'B25', dados['ato'])
    safe_write(ws, 'G25', dados['comissao'])

    output_path = f"Proposta_{dados['unidade'].replace(' ', '_')}.xlsx"
    wb.save(output_path)
    return output_path

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["Vendas", "Admin"])

if aba == "Admin":
    st.header("⚙️ Painel Administrativo")
    senha = st.text_input("Senha", type="password")
    if senha == "admin123":
        arq = st.file_uploader("Suba a Tabela Frei Galvão", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['loteamentos'] = df.dropna(how='all', axis=1)
            st.success("Tabela carregada!")

else:
    st.header("📝 Preencher Proposta Home Buy")
    
    if st.session_state['loteamentos'] is None:
        st.info("Aguardando upload da tabela no Admin.")
    elif not os.path.exists(ARQUIVO_MODELO):
        st.error(f"O arquivo {ARQUIVO_MODELO} não foi encontrado no GitHub!")
    else:
        df = st.session_state['loteamentos']
        cols = df.columns.tolist()
        lotes = df[df[cols[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        with st.form("main_form"):
            unid = st.selectbox("Selecione o Lote", lotes[cols[0]].unique())
            
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Cliente")
            cpf = c2.text_input("CPF/CNPJ")
            
            c3, c4, c5 = st.columns(3)
            nac = c3.text_input("Nacionalidade", "Brasileiro")
            prof = c4.text_input("Profissão")
            fone = c5.text_input("Celular")
            
            email = st.text_input("E-mail")
            est = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "União Estável"])
            
            st.write("---")
            cnome = st.text_input("Nome Cônjuge")
            ccpf = st.text_input("CPF Cônjuge")

            # O botão de formulário apenas PROCESSA os dados
            gerar = st.form_submit_button("Preparar Proposta")

            if gerar:
                dados_lote = lotes[lotes[cols[0]] == unid].iloc[0]
                v_tot = float(dados_lote[cols[2]])
                
                info = {
                    'nome': nome, 'cpf': cpf, 'fone': fone, 'nac': nac, 'prof': prof,
                    'est_civil': est, 'email': email, 'cnome': cnome, 'ccpf': ccpf,
                    'unidade': unid, 'valor_total': v_tot, 'ato': v_tot * 0.01,
                    'comissao': v_tot * 0.053
                }
                
                try:
                    caminho = preencher_proposta_excel(info)
                    # Guardamos o caminho no session_state
                    st.session_state['arquivo_pronto'] = caminho
                    st.session_state['unidade_gerada'] = unid
                except Exception as e:
                    st.error(f"Erro: {e}")

        # O BOTÃO DE DOWNLOAD FICA FORA DO FORMULÁRIO
        if st.session_state['arquivo_pronto']:
            st.success(f"✅ Proposta da unidade {st.session_state['unidade_gerada']} pronta!")
            with open(st.session_state['arquivo_pronto'], "rb") as f:
                st.download_button(
                    label="📥 BAIXAR AGORA (.xlsx)",
                    data=f,
                    file_name=f"Proposta_{st.session_state['unidade_gerada']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )