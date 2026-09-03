import streamlit as st
import pandas as pd
import os
from robo import atualizar_banco

st.set_page_config(page_title="Radar de Vagas", page_icon="🎯", layout="wide")

ARQUIVO_CSV = "vagas.csv"

def carregar_css(caminho_css):
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

if not os.path.exists(ARQUIVO_CSV):
    st.info("Banco de dados vazio. Clique em 'Atualizar Vagas Agora' na barra lateral.")
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

# Barra Lateral
with st.sidebar:
    st.markdown("### ⚙️ Painel de Controle")
    if st.button("🔄 Atualizar Vagas Agora", type="primary", use_container_width=True):
        with st.spinner("Varrendo LinkedIn, Gupy e InfoJobs..."):
            atualizar_banco()
        st.success("Sincronização concluída!")
        st.rerun()

# Contadores
ativas_df = df[df["enviada"] == False]
total_ativas = len(ativas_df)
suporte_cnt = len(ativas_df[ativas_df["area"] == "Suporte / TI"])
dev_cnt = len(ativas_df[ativas_df["area"] == "Desenvolvimento"])
remoto_cnt = len(ativas_df[ativas_df["modalidade"] == "Remoto"])
industria_cnt = len(ativas_df[ativas_df["tipo"] == "Indústria"])
enviadas_cnt = len(df[df["enviada"] == True])

# Cabeçalho Principal
st.markdown("<h1 style='margin-bottom:0;'>🎯 Radar de Oportunidades</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#94a3b8;'>Monitoramento ativo de vagas em Suporte, Infraestrutura e Desenvolvimento</p>", unsafe_allow_html=True)

# Grid de Cards no Topo
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

# Filtragem do dataset
if st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Candidaturas Realizadas ({enviadas_cnt})")
    df_exibicao = df[df["enviada"] == True].copy()
else:
    df_exibicao = df[df["enviada"] == False].copy()
    if st.session_state.pagina_atual == "Suporte":
        st.subheader(f"🛠️ Vagas de Suporte e Infra ({suporte_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Suporte / TI"]
    elif st.session_state.pagina_atual == "Dev":
        st.subheader(f"💻 Vagas de Programação e Software ({dev_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Desenvolvimento"]
    elif st.session_state.pagina_atual == "Remoto":
        st.subheader(f"🏠 Oportunidades Remotas ({remoto_cnt})")
        df_exibicao = df_exibicao[df_exibicao["modalidade"] == "Remoto"]
    elif st.session_state.pagina_atual == "Indústria":
        st.subheader(f"🏭 Vagas em Polo Industrial / Suape / Cabo ({industria_cnt})")
        df_exibicao = df_exibicao[df_exibicao["tipo"] == "Indústria"]
    else:
        st.subheader(f"📋 Todas as Vagas Disponíveis ({total_ativas})")

df_exibicao = df_exibicao.sort_values(by="aderencia", ascending=False)

if df_exibicao.empty:
    st.info("Nenhuma vaga cadastrada nesta categoria no momento.")
else:
    for _, vaga in df_exibicao.iterrows():
        fonte = vaga["fonte"]
        classe_fonte = "badge-linkedin" if fonte == "LinkedIn" else ("badge-gupy" if fonte == "Gupy" else "badge-infojobs")
        icone_cargo = "💻" if vaga.get("area") == "Desenvolvimento" else "🛠️"
        
        # Bloco visual do card com badges estilizadas
        st.markdown(f"""
        <div class="job-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div class="job-title">{icone_cargo} {vaga['titulo']}</div>
                    <div style="margin-bottom: 12px;">
                        <span class="badge-empresa">🏢 {vaga['empresa']}</span> &nbsp;•&nbsp; 
                        <span style="color:#94a3b8; font-size:0.9rem;">📍 {vaga['local']}</span>
                    </div>
                </div>
            </div>
            <div>
                <span class="badge {classe_fonte}">🌐 {fonte}</span>
                <span class="badge badge-area">🏷️ {vaga['area']}</span>
                <span class="badge badge-modalidade">🏠 {vaga['modalidade']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Barra de Aderência e Botões logo abaixo do card
        porc = int(vaga['aderencia'] * 100)
        st.progress(float(vaga['aderencia']), text=f"Match com perfil: {porc}% • Tags: {vaga['tags']}")

        btn_c1, btn_c2, btn_c3 = st.columns([1, 1.4, 0.8])
        with btn_c1:
            st.link_button("Acessar vaga ↗", vaga["link"], use_container_width=True)
        with btn_c2:
            if vaga["enviada"]:
                if st.button("↩️ Reativar vaga", key=f"rec_{vaga['id']}", use_container_width=True):
                    df.loc[df["link"] == vaga["link"], "enviada"] = False
                    df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                    st.rerun()
            else:
                if st.button("Marcar enviada ✔️", key=f"env_{vaga['id']}", type="primary", use_container_width=True):
                    df.loc[df["link"] == vaga["link"], "enviada"] = True
                    df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                    st.rerun()
        with btn_c3:
            if st.button("🗑️ Expirada", key=f"del_{vaga['id']}", use_container_width=True):
                df = df[df["link"] != vaga["link"]]
                df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)