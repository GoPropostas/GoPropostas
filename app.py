import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import subprocess
import os
import json
from datetime import datetime

st.set_page_config(layout="wide")

# ---------------- USUÁRIOS ----------------
USUARIOS_FILE = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r") as f:
        return json.load(f)

def salvar_usuarios(users):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ---------------- LOGIN ----------------
def tela_login():
    st.title("🔐 Sistema de Propostas")

    abas = st.tabs(["Login", "Criar conta"])
    usuarios = carregar_usuarios()

    with abas[0]:
        user = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", key="btn_login"):
            if user in usuarios and usuarios[user]["senha"] == senha:
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
                st.session_state["tipo"] = usuarios[user]["tipo"]
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    with abas[1]:
        novo = st.text_input("Novo usuário", key="cad_user")
        senha_nova = st.text_input("Senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirm")

        if st.button("Criar conta", key="btn_cadastro"):
            if novo in usuarios:
                st.warning("Usuário já existe")
            elif senha_nova != confirmar:
                st.warning("Senhas não conferem")
            else:
                usuarios[novo] = {"senha": senha_nova, "tipo": "corretor"}
                salvar_usuarios(usuarios)
                st.success("Conta criada! Faça login.")

def logout():
    if st.sidebar.button("🚪 Sair", key="logout"):
        st.session_state.clear()
        st.rerun()

# ---------------- CONTROLE LOGIN ----------------
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()

st.sidebar.write(f"👤 {st.session_state['usuario']}")
logout()

# ---------------- EMPREENDIMENTOS ----------------
empreendimentos = {
    "Frei Galvão": {
        "proprietario": "Frei Galvão empreendimentos imobiliários",
        "nome": "Loteamento Frei Galvão",
        "logradouro": "Avenida Fazenda Bananal",
        "tabela": "tabela_frei_galvao.xlsx"
    }
}

@st.cache_data
def carregar_tabela(arquivo):
    df = pd.read_excel(arquivo, skiprows=11)
    df.columns = df.columns.str.strip().str.lower()
    return df

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

def excel_para_pdf(arquivo):
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", arquivo])
    return arquivo.replace(".xlsx", ".pdf")

# ---------------- EXCEL ----------------
def preencher_proposta(d, modelo="modelo_proposta.xlsx"):
    wb = load_workbook(modelo)
    ws = wb.active

    # CLIENTE
    ws["E5"] = d["nome"]
    ws["D6"] = d["cpf"]
    ws["J6"] = d["telefone"]
    ws["O6"] = d["fixo"]
    ws["D7"] = d["nacionalidade"]
    ws["J7"] = d["profissao"]
    ws["P7"] = d["fone_pref"]
    ws["D8"] = d["estado_civil"]
    ws["O8"] = d["renda"]
    ws["E9"] = d["email"]

    # CONJUGE
    ws["G11"] = d["conjuge"]
    ws["D13"] = d["cpf2"]
    ws["J13"] = d["tel2"]
    ws["O13"] = d["fixo2"]
    ws["D14"] = d["nac2"]
    ws["J14"] = d["prof2"]
    ws["P14"] = d["fone2"]
    ws["D15"] = d["civil2"]
    ws["O15"] = d["renda2"]

    # LOTE
    ws["G18"] = d["proprietario"]
    ws["G19"] = d["empreendimento"]
    ws["C20"] = d["logradouro"]
    ws["I20"] = d["unidade"]
    ws["Q20"] = d["area"]

    ws["C21"] = d["valor_negocio"]
    ws["J21"] = d["entrada_total"]
    ws["O21"] = d["valor_imovel"]

    ws["C24"] = d["entrada_imovel"]
    ws["C25"] = d["parcela_36"]
    ws["C26"] = d["saldo"]

    # 🔥 BLOCO 24–26 (INCLUÍDO)
    ws["B24"] = 1
    ws["B25"] = 36
    ws["B26"] = 1

    ws["G24"] = "Única"
    ws["G25"] = "Mensal"
    ws["G26"] = "Única"

    ws["K24"] = d["data_empreendedor"]
    ws["K25"] = d["data_parcelas"]
    ws["K26"] = d["data_saldo"]

    # ENTRADA
    ws["B33"] = 1
    ws["C33"] = d["ato"]
    ws["G33"] = "Única"
    ws["P33"] = "À vista"

    ws["B34"] = d["parcelas_iguais"]
    ws["C34"] = d["valor_parcela_igual"]
    ws["G34"] = "Mensal" if d["parcelas_iguais"] > 0 else ""
    ws["P34"] = "Fixo"

    if d["usar_diferente"]:
        ws["B35"] = 1
        ws["C35"] = d["parcela_diferente"]
        ws["G35"] = "Única"
        ws["P35"] = "Fixa"
        ws["K35"] = d["data_parcela_diferente"]

    arquivo = "proposta.xlsx"
    wb.save(arquivo)
    return arquivo

# ---------------- APP ----------------

st.subheader("🏢 Empreendimento")
emp_nome = st.selectbox("Selecione", list(empreendimentos.keys()), key="emp")
emp = empreendimentos[emp_nome]

df = carregar_tabela(emp["tabela"])
col = df.columns[0]

unidade = st.selectbox("Lote", df[col].dropna().unique(), key="lote")
linha = df[df[col] == unidade].iloc[0]

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
st.subheader("👤 Cliente")
nome = st.text_input("Nome", key="nome")
cpf = st.text_input("CPF", key="cpf")
telefone = st.text_input("Telefone", key="tel")
fixo = st.text_input("Fixo", key="fixo")
nacionalidade = st.text_input("Nacionalidade", key="nac")
profissao = st.text_input("Profissão", key="prof")
fone_pref = st.text_input("Fone preferência", key="fonepref")
estado_civil = st.text_input("Estado civil", key="civil")
renda = st.text_input("Renda", key="renda")
email = st.text_input("Email", key="email")

# 🔥 DATAS (INCLUÍDO)
st.subheader("📅 Datas de Pagamento")
data_empreendedor = st.date_input("Data Vencimento Empreendedor")
data_parcelas = st.date_input("Data Parcelas (36x)")
data_saldo = st.date_input("Data Saldo Devedor")

# (resto do seu código continua igual...)

# GERAR
if st.button("GERAR PDF"):
    dados = {
        # (seus dados continuam iguais...)
        "data_empreendedor": data_empreendedor.strftime("%d/%m/%Y") if data_empreendedor else "",
        "data_parcelas": data_parcelas.strftime("%d/%m/%Y") if data_parcelas else "",
        "data_saldo": data_saldo.strftime("%d/%m/%Y") if data_saldo else ""
    }

    excel = preencher_proposta(dados)
    pdf = excel_para_pdf(excel)

    with open(pdf, "rb") as f:
        st.download_button("📥 Baixar PDF", f, file_name=f"Proposta_{unidade}.pdf")