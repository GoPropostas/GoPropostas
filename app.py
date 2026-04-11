# 🔥 SUBSTITUA APENAS ESSA PARTE DAS CONDIÇÕES

# PARCELAS INTELIGENTES
st.subheader("💰 Condições")

valor_cliente = st.number_input("Entrada cliente", min_value=0.0, key="entrada")
personalizar = st.checkbox("⚙️ Personalizar", key="pers")

ato_manual = st.number_input("Valor ato", min_value=0.0, key="ato_manual") if personalizar else 0
ato = ato_manual if ato_manual > 0 else ato_min

# 🔥 NOVA LÓGICA CORRETA
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

# 🔥 PAINEL DETALHES DO LOTE
st.divider()
st.subheader("🏡 Detalhes do Lote")

l1, l2, l3 = st.columns(3)

l1.metric("Unidade", unidade)
l1.metric("Área (m²)", f"{area:.2f}")

l2.metric("Valor Negócio", f"R$ {valor_negocio:,.2f}")
l2.metric("Valor Imóvel", f"R$ {valor_imovel:,.2f}")

l3.metric("Entrada Imóvel", f"R$ {entrada_imovel:,.2f}")
l3.metric("Intermediação", f"R$ {intermed:,.2f}")

# 🔥 PAINEL DE CÁLCULO
st.divider()
st.subheader("📊 Painel de Cálculo")

c1, c2, c3 = st.columns(3)

c1.metric("Valor do Negócio", f"R$ {valor_negocio:,.2f}")
c1.metric("Entrada Total", f"R$ {entrada_total:,.2f}")

c2.metric("Entrada Cliente", f"R$ {valor_cliente:,.2f}")
c2.metric("Ato", f"R$ {ato:,.2f}")

c3.metric("Restante Entrada", f"R$ {restante:,.2f}")
c3.metric("Parcelas", parcelas)

st.markdown("### 📅 Parcelamento")

if parcelas > 1:
    if usar_diferente:
        st.warning(f"{parcelas_iguais}x de R$ {valor_parcela_igual:,.2f} + 1x de R$ {parcela_diferente:,.2f}")
    else:
        st.success(f"{parcelas}x de R$ {valor_parcela_igual:,.2f}")
else:
    st.success("Pagamento à vista")

# ALERTAS
if valor_cliente < ato:
    st.error("⚠️ Entrada não cobre o ATO")

if restante == 0:
    st.success("✅ Entrada quitada")