import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import subprocess
import os
from datetime import datetime

st.set_page_config(layout="wide")

# ---------------- EMPREENDIMENTOS ----------------
empreendimentos = {
    "Frei Galvão": {
        "proprietario": "Frei Galvão empreendimentos imobiliários",
        "nome": "Loteamento Frei Galvão",
        "logradouro": "Avenida Fazenda Bananal",
        "tabela": "tabela_frei_galvao.xlsx"
    }
}

# ---------------- CACHE ----------------
@st.cache_data
def carregar_tabela(arquivo):
    df = pd.read_excel(arquivo, skiprows=11)
    df.columns = df.columns.str.strip().str.lower()
    return df

# ---------------- FUNÇÕES ----------------
def limpar(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    texto = str(valor).replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except:
        return 0.0

def buscar(linha, nomes):
    for col in linha.index:
        for nome in nomes:
            if nome.lower() in col.lower():
                return limpar(linha[col])
    return 0.0

def excel_para_pdf(arquivo_excel):
    pasta = os.path.dirname(os.path.abspath(arquivo_excel))
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf",
        arquivo_excel, "--outdir", pasta
    ])
    return arquivo_excel.replace(".xlsx", ".pdf")

# ---------------- EXCEL ----------------
def preencher_proposta(d, modelo="modelo_proposta.xlsx"):

    if not os.path.exists(modelo):
        raise FileNotFoundError("Modelo não encontrado")

    wb = load_workbook(modelo)
    ws = wb.active

    # CLIENTE
    ws["E5"] = d["nome"]
    ws["D6"] = d["cpf"]

    # EMPREENDIMENTO
    ws["G18"] = d["proprietario"]
    ws["G19"] = d["empreendimento"]
    ws["C20"] = d["logradouro"]
    ws["I20"] = d["unidade"]
    ws["Q20"] = d["area"]

    ws["C21"] = d["valor_negocio"]
    ws["J21"] = d["entrada_total"]
    ws["O21"] = d["valor_imovel"]

    # TABELA
    ws["B24"] = 1
    ws["B25"] = 36
    ws["B26"] = 1

    ws["C24"] = d["entrada_imovel"]
    ws["C25"] = d["parcela_36"]
    ws["C26"] = d["saldo"]

    ws["G24"] = "Única"
    ws["G25"] = "Mensal"
    ws["G26"] = "Única"

    # COLUNA P
    ws["P24"] = "Fixo"
    ws["P25"] = "Reajustável"
    ws["P26"] = "Reajustável"
    ws["P33"] = "À vista"
    ws["P34"] = "Fixo"

    # ENTRADA
    ws["C33"] = d["ato"]
    ws["C34"] = d["parcela_entrada"]

    arquivo = "proposta.xlsx"
    wb.save(arquivo)
    return arquivo

# ---------------- APP ----------------

st.sidebar.title("Sistema")

if st.sidebar.button("🔄 Atualizar tabela"):
    st.cache_data.clear()
    st.success("Tabela atualizada!")

# EMPREENDIMENTO
st.subheader("🏢 Empreendimento")
emp_nome = st.selectbox("Selecione", list(empreendimentos.keys()))
emp = empreendimentos[emp_nome]

df = carregar_tabela(emp["tabela"])

col = df.columns[0]
unidade = st.selectbox("Lote", df[col].dropna().unique())
linha = df[df[col] == unidade].iloc[0]

# VALORES
valor_negocio = buscar(linha, ["valor negócio"])
entrada_imovel = buscar(linha, ["entrada imovel"])
intermed = buscar(linha, ["intermediação"])
parcela_36 = buscar(linha, ["36x"])
saldo = buscar(linha, ["saldo"])
area = buscar(linha, ["área", "area"])
valor_imovel = buscar(linha, ["valor imóvel"])

entrada_total = intermed + entrada_imovel
ato_min = valor_negocio * 0.003

# CLIENTE
st.subheader("Cliente")
nome = st.text_input("Nome")
cpf = st.text_input("CPF")

# ENTRADA
st.subheader("Entrada")
valor_cliente = st.number_input("Entrada do cliente", min_value=0.0)

# PERSONALIZAÇÃO
personalizar = st.checkbox("⚙️ Opções personalizáveis")

if personalizar:
    ato_manual = st.number_input("Valor de ato", min_value=0.0)
else:
    ato_manual = 0

# ATO
ato = ato_manual if ato_manual > 0 else ato_min

# PARCELAS
restante = entrada_total - valor_cliente
if restante < 0:
    restante = 0

parcelas = st.slider("Parcelar entrada", 1, 4, 1)

parcelas_lista = []

if personalizar and parcelas > 1:
    st.write("Parcelas personalizadas")
    soma = 0

    for i in range(parcelas):
        val = st.number_input(f"Parcela {i+1}", min_value=0.0, key=i)
        parcelas_lista.append(val)
        soma += val

    parcela_entrada = parcelas_lista[0] if parcelas_lista else 0

else:
    parcela_entrada = restante / parcelas if parcelas > 1 else 0

# ---------------- CONFERÊNCIA ----------------

st.divider()
st.subheader("📊 Conferência da Proposta")

c1, c2, c3 = st.columns(3)

c1.metric("Unidade", unidade)
c1.metric("Área", f"{area:.2f}")

c2.metric("Valor Negócio", f"R$ {valor_negocio:,.2f}")
c2.metric("Valor Imóvel", f"R$ {valor_imovel:,.2f}")

c3.metric("Entrada Imóvel", f"R$ {entrada_imovel:,.2f}")
c3.metric("Intermediação", f"R$ {intermed:,.2f}")

st.info(f"Entrada Total: R$ {entrada_total:,.2f}")

c4, c5, c6 = st.columns(3)

c4.metric("Entrada Cliente", f"R$ {valor_cliente:,.2f}")
c5.metric("Ato", f"R$ {ato:,.2f}")

restante_entrada = entrada_total - valor_cliente
if restante_entrada < 0:
    restante_entrada = 0

c6.metric("Restante", f"R$ {restante_entrada:,.2f}")

if parcelas > 1:
    if personalizar:
        soma_parcelas = sum(parcelas_lista)
        st.warning(f"Soma parcelas: {soma_parcelas:.2f}")
        if abs(soma_parcelas - restante_entrada) > 0.01:
            st.error("Parcelas não fecham")
    else:
        st.success(f"{parcelas}x de R$ {parcela_entrada:.2f}")

if ato > valor_cliente:
    st.error("Ato maior que entrada!")

# ---------------- GERAR ----------------

if st.button("GERAR PDF"):
    try:
        dados = {
            "nome": nome,
            "cpf": cpf,
            "proprietario": emp["proprietario"],
            "empreendimento": emp["nome"],
            "logradouro": emp["logradouro"],
            "unidade": unidade,
            "area": area,
            "valor_negocio": valor_negocio,
            "entrada_total": entrada_total,
            "valor_imovel": valor_imovel,
            "entrada_imovel": entrada_imovel,
            "parcela_36": parcela_36,
            "saldo": saldo,
            "ato": ato,
            "parcela_entrada": parcela_entrada
        }

        excel = preencher_proposta(dados)
        pdf = excel_para_pdf(excel)

        if os.path.exists(pdf):
            with open(pdf, "rb") as f:
                st.download_button(
                    "📥 Baixar PDF",
                    f,
                    file_name=f"Proposta_{unidade}.pdf",
                    mime="application/pdf"
                )

            st.success("Proposta gerada!")

        else:
            st.error("Erro ao gerar PDF")

    except Exception as e:
        st.error(f"Erro: {e}")