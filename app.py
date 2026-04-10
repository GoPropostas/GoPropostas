import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Home Buy - Preenchimento Oficial", layout="wide")

# Caminho do seu modelo original (DEVE ESTAR NO GITHUB)
MODELO_EXCEL = "PROPOSTA LOTEAMENTO HOME BUY (1).xlsx"

def preencher_excel_oficial(dados):
    # 1. Carrega o seu modelo original
    wb = load_workbook(MODELO_EXCEL)
    ws = wb.active # Seleciona a aba da proposta

    # 2. Mapeamento de Células (Ajuste as letras/números conforme seu Excel)
    # Exemplo baseado na leitura visual do seu modelo:
    ws['B5'] = dados['nome']
    ws['B6'] = dados['cpf']
    ws['I6'] = dados['fone']
    ws['B7'] = dados['nacionalidade']
    ws['I7'] = dados['profissao']
    ws['B8'] = dados['estado_civil']
    ws['B9'] = dados['email']
    
    # Dados do Cônjuge
    ws['B12'] = dados['c_nome']
    ws['B13'] = dados['c_cpf']
    
    # Dados do Imóvel
    ws['G20'] = dados['unidade']
    ws['B22'] = dados['rua']
    ws['B24'] = dados['valor_total']
    ws['B25'] = dados['ato']
    ws['F25'] = dados['intermed']
    
    # 3. Salva em um arquivo temporário
    output_path = f"Proposta_{dados['unidade']}.xlsx"
    wb.save(output_path)
    return output_path

# --- INTERFACE ---
st.title("📝 Preencher Proposta Original Home Buy")

if not os.path.exists(MODELO_EXCEL):
    st.error(f"Erro: O arquivo '{MODELO_EXCEL}' não foi encontrado no GitHub. Suba o arquivo .xlsx para o repositório.")
else:
    with st.form("form_proposta"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Proponente")
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF/CNPJ")
            nac = st.text_input("Nacionalidade", "Brasileiro")
            prof = st.text_input("Profissão")
            est = st.text_input("Estado Civil")
            email = st.text_input("E-mail")
            fone = st.text_input("Celular")
            
        with col2:
            st.subheader("Imóvel e Pagamento")
            unid = st.text_input("Unidade (Ex: QD 01 LOTE 05)")
            rua = st.text_input("Endereço do Lote")
            v_tot = st.number_input("Valor Total", format="%.2f")
            v_ato = v_tot * 0.01
            v_int = v_tot * 0.053
            
            st.subheader("Cônjuge")
            cnome = st.text_input("Nome Cônjuge")
            ccpf = st.text_input("CPF Cônjuge")

        submit = st.form_submit_button("Gerar Proposta Preenchida")

    if submit:
        dados = {
            'nome': nome, 'cpf': cpf, 'nacionalidade': nac, 'profissao': prof,
            'estado_civil': est, 'email': email, 'fone': fone,
            'c_nome': cnome, 'c_cpf': ccpf, 'unidade': unid, 'rua': rua,
            'valor_total': v_tot, 'ato': v_ato, 'intermed': v_int
        }
        
        try:
            caminho_gerado = preencher_excel_oficial(dados)
            
            with open(caminho_gerado, "rb") as file:
                st.success("✅ Proposta gerada com sucesso utilizando seu modelo original!")
                st.download_button(
                    label="📥 Baixar Proposta Preenchida (Excel)",
                    data=file,
                    file_name=f"Proposta_{unid}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            st.info("Dica: Ao abrir o Excel, basta salvar como PDF para enviar ao cliente. Gerar PDF direto com formatação complexa de Excel via Python costuma quebrar o layout; baixar o Excel preenchido garante que tudo esteja no lugar.")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")