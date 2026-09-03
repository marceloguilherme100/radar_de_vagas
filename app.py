import streamlit as st
import pandas as pd
import os
from streamlit_local_storage import LocalStorage
from robo import atualizar_banco

st.set_page_config(page_title="Radar de Vagas", page_icon="🎯", layout="wide")

# Inicializa o armazenamento local do navegador
local_storage = LocalStorage()

def carregar_css(caminho_css):
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

# Recupera os dados salvos no navegador (ou cria conjuntos vazios)
enviadas_storage = local_storage.getItem("vagas_enviadas") or []
expiradas_storage = local_storage.getItem("vagas_expiradas") or []

# Converte em sets para busca rápida
set_enviadas = set(enviadas_storage)
set_expiradas = set(expiradas_storage)

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Todas"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

ARQUIVO_CSV = "vagas.csv"

if os.path.exists(ARQUIVO_CSV):
    df = pd.read_csv(ARQUIVO_CSV)
    if "area" not in df.columns:
        df["area"] = df["titulo"].apply(
            lambda t: "Desenvolvimento" if any(k in str(t).lower() for k in ["dev", "programador", "software", "python", "frontend", "backend", "fullstack"]) else "Suporte / TI"
        )
else:
    st.info("Banco de dados vazio. Clique em 'Atualizar Vagas Agora' na barra lateral.")
    st.stop()

# Aplica os filtros persistentes do LocalStorage
# 1. Remove vagas marcadas como expiradas/excluídas
df = df[~df["link"].isin(set_expiradas)].copy()

# 2. Marca status de enviada com base no navegador
df["enviada"] = df["link"].apply(lambda link: link in set_enviadas)

# Barra lateral
with st.sidebar:
    st.header("⚙️ Ações")
    if st.button("🔄 Atualizar Vagas Agora", type="primary", use_container_width=True):
        with st.spinner("Buscando novas oportunidades..."):
            atualizar_banco()
        st.success("Vagas atualizadas!")
        st.rerun()

    st.divider()
    if st.button("🧹 Limpar Histórico do Navegador"):
        local_storage.deleteItem("vagas_enviadas")
        local_storage.deleteItem("vagas_expiradas")
        st.rerun()

# Contadores para os Cards
ativas_df = df[df["enviada"] == False]
total_ativas = len(ativas_df)
suporte_cnt = len(ativas_df[ativas_df["area"] == "Suporte / TI"])
dev_cnt = len(ativas_df[ativas_df["area"] == "Desenvolvimento"])
remoto_cnt = len(ativas_df[ativas_df["modalidade"] == "Remoto"])
industria_cnt = len(ativas_df[ativas_df["tipo"] == "Indústria"])
enviadas_cnt = len(df[df["enviada"] == True])

st.title("🎯 Radar de Vagas - Marcelo")
st.markdown("**Monitoramento Estratégico:** Suporte / Redes / Infra (RMR e Polo) & Dev / Programação (Remoto e Local)")
st.divider()

# Cards Clicáveis
st.subheader("Categorias de Oportunidades")
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    if st.button(f"📋 Todas\n({total_ativas})", use_container_width=True, on_click=mudar_pagina, args=("Todas",)):
        pass
with c2:
    if st.button(f"🛠️ Suporte & TI\n({suporte_cnt})", use_container_width=True, on_click=mudar_pagina, args=("Suporte",)):
        pass
with c3:
    if st.button(f"💻 Dev / Software\n({dev_cnt})", use_container_width=True, on_click=mudar_pagina, args=("Dev",)):
        pass
with c4:
    if st.button(f"🏠 Remoto\n({remoto_cnt})", use_container_width=True, on_click=mudar_pagina, args=("Remoto",)):
        pass
with c5:
    if st.button(f"🏭 Indústria\n({industria_cnt})", use_container_width=True, on_click=mudar_pagina, args=("Indústria",)):
        pass
with c6:
    if st.button(f"📤 Enviadas\n({enviadas_cnt})", use_container_width=True, on_click=mudar_pagina, args=("Enviadas",)):
        pass

st.divider()

# Filtragem de visualização
if st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Histórico de Candidaturas Realizadas ({enviadas_cnt})")
    df_exibicao = df[df["enviada"] == True].copy()
else:
    df_exibicao = df[df["enviada"] == False].copy()
    
    if st.session_state.pagina_atual == "Suporte":
        st.subheader(f"🛠️ Vagas de Suporte, Helpdesk, Redes e Técnico ({suporte_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Suporte / TI"]
    elif st.session_state.pagina_atual == "Dev":
        st.subheader(f"💻 Vagas de Programação, Dev e Software ({dev_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Desenvolvimento"]
    elif st.session_state.pagina_atual == "Remoto":
        st.subheader(f"🏠 Vagas Remotas Brasil ({remoto_cnt})")
        df_exibicao = df_exibicao[df_exibicao["modalidade"] == "Remoto"]
    elif st.session_state.pagina_atual == "Indústria":
        st.subheader(f"🏭 Vagas Indústria / Suape / Cabo ({industria_cnt})")
        df_exibicao = df_exibicao[df_exibicao["tipo"] == "Indústria"]
    else:
        st.subheader(f"📋 Todas as Vagas Disponíveis ({total_ativas})")

if st.session_state.pagina_atual != "Todas":
    if st.button("⬅️ Ver Todas as Vagas Disponíveis"):
        st.session_state.pagina_atual = "Todas"
        st.rerun()

df_exibicao = df_exibicao.sort_values(by="aderencia", ascending=False)

if df_exibicao.empty:
    st.info("Nenhuma vaga encontrada nesta visualização.")
else:
    for _, vaga in df_exibicao.iterrows():
        with st.container():
            icone = "💻" if vaga.get("area") == "Desenvolvimento" else "🛠️"
            st.subheader(f"{icone} {vaga['titulo']}")
            st.markdown(f"**Empresa:** {vaga['empresa']} | 📍 {vaga['local']} | 🏷️ **Área:** {vaga.get('area', 'TI Geral')} | 🏠 {vaga['modalidade']}")
            
            porc = int(vaga['aderencia'] * 100)
            st.progress(float(vaga['aderencia']), text=f"Aderência: {porc}% ({vaga['tags']})")
            
            btn_c1, btn_c2, btn_c3 = st.columns([1, 1.3, 1])
            with btn_c1:
                st.link_button("Ver vaga ↗", vaga["link"])
                
            with btn_c2:
                if vaga["enviada"]:
                    if st.button("↩️ Reativar", key=f"rec_{vaga['id']}"):
                        set_enviadas.discard(vaga["link"])
                        local_storage.setItem("vagas_enviadas", list(set_enviadas))
                        st.rerun()
                else:
                    if st.button("Marcar enviada ✔️", key=f"env_{vaga['id']}", type="primary"):
                        set_enviadas.add(vaga["link"])
                        local_storage.setItem("vagas_enviadas", list(set_enviadas))
                        st.rerun()

            with btn_c3:
                if st.button("🗑️ Expirada", key=f"del_{vaga['id']}"):
                    set_expiradas.add(vaga["link"])
                    local_storage.setItem("vagas_expiradas", list(set_expiradas))
                    st.rerun()

        st.markdown("---")