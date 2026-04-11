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
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
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
    subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf", arquivo],
        check=False
    )
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

    # --- NOVAS FUNÇÕES MAPEADAS (B24 até K26) ---
    ws["B24"] = 1
    ws["C24"] = d["entrada_imovel"]
    ws["G24"] = "Única"
    ws["K24"] = d["data_venc_emp"]

    ws["B25"] = "36x"
    ws["C25"] = d["parcela_36"]
    ws["G25"] = "Mensal"
    ws["K25"] = d["data_parcelas"]

    ws["B26"] = 1
    ws["C26"] = d["saldo"]
    ws["G26"] = "Única"
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

# CLIENTE E CONJUGE
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

st.subheader("👫 Cônjuge")
conjuge = st.text_input("Nome", key="conj")
cpf2 = st.text_input("CPF", key="cpf2")
tel2 = st.text_input("Telefone", key="tel2")
fixo2 = st.text_input("Fixo", key="fixo2")
nac2 = st.text_input("Nacionalidade", key="nac2")
prof2 = st.text_input("Profissão", key="prof2")
fone2 = st.text_input("Fone preferência", key="fone2")
civil2 = st.text_input("Estado civil", key="civil2")
renda2 = st.text_input("Renda", key="renda2")

# --- NOVOS CAMPOS DE DATA SOLICITADOS ---
st.subheader("📅 Datas de Vencimento")
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    data_venc_emp = st.date_input("Data Vencimento Empreendedor", key="venc_emp")
with col_d2:
    data_parcelas = st.date_input("Data Parcelas", key="venc_parc")
with col_d3:
    data_saldo = st.date_input("Data Saldo Devedor", key="venc_saldo")

# PARCELAS INTELIGENTES
st.subheader("💰 Condições")
valor_cliente = st.number_input("Entrada cliente", min_value=0.0, key="entrada")
personalizar = st.checkbox("⚙️ Personalizar", key="pers")

ato_manual = st.number_input("Valor ato", min_value=0.0, key="ato_manual") if personalizar else 0
ato = ato_manual if ato_manual > 0 else ato_min

# LÓGICA CORRIGIDA:
# o cliente paga primeiro o ato; o restante abate na entrada parcelada
valor_para_entrada = valor_cliente - ato
if valor_para_entrada < 0:
    valor_para_entrada = 0

restante = entrada_total - valor_para_entrada
if restante < 0:
    restante = 0

parcelas = st.slider("Parcelas", 1, 4, 1, key="parc")
parcelas_iguais = parcelas
valor_parcela_igual = restante / parcelas if parcelas > 0 else 0
usar_diferente = False
parcela_diferente = 0
data_parcela_diferente = ""

if personalizar and parcelas > 1:
    parcela_editada = st.number_input("Parcela diferente", min_value=0.0, key="diff")
    restante_auto = restante - parcela_editada
    if restante_auto < 0:
        restante_auto = 0
    valor_parcela_igual = restante_auto / (parcelas - 1)

    if abs(parcela_editada - valor_parcela_igual) > 0.01:
        usar_diferente = True
        parcela_diferente = parcela_editada
        parcelas_iguais = parcelas - 1
        data_parcela_diferente = st.date_input("Data parcela diferente", key="data_diff")

# ---------------- PAINEL DETALHES DO LOTE ----------------
st.divider()
st.subheader("🏡 Detalhes do Lote")

l1, l2, l3 = st.columns(3)

l1.metric("Unidade", unidade)
l1.metric("Área (m²)", f"{area:.2f}")

l2.metric("Valor Negócio", f"R$ {valor_negocio:,.2f}")
l2.metric("Valor Imóvel", f"R$ {valor_imovel:,.2f}")

l3.metric("Entrada Imóvel", f"R$ {entrada_imovel:,.2f}")
l3.metric("Intermediação", f"R$ {intermed:,.2f}")

# ---------------- PAINEL DE CÁLCULO ----------------
st.divider()
st.subheader("📊 Painel de Cálculo")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Valor do Negócio", f"R$ {valor_negocio:,.2f}")
c1.metric("📥 Entrada Total", f"R$ {entrada_total:,.2f}")

c2.metric("💵 Entrada Cliente", f"R$ {valor_cliente:,.2f}")
c2.metric("📌 Ato", f"R$ {ato:,.2f}")

c3.metric("📉 Restante Entrada", f"R$ {restante:,.2f}")
c3.metric("📆 Parcelas", parcelas)

st.markdown("### 📅 Parcelamento")

if parcelas > 1:
    if usar_diferente:
        st.warning(
            f"{parcelas_iguais}x de R$ {valor_parcela_igual:,.2f} + "
            f"1x de R$ {parcela_diferente:,.2f}"
        )
    else:
        st.success(f"{parcelas}x de R$ {valor_parcela_igual:,.2f}")
else:
    st.success("Pagamento à vista")

if valor_cliente < ato:
    st.error("⚠️ Entrada não cobre o ATO")

if restante == 0:
    st.success("✅ Entrada quitada")

# GERAR
if st.button("GERAR PDF"):
    dados = {
        "nome": nome,
        "cpf": cpf,
        "telefone": telefone,
        "fixo": fixo,
        "nacionalidade": nacionalidade,
        "profissao": profissao,
        "fone_pref": fone_pref,
        "estado_civil": estado_civil,
        "renda": renda,
        "email": email,
        "conjuge": conjuge,
        "cpf2": cpf2,
        "tel2": tel2,
        "fixo2": fixo2,
        "nac2": nac2,
        "prof2": prof2,
        "fone2": fone2,
        "civil2": civil2,
        "renda2": renda2,
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
        "data_parcela_diferente": data_parcela_diferente.strftime("%d/%m/%Y") if usar_diferente else "",
        "data_venc_emp": data_venc_emp.strftime("%d/%m/%Y"),
        "data_parcelas": data_parcelas.strftime("%d/%m/%Y"),
        "data_saldo": data_saldo.strftime("%d/%m/%Y")
    }

    excel = preencher_proposta(dados)
    pdf = excel_para_pdf(excel)

    with open(pdf, "rb") as f:
        st.download_button(
            "📥 Baixar PDF",
            f,
            file_name=f"Proposta_{unidade}.pdf",
            mime="application/pdf"
        )