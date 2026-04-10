import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Home Buy Oficial", layout="wide")
TEMPLATE_EXCEL = "PROPOSTA LOTEAMENTO HOME BUY.xlsx"

if 'db_precos' not in st.session_state:
    st.session_state['db_precos'] = None

# --- FUNÇÃO DE ESCRITA SEGURA ---
def write(ws, coord, valor):
    if not valor: valor = ""
    cell = ws[coord]
    if isinstance(cell, MergedCell):
        for range_ in ws.merged_cells.ranges:
            if coord in range_:
                ws.cell(range_.min_row, range_.min_col).value = valor
                break
    else:
        ws[coord] = valor

def gerar_proposta_completa(d):
    wb = load_workbook(TEMPLATE_EXCEL)
    
    # --- ABA 1: PROPOSTA ---
    ws1 = wb["PROPOSTA"]
    # Proponente
    write(ws1, 'C5', d['nome'])
    write(ws1, 'C6', d['cpf'])
    write(ws1, 'I6', d['fone'])
    write(ws1, 'O6', d['fone_fixo'])
    write(ws1, 'C7', d['nac'])
    write(ws1, 'I7', d['prof'])
    write(ws1, 'O7', d['fone_ref'])
    write(ws1, 'C8', d['est_civil'])
    write(ws1, 'O8', d['renda'])
    write(ws1, 'C9', d['email'])
    
    # Cônjuge
    write(ws1, 'C13', d['cnome'])
    write(ws1, 'C14', d['ccpf'])
    write(ws1, 'I14', d['cfone'])
    write(ws1, 'O15', d['cfone_ref'])
    write(ws1, 'O16', d['crenda'])

    # Dados do Imóvel e Valores
    write(ws1, 'C20', d['loteamento'])
    write(ws1, 'J20', d['unidade'])
    write(ws1, 'C22', d['valor_venda'])      # Valor Total do Negócio
    write(ws1, 'I22', d['valor_comissao'])   # Valor da Comissão
    write(ws1, 'C23', d['valor_imovel'])     # Valor Total do Imóvel

    # --- ABA 2: CONTRATO DE INTERMEDIAÇÃO ---
    if "CONTRATO DE INTERMEDIAÇÃO" in wb.sheetnames:
        ws2 = wb["CONTRATO DE INTERMEDIAÇÃO"]
        write(ws2, 'B6', d['nome'])
        write(ws2, 'I6', d['cpf'])
        write(ws2, 'B7', d['cnome'])
        write(ws2, 'I7', d['ccpf'])
        write(ws2, 'B23', d['loteamento'])
        write(ws2, 'J23', d['unidade'])
        write(ws2, 'L25', d['valor_venda'])

    output = f"Proposta_{d['unidade'].replace(' ', '_')}.xlsx"
    wb.save(output)
    return output

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["Vendas", "Admin"])

if menu == "Admin":
    st.header("⚙️ Gestão de Tabelas")
    if st.text_input("Senha", type="password") == "admin123":
        arq = st.file_uploader("Upload Tabela Frei Galvão (.xlsx)", type=['xlsx'])
        if arq:
            df = pd.read_excel(arq, skiprows=11)
            st.session_state['db_precos'] = df.dropna(how='all', axis=1)
            st.success("Tabela integrada com sucesso!")

else:
    st.header("📝 Nova Proposta Home Buy")
    
    if st.session_state['db_precos'] is None:
        st.info("Aguardando upload da tabela de preços no menu Admin.")
    elif not os.path.exists(TEMPLATE_EXCEL):
        st.error(f"🚨 Ficheiro '{TEMPLATE_EXCEL}' não encontrado! Certifica-te de que subiste o ficheiro para o GitHub.")
    else:
        df = st.session_state['db_precos']
        lotes = df[df[df.columns[0]].astype(str).str.contains('LOTE', case=False, na=False)]

        with st.form("proposta_form"):
            st.subheader("1. Unidade")
            unid = st.selectbox("Escolha o Lote", lotes[df.columns[0]].unique())
            
            st.subheader("2. Dados do Proponente")
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome Completo")
            cpf = c2.text_input("CPF/CNPJ")
            email = c3.text_input("E-mail")
            
            c4, c5, c6 = st.columns(3)
            nac = c4.text_input("Nacionalidade", "Brasileiro")
            prof = c5.text_input("Profissão")
            renda = c6.text_input("Renda Mensal (R$)")
            
            c7, c8, c9 = st.columns(3)
            est = st.selectbox("Estado Civil", ["Solteiro", "Casado", "União Estável", "Divorciado", "Viúvo"])
            fone = c8.text_input("Telemóvel")
            f_fixo = c9.text_input("Fone Fixo / Referência")

            st.subheader("3. Dados do Cônjuge")
            cc1, cc2, cc3 = st.columns(3)
            cnome = cc1.text_input("Nome Cônjuge")
            ccpf = cc2.text_input("CPF Cônjuge")
            crenda = cc3.text_input("Renda Cônjuge")

            if st.form_submit_button("Gerar Proposta"):
                dados_lote = lotes[lotes[df.columns[0]] == unid].iloc[0]
                v_venda = float(dados_lote[df.columns[2]])
                
                info = {
                    'nome': nome, 'cpf': cpf, 'fone': fone, 'fone_fixo': f_fixo,
                    'nac': nac, 'prof': prof, 'fone_ref': f_fixo, 'est_civil': est,
                    'renda': renda, 'email': email,
                    'cnome': cnome, 'ccpf': ccpf, 'cfone': '', 'cnac': '',
                    'cprof': '', 'cfone_ref': '', 'crenda': crenda,
                    'loteamento': "RESIDENCIAL FREI GALVÃO", 'unidade': unid,
                    'valor_venda': v_venda, 'valor_comissao': v_venda * 0.053,
                    'valor_imovel': v_venda, 'valor_ato': v_venda * 0.01
                }
                st.session_state['path'] = gerar_proposta_completa(info)

        if 'path' in st.session_state:
            with open(st.session_state['path'], "rb") as f:
                st.download_button("📥 BAIXAR PROPOSTA PREENCHIDA", f, file_name=st.session_state['path'])