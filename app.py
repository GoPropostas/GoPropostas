import os
import io
import base64
import zipfile
import subprocess
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from supabase import Client, create_client

st.set_page_config(
    page_title="GoPropostas",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

EDGE_FUNCTION_CREATE_SUBSCRIPTION_URL = "https://kwsnjozsfvhrddxycoco.supabase.co/functions/v1/create-subscription"
EDGE_FUNCTION_CREATE_PIX_URL = "https://kwsnjozsfvhrddxycoco.supabase.co/functions/v1/create-pix"
LOGO_PATH = "Apresentação de logo moderno e profissional.png"
CONTRATO_INTERMEDIACAO_MODELO = "Contrato de Intermediação (3).xlsx"
MODELO_PROPOSTA = "modelo_proposta.xlsx"

# ---------------- VISUAL ----------------
def img_to_base64(path: str) -> str:
    if not Path(path).exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = img_to_base64(LOGO_PATH)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #062B36 0%, #073846 55%, #0A4C5B 100%);
    }

    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 2rem;
        max-width: 1380px;
    }

    header[data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0.85);
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #06232C 0%, #083845 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] * {
        color: #F4F7FA !important;
    }

    .gp-topbar-wrap {
        padding-top: 0.75rem;
        margin-bottom: 1.25rem;
    }

    .gp-topbar {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 18px;
        margin-top: 0;
        margin-bottom: 20px;
        padding: 18px 24px;
        border-radius: 24px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.18);
        overflow: visible;
        min-height: 116px;
    }

    .gp-topbar img {
        max-height: 78px;
        height: auto;
        width: auto;
        object-fit: contain;
        display: block;
        border-radius: 12px;
        flex-shrink: 0;
    }

    .gp-title {
        color: #F4F7FA;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
    }

    .gp-subtitle {
        color: rgba(244,247,250,0.82);
        font-size: 0.98rem;
        margin-top: 4px;
    }

    .gp-card {
        background: #F8FBFD;
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.16);
        border: 1px solid rgba(12,109,132,0.10);
        margin-bottom: 18px;
    }

    .gp-card,
    .gp-card * {
        color: #062B36 !important;
    }

    .gp-card-dark {
        background: linear-gradient(135deg, #0A3D4B 0%, #0C6D84 100%);
        color: white;
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
        margin-bottom: 18px;
    }

    .gp-card-dark,
    .gp-card-dark * {
        color: white !important;
    }

    .gp-section-title {
        color: #062B36;
        font-size: 1.15rem;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .gp-card-dark .gp-section-title {
        color: white !important;
    }

    .gp-highlight {
        color: #F97316 !important;
        font-weight: 800;
    }

    div[data-testid="stMetric"] {
        background: white;
        border-radius: 18px;
        padding: 14px 16px;
        border: 1px solid rgba(12,109,132,0.10);
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }

    div[data-testid="stMetric"] * {
        color: #062B36 !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #0C6D84 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #062B36 !important;
        font-weight: 800 !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(90deg, #F97316 0%, #FF8E2B 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        min-height: 46px !important;
        box-shadow: 0 10px 18px rgba(249,115,22,0.28) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        filter: brightness(1.03);
    }

    .stTextInput > div > div > input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {
        border-radius: 14px !important;
        border: 1px solid rgba(12,109,132,0.18) !important;
        background: #FFFFFF !important;
        color: #062B36 !important;
        -webkit-text-fill-color: #062B36 !important;
        caret-color: #062B36 !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stNumberInput input::placeholder,
    .stDateInput input::placeholder,
    .stTextArea textarea::placeholder,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder {
        color: #6B7C85 !important;
        opacity: 1 !important;
    }

    .stSelectbox div[data-baseweb="select"] * {
        color: #062B36 !important;
    }

    .stDateInput svg,
    .stSelectbox svg {
        fill: #062B36 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.08);
        color: #F4F7FA;
        border-radius: 12px;
        padding: 10px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: #F97316 !important;
        color: white !important;
    }

    hr {
        border-color: rgba(255,255,255,0.12);
    }

    .gp-mini {
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
    }

    label, .stMarkdown, .stCaption, p, span {
        color: inherit;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 4.5rem !important;
        }

        .gp-topbar {
            flex-direction: column;
            text-align: center;
            min-height: auto;
            padding: 18px;
        }

        .gp-topbar img {
            max-height: 70px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="gp-topbar-wrap">
    <div class="gp-topbar">
        {"<img src='data:image/png;base64," + logo_base64 + "'>" if logo_base64 else ""}
        <div>
            <div class="gp-title">GoPropostas</div>
            <div class="gp-subtitle">Sistema corporativo de propostas imobiliárias</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- SUPABASE LOGIN ----------------
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip(),
        st.secrets["SUPABASE_KEY"].strip(),
    )

def buscar_profile_por_id(user_id: str):
    supabase = get_supabase()
    resp = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None

def buscar_profile_por_email(email: str):
    supabase = get_supabase()
    resp = (
        supabase.table("profiles")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None

def buscar_assinatura(user_id: str):
    supabase = get_supabase()
    resp = (
        supabase.table("assinaturas")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None

def assinatura_ativa_para_acesso(assinatura: dict) -> bool:
    if not assinatura:
        return False
    if not assinatura.get("assinatura_ativa"):
        return False

    proximo = assinatura.get("proximo_cobranca_em")
    if not proximo:
        return bool(assinatura.get("assinatura_ativa"))

    try:
        proximo_dt = datetime.fromisoformat(str(proximo).replace("Z", "+00:00"))
        agora = datetime.now(proximo_dt.tzinfo) if proximo_dt.tzinfo else datetime.now()
        return proximo_dt >= agora
    except Exception:
        return bool(assinatura.get("assinatura_ativa"))

def atualizar_profile_config(user_id: str, nome: str, nome_imobiliaria: str, nome_gerente: str, nome_diretor: str):
    return (
        get_supabase()
        .table("profiles")
        .update({
            "nome": nome,
            "nome_imobiliaria": nome_imobiliaria,
            "nome_gerente": nome_gerente,
            "nome_diretor": nome_diretor,
        })
        .eq("id", user_id)
        .execute()
    )

def criar_assinatura_mp(user_id: str, email: str):
    headers = {"Content-Type": "application/json"}
    payload = {"user_id": user_id, "email": email}

    resp = requests.post(
        EDGE_FUNCTION_CREATE_SUBSCRIPTION_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    try:
        return resp.json()
    except Exception:
        return {
            "error": f"Resposta inválida da função: status {resp.status_code}",
            "raw_text": resp.text,
        }

def criar_pix(user_id: str, email: str):
    headers = {"Content-Type": "application/json"}
    payload = {"user_id": user_id, "email": email}

    resp = requests.post(
        EDGE_FUNCTION_CREATE_PIX_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    try:
        return resp.json()
    except Exception:
        return {
            "error": f"Resposta inválida da função PIX: status {resp.status_code}",
            "raw_text": resp.text,
        }

def login_com_supabase(email: str, senha: str):
    supabase = get_supabase()
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": senha,
    })

def cadastrar_com_supabase(
    nome: str,
    email: str,
    senha: str,
    nome_imobiliaria: str,
    nome_gerente: str,
    nome_diretor: str,
):
    supabase = get_supabase()
    return supabase.auth.sign_up({
        "email": email,
        "password": senha,
        "options": {
            "data": {
                "nome": nome,
                "nome_imobiliaria": nome_imobiliaria,
                "nome_gerente": nome_gerente,
                "nome_diretor": nome_diretor,
            }
        }
    })

def init_auth_state():
    defaults = {
        "logado": False,
        "usuario_id": "",
        "usuario_email": "",
        "usuario_nome": "",
        "tipo": "",
        "sb_access_token": "",
        "sb_refresh_token": "",
        "abrir_configuracoes": False,
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

def aplicar_login(profile: dict):
    st.session_state["logado"] = True
    st.session_state["usuario_id"] = profile["id"]
    st.session_state["usuario_email"] = profile["email"]
    st.session_state["usuario_nome"] = profile.get("nome") or profile["email"]
    st.session_state["tipo"] = profile.get("tipo", "corretor")

def salvar_tokens_da_sessao(auth_response):
    session = getattr(auth_response, "session", None)
    if session:
        st.session_state["sb_access_token"] = session.access_token or ""
        st.session_state["sb_refresh_token"] = session.refresh_token or ""

def tentar_restaurar_sessao():
    if st.session_state.get("logado"):
        return

    access_token = st.session_state.get("sb_access_token", "")
    refresh_token = st.session_state.get("sb_refresh_token", "")

    if not access_token or not refresh_token:
        return

    try:
        supabase = get_supabase()
        supabase.auth.set_session(access_token, refresh_token)
        sessao = supabase.auth.get_session()
        session = getattr(sessao, "session", None)

        if not session or not session.user:
            return

        profile = buscar_profile_por_id(session.user.id)
        if profile:
            aplicar_login(profile)
    except Exception:
        pass

def tela_login():
    st.markdown('<div class="gp-card-dark">', unsafe_allow_html=True)
    st.title("🔐 Entrar no sistema")
    st.markdown('<div class="gp-mini">Acesse ou crie sua conta para continuar.</div>', unsafe_allow_html=True)

    abas = st.tabs(["Login", "Criar conta"])

    with abas[0]:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", key="btn_login", use_container_width=True):
            try:
                resp = login_com_supabase(email, senha)
                user = resp.user

                if not user:
                    st.error("Email ou senha inválidos.")
                    return

                salvar_tokens_da_sessao(resp)

                profile = buscar_profile_por_id(user.id)
                if not profile:
                    st.error("Perfil não encontrado. Verifique se o trigger do Supabase foi criado.")
                    return

                aplicar_login(profile)
                st.success("Login realizado com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro no login: {e}")

    with abas[1]:
        nome_cadastro = st.text_input("Nome completo", key="cad_nome")
        nome_imobiliaria = st.text_input("Nome da Imobiliária completo", key="cad_imobiliaria")
        nome_gerente = st.text_input("Nome do gerente completo", key="cad_gerente")
        nome_diretor = st.text_input("Nome do diretor da imobiliária completo", key="cad_diretor")
        email_cadastro = st.text_input("Email", key="cad_email")
        senha_cadastro = st.text_input("Senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirm")

        if st.button("Criar conta", key="btn_cadastro", use_container_width=True):
            if senha_cadastro != confirmar:
                st.warning("Senhas não conferem.")
                return

            if (
                not nome_cadastro.strip()
                or not nome_imobiliaria.strip()
                or not nome_gerente.strip()
                or not nome_diretor.strip()
                or not email_cadastro.strip()
                or not senha_cadastro.strip()
            ):
                st.warning("Preencha todos os campos.")
                return

            try:
                existente = buscar_profile_por_email(email_cadastro)
                if existente:
                    st.warning("Já existe uma conta com esse email.")
                    return

                resp = cadastrar_com_supabase(
                    nome_cadastro,
                    email_cadastro,
                    senha_cadastro,
                    nome_imobiliaria,
                    nome_gerente,
                    nome_diretor,
                )
                user = resp.user

                if user:
                    st.success("Conta criada com sucesso! Agora faça login.")
                else:
                    st.success("Conta criada! Verifique seu email para confirmar o cadastro antes de entrar.")

            except Exception as e:
                st.error(f"Erro ao criar conta: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

def logout():
    if st.sidebar.button("🚪 Sair", key="logout", use_container_width=True):
        try:
            get_supabase().auth.sign_out()
        except Exception:
            pass

        for chave in [
            "logado", "usuario_id", "usuario_email", "usuario_nome", "tipo",
            "sb_access_token", "sb_refresh_token", "abrir_configuracoes"
        ]:
            if chave in st.session_state:
                del st.session_state[chave]

        st.rerun()

# ---------------- CONTROLE LOGIN ----------------
init_auth_state()
tentar_restaurar_sessao()

if not st.session_state["logado"]:
    tela_login()
    st.stop()

assinatura = buscar_assinatura(st.session_state["usuario_id"])
eh_admin = st.session_state.get("tipo") == "admin"
acesso_liberado = eh_admin or assinatura_ativa_para_acesso(assinatura)

if not acesso_liberado:
    st.markdown("""
    <div class="gp-card-dark">
        <div style="font-size:1.5rem;font-weight:800;">💳 Assinatura GoPropostas</div>
        <div style="margin-top:8px;font-size:1rem;opacity:0.92;">
            Escolha a melhor forma para acessar o sistema:
        </div>
        <div style="margin-top:16px;font-size:1.95rem;font-weight:900;">
            R$ 15,00 <span style="font-size:1rem;font-weight:500;">/ mês</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if assinatura:
        st.info(f"Status atual: {assinatura.get('status', 'pendente')}")
        if assinatura.get("proximo_cobranca_em"):
            st.caption(f"Validade / próxima cobrança: {assinatura.get('proximo_cobranca_em')}")

    col_pag_1, col_pag_2 = st.columns(2)

    with col_pag_1:
        st.markdown('<div class="gp-card">', unsafe_allow_html=True)
        st.markdown('<div class="gp-section-title">💳 Assinatura no cartão</div>', unsafe_allow_html=True)
        st.write("Cobrança recorrente automática mensal.")
        if st.button("Assinar no cartão", use_container_width=True):
            try:
                data = criar_assinatura_mp(
                    st.session_state["usuario_id"],
                    st.session_state["usuario_email"]
                )
                link = data.get("init_point") or data.get("sandbox_init_point")

                if link:
                    st.link_button("👉 Ir para pagamento", link, use_container_width=True)
                else:
                    st.error(f"Erro ao gerar link de pagamento: {data}")
            except Exception as e:
                st.error(f"Erro ao iniciar assinatura: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pag_2:
        st.markdown('<div class="gp-card">', unsafe_allow_html=True)
        st.markdown('<div class="gp-section-title">🧾 PIX mensal</div>', unsafe_allow_html=True)
        st.write("Pague manualmente via PIX e tenha acesso por 30 dias.")
        if st.button("Gerar PIX", use_container_width=True):
            try:
                data = criar_pix(
                    st.session_state["usuario_id"],
                    st.session_state["usuario_email"]
                )

                if "qr_code_base64" in data:
                    st.image(f"data:image/png;base64,{data['qr_code_base64']}")
                    st.code(data["qr_code"])
                    st.success("Escaneie ou copie o PIX.")
                else:
                    st.error(f"Erro ao gerar PIX: {data}")
            except Exception as e:
                st.error(f"Erro ao gerar PIX: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

st.sidebar.write(f"👤 {st.session_state['usuario_nome']}")
st.sidebar.write(f"📧 {st.session_state['usuario_email']}")
st.sidebar.write(f"🔑 {st.session_state['tipo']}")

if st.sidebar.button("⚙️ Configurações", use_container_width=True):
    st.session_state["abrir_configuracoes"] = not st.session_state.get("abrir_configuracoes", False)

logout()

if st.session_state.get("abrir_configuracoes", False):
    profile = buscar_profile_por_id(st.session_state["usuario_id"])

    st.markdown('<div class="gp-card"><div class="gp-section-title">⚙️ Configurações da Conta</div>', unsafe_allow_html=True)

    if profile:
        novo_nome = st.text_input("Nome completo", value=profile.get("nome", ""), key="cfg_nome")
        nova_imobiliaria = st.text_input(
            "Nome da Imobiliária completo",
            value=profile.get("nome_imobiliaria", ""),
            key="cfg_imobiliaria"
        )
        novo_gerente = st.text_input(
            "Nome do gerente completo",
            value=profile.get("nome_gerente", ""),
            key="cfg_gerente"
        )
        novo_diretor = st.text_input(
            "Nome do diretor da imobiliária completo",
            value=profile.get("nome_diretor", ""),
            key="cfg_diretor"
        )

        if st.button("Salvar configurações", key="btn_salvar_cfg", use_container_width=True):
            try:
                atualizar_profile_config(
                    st.session_state["usuario_id"],
                    novo_nome,
                    nova_imobiliaria,
                    novo_gerente,
                    novo_diretor,
                )
                st.session_state["usuario_nome"] = novo_nome
                st.success("Configurações salvas com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar configurações: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- EMPREENDIMENTOS ----------------
empreendimentos = {
    "Frei Galvão": {
        "proprietario": "Frei Galvão empreendimentos imobiliários",
        "nome": "Loteamento Frei Galvão",
        "logradouro": "Avenida Fazenda Bananal",
        "tabela": "tabela_frei_galvao.xlsx",
        "contrato_nome": "Residencial Frei Galvão",
    }
}

# ---------------- UTILITÁRIOS ----------------
@st.cache_data
def carregar_tabela(arquivo, mod_time):
    df = pd.read_excel(arquivo, skiprows=11)
    df.columns = df.columns.str.strip().str.lower()
    return df

def limpar(valor):
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except Exception:
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
        check=False,
    )
    return arquivo.replace(".xlsx", ".pdf")

def calcular_idade_em_data(nascimento: date, data_referencia: date) -> int:
    return data_referencia.year - nascimento.year - (
        (data_referencia.month, data_referencia.day) < (nascimento.month, nascimento.day)
    )

def adicionar_meses(data_base: date, meses: int) -> date:
    ano = data_base.year + (data_base.month - 1 + meses) // 12
    mes = (data_base.month - 1 + meses) % 12 + 1
    ultimo_dia = [
        31,
        29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    ][mes - 1]
    dia = min(data_base.day, ultimo_dia)
    return date(ano, mes, dia)

def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def criar_zip_bytes(arquivos: list[str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in arquivos:
            if os.path.exists(arquivo):
                zf.write(arquivo, arcname=os.path.basename(arquivo))
    buffer.seek(0)
    return buffer.getvalue()

def configurar_impressao(ws, orientation="portrait"):
    ws.page_setup.orientation = orientation
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.print_options.verticalCentered = False

# ---------------- EXCEL PROPOSTA ----------------
def preencher_proposta(d, modelo=MODELO_PROPOSTA):
    wb = load_workbook(modelo)
    ws = wb.active

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

    ws["G11"] = d["conjuge"]
    ws["D13"] = d["cpf2"]
    ws["J13"] = d["tel2"]
    ws["O13"] = d["fixo2"]
    ws["D14"] = d["nac2"]
    ws["J14"] = d["prof2"]
    ws["P14"] = d["fone2"]
    ws["D15"] = d["civil2"]
    ws["O15"] = d["renda2"]

    ws["G18"] = d["proprietario"]
    ws["G19"] = d["empreendimento"]
    ws["C20"] = d["logradouro"]
    ws["I20"] = d["unidade"]
    ws["Q20"] = d["area"]

    ws["C21"] = d["valor_negocio"]
    ws["J21"] = d["entrada_total"]
    ws["O21"] = d["valor_imovel"]

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

    ws["P24"] = "Fixo"
    ws["P25"] = "Reajustável"
    ws["P26"] = "Reajustável"

    ws["B33"] = 1
    ws["C33"] = d["entrada_cliente"]
    ws["G33"] = "Única"
    ws["P33"] = "À vista"
    ws["K33"] = d["data_ato"]
    ws["K33"].alignment = Alignment(horizontal="center", vertical="center")

    if d["entrada_quitada"]:
        ws["B34"] = ""
        ws["C34"] = ""
        ws["G34"] = ""
        ws["P34"] = ""
        ws["K34"] = ""

        ws["B35"] = ""
        ws["C35"] = ""
        ws["G35"] = ""
        ws["P35"] = ""
        ws["K35"] = ""
    else:
        ws["B34"] = d["parcelas_iguais"]
        ws["C34"] = d["valor_parcela_igual"]
        ws["G34"] = "Mensal" if d["parcelas_iguais"] > 0 else ""
        ws["P34"] = "Fixo"
        ws["K34"] = d["data_parc_entrada"]
        ws["K34"].alignment = Alignment(horizontal="center", vertical="center")

        if d["usar_diferente"]:
            ws["B35"] = 1
            ws["C35"] = d["parcela_diferente"]
            ws["G35"] = "Única"
            ws["P35"] = "Fixa"
            ws["K35"] = d["data_parcela_diferente_manual"]

            for cel in ["B35", "G35", "K35", "P35"]:
                ws[cel].alignment = Alignment(horizontal="center", vertical="center")
        else:
            ws["B35"] = ""
            ws["C35"] = ""
            ws["G35"] = ""
            ws["P35"] = ""
            ws["K35"] = ""

    configurar_impressao(ws, "portrait")

    arquivo = "proposta.xlsx"
    wb.save(arquivo)
    return arquivo

# ---------------- EXCEL CONTRATO ----------------
def preencher_contrato_intermediacao(d, modelo=CONTRATO_INTERMEDIACAO_MODELO):
    wb = load_workbook(modelo)
    ws = wb.active

    ws["C5"] = d["nome"]
    ws["C6"] = d["conjuge"]
    ws["I5"] = d["cpf"]
    ws["I6"] = d["cpf2"]
    ws["L5"] = d["rg"]
    ws["L6"] = d["rg2"]

    ws["C10"] = d["nome_imobiliaria"]
    ws["C11"] = d["nome_corretor"]
    ws["C12"] = "Monyke Procopio"
    ws["C13"] = d["nome_gerente"]
    ws["C14"] = d["nome_diretor"]

    ws["D17"] = d["empreendimento_contrato"]
    ws["J17"] = d["unidade"]
    ws["J19"] = d["valor_negocio"]
    ws["D19"] = d["data_contrato_intermediacao"]
    ws["K23"] = d["valor_total_comissao"]

    ws["E26"] = d["valor_imobiliaria"]
    ws["E27"] = d["valor_corretor"]
    ws["E28"] = d["valor_ato_minimo"]
    ws["E29"] = d["valor_gerente"]
    ws["E30"] = d["valor_total_distribuicao"]

    ws["F26"] = f"{d['porcentagem_imobiliaria']:.2f}%"
    ws["F27"] = f"{d['porcentagem_corretor']:.2f}%"
    ws["F28"] = "0.30%"
    ws["F29"] = f"{d['porcentagem_gerente']:.2f}%"
    ws["F30"] = "5.30%"

    ws["C50"] = d["nome_corretor"]
    ws["J50"] = d["nome_gerente"]
    ws["C54"] = d["nome_diretor"]

    configurar_impressao(ws, "portrait")

    arquivo = "contrato_intermediacao.xlsx"
    wb.save(arquivo)
    return arquivo

# ---------------- APP ----------------
profile_atual = buscar_profile_por_id(st.session_state["usuario_id"]) or {}

st.markdown('<div class="gp-card"><div class="gp-section-title">🏢 Empreendimento</div>', unsafe_allow_html=True)

emp_nome = st.selectbox("Selecione", list(empreendimentos.keys()), key="emp")
emp = empreendimentos[emp_nome]

caminho_tabela = Path(emp["tabela"])
if not caminho_tabela.exists():
    st.error(f"Arquivo da tabela não encontrado: {emp['tabela']}")
    st.stop()

mod_time = caminho_tabela.stat().st_mtime
df = carregar_tabela(str(caminho_tabela), mod_time)

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

st.markdown('</div>', unsafe_allow_html=True)

col_form_1, col_form_2 = st.columns(2)

with col_form_1:
    st.markdown('<div class="gp-card"><div class="gp-section-title">👤 Cliente</div>', unsafe_allow_html=True)
    nome = st.text_input("Nome", key="nome")
    cpf = st.text_input("CPF", key="cpf")
    rg = st.text_input("RG", key="rg")
    telefone = st.text_input("Telefone", key="tel")
    fixo = st.text_input("Fixo", key="fixo")
    nacionalidade = st.text_input("Nacionalidade", key="nac")
    profissao = st.text_input("Profissão", key="prof")
    fone_pref = st.text_input("Fone preferência", key="fonepref")
    estado_civil = st.text_input("Estado civil", key="civil")
    renda = st.text_input("Renda", key="renda")
    email = st.text_input("Email", key="email")
    data_nascimento = st.date_input(
        "Data de nascimento do cliente",
        value=date(1980, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        key="data_nascimento"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_form_2:
    st.markdown('<div class="gp-card"><div class="gp-section-title">👫 Cônjuge</div>', unsafe_allow_html=True)
    conjuge = st.text_input("Nome", key="conj")
    cpf2 = st.text_input("CPF", key="cpf2")
    rg2 = st.text_input("RG", key="rg2")
    tel2 = st.text_input("Telefone", key="tel2")
    fixo2 = st.text_input("Fixo", key="fixo2")
    nac2 = st.text_input("Nacionalidade", key="nac2")
    prof2 = st.text_input("Profissão", key="prof2")
    fone2 = st.text_input("Fone preferência", key="fone2")
    civil2 = st.text_input("Estado civil", key="civil2")
    renda2 = st.text_input("Renda", key="renda2")
    st.markdown('</div>', unsafe_allow_html=True)

col_data_1, col_data_2 = st.columns(2)

with col_data_1:
    st.markdown('<div class="gp-card"><div class="gp-section-title">📅 Datas de Vencimento</div>', unsafe_allow_html=True)
    data_venc_emp = st.date_input("Data Vencimento Empreendedor", key="venc_emp")
    data_parcelas = st.date_input("Data Parcelas", key="venc_parc")
    data_saldo = st.date_input("Data Saldo Devedor", key="venc_saldo")
    st.markdown('</div>', unsafe_allow_html=True)

with col_data_2:
    st.markdown('<div class="gp-card"><div class="gp-section-title">📅 Datas da Entrada</div>', unsafe_allow_html=True)
    data_ato = st.date_input("Data do ato", key="data_ato")
    data_parc_entrada = st.date_input("Data primeiras parcelas entrada", key="data_parc_entrada")
    data_parc_diferente = st.date_input("Data da parcela diferente", key="data_parc_dif")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="gp-card"><div class="gp-section-title">💰 Condições</div>', unsafe_allow_html=True)

valor_cliente = st.number_input("Entrada cliente", min_value=0.0, key="entrada")
personalizar = st.checkbox("⚙️ Personalizar", key="pers")

ato_manual = st.number_input("Valor ato", min_value=0.0, key="ato_manual") if personalizar else 0
ato = ato_manual if ato_manual > 0 else ato_min

restante = entrada_total - valor_cliente
if restante < 0:
    restante = 0

entrada_quitada = restante <= 0.01

valor_minimo_entrada = ato_min
erros_validacao = []
avisos_validacao = []

if valor_cliente <= 0:
    avisos_validacao.append("Nenhum valor foi informado em Entrada cliente.")

if valor_cliente < valor_minimo_entrada:
    erros_validacao.append(
        f"Entrada cliente menor que o mínimo. Mínimo recomendado: {formatar_moeda(valor_minimo_entrada)}"
    )

if valor_cliente > entrada_total:
    avisos_validacao.append("Entrada cliente maior que a entrada total. O excedente não será parcelado.")

parcelas = st.slider("Parcelas", 1, 4, 1, key="parc")

usar_diferente = False
parcela_diferente = 0
data_parcela_diferente = ""
parcelas_iguais = 0
valor_parcela_igual = 0

if not entrada_quitada:
    parcelas_iguais = parcelas
    valor_parcela_igual = restante / parcelas if parcelas > 0 else 0

if personalizar and parcelas > 1 and not entrada_quitada:
    parcela_editada = st.number_input("Parcela diferente", min_value=0.0, key="diff")
    restante_auto = restante - parcela_editada

    if restante_auto < 0:
        restante_auto = 0
        avisos_validacao.append("A parcela diferente está maior que o restante disponível.")

    valor_parcela_igual = restante_auto / (parcelas - 1)

    if abs(parcela_editada - valor_parcela_igual) > 0.01:
        usar_diferente = True
        parcela_diferente = parcela_editada
        parcelas_iguais = parcelas - 1
        data_parcela_diferente = st.date_input("Data parcela diferente", key="data_diff")

        if parcela_diferente > restante:
            erros_validacao.append("A parcela diferente não pode ser maior que o restante da entrada.")

st.markdown('</div>', unsafe_allow_html=True)

with st.expander("📑 Detalhes Contrato de Intermediação", expanded=False):
    data_contrato_intermediacao = st.date_input("Data Contrato de Intermediação", key="data_contrato_intermediacao")
    porcentagem_imobiliaria = st.number_input("Porcentagem Imobiliária", min_value=0.0, step=0.01, key="pct_imobiliaria")
    porcentagem_corretor = st.number_input("Porcentagem Corretor", min_value=0.0, step=0.01, key="pct_corretor")
    porcentagem_gerente = st.number_input("Porcentagem Gerente", min_value=0.0, step=0.01, key="pct_gerente")

valor_imobiliaria = valor_negocio * (porcentagem_imobiliaria / 100)
valor_corretor = valor_negocio * (porcentagem_corretor / 100)
valor_gerente = valor_negocio * (porcentagem_gerente / 100)
valor_ato_minimo = ato_min
valor_total_distribuicao = valor_imobiliaria + valor_corretor + valor_ato_minimo + valor_gerente
valor_total_comissao = valor_negocio * 0.053

if abs(valor_total_distribuicao - valor_total_comissao) > 0.01:
    erros_validacao.append(
        "Contrato de intermediação inválido: a soma de E26, E27, E28 e E29 deve ser exatamente 5,30% do valor total do negócio."
    )

st.markdown('<div class="gp-card"><div class="gp-section-title">🏡 Detalhes do Lote</div>', unsafe_allow_html=True)
col_l1, col_l2 = st.columns(2)
with col_l1:
    st.metric("Unidade", unidade)
    st.metric("Área (m²)", f"{area:.2f}")
    st.metric("Entrada Imóvel", formatar_moeda(entrada_imovel))

with col_l2:
    st.metric("Valor Negócio", formatar_moeda(valor_negocio))
    st.metric("Valor Imóvel", formatar_moeda(valor_imovel))
    st.metric("Intermediação", formatar_moeda(intermed))
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="gp-card"><div class="gp-section-title">📊 Painel de Cálculo</div>', unsafe_allow_html=True)
col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric("Entrada Total", formatar_moeda(entrada_total))
    st.metric("Entrada Cliente (C33)", formatar_moeda(valor_cliente))
    st.metric("Valor mínimo", formatar_moeda(valor_minimo_entrada))

with col_c2:
    st.metric("Ato informado", formatar_moeda(ato))
    st.metric("Restante para parcelar", formatar_moeda(restante))
    st.metric("Quantidade de parcelas", f"{parcelas}")

st.markdown("### 📅 Parcelamento da entrada")
if entrada_quitada:
    st.success("Entrada paga à vista")
elif parcelas > 1:
    if usar_diferente:
        st.info(
            f"{parcelas_iguais}x de {formatar_moeda(valor_parcela_igual)} + "
            f"1x de {formatar_moeda(parcela_diferente)}"
        )
    else:
        st.success(f"{parcelas}x de {formatar_moeda(valor_parcela_igual)}")
else:
    st.success("Pagamento em parcela única")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="gp-card"><div class="gp-section-title">📑 Painel Contrato de Intermediação</div>', unsafe_allow_html=True)
col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.metric("5,30% do negócio", formatar_moeda(valor_total_comissao))
    st.metric("Imobiliária", formatar_moeda(valor_imobiliaria))
with col_i2:
    st.metric("Corretor", formatar_moeda(valor_corretor))
    st.metric("0,30% entrada mínima", formatar_moeda(valor_ato_minimo))
with col_i3:
    st.metric("Gerente", formatar_moeda(valor_gerente))
    st.metric("Total distribuição", formatar_moeda(valor_total_distribuicao))
st.markdown('</div>', unsafe_allow_html=True)

if avisos_validacao:
    for aviso in avisos_validacao:
        st.warning(f"⚠️ {aviso}")

if erros_validacao:
    for erro in erros_validacao:
        st.error(f"❌ {erro}")

proposta_pode_ser_gerada = len(erros_validacao) == 0

if st.button("Gerar Proposta + Contrato", use_container_width=True, disabled=not proposta_pode_ser_gerada):
    data_final_36_parcelas = adicionar_meses(data_parcelas, 36)
    idade_apos_36 = calcular_idade_em_data(data_nascimento, data_final_36_parcelas)

    if idade_apos_36 >= 75:
        st.warning("Cliente não conseguirá refinanciar após as 36 parcelas (idade superior a 75 anos)")

    dados = {
        "nome": nome,
        "cpf": cpf,
        "rg": rg,
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
        "rg2": rg2,
        "tel2": tel2,
        "fixo2": fixo2,
        "nac2": nac2,
        "prof2": prof2,
        "fone2": fone2,
        "civil2": civil2,
        "renda2": renda2,
        "proprietario": emp["proprietario"],
        "empreendimento": emp["nome"],
        "empreendimento_contrato": emp.get("contrato_nome", emp["nome"]),
        "logradouro": emp["logradouro"],
        "unidade": unidade,
        "area": area,
        "valor_negocio": valor_negocio,
        "entrada_total": entrada_total,
        "valor_imovel": valor_imovel,
        "entrada_imovel": entrada_imovel,
        "parcela_36": parcela_36,
        "saldo": saldo,
        "entrada_cliente": valor_cliente,
        "entrada_quitada": entrada_quitada,
        "ato": ato,
        "parcelas_iguais": parcelas_iguais,
        "valor_parcela_igual": valor_parcela_igual,
        "usar_diferente": usar_diferente,
        "parcela_diferente": parcela_diferente,
        "data_parcela_diferente": data_parcela_diferente.strftime("%d/%m/%Y") if usar_diferente else "",
        "data_venc_emp": data_venc_emp.strftime("%d/%m/%Y"),
        "data_parcelas": data_parcelas.strftime("%d/%m/%Y"),
        "data_saldo": data_saldo.strftime("%d/%m/%Y"),
        "data_ato": data_ato.strftime("%d/%m/%Y") if data_ato else "",
        "data_parc_entrada": data_parc_entrada.strftime("%d/%m/%Y") if data_parc_entrada else "",
        "data_parcela_diferente_manual": data_parc_diferente.strftime("%d/%m/%Y") if data_parc_diferente else "",
        "data_contrato_intermediacao": data_contrato_intermediacao.strftime("%d/%m/%Y") if data_contrato_intermediacao else "",
        "nome_imobiliaria": profile_atual.get("nome_imobiliaria", ""),
        "nome_corretor": profile_atual.get("nome", st.session_state["usuario_nome"]),
        "nome_gerente": profile_atual.get("nome_gerente", ""),
        "nome_diretor": profile_atual.get("nome_diretor", ""),
        "porcentagem_imobiliaria": porcentagem_imobiliaria,
        "porcentagem_corretor": porcentagem_corretor,
        "porcentagem_gerente": porcentagem_gerente,
        "valor_imobiliaria": valor_imobiliaria,
        "valor_corretor": valor_corretor,
        "valor_gerente": valor_gerente,
        "valor_ato_minimo": valor_ato_minimo,
        "valor_total_distribuicao": valor_total_distribuicao,
        "valor_total_comissao": valor_total_comissao,
    }

    excel_proposta = preencher_proposta(dados)
    excel_contrato = preencher_contrato_intermediacao(dados)

    pdf_proposta = excel_para_pdf(excel_proposta)
    pdf_contrato = excel_para_pdf(excel_contrato)

    zip_excels = criar_zip_bytes([excel_proposta, excel_contrato])
    zip_pdfs = criar_zip_bytes([pdf_proposta, pdf_contrato])

    st.success("✅ Proposta e contrato gerados com sucesso!")

    col_down_1, col_down_2 = st.columns(2)

    with col_down_1:
        st.download_button(
            "📥 Baixar 2 arquivos em Excel",
            data=zip_excels,
            file_name=f"Excels_{unidade}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    with col_down_2:
        st.download_button(
            "📥 Baixar 2 arquivos em PDF",
            data=zip_pdfs,
            file_name=f"PDFs_{unidade}.zip",
            mime="application/zip",
            use_container_width=True,
        )
