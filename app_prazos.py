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
        # Título do PDF
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatório de Contagem de Prazo - CPC/CNJ', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Posicionamento a 1.5cm do fim da página
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128) # Cinza para o rodapé
        
        # Página na esquerda
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'L')
        
        # Créditos na direita (Alinhado à direita com margem zero)
        # Usamos cell(0...) mas o texto ficaria na esquerda se não forçar o 'R' com ln=0 não funciona bem.
        # Truque do FPDF para alinhar à direita na mesma linha:
        self.set_x(-100) # Move cursor para a direita
        self.cell(0, 10, 'FEITO POR TALISON OLIVEIRA BARBOSA', 0, 0, 'R')

def criar_pdf(nome_escritorio, dt_disp, dt_pub, dt_inicio, dt_final, dias_prazo, df_detalhes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Cabeçalho do Escritório
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"{nome_escritorio}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, "Sistema de Controle de Prazos", 0, 1, 'L')
    pdf.ln(5)

    # 2. Resumo das Datas
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumo dos Marcos Temporais:", 0, 1, 'L')
    pdf.set_font("Arial", size=11)
    
    if dt_disp:
        pdf.cell(0, 8, f"Disponibilização (DJEN): {dt_disp.strftime('%d/%m/%Y')}", 0, 1)
    
    pdf.cell(0, 8, f"Data da Publicação: {dt_pub.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"Início da Contagem: {dt_inicio.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"Prazo Total: {dias_prazo} dias úteis", 0, 1)
    
    pdf.set_text_color(220, 50, 50) # Vermelho para destaque
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"DATA FATAL (VENCIMENTO): {dt_final.strftime('%d/%m/%Y')}", 0, 1)
    pdf.set_text_color(0, 0, 0) # Volta para preto
    pdf.ln(5)

    # 3. Tabela de Detalhamento
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Detalhamento Dia a Dia:", 0, 1, 'L')
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(200, 220, 255) # Azul claro
    pdf.cell(30, 8, "Data", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Dia da Semana", 1, 0, 'C', 1)
    pdf.cell(80, 8, "Status", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Contagem", 1, 1, 'C', 1)

    # Linhas da Tabela
    pdf.set_font("Arial", size=10)
    for index, row in df_detalhes.iterrows():
        pdf.cell(30, 8, row['Data'], 1, 0, 'C')
        pdf.cell(40, 8, row['Dia da Semana'], 1, 0, 'C')
        
        # Tratamento de caracteres especiais
        status_clean = row['Status'].replace("❌", "X").replace("✅", "OK")
        pdf.cell(80, 8, status_clean, 1, 0, 'L')
        
        pdf.cell(40, 8, row['Contagem do Prazo'], 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- FUNÇÕES AUXILIARES ---
def nome_dia_pt(data):
    dias = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    return dias[data.weekday()]

br_holidays = holidays.Brazil()

def is_business_day(date_obj):
    if date_obj.weekday() >= 5 or date_obj in br_holidays: return False
    return True

def get_next_business_day(date_obj):
    next_day = date_obj + timedelta(days=1)
    while not is_business_day(next_day): next_day += timedelta(days=1)
    return next_day

# --- INTERFACE ---
st.title("⚖️ Calculadora DERKIAM")
st.markdown("### Sistema de Contagem (CPC/CNJ)")

# Input do Nome do Escritório (Agora fixo com o valor padrão)
nome_escritorio = st.text_input("Nome do Escritório / Advogado:", "DERKIAM ADVOCACIA")

col1, col2 = st.columns(2)
with col1:
    data_input = st.date_input("Selecione a Data:", datetime.date.today(), format="DD/MM/YYYY")
    tipo_data = st.radio("Refere-se a:", ("Disponibilização (DJEN)", "Publicação Certificada"))
with col2:
    dias_prazo = st.number_input("Prazo (dias úteis):", min_value=1, value=15)

if st.button("CALCULAR PRAZO", type="primary"):
    # Lógica de Cálculo
    if tipo_data == "Disponibilização (DJEN)":
        dt_disp = data_input
        dt_pub = get_next_business_day(dt_disp)
        dt_inicio = get_next_business_day(dt_pub)
    else:
        dt_disp = None
        dt_pub = data_input
        dt_inicio = get_next_business_day(dt_pub)
    
    # Loop de Contagem
    lista_detalhes = []
    dias_contados = 0
    data_atual = dt_inicio
    
    while dias_contados < dias_prazo:
        eh_fds = data_atual.weekday() >= 5
        eh_feriado = data_atual in br_holidays
        nome_feriado = br_holidays.get(data_atual) if eh_feriado else ""
        
        if eh_fds:
            status = "❌ Fim de Semana"
        elif eh_feriado:
            status = f"❌ Feriado ({nome_feriado})"
        else:
            dias_contados += 1
            status = "✅ Dia Útil"
            if dias_contados == dias_prazo: dt_final = data_atual

        lista_detalhes.append({
            "Data": data_atual.strftime("%d/%m/%Y"),
            "Dia da Semana": nome_dia_pt(data_atual),
            "Status": status,
            "Contagem do Prazo": f"{dias_contados}º Dia" if status == "✅ Dia Útil" else "-"
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

    # Área do PDF
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
