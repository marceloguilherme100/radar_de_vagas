import streamlit as st
import pandas as pd
import os
from robo import atualizar_banco

st.set_page_config(
    page_title="Radar de Vagas", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

ARQUIVO_CSV = "vagas.csv"

def carregar_css(caminho_css):
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

if not os.path.exists(ARQUIVO_CSV):
    st.info("Banco de dados vazio. Clique em 'Atualizar Vagas Agora'.")
    if st.button("🔄 Atualizar Vagas Agora", type="primary"):
        with st.spinner("Varrendo plataformas..."):
            atualizar_banco()
        st.rerun()
    st.stop()

df = pd.read_csv(ARQUIVO_CSV)

if "enviada" not in df.columns:
    df["enviada"] = False
else:
    df["enviada"] = df["enviada"].fillna(False).astype(bool)

if "area" not in df.columns:
    df["area"] = df["titulo"].apply(
        lambda t: "Desenvolvimento" if any(k in str(t).lower() for k in ["dev", "programador", "software", "python", "frontend", "backend", "fullstack"]) else "Suporte / TI"
    )

def identificar_fonte(vaga):
    if "fonte" in vaga and pd.notna(vaga["fonte"]):
        return str(vaga["fonte"])
    lnk = str(vaga.get("link", "")).lower()
    if "gupy" in lnk:
        return "Gupy"
    if "infojobs" in lnk:
        return "InfoJobs"
    return "LinkedIn"

df["fonte"] = df.apply(identificar_fonte, axis=1)

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Todas"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

# Contadores
ativas_df = df[df["enviada"] == False]
total_ativas = len(ativas_df)
suporte_cnt = len(ativas_df[ativas_df["area"] == "Suporte / TI"])
dev_cnt = len(ativas_df[ativas_df["area"] == "Desenvolvimento"])
remoto_cnt = len(ativas_df[ativas_df["modalidade"] == "Remoto"])
industria_cnt = len(ativas_df[ativas_df["tipo"] == "Indústria"])
enviadas_cnt = len(df[df["enviada"] == True])

# Cabeçalho Principal com Botão de Ação integrado ao lado do título
col_titulo, col_btn = st.columns([4, 1])

with col_titulo:
    st.markdown("<h1 style='margin-top: 0; margin-bottom: 0;'>🎯 Radar de Oportunidades</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; margin-top: 4px;'>Monitoramento ativo de vagas em Suporte, Infraestrutura e Desenvolvimento</p>", unsafe_allow_html=True)

with col_btn:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar Vagas", type="primary", use_container_width=True):
        with st.spinner("Varrendo LinkedIn, Gupy e InfoJobs..."):
            atualizar_banco()
        st.success("Atualizado!")
        st.rerun()

# Cards de Filtros no Topo
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    if st.button(f"📋 Todas\n\n{total_ativas}", use_container_width=True, on_click=mudar_pagina, args=("Todas",)):
        pass
with c2:
    if st.button(f"🛠️ Suporte\n\n{suporte_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Suporte",)):
        pass
with c3:
    if st.button(f"💻 Dev\n\n{dev_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Dev",)):
        pass
with c4:
    if st.button(f"🏠 Remoto\n\n{remoto_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Remoto",)):
        pass
with c5:
    if st.button(f"🏭 Polo / Suape\n\n{industria_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Indústria",)):
        pass
with c6:
    if st.button(f"📤 Enviadas\n\n{enviadas_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Enviadas",)):
        pass

st.markdown("<br>", unsafe_allow_html=True)

# Listagem de Vagas (continua o restante do código normalmente...)