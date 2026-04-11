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

# ---------------- LOGIN / CADASTRO ----------------
def tela_login():
    st.title("🔐 Sistema de Propostas")

    abas = st.tabs(["Login", "Criar conta"])
    usuarios = carregar_usuarios()

    # LOGIN
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

    # CADASTRO
    with abas[1]:
        novo = st.text_input("Novo usuário", key="cad_user")
        senha_nova = st.text_input("Senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirm")

        if st.button("Criar conta", key="btn_cadastro"):
            if novo in usuarios:
                st.warning("Usuário já existe")
            elif senha_nova != confirmar:
                st.warning("Senhas não conferem")
            elif novo == "" or senha_nova == "":
                st.warning("Preencha tudo")
            else:
                usuarios[novo] = {
                    "senha": senha_nova,
                    "tipo": "corretor"
                }
                salvar_usuarios(usuarios)
                st.success("Conta criada! Faça login.")

def tela_admin():
    st.sidebar.subheader("👤 Criar Corretor")

    usuarios = carregar_usuarios()

    novo = st.sidebar.text_input("Novo usuário", key="admin_user")
    senha = st.sidebar.text_input("Senha", type="password", key="admin_senha")

    if st.sidebar.button("Cadastrar", key="btn_admin"):
        if novo in usuarios:
            st.sidebar.warning("Já existe")
        else:
            usuarios[novo] = {"senha": senha, "tipo": "corretor"}
            salvar_usuarios(usuarios)
            st.sidebar.success("Criado!")

def logout():
    if st.sidebar.button("🚪 Sair", key="logout_btn"):
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

if st.session_state["tipo"] == "admin":
    tela_admin()

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

def excel_para_pdf(arquivo_excel):
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", arquivo_excel])
    return arquivo_excel.replace(".xlsx", ".pdf")

def preencher_proposta(d, modelo="modelo_proposta.xlsx"):
    wb = load_workbook(modelo)
    ws = wb.active

    ws["E5"] = d["nome"]
    ws["D6"] = d["cpf"]

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

    ws["P24"] = "Fixo"
    ws["P25"] = "Reajustável"
    ws["P26"] = "Reajustável"
    ws["P33"] = "À vista"
    ws["P34"] = "Fixo"

    ws["B33"] = 1
    ws["C33"] = d["ato"]

    ws["B34"] = d["parcelas_iguais"]
    ws["C34"] = d["valor_parcela_igual"]

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
emp_nome = st.selectbox("Selecione", list(empreendimentos.keys()), key="emp_select")
emp = empreendimentos[emp_nome]

df = carregar_tabela(emp["tabela"])
col = df.columns[0]

unidade = st.selectbox("Lote", df[col].dropna().unique(), key="lote_select")
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

st.subheader("Cliente")
nome = st.text_input("Nome", key="nome_cliente")
cpf = st.text_input("CPF", key="cpf_cliente")

st.subheader("Entrada")
valor_cliente = st.number_input("Entrada do cliente", min_value=0.0, key="entrada_cliente")

personalizar = st.checkbox("⚙️ Opções personalizáveis", key="personalizar")

ato_manual = st.number_input("Valor de ato", min_value=0.0, key="ato_manual") if personalizar else 0
ato = ato_manual if ato_manual > 0 else ato_min

restante = entrada_total - valor_cliente
if restante < 0: restante = 0

parcelas = st.slider("Parcelar entrada", 1, 4, 1, key="parcelas")

parcelas_iguais = parcelas
valor_parcela_igual = restante / parcelas if parcelas > 0 else 0
usar_diferente = False
parcela_diferente = 0
data_parcela_diferente = ""

if personalizar and parcelas > 1:
    parcela_editada = st.number_input("Parcela diferente", min_value=0.0, key="parcela_diff")
    restante_auto = restante - parcela_editada
    if restante_auto < 0: restante_auto = 0

    valor_parcela_igual = restante_auto / (parcelas - 1)

    if abs(parcela_editada - valor_parcela_igual) > 0.01:
        usar_diferente = True
        parcela_diferente = parcela_editada
        parcelas_iguais = parcelas - 1
        data_parcela_diferente = st.date_input("Data parcela diferente", key="data_diff")

# ---------------- GERAR ----------------
if st.button("GERAR PDF", key="btn_pdf"):

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
        "parcelas_iguais": parcelas_iguais,
        "valor_parcela_igual": valor_parcela_igual,
        "usar_diferente": usar_diferente,
        "parcela_diferente": parcela_diferente,
        "data_parcela_diferente": data_parcela_diferente.strftime("%d/%m/%Y") if usar_diferente else ""
    }

    excel = preencher_proposta(dados)
    pdf = excel_para_pdf(excel)

    with open(pdf, "rb") as f:
        st.download_button("📥 Baixar PDF", f, file_name=f"Proposta_{unidade}.pdf", key="download_pdf")