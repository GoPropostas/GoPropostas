import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- FUNÇÃO DE LIMPEZA DE DADOS ---
def para_float(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    texto = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto)
    except:
        return 0.0

# --- VALIDAÇÃO DE CPF ---
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    return len(cpf) == 11

# --- CLASSE PDF ---
class HomeBuyPDF(FPDF):
    def header(self):
        self.set_fill_color(23, 55, 94)
        self.rect(10, 10, 190, 10, 'F')
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(190, 10, 'PROPOSTA DE COMPRA DE LOTEAMENTO', 0, 1, 'C')
        self.ln(5)

    def seccao(self, titulo):
        self.set_fill_color(240, 240, 240)
        self.set_text_color(23, 55, 94)
        self.set_font('Arial', 'B', 10)
        self.cell(190, 7, f" {titulo}", 0, 1, 'L', True)
        self.ln(2)

    def campo(self, label, valor, largura, nova_linha=False):
        self.set_font('Arial', 'B', 8)
        self.cell(largura * 0.35, 6, f"{label}:", 0, 0)
        self.set_font('Arial', '', 9)
        x, y = self.get_x(), self.get_y()
        self.cell(largura * 0.65, 6, str(valor), 0, 0)
        self.line(x, y + 5, x + (largura * 0.65) - 2, y + 5)
        if nova_linha: self.ln(8)

def gerar_pdf(d):
    pdf = HomeBuyPDF()
    pdf.add_page()
    pdf.seccao("PROPONENTE / EMPRESA")
    pdf.campo("NOME", d['nome'], 190, True)
    pdf.campo("CPF", d['cpf'], 95)
    pdf.campo("FONE", d['fone'], 95, True)
    pdf.ln(2)
    pdf.seccao("CARACTERIZAÇÃO DO IMÓVEL")
    pdf.campo("UNIDADE", d['unidade'], 190, True)
    pdf.campo("VALOR NEGÓCIO", f"R$ {d['v_negocio']:,.2f}", 95)
    pdf.ln(2)
    pdf.seccao("CONDIÇÕES DE PAGAMENTO")
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(190, 8, f"VALOR TOTAL DA ENTRADA: R$ {d['v_entrada_total']:,.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(190, 6, d['txt_pagamento'], 'B')
    path = f"Proposta_{d['unidade'].replace(' ', '_')}.pdf"
    pdf.output(path)
    return path

# --- INTERFACE ---
if 'db' not in st.session_state: st.session_state['db'] = None

menu = st.sidebar.radio("Navegação", ["Corretor", "Admin"])

if menu == "Admin":
    st.header("⚙️ Configurações")
    if st.text_input("Senha", type="password") == "admin123":
        up = st.file_uploader("Subir Tabela", type=['xlsx'])
        if up:
            df_admin = pd.read_excel(up, skiprows=11)
            df_admin.columns = [str(c).strip() for c in df_admin.columns]
            st.session_state['db'] = df_admin
            st.success("Tabela carregada!")
else:
    st.header("📝 Gerar Proposta")
    if st.session_state['db'] is None:
        st.info("Aguardando tabela do Admin.")
    else:
        df = st.session_state['db']
        col_lote = df.columns[0]
        lotes = df[df[col_lote].astype(str).str.contains('LOTE', case=False, na=False)]

        # 1. ESCOLHA DA UNIDADE (FORA DO FORM PARA CALCULAR NA HORA)
        u = st.selectbox("Selecione a Unidade", lotes[col_lote].unique())
        dados = lotes[lotes[col_lote] == u].iloc[0]

        # 2. CAPTURA DOS VALORES DAS COLUNAS (COM LIMPEZA)
        v_negocio = para_float(dados.get("Valor Negócio", 0))
        v_intermed = para_float(dados.get("Intermediação", 0))
        v_ent_imov = para_float(dados.get("Entrada Imóvel", 0))
        
        # 3. SOMA AUTOMÁTICA DA ENTRADA
        soma_entrada_final = v_intermed + v_ent_imov

        # 4. PAINEL DE CONFERÊNCIA (SEM FAIXA BRANCA, USANDO MÉTRICAS)
        st.write("### 📊 Resumo Financeiro da Unidade")
        c_a, c_b, c_c = st.columns(3)
        c_a.metric("Valor Negócio", f"R$ {v_negocio:,.2f}")
        c_b.metric("Intermediação", f"R$ {v_intermed:,.2f}")
        c_c.metric("Entrada Imóvel", f"R$ {v_ent_imov:,.2f}")
        
        st.success(f"💰 **ENTRADA TOTAL CALCULADA:** R$ {soma_entrada_final:,.2f}")
        st.write("---")

        with st.form("form_venda_final"):
            st.subheader("👤 Dados do Cliente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Cliente")
            cpf = c2.text_input("CPF")
            fone = st.text_input("Telefone")

            st.subheader("💳 Condições da Entrada")
            # Este campo puxa o valor da soma automaticamente
            v_entrada_user = st.number_input("Confirmar Valor da Entrada", value=soma_entrada_final, key=f"ent_{u}")
            num_parc = st.slider("Parcelar o restante em:", 1, 4, 1)

            # Cálculos das parcelas
            ato_calc = v_negocio * 0.003
            saldo_parc = v_entrada_user - ato_calc
            valor_da_parcela = saldo_parc / num_parc if saldo_parc > 0 else 0

            st.info(f"O cálculo será: Ato de R$ {ato_calc:,.2f} + {num_parc} parcelas de R$ {valor_da_parcela:,.2f}")

            if st.form_submit_button("🚀 GERAR PROPOSTA"):
                if not nome or not cpf:
                    st.error("Preencha os dados do cliente.")
                else:
                    texto_pagamento = (
                        f"O pagamento da entrada será realizado da seguinte forma:\n"
                        f"- ATO (0,30% sobre o Valor do Negócio): R$ {ato_calc:,.2f}\n"
                        f"- SALDO DA ENTRADA: R$ {saldo_parc:,.2f} parcelado em {num_parc}x de R$ {valor_da_parcela:,.2f} mensais."
                    )

                    info_pdf = {
                        'nome': nome, 'cpf': cpf, 'fone': fone, 'unidade': u,
                        'v_negocio': v_negocio, 'v_entrada_total': v_entrada_user,
                        'v_intermed': v_intermed, 'v_ent_imovel': v_ent_imov,
                        'txt_pagamento': texto_pagamento
                    }
                    
                    st.session_state['pdf_gerado'] = gerar_pdf(info_pdf)
                    st.success("✅ Proposta gerada com os valores conferidos!")

        if 'pdf_gerado' in st.session_state:
            with open(st.session_state['pdf_gerado'], "rb") as f:
                st.download_button("📥 Baixar PDF Agora", f, file_name=st.session_state['pdf_gerado'], use_container_width=True)