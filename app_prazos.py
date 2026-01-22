import streamlit as st
import datetime
from datetime import timedelta
import holidays
import pandas as pd
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora DERKIAM", page_icon="⚖️")

# --- FUNÇÃO DE GERAR PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatorio de Contagem de Prazo - CPC/CNJ', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'L')
        self.set_x(-100)
        self.cell(0, 10, 'FEITO POR TALISON OLIVEIRA BARBOSA', 0, 0, 'R')

def criar_pdf(nome_escritorio, dt_disp, dt_pub, dt_inicio, dt_final, dias_prazo, df_detalhes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"{nome_escritorio}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, "Sistema de Controle de Prazos - Com Recesso Forense", 0, 1, 'L')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumo dos Marcos Temporais:", 0, 1, 'L')
    pdf.set_font("Arial", size=11)
    
    if dt_disp:
        pdf.cell(0, 8, f"Disponibilizacao (DJEN): {dt_disp.strftime('%d/%m/%Y')}", 0, 1)
    
    pdf.cell(0, 8, f"Data da Publicacao: {dt_pub.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"Inicio da Contagem: {dt_inicio.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"Prazo Total: {dias_prazo} dias uteis", 0, 1)
    
    pdf.set_text_color(220, 50, 50)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"DATA FATAL (VENCIMENTO): {dt_final.strftime('%d/%m/%Y')}", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 8, "Data", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Dia Semana", 1, 0, 'C', 1)
    pdf.cell(85, 8, "Status", 1, 0, 'C', 1)
    pdf.cell(35, 8, "Contagem", 1, 1, 'C', 1)

    pdf.set_font("Arial", size=9)
    for index, row in df_detalhes.iterrows():
        pdf.cell(30, 7, row['Data'], 1, 0, 'C')
        pdf.cell(40, 7, row['Dia da Semana'], 1, 0, 'C')
        status_clean = row['Status'].replace("❌", "X").replace("✅", "OK")
        pdf.cell(85, 7, status_clean[:45], 1, 0, 'L')
        pdf.cell(35, 7, row['Contagem do Prazo'], 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- LÓGICA DE NEGÓCIO ---
def nome_dia_pt(data):
    dias = {0: "Segunda-feira", 1: "Terca-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sabado", 6: "Domingo"}
    return dias[data.weekday()]

br_holidays = holidays.Brazil()

def is_recesso(data):
    """Verifica suspensão do Art. 220 do CPC (20/12 a 20/01)"""
    mes = data.month
    dia = data.day
    if (mes == 12 and dia >= 20) or (mes == 1 and dia <= 20):
        return True
    return False

def is_business_day(date_obj):
    if is_recesso(date_obj): return False
    if date_obj.weekday() >= 5 or date_obj in br_holidays: return False
    return True

def get_next_business_day(date_obj):
    next_day = date_obj + timedelta(days=1)
    while not is_business_day(next_day): next_day += timedelta(days=1)
    return next_day

# --- INTERFACE ---
st.title("⚖️ Calculadora DERKIAM")
st.markdown("### Contagem CPC/CNJ com Recesso Forense (Art. 220)")

nome_escritorio = st.text_input("Nome do Escritório / Advogado:", "DERKIAM ADVOCACIA")

col1, col2 = st.columns(2)
with col1:
    data_input = st.date_input("Selecione a Data:", datetime.date.today(), format="DD/MM/YYYY")
    tipo_data = st.radio("Refere-se a:", ("Disponibilização (DJEN)", "Publicação Certificada"))
with col2:
    dias_prazo = st.number_input("Prazo (dias úteis):", min_value=1, value=15)

if st.button("CALCULAR PRAZO", type="primary"):
    if tipo_data == "Disponibilização (DJEN)":
        dt_disp = data_input
        dt_pub = get_next_business_day(dt_disp)
        dt_inicio = get_next_business_day(dt_pub)
    else:
        dt_disp = None
        dt_pub = data_input
        dt_inicio = get_next_business_day(dt_pub)
    
    lista_detalhes = []
    dias_contados = 0
    data_atual = dt_inicio
    
    # Limite de segurança para evitar loops infinitos
    max_iter = 500 
    cont_iter = 0

    while dias_contados < dias_prazo and cont_iter < max_iter:
        cont_iter += 1
        eh_recesso = is_recesso(data_atual)
        eh_fds = data_atual.weekday() >= 5
        eh_feriado = data_atual in br_holidays
        nome_feriado = br_holidays.get(data_atual) if eh_feriado else ""
        
        status = ""
        if eh_recesso:
            status = "❌ SUSPENSO (Recesso Art. 220 CPC)"
        elif eh_fds:
            status = "❌ Fim de Semana"
        elif eh_feriado:
            status = f"❌ Feriado ({nome_feriado})"
        else:
            dias_contados += 1
            status = "✅ Dia Util"
            if dias_contados == dias_prazo: dt_final = data_atual

        lista_detalhes.append({
            "Data": data_atual.strftime("%d/%m/%Y"),
            "Dia da Semana": nome_dia_pt(data_atual),
            "Status": status,
            "Contagem do Prazo": f"{dias_contados}o Dia" if status == "✅ Dia Util" else "-"
        })
        
        if dias_contados < dias_prazo: data_atual += timedelta(days=1)

    # Exibição
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("1. Disponibilização", dt_disp.strftime("%d/%m") if dt_disp else "N/A")
    c2.metric("2. Publicação", dt_pub.strftime("%d/%m"))
    c3.metric("3. Início Contagem", dt_inicio.strftime("%d/%m"))
    c4.error(f"**FATAL: {dt_final.strftime('%d/%m/%Y')}**")
    
    st.success(f"O prazo termina em **{dt_final.strftime('%d/%m/%Y')}** ({nome_dia_pt(dt_final)}).")

    df_detalhes = pd.DataFrame(lista_detalhes)
    st.subheader("📄 Exportar Relatório")
    
    pdf_bytes = criar_pdf(nome_escritorio, dt_disp, dt_pub, dt_inicio, dt_final, dias_prazo, df_detalhes)
    
    st.download_button(
        label="Baixar Relatório em PDF",
        data=pdf_bytes,
        file_name=f"prazo_DERKIAM_{dt_final.strftime('%d-%m-%Y')}.pdf",
        mime="application/pdf"
    )

    st.subheader("🔎 Detalhamento na Tela")
    st.dataframe(df_detalhes, use_container_width=True, hide_index=True)
    st.caption("Desenvolvido por Talison Oliveira Barbosa")
