import base64
import io
import os
import subprocess
import textwrap
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from supabase import Client, create_client

st.set_page_config(
    page_title="GoPropostas V2",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PADRAO = "logo_padrao.png"
MODELO_PROPOSTA_PADRAO = "modelo_proposta.xlsx"
MODELO_CONTRATO_PADRAO = "Contrato de Intermediação (3).xlsx"


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip(),
        st.secrets["SUPABASE_KEY"].strip(),
    )


def img_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode()


def aplicar_tema(imob=None):
    cor_primaria = "#0C6D84"
    cor_secundaria = "#F97316"
    bg_inicio = "#062B36"
    bg_fim = "#0A4C5B"

    if imob:
        cor_primaria = imob.get("cor_primaria") or cor_primaria
        cor_secundaria = imob.get("cor_secundaria") or cor_secundaria
        bg_inicio = imob.get("background_inicio") or bg_inicio
        bg_fim = imob.get("background_fim") or bg_fim

    st.markdown(
        f"""
<style>
.stApp {{
    background: linear-gradient(180deg, {bg_inicio} 0%, {bg_fim} 100%);
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {bg_inicio} 0%, {bg_fim} 100%);
}}

.gp-card {{
    background: #F8FBFD;
    border-radius: 24px;
    padding: 22px 24px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.16);
    border: 1px solid rgba(12,109,132,0.10);
    margin-bottom: 18px;
}}

.gp-card, .gp-card * {{
    color: #062B36 !important;
}}

.gp-card-dark {{
    background: linear-gradient(135deg, {bg_inicio} 0%, {cor_primaria} 100%);
    color: white;
    border-radius: 24px;
    padding: 22px 24px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    margin-bottom: 18px;
}}

.gp-card-dark, .gp-card-dark * {{
    color: white !important;
}}

.gp-title {{
    color: #F4F7FA;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
}}

.gp-subtitle {{
    color: rgba(244,247,250,0.82);
    font-size: 0.98rem;
    margin-top: 4px;
}}

.gp-section-title {{
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 14px;
}}

.stButton > button,
.stDownloadButton > button {{
    background: linear-gradient(90deg, {cor_secundaria} 0%, {cor_primaria} 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 800 !important;
    min-height: 46px !important;
}}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {{
    border-radius: 14px !important;
}}

.gp-member {{
    background: rgba(255,255,255,0.92);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(12,109,132,0.10);
}}

.gp-member * {{
    color: #062B36 !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(imob=None):
    titulo = imob["nome"] if imob else "GoPropostas V2"
    subtitulo = "Sistema multi-imobiliária"
    logo_base64 = img_to_base64(LOGO_PADRAO)

    html = f"""
<div style="margin-bottom:20px;padding:18px 24px;border-radius:24px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:18px;">
    {"<img src='data:image/png;base64," + logo_base64 + "' style='max-height:78px;border-radius:12px;' />" if logo_base64 else ""}
    <div>
        <div class="gp-title">{titulo}</div>
        <div class="gp-subtitle">{subtitulo}</div>
    </div>
</div>
"""
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)


def init_state():
    defaults = {
        "logado": False,
        "usuario_id": "",
        "usuario_email": "",
        "usuario_nome": "",
        "role_global": "usuario",
        "sb_access_token": "",
        "sb_refresh_token": "",
        "imobiliaria_id": "",
        "imobiliaria_nome": "",
        "cargo_imobiliaria": "",
        "status_vinculo": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def aplicar_login(profile: dict):
    st.session_state["logado"] = True
    st.session_state["usuario_id"] = profile["id"]
    st.session_state["usuario_email"] = profile.get("email", "")
    st.session_state["usuario_nome"] = profile.get("nome") or profile.get("email", "")
    st.session_state["role_global"] = profile.get("role_global", "usuario")


def salvar_tokens(auth_response):
    session = getattr(auth_response, "session", None)
    if session:
        st.session_state["sb_access_token"] = session.access_token or ""
        st.session_state["sb_refresh_token"] = session.refresh_token or ""


def restaurar_sessao():
    if st.session_state.get("logado"):
        return

    access_token = st.session_state.get("sb_access_token", "")
    refresh_token = st.session_state.get("sb_refresh_token", "")

    if not access_token or not refresh_token:
        return

    try:
        sb = get_supabase()
        sb.auth.set_session(access_token, refresh_token)
        sessao = sb.auth.get_session()
        session = getattr(sessao, "session", None)

        if not session or not session.user:
            return

        profile = buscar_profile_por_id(session.user.id)
        if profile:
            aplicar_login(profile)
    except Exception:
        pass


def limpar_estado_imobiliaria():
    st.session_state["imobiliaria_id"] = ""
    st.session_state["imobiliaria_nome"] = ""
    st.session_state["cargo_imobiliaria"] = ""
    st.session_state["status_vinculo"] = ""


def logout():
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        try:
            get_supabase().auth.sign_out()
        except Exception:
            pass

        for k in list(st.session_state.keys()):
            del st.session_state[k]

        st.rerun()


# =========================
# BANCO
# =========================
def buscar_profile_por_id(user_id: str):
    resp = (
        get_supabase()
        .table("profiles")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def buscar_profile_por_email(email: str):
    resp = (
        get_supabase()
        .table("profiles")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def listar_imobiliarias_ativas():
    resp = (
        get_supabase()
        .table("imobiliarias")
        .select("*")
        .eq("ativa", True)
        .order("nome")
        .execute()
    )
    return resp.data or []


def buscar_imobiliaria_por_id(imobiliaria_id: str):
    resp = (
        get_supabase()
        .table("imobiliarias")
        .select("*")
        .eq("id", imobiliaria_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def buscar_vinculos_usuario(user_id: str):
    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .select("*, imobiliarias(*)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


def buscar_vinculo(user_id: str, imobiliaria_id: str):
    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .select("*")
        .eq("user_id", user_id)
        .eq("imobiliaria_id", imobiliaria_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def solicitar_acesso(user_id: str, imobiliaria_id: str):
    existente = buscar_vinculo(user_id, imobiliaria_id)
    if existente:
        return existente

    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .insert(
            {
                "user_id": user_id,
                "imobiliaria_id": imobiliaria_id,
                "cargo": "corretor",
                "status": "pendente",
            }
        )
        .execute()
    )
    return resp.data[0] if resp.data else None


def listar_solicitacoes_pendentes():
    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .select("*, imobiliarias(*)")
        .eq("status", "pendente")
        .order("created_at")
        .execute()
    )
    return resp.data or []


def listar_solicitacoes_pendentes_por_imobiliaria(imobiliaria_id: str):
    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .select("*, imobiliarias(*)")
        .eq("status", "pendente")
        .eq("imobiliaria_id", imobiliaria_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


def listar_membros_imobiliaria(imobiliaria_id: str):
    resp = (
        get_supabase()
        .table("usuarios_imobiliarias")
        .select("*")
        .eq("imobiliaria_id", imobiliaria_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


def aprovar_vinculo(vinculo_id: str, aprovador_id: str, cargo: str):
    return (
        get_supabase()
        .table("usuarios_imobiliarias")
        .update(
            {
                "status": "aprovado",
                "cargo": cargo,
                "aprovado_por": aprovador_id,
                "aprovado_em": datetime.utcnow().isoformat(),
            }
        )
        .eq("id", vinculo_id)
        .execute()
    )


def rejeitar_vinculo(vinculo_id: str):
    return (
        get_supabase()
        .table("usuarios_imobiliarias")
        .update({"status": "rejeitado"})
        .eq("id", vinculo_id)
        .execute()
    )


def alterar_cargo_vinculo(vinculo_id: str, novo_cargo: str):
    return (
        get_supabase()
        .table("usuarios_imobiliarias")
        .update({"cargo": novo_cargo})
        .eq("id", vinculo_id)
        .execute()
    )


def alterar_status_vinculo(vinculo_id: str, novo_status: str):
    return (
        get_supabase()
        .table("usuarios_imobiliarias")
        .update({"status": novo_status})
        .eq("id", vinculo_id)
        .execute()
    )


def buscar_nome_email_usuario(user_id: str):
    perfil = buscar_profile_por_id(user_id)
    if not perfil:
        return "", ""
    return perfil.get("nome", ""), perfil.get("email", "")


def listar_empreendimentos():
    resp = (
        get_supabase()
        .table("empreendimentos")
        .select("*")
        .eq("ativo", True)
        .order("nome")
        .execute()
    )
    return resp.data or []


def buscar_regra_imobiliaria(imobiliaria_id: str):
    resp = (
        get_supabase()
        .table("regras_imobiliaria")
        .select("*")
        .eq("imobiliaria_id", imobiliaria_id)
        .eq("ativo", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


# =========================
# AUTH
# =========================
def login(email: str, senha: str):
    return get_supabase().auth.sign_in_with_password(
        {
            "email": email.strip(),
            "password": senha,
        }
    )


def cadastrar(nome: str, email: str, senha: str):
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()

    resp = requests.post(
        f"{url}/auth/v1/signup",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "email": email.strip(),
            "password": senha,
            "data": {"nome": nome.strip()},
        },
        timeout=10,
    )
    return resp


# =========================
# PERMISSÕES
# =========================
def eh_superadmin():
    return st.session_state.get("role_global") == "superadmin"


def pode_ver_todas():
    return eh_superadmin() or st.session_state.get("cargo_imobiliaria") == "administrador"


def pode_aprovar():
    return pode_ver_todas() or st.session_state.get("cargo_imobiliaria") == "diretor"


def pode_gerenciar_membros():
    return pode_ver_todas()


# =========================
# UTILITÁRIOS PROPOSTA
# =========================
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


def criar_zip_bytes(arquivos):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in arquivos:
            if arquivo and os.path.exists(arquivo):
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


def preencher_proposta(d, modelo=MODELO_PROPOSTA_PADRAO):
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
        for cel in ["B34", "C34", "G34", "P34", "K34", "B35", "C35", "G35", "P35", "K35"]:
            ws[cel] = ""
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
            for cel in ["B35", "C35", "G35", "P35", "K35"]:
                ws[cel] = ""

    configurar_impressao(ws, "portrait")
    arquivo = "proposta.xlsx"
    wb.save(arquivo)
    return arquivo


def preencher_contrato_intermediacao(d, modelo=MODELO_CONTRATO_PADRAO):
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
    ws["F28"] = f"{d['porcentagem_ato_minimo']:.2f}%"
    ws["F29"] = f"{d['porcentagem_gerente']:.2f}%"
    ws["F30"] = f"{d['porcentagem_total_comissao']:.2f}%"

    ws["C50"] = d["nome_corretor"]
    ws["J50"] = d["nome_gerente"]
    ws["C54"] = d["nome_diretor"]

    configurar_impressao(ws, "portrait")
    arquivo = "contrato_intermediacao.xlsx"
    wb.save(arquivo)
    return arquivo


# =========================
# TELAS
# =========================
def tela_login():
    st.markdown('<div class="gp-card-dark">', unsafe_allow_html=True)
    st.title("🔐 Entrar no sistema")
    abas = st.tabs(["Login", "Criar conta"])

    with abas[0]:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar", use_container_width=True):
            try:
                resp = login(email, senha)
                user = resp.user

                if not user:
                    st.error("Email ou senha inválidos.")
                    return

                salvar_tokens(resp)

                profile = buscar_profile_por_id(user.id)
                if not profile:
                    st.error("Perfil não encontrado.")
                    return

                aplicar_login(profile)
                st.success("Login realizado com sucesso.")
                st.rerun()

            except Exception as e:
                st.error(f"Erro no login: {e}")

    with abas[1]:
        nome = st.text_input("Nome completo", key="cad_nome")
        email = st.text_input("Email", key="cad_email")
        senha = st.text_input("Senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirm")

        if st.button("Criar conta", key="btn_cadastro", use_container_width=True):
            if senha != confirmar:
                st.warning("Senhas não conferem.")
                return

            if not nome.strip() or not email.strip() or not senha.strip():
                st.warning("Preencha todos os campos.")
                return

            try:
                existente = buscar_profile_por_email(email)
                if existente:
                    st.warning("Já existe uma conta com esse email.")
                    return

                resp = cadastrar(nome, email, senha)

                if resp.status_code in (200, 201):
                    st.success("Conta criada com sucesso. Agora faça login.")
                else:
                    try:
                        erro_json = resp.json()
                        st.error(f"Erro ao criar conta: {erro_json}")
                    except Exception:
                        st.error(f"Erro ao criar conta: {resp.text}")

            except Exception as e:
                st.error(f"Erro ao criar conta: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


def tela_escolha_imobiliaria():
    st.markdown('<div class="gp-card"><div class="gp-section-title">🏢 Escolha uma imobiliária</div>', unsafe_allow_html=True)

    imobiliarias = listar_imobiliarias_ativas()
    vinculos = buscar_vinculos_usuario(st.session_state["usuario_id"])
    mapa_vinculos = {v["imobiliaria_id"]: v for v in vinculos}

    if not imobiliarias:
        st.warning("Nenhuma imobiliária cadastrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for imob in imobiliarias:
        st.subheader(imob["nome"])
        vinculo = mapa_vinculos.get(imob["id"])

        if eh_superadmin():
            st.success("Acesso liberado como superadmin.")
            if st.button(f"Entrar em {imob['nome']}", key=f"entrar_super_{imob['id']}", use_container_width=True):
                st.session_state["imobiliaria_id"] = imob["id"]
                st.session_state["imobiliaria_nome"] = imob["nome"]
                st.session_state["cargo_imobiliaria"] = "administrador"
                st.session_state["status_vinculo"] = "aprovado"
                st.rerun()
            st.divider()
            continue

        if vinculo:
            status = vinculo["status"]

            if status == "aprovado":
                st.success(f"Acesso aprovado como {vinculo['cargo']}.")
                if st.button(f"Entrar em {imob['nome']}", key=f"entrar_{imob['id']}", use_container_width=True):
                    st.session_state["imobiliaria_id"] = imob["id"]
                    st.session_state["imobiliaria_nome"] = imob["nome"]
                    st.session_state["cargo_imobiliaria"] = vinculo["cargo"]
                    st.session_state["status_vinculo"] = vinculo["status"]
                    st.rerun()

            elif status == "pendente":
                st.info("Sua solicitação está pendente.")

            elif status == "rejeitado":
                st.error("Sua solicitação foi rejeitada.")
        else:
            if st.button(f"Solicitar acesso a {imob['nome']}", key=f"sol_{imob['id']}", use_container_width=True):
                solicitar_acesso(st.session_state["usuario_id"], imob["id"])
                st.success("Solicitação enviada.")
                st.rerun()

        st.divider()

    st.markdown("</div>", unsafe_allow_html=True)


def painel_aprovacoes():
    if not pode_aprovar():
        st.warning("Você não tem permissão para ver solicitações.")
        return

    st.markdown('<div class="gp-card"><div class="gp-section-title">✅ Solicitações pendentes</div>', unsafe_allow_html=True)

    if pode_ver_todas():
        solicitacoes = listar_solicitacoes_pendentes()
    else:
        solicitacoes = listar_solicitacoes_pendentes_por_imobiliaria(st.session_state["imobiliaria_id"])

    if not solicitacoes:
        st.info("Nenhuma solicitação pendente.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for s in solicitacoes:
        imob = s.get("imobiliarias") or {}
        nome_usuario, email_usuario = buscar_nome_email_usuario(s["user_id"])

        st.markdown('<div class="gp-member">', unsafe_allow_html=True)
        st.write(f"**Usuário:** {nome_usuario} — {email_usuario}")
        st.write(f"**Imobiliária:** {imob.get('nome', '')}")

        if pode_ver_todas():
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Aprovar Corretor", key=f"cor_{s['id']}"):
                    aprovar_vinculo(s["id"], st.session_state["usuario_id"], "corretor")
                    st.rerun()
            with c2:
                if st.button("Aprovar Diretor", key=f"dir_{s['id']}"):
                    aprovar_vinculo(s["id"], st.session_state["usuario_id"], "diretor")
                    st.rerun()
            with c3:
                if st.button("Aprovar Administrador", key=f"adm_{s['id']}"):
                    aprovar_vinculo(s["id"], st.session_state["usuario_id"], "administrador")
                    st.rerun()
            with c4:
                if st.button("Rejeitar", key=f"rej_{s['id']}"):
                    rejeitar_vinculo(s["id"])
                    st.rerun()
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Aprovar Corretor", key=f"ap_{s['id']}"):
                    aprovar_vinculo(s["id"], st.session_state["usuario_id"], "corretor")
                    st.rerun()
            with c2:
                if st.button("Rejeitar", key=f"rp_{s['id']}"):
                    rejeitar_vinculo(s["id"])
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def painel_membros_imobiliaria():
    if not st.session_state.get("imobiliaria_id"):
        return

    membros = listar_membros_imobiliaria(st.session_state["imobiliaria_id"])

    st.markdown('<div class="gp-card"><div class="gp-section-title">👥 Membros da imobiliária</div>', unsafe_allow_html=True)

    if not membros:
        st.info("Nenhum membro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for membro in membros:
        nome, email = buscar_nome_email_usuario(membro["user_id"])
        status_atual = membro.get("status", "")
        cargo_atual = membro.get("cargo", "")

        st.markdown('<div class="gp-member">', unsafe_allow_html=True)
        st.write(f"**Nome:** {nome or '-'}")
        st.write(f"**Email:** {email or '-'}")
        st.write(f"**Status atual:** {status_atual}")
        st.write(f"**Cargo atual:** {cargo_atual}")

        if pode_gerenciar_membros():
            col1, col2 = st.columns(2)

            with col1:
                lista_cargos = ["corretor", "diretor", "administrador"]
                indice_cargo = lista_cargos.index(cargo_atual) if cargo_atual in lista_cargos else 0

                novo_cargo = st.selectbox(
                    f"Novo cargo para {email or membro['user_id']}",
                    lista_cargos,
                    index=indice_cargo,
                    key=f"cargo_sel_{membro['id']}",
                )

                if st.button("Salvar cargo", key=f"salvar_cargo_{membro['id']}", use_container_width=True):
                    alterar_cargo_vinculo(membro["id"], novo_cargo)
                    st.success("Cargo atualizado com sucesso.")
                    st.rerun()

            with col2:
                lista_status = ["aprovado", "pendente", "rejeitado"]
                indice_status = lista_status.index(status_atual) if status_atual in lista_status else 0

                novo_status = st.selectbox(
                    f"Novo status para {email or membro['user_id']}",
                    lista_status,
                    index=indice_status,
                    key=f"status_sel_{membro['id']}",
                )

                if st.button("Salvar status", key=f"salvar_status_{membro['id']}", use_container_width=True):
                    alterar_status_vinculo(membro["id"], novo_status)
                    st.success("Status atualizado com sucesso.")
                    st.rerun()

        else:
            st.info("Você não tem permissão para alterar cargos.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def tela_empreendimentos():
    empreendimentos = listar_empreendimentos()

    st.markdown('<div class="gp-card"><div class="gp-section-title">🏢 Empreendimentos</div>', unsafe_allow_html=True)

    if not empreendimentos:
        st.warning("Nenhum empreendimento cadastrado.")
    else:
        for emp in empreendimentos:
            st.markdown('<div class="gp-member">', unsafe_allow_html=True)
            st.write(f"**Nome:** {emp.get('nome', '-')}")
            st.write(f"**Proprietário:** {emp.get('proprietario', '-')}")
            st.write(f"**Logradouro:** {emp.get('logradouro', '-')}")
            st.write(f"**Contrato:** {emp.get('contrato_nome', '-')}")
            st.write(f"**Tabela:** {emp.get('tabela_arquivo', '-')}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def tela_regras_imobiliaria():
    regra = buscar_regra_imobiliaria(st.session_state["imobiliaria_id"])

    st.markdown('<div class="gp-card"><div class="gp-section-title">📑 Regras da imobiliária</div>', unsafe_allow_html=True)

    if not regra:
        st.error("Regra financeira não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.write(f"**Total comissão:** {float(regra['porcentagem_total_comissao']):.2f}%")
    st.write(f"**Ato mínimo:** {float(regra['porcentagem_ato_minimo']):.2f}%")
    st.write(f"**Imobiliária:** {float(regra['porcentagem_imobiliaria']):.2f}%")
    st.write(f"**Corretor:** {float(regra['porcentagem_corretor']):.2f}%")
    st.write(f"**Gerente:** {float(regra['porcentagem_gerente']):.2f}%")

    st.markdown("</div>", unsafe_allow_html=True)


def tela_home():
    st.markdown('<div class="gp-card"><div class="gp-section-title">🏠 Painel inicial</div>', unsafe_allow_html=True)
    st.write(f"Usuário: **{st.session_state['usuario_nome']}**")
    st.write(f"Imobiliária ativa: **{st.session_state['imobiliaria_nome']}**")
    st.write(f"Cargo: **{st.session_state['cargo_imobiliaria']}**")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="gp-card"><div class="gp-section-title">📌 Resumo</div>', unsafe_allow_html=True)
    st.write("Use o menu lateral para navegar entre as áreas do sistema.")
    st.markdown("</div>", unsafe_allow_html=True)


def tela_nova_proposta():
    st.markdown('<div class="gp-card"><div class="gp-section-title">📝 Nova Proposta</div>', unsafe_allow_html=True)

    empreendimentos = listar_empreendimentos()
    if not empreendimentos:
        st.warning("Nenhum empreendimento cadastrado.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    mapa_empreendimentos = {e["nome"]: e for e in empreendimentos}
    emp_nome = st.selectbox("Empreendimento", list(mapa_empreendimentos.keys()), key="prop_emp")
    emp = mapa_empreendimentos[emp_nome]

    tabela_arquivo = emp.get("tabela_arquivo") or ""
    caminho_tabela = Path(tabela_arquivo)

    if not caminho_tabela.exists():
        st.error(f"Arquivo da tabela não encontrado: {tabela_arquivo}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    mod_time = caminho_tabela.stat().st_mtime
    df = carregar_tabela(str(caminho_tabela), mod_time)

    primeira_coluna = df.columns[0]
    unidades = df[primeira_coluna].dropna().unique().tolist()

    unidade = st.selectbox("Lote", unidades, key="prop_lote")
    linha = df[df[primeira_coluna] == unidade].iloc[0]

    valor_negocio = buscar(linha, ["valor negócio", "valor negocio"])
    entrada_imovel = buscar(linha, ["entrada imovel", "entrada imóvel"])
    intermed = buscar(linha, ["intermediação", "intermediacao"])
    parcela_36 = buscar(linha, ["36x"])
    saldo = buscar(linha, ["saldo"])
    area = buscar(linha, ["área", "area"])
    valor_imovel = buscar(linha, ["valor imóvel", "valor imovel"])

    entrada_total = intermed + entrada_imovel

    regra = buscar_regra_imobiliaria(st.session_state["imobiliaria_id"])
    if not regra:
        st.error("Regra financeira não encontrada para esta imobiliária.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    pct_total = float(regra.get("porcentagem_total_comissao", 5.30))
    pct_ato = float(regra.get("porcentagem_ato_minimo", 0.30))
    pct_imobiliaria = float(regra.get("porcentagem_imobiliaria", 2.00))
    pct_corretor = float(regra.get("porcentagem_corretor", 2.00))
    pct_gerente = float(regra.get("porcentagem_gerente", 1.00))

    ato_min = valor_negocio * (pct_ato / 100)

    st.markdown("</div>", unsafe_allow_html=True)

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
        st.markdown("</div>", unsafe_allow_html=True)

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
        st.markdown("</div>", unsafe_allow_html=True)

    col_data_1, col_data_2 = st.columns(2)

    with col_data_1:
        st.markdown('<div class="gp-card"><div class="gp-section-title">📅 Datas de Vencimento</div>', unsafe_allow_html=True)
        data_venc_emp = st.date_input("Data Vencimento Empreendedor", key="venc_emp")
        data_parcelas = st.date_input("Data Parcelas", key="venc_parc")
        data_saldo = st.date_input("Data Saldo Devedor", key="venc_saldo")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_data_2:
        st.markdown('<div class="gp-card"><div class="gp-section-title">📅 Datas da Entrada</div>', unsafe_allow_html=True)
        data_ato = st.date_input("Data do ato", key="data_ato")
        data_parc_entrada = st.date_input("Data primeiras parcelas entrada", key="data_parc_entrada")
        data_parc_diferente = st.date_input("Data da parcela diferente", key="data_parc_dif")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="gp-card"><div class="gp-section-title">💰 Condições</div>', unsafe_allow_html=True)

    valor_cliente = st.number_input("Entrada cliente", min_value=0.0, key="entrada")
    personalizar = st.checkbox("⚙️ Personalizar", key="pers")

    ato_manual = st.number_input("Valor ato", min_value=0.0, key="ato_manual") if personalizar else 0.0
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
    parcela_diferente = 0.0
    parcelas_iguais = 0
    valor_parcela_igual = 0.0

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

            if parcela_diferente > restante:
                erros_validacao.append("A parcela diferente não pode ser maior que o restante da entrada.")

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📑 Regras do Contrato de Intermediação", expanded=False):
        data_contrato_intermediacao = st.date_input("Data Contrato de Intermediação", key="data_contrato_intermediacao")
        st.metric("Imobiliária", f"{pct_imobiliaria:.2f}%")
        st.metric("Corretor", f"{pct_corretor:.2f}%")
        st.metric("Ato mínimo", f"{pct_ato:.2f}%")
        st.metric("Gerente", f"{pct_gerente:.2f}%")
        st.metric("Total comissão", f"{pct_total:.2f}%")

    valor_imobiliaria = valor_negocio * (pct_imobiliaria / 100)
    valor_corretor = valor_negocio * (pct_corretor / 100)
    valor_gerente = valor_negocio * (pct_gerente / 100)
    valor_ato_minimo = valor_negocio * (pct_ato / 100)
    valor_total_distribuicao = valor_imobiliaria + valor_corretor + valor_ato_minimo + valor_gerente
    valor_total_comissao = valor_negocio * (pct_total / 100)

    if abs(valor_total_distribuicao - valor_total_comissao) > 0.01:
        erros_validacao.append(
            f"Contrato de intermediação inválido: a soma da distribuição deve ser exatamente {pct_total:.2f}% do valor total do negócio."
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
    st.markdown("</div>", unsafe_allow_html=True)

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
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="gp-card"><div class="gp-section-title">📑 Painel Contrato de Intermediação</div>', unsafe_allow_html=True)
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.metric(f"{pct_total:.2f}% do negócio", formatar_moeda(valor_total_comissao))
        st.metric("Imobiliária", formatar_moeda(valor_imobiliaria))
    with col_i2:
        st.metric("Corretor", formatar_moeda(valor_corretor))
        st.metric(f"{pct_ato:.2f}% entrada mínima", formatar_moeda(valor_ato_minimo))
    with col_i3:
        st.metric("Gerente", formatar_moeda(valor_gerente))
        st.metric("Total distribuição", formatar_moeda(valor_total_distribuicao))
    st.markdown("</div>", unsafe_allow_html=True)

    if avisos_validacao:
        for aviso in avisos_validacao:
            st.warning(f"⚠️ {aviso}")

    if erros_validacao:
        for erro in erros_validacao:
            st.error(f"❌ {erro}")

    proposta_pode_ser_gerada = len(erros_validacao) == 0

    if st.button("Gerar Proposta + Contrato", use_container_width=True, disabled=not proposta_pode_ser_gerada):
        try:
            data_final_36_parcelas = adicionar_meses(data_parcelas, 36)
            idade_apos_36 = calcular_idade_em_data(data_nascimento, data_final_36_parcelas)

            if idade_apos_36 >= 75:
                st.warning("Cliente não conseguirá refinanciar após as 36 parcelas (idade superior a 75 anos)")

            imobiliaria_atual = buscar_imobiliaria_por_id(st.session_state["imobiliaria_id"]) or {}

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
                "data_venc_emp": data_venc_emp.strftime("%d/%m/%Y"),
                "data_parcelas": data_parcelas.strftime("%d/%m/%Y"),
                "data_saldo": data_saldo.strftime("%d/%m/%Y"),
                "data_ato": data_ato.strftime("%d/%m/%Y") if data_ato else "",
                "data_parc_entrada": data_parc_entrada.strftime("%d/%m/%Y") if data_parc_entrada else "",
                "data_parcela_diferente_manual": data_parc_diferente.strftime("%d/%m/%Y") if data_parc_diferente else "",
                "data_contrato_intermediacao": data_contrato_intermediacao.strftime("%d/%m/%Y") if data_contrato_intermediacao else "",
                "nome_imobiliaria": imobiliaria_atual.get("nome", ""),
                "nome_corretor": st.session_state["usuario_nome"],
                "nome_gerente": imobiliaria_atual.get("nome_gerente", ""),
                "nome_diretor": imobiliaria_atual.get("nome_diretor", ""),
                "porcentagem_imobiliaria": pct_imobiliaria,
                "porcentagem_corretor": pct_corretor,
                "porcentagem_ato_minimo": pct_ato,
                "porcentagem_gerente": pct_gerente,
                "porcentagem_total_comissao": pct_total,
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

        except Exception as e:
            st.error(f"Erro ao gerar proposta e contrato: {e}")


# =========================
# MAIN
# =========================
init_state()
restaurar_sessao()

imob = buscar_imobiliaria_por_id(st.session_state["imobiliaria_id"]) if st.session_state.get("imobiliaria_id") else None
aplicar_tema(imob)
render_topbar(imob)

if not st.session_state["logado"]:
    tela_login()
    st.stop()

st.sidebar.write(f"👤 {st.session_state['usuario_nome']}")
st.sidebar.write(f"📧 {st.session_state['usuario_email']}")
st.sidebar.write(f"🌐 Perfil global: {st.session_state['role_global']}")

if st.session_state.get("imobiliaria_nome"):
    st.sidebar.write(f"🏢 {st.session_state['imobiliaria_nome']}")
if st.session_state.get("cargo_imobiliaria"):
    st.sidebar.write(f"🔑 {st.session_state['cargo_imobiliaria']}")

if st.sidebar.button("🔄 Trocar imobiliária", use_container_width=True):
    limpar_estado_imobiliaria()
    st.rerun()

logout()

if not st.session_state.get("imobiliaria_id"):
    tela_escolha_imobiliaria()
    st.stop()

menu = st.sidebar.radio(
    "📂 Navegação",
    [
        "Início",
        "Solicitações",
        "Membros",
        "Empreendimentos",
        "Regras",
        "Nova Proposta",
    ],
)

if menu == "Início":
    tela_home()
elif menu == "Solicitações":
    painel_aprovacoes()
elif menu == "Membros":
    painel_membros_imobiliaria()
elif menu == "Empreendimentos":
    tela_empreendimentos()
elif menu == "Regras":
    tela_regras_imobiliaria()
elif menu == "Nova Proposta":
    tela_nova_proposta()
