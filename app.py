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

# ---------------- CACHE TABELA ----------------
@st.cache_data
def carregar_tabela(arquivo):
    df = pd.read_excel(arquivo, skiprows=11)
    df.columns = df.columns.str.strip().str.lower()
    return df

# ---------------- LIMPEZA ----------------
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

# ---------------- PDF ----------------
def excel_para_pdf(arquivo_excel):
    pasta = os.path.dirname(os.path.abspath(arquivo_excel))

    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        arquivo_excel,
        "--outdir", pasta
    ])

    return arquivo_excel.replace(".xlsx", ".pdf")

# ---------------- PREENCHER EXCEL ----------------
def preencher_proposta(d, modelo="modelo_proposta.xlsx"):

    if not os.path.exists(modelo):
        raise FileNotFoundError(f"Arquivo não encontrado: {modelo}")

    wb = load_workbook(modelo)
    ws = wb.active

    # CLIENTE
    ws["E5"] = d["nome"]
    ws["D6"] = d["cpf"]
    ws["J6"] = d["telefone"]
    ws["O6"] = d["fone_fixo"]
    ws["D7"] = d["nacionalidade"]
    ws["J7"] = d["profissao"]
    ws["P7"] = d["fone_pref"]
    ws["D8"] = d["estado_civil"]
    ws["O8"] = d["renda"]
    ws["E9"] = d["email"]

    # SEGUNDO PROPONENTE
    ws["G11"] = d["nome2"]
    ws["D13"] = d["cpf2"]
    ws["J13"] = d["telefone2"]
    ws["O13"] = d["fone_fixo2"]
    ws["D14"] = d["nacionalidade2"]
    ws["J14"] = d["profissao2"]
    ws["P14"] = d["fone_pref2"]
    ws["D15"] = d["estado_civil2"]
    ws["O15"] = d["renda2"]

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

    ws["K24"] = d["data_venc"]
    ws["K25"] = d["data_parc"]
    ws["K26"] = d["data_saldo"]

    # ENTRADA PERSONALIZADA
    ws["B33"] = 1
    ws["B34"] = d["parcelas_ent"] if d["parcelas_ent"] > 1 else ""

    ws["C33"] = d["ato"]
    ws["C34"] = d["vl_parcela_ent"] if d["parcelas_ent"] > 1 else ""

    ws["G33"] = "Única"
    ws["G34"] = "Mensal" if d["parcelas_ent"] > 1 else ""

    ws["K33"] = datetime.today().strftime("%d/%m/%Y")
    ws["K34"] = d["data_parc_ent"] if d["parcelas_ent"] > 1 else ""

    arquivo = "proposta.xlsx"
    wb.save(arquivo)
    return arquivo

# ---------------- APP ----------------

st.sidebar.title("⚙️ Sistema")

# BOTÃO ATUALIZAR
if st.sidebar.button("🔄 Atualizar tabela"):
    st.cache_data.clear()
    st.success("Tabela atualizada!")

# EMPREENDIMENTO
st.subheader("🏢 Empreendimento")
emp_nome = st.selectbox("Selecione", list(empreendimentos.keys()))
emp = empreendimentos[emp_nome]

# CARREGAR TABELA AUTOMÁTICA
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
telefone = st.text_input("Telefone")
fone_fixo = st.text_input("Fixo")
nacionalidade = st.text_input("Nacionalidade")
profissao = st.text_input("Profissão")
fone_pref = st.text_input("Fone preferência")
estado_civil = st.text_input("Estado civil")
renda = st.text_input("Renda")
email = st.text_input("Email")

# ENTRADA
st.subheader("Entrada")
valor_cliente = st.number_input("Entrada do cliente")

ato = min(valor_cliente, ato_min)
restante = entrada_total - valor_cliente
if restante < 0:
    restante = 0

parcelas_ent = st.slider("Parcelar entrada", 1, 4, 1)
vl_parcela_ent = restante / parcelas_ent if parcelas_ent > 1 else 0

# DATAS
st.subheader("Datas")
data_venc = st.date_input("Vencimento")
data_parc = st.date_input("Parcelas 36x")
data_saldo = st.date_input("Saldo")
data_parc_ent = st.date_input("Parcelas entrada")

# GERAR
if st.button("GERAR PDF"):
    try:
        dados = {
            "nome": nome,
            "cpf": cpf,
            "telefone": telefone,
            "fone_fixo": fone_fixo,
            "nacionalidade": nacionalidade,
            "profissao": profissao,
            "fone_pref": fone_pref,
            "estado_civil": estado_civil,
            "renda": renda,
            "email": email,

            "nome2": "",
            "cpf2": "",
            "telefone2": "",
            "fone_fixo2": "",
            "nacionalidade2": "",
            "profissao2": "",
            "fone_pref2": "",
            "estado_civil2": "",
            "renda2": "",

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

            "data_venc": data_venc.strftime("%d/%m/%Y"),
            "data_parc": data_parc.strftime("%d/%m/%Y"),
            "data_saldo": data_saldo.strftime("%d/%m/%Y"),
            "data_parc_ent": data_parc_ent.strftime("%d/%m/%Y"),

            "ato": ato,
            "parcelas_ent": parcelas_ent,
            "vl_parcela_ent": vl_parcela_ent
        }

        excel_file = preencher_proposta(dados)
        pdf_file = excel_para_pdf(excel_file)

        if os.path.exists(pdf_file):
            nome_arquivo = f"Proposta_{unidade.replace(' ', '_')}.pdf"

            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📥 Baixar PDF",
                    f,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )

            st.success("✅ Proposta gerada!")

        else:
            st.error("❌ PDF não foi gerado")

    except Exception as e:
        st.error(f"Erro: {e}")