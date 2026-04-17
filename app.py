import streamlit as st
import requests
from datetime import datetime, timezone

st.set_page_config(page_title="GoPropostas", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
MP_ACCESS_TOKEN = st.secrets["MP_ACCESS_TOKEN"]

WEBHOOK_URL = f"{SUPABASE_URL}/functions/v1/mercadopago-webhook"

def criar_pagamento(relacao_id, email):
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "items": [
            {
                "title": "Acesso GoPropostas",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": 29.90
            }
        ],
        "payer": {"email": email},
        "external_reference": str(relacao_id),
        "notification_url": WEBHOOK_URL,
        "back_urls": {
            "success": "https://gopropostas-v2.streamlit.app",
            "failure": "https://gopropostas-v2.streamlit.app",
            "pending": "https://gopropostas-v2.streamlit.app"
        },
        "auto_return": "approved"
    }

    response = requests.post(
        "https://api.mercadopago.com/checkout/preferences",
        headers=headers,
        json=body,
        timeout=30
    )

    if response.status_code not in [200, 201]:
        raise Exception(response.text)

    return response.json()

def atualizar_status(relacao_id, dados):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/usuarios_imobiliarias?id=eq.{relacao_id}",
        headers=headers,
        json=dados,
        timeout=30
    )

    if resp.status_code not in [200, 204]:
        raise Exception(resp.text)

st.title("GoPropostas V2 🚀")
st.markdown("### 💳 Pagamento de acesso")

usuario_id = st.text_input("ID do usuário")
email = st.text_input("Email")
relacao_id = st.text_input("ID da relação (usuarios_imobiliarias.id)")

if st.button("Gerar pagamento", use_container_width=True):
    if not relacao_id or not email:
        st.error("Preencha os campos")
    else:
        try:
            pref = criar_pagamento(relacao_id, email)
            link = pref.get("init_point")

            if link:
                atualizar_status(relacao_id, {
                    "pagamento_status": "aguardando",
                    "pagamento_link": link,
                    "pagamento_criado_em": datetime.now(timezone.utc).isoformat()
                })

                st.success("Pagamento gerado com sucesso!")
                st.link_button("👉 Pagar agora", link, use_container_width=True)

            else:
                st.error("Erro ao gerar link de pagamento")

        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.info("Após o pagamento, o webhook libera acesso automaticamente.")
