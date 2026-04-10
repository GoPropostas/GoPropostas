import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- LIMPEZA DE VALORES ---
def limpar_e_converter(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    texto = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except:
        return 0.0

# --- BUSCAR COLUNA FLEXÍVEL ---
def buscar_coluna(linha, nomes):
    for nome in nomes:
        if nome in linha.index:
            return limpar_e_converter(linha[nome])
    return 0.0

# --- PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(190, 10, 'PROPOSTA DE COMPRA', 0, 1, 'C')

def gerar_pdf(d):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)

    pdf.cell(190, 8, f"Unidade: {d['unidade']}", 0, 1)
    pdf.cell(190, 8, f"Valor Negócio: R$ {d['v_negocio']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"Entrada Total: R$ {d['entrada_total']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"Ato (dentro da entrada): R$ {d['ato']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"Entrada Restante: R$ {d['entrada_restante']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"{d['parcelas']}x de R$ {d['valor_parcela']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"Parcelas 36x: R$ {d['parcela_36']:,.2f}", 0, 1)
    pdf.cell(190, 8, f"Saldo Devedor: R$ {d['saldo']:,.2f}", 0, 1)

    path = "proposta.pdf"
    pdf.output(path)
    return path

# --- CONFIG APP ---
st.set_page_config(layout="wide")

if 'db' not in st.session_state:
    st.session_state['db'] = None

menu = st.sidebar.radio("Menu", ["Corretor", "Admin"])

# --- ADMIN ---
if menu == "Admin":
    st.header("⚙️ Upload da Tabela")

    if st.text_input("Senha", type="password") == "admin123":
        arquivo = st.file_uploader("Enviar Excel", type=['xlsx'])

        if arquivo:
            df = pd.read_excel(arquivo, skiprows=11)

            # LIMPAR COLUNAS
            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.lower()
                .str.replace('\n', ' ')
            )

            st.session_state['db'] = df
            st.success("Tabela carregada!")

# --- CORRETOR ---
else:
    st.header("📝 Gerador de Propostas")

    if st.session_state['db'] is None:
        st.info("Envie a tabela no modo Admin")
    else:
        df = st.session_state['db']

        col_lote = df.columns[0]
        lotes = df[df[col_lote].notna()]

        unidade = st.selectbox("Selecione o Lote", lotes[col_lote].unique())
        linha = lotes[lotes[col_lote] == unidade].iloc[0]

        # --- DADOS DA PLANILHA ---
        valor_negocio = buscar_coluna(linha, ["valor negócio", "valor negocio"])
        intermed = buscar_coluna(linha, ["intermediação", "intermediacao"])
        entrada_imovel = buscar_coluna(linha, ["entrada imóvel", "entrada imovel"])
        parcela_36 = buscar_coluna(linha, ["36x", "parcela 36x"])
        saldo = buscar_coluna(linha, ["saldo", "saldo devedor"])

        # --- CÁLCULOS BASE ---
        entrada_total = intermed + entrada_imovel
        ato_minimo = valor_negocio * 0.003

        st.subheader("📊 Dados do Lote")
        st.write(f"Valor Negócio: R$ {valor_negocio:,.2f}")
        st.write(f"Entrada Total (já com ato): R$ {entrada_total:,.2f}")
        st.write(f"Ato mínimo (0,30%): R$ {ato_minimo:,.2f}")

        st.divider()

        # --- INPUT CLIENTE ---
        valor_cliente = st.number_input("Valor que o cliente quer dar de entrada", min_value=0.0)

        # --- LÓGICA CORRETA (ATO EMBUTIDO) ---
        ato = min(valor_cliente, ato_minimo)

        entrada_restante = entrada_total - valor_cliente
        if entrada_restante < 0:
            entrada_restante = 0

        parcelas = st.slider("Parcelar restante da entrada", 1, 4, 1)

        valor_parcela = entrada_restante / parcelas if entrada_restante > 0 else 0

        # --- VISUAL ---
        st.divider()
        st.subheader("📋 Simulação")

        st.write(f"💰 Cliente pagou: R$ {valor_cliente:,.2f}")
        st.write(f"📌 Ato (dentro do valor): R$ {ato:,.2f}")
        st.write(f"📊 Entrada restante: R$ {entrada_restante:,.2f}")
        st.write(f"📅 {parcelas}x de R$ {valor_parcela:,.2f}")

        st.write("---")
        st.write(f"📆 Parcelas 36x (tabela): R$ {parcela_36:,.2f}")
        st.write(f"🏦 Saldo Devedor: R$ {saldo:,.2f}")

        # --- GERAR PDF ---
        if st.button("📄 Gerar Proposta"):
            dados = {
                "unidade": unidade,
                "v_negocio": valor_negocio,
                "entrada_total": entrada_total,
                "ato": ato,
                "entrada_restante": entrada_restante,
                "parcelas": parcelas,
                "valor_parcela": valor_parcela,
                "parcela_36": parcela_36,
                "saldo": saldo
            }

            caminho = gerar_pdf(dados)

            with open(caminho, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name="proposta.pdf")