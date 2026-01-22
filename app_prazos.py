import streamlit as st
import datetime
from datetime import timedelta
import holidays
import pandas as pd # Usado para criar a tabela de detalhamento

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Calculadora de Prazos CPC", page_icon="⚖️")

# --- TRADUÇÃO MANUAL DOS DIAS ---
def nome_dia_pt(data):
    dias = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }
    return dias[data.weekday()]

# --- MOTOR DE CÁLCULO (BACKEND) ---
br_holidays = holidays.Brazil()

def is_business_day(date_obj):
    """Verifica se é dia útil (Seg-Sex e não feriado)"""
    if date_obj.weekday() >= 5:  # 5=Sábado, 6=Domingo
        return False
    if date_obj in br_holidays:
        return False
    return True

def get_next_business_day(date_obj):
    """Encontra o próximo dia útil a partir de uma data"""
    next_day = date_obj + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day

# --- INTERFACE DO USUÁRIO (FRONTEND) ---

st.title("⚖️ Calculadora de Prazos Processuais")
st.markdown("### Sistema de Contagem (CPC/CNJ)")

col1, col2 = st.columns(2)

with col1:
    data_input = st.date_input("Selecione a Data:", datetime.date.today(), format="DD/MM/YYYY")
    tipo_data = st.radio("Essa data refere-se a:", ("Disponibilização (DJEN)", "Publicação Certificada"))

with col2:
    dias_prazo = st.number_input("Prazo (em dias úteis):", min_value=1, value=15, step=1)
    st.info(f"📅 A contagem excluirá fins de semana e feriados nacionais.")

# Botão de Ação
if st.button("CALCULAR PRAZO", type="primary"):
    
    # 1. Definir Marcos Iniciais
    if tipo_data == "Disponibilização (DJEN)":
        dt_disponibilizacao = data_input
        dt_publicacao = get_next_business_day(dt_disponibilizacao)
        # O prazo inicia no primeiro dia útil SEGUINTE à publicação
        dt_inicio_contagem = get_next_business_day(dt_publicacao)
    else:
        dt_disponibilizacao = None
        dt_publicacao = data_input
        dt_inicio_contagem = get_next_business_day(dt_publicacao)
    
    # 2. Loop de Contagem Detalhada (Dia a Dia)
    lista_detalhes = []
    dias_contados = 0
    data_atual = dt_inicio_contagem
    
    # O loop continua até atingirmos o número de dias do prazo
    while dias_contados < dias_prazo:
        # Verifica o status do dia atual
        eh_fds = data_atual.weekday() >= 5
        eh_feriado = data_atual in br_holidays
        nome_feriado = br_holidays.get(data_atual) if eh_feriado else ""
        
        status = ""
        contagem_texto = "-"
        
        if eh_fds:
            status = "❌ Fim de Semana"
            tipo_linha = "ignorado"
        elif eh_feriado:
            status = f"❌ Feriado ({nome_feriado})"
            tipo_linha = "ignorado"
        else:
            dias_contados += 1
            status = "✅ Dia Útil"
            contagem_texto = f"{dias_contados}º Dia"
            tipo_linha = "contado"
            
            # Se for o último dia, salvamos como data final
            if dias_contados == dias_prazo:
                dt_final = data_atual

        # Adiciona na lista para a tabela
        lista_detalhes.append({
            "Data": data_atual.strftime("%d/%m/%Y"),
            "Dia da Semana": nome_dia_pt(data_atual),
            "Status": status,
            "Contagem do Prazo": contagem_texto
        })
        
        # Avança para o próximo dia se ainda não acabou o prazo
        if dias_contados < dias_prazo:
             data_atual += timedelta(days=1)
        # Se acabou o prazo (dias_contados == dias_prazo), o loop para e a data_atual é o vencimento.

    # --- EXIBIÇÃO DOS RESULTADOS ---
    st.divider()
    st.subheader("📊 Resumo da Contagem")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        lbl = "1. Disponibilização"
        val = dt_disponibilizacao.strftime("%d/%m") if dt_disponibilizacao else "N/A"
        st.metric(lbl, val)
    with c2:
        st.metric("2. Publicação", dt_publicacao.strftime("%d/%m"))
    with c3:
        st.metric("3. Início Contagem", dt_inicio_contagem.strftime("%d/%m"))
    with c4:
        st.error(f"**FATAL: {dt_final.strftime('%d/%m/%Y')}**")

    # --- TABELA DETALHADA ---
    st.write("")
    st.subheader("🔎 Detalhamento Dia a Dia")
    
    # Transformando a lista em Tabela Visual (DataFrame)
    df = pd.DataFrame(lista_detalhes)
    
    # Mostrando a tabela (use_container_width ajusta à largura da tela)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.success(f"O prazo termina em **{dt_final.strftime('%d/%m/%Y')}** ({nome_dia_pt(dt_final)}).")