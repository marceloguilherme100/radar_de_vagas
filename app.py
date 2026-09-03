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

# Carrega e higieniza a base
if not os.path.exists(ARQUIVO_CSV):
    st.info("Banco de dados vazio. Clique em 'Atualizar Vagas Agora' na barra lateral.")
    st.stop()

df = pd.read_csv(ARQUIVO_CSV)

# Garante a existência das colunas de controle
if "enviada" not in df.columns:
    df["enviada"] = False
else:
    df["enviada"] = df["enviada"].fillna(False).astype(bool)

if "area" not in df.columns:
    df["area"] = df["titulo"].apply(
        lambda t: "Desenvolvimento" if any(k in str(t).lower() for k in ["dev", "programador", "software", "python", "frontend", "backend", "fullstack"]) else "Suporte / TI"
    )

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Todas"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

# Barra Lateral
with st.sidebar:
    st.header("⚙️ Ações")
    if st.button("🔄 Atualizar Vagas Agora", type="primary", use_container_width=True):
        with st.spinner("Buscando novas oportunidades..."):
            atualizar_banco()
        st.success("Vagas atualizadas!")
        st.rerun()

# Contadores
ativas_df = df[df["enviada"] == False]
total_ativas = len(ativas_df)
suporte_cnt = len(ativas_df[ativas_df["area"] == "Suporte / TI"])
dev_cnt = len(ativas_df[ativas_df["area"] == "Desenvolvimento"])
remoto_cnt = len(ativas_df[ativas_df["modalidade"] == "Remoto"])
industria_cnt = len(ativas_df[ativas_df["tipo"] == "Indústria"])
enviadas_cnt = len(df[df["enviada"] == True])

st.title("🎯 Radar de Vagas")
st.markdown("**Painel de Oportunidades:** Suporte / TI & Desenvolvimento")
st.divider()

# Cards Clicáveis
st.subheader("Categorias")
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

# Exibição conforme o filtro selecionado
if st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Histórico de Candidaturas Realizadas ({enviadas_cnt})")
    df_exibicao = df[df["enviada"] == True].copy()
else:
    df_exibicao = df[df["enviada"] == False].copy()
    if st.session_state.pagina_atual == "Suporte":
        st.subheader(f"🛠️ Suporte, Helpdesk e Redes ({suporte_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Suporte / TI"]
    elif st.session_state.pagina_atual == "Dev":
        st.subheader(f"💻 Programação e Software ({dev_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Desenvolvimento"]
    elif st.session_state.pagina_atual == "Remoto":
        st.subheader(f"🏠 Vagas Remotas ({remoto_cnt})")
        df_exibicao = df_exibicao[df_exibicao["modalidade"] == "Remoto"]
    elif st.session_state.pagina_atual == "Indústria":
        st.subheader(f"🏭 Polo Industrial / Suape / Cabo ({industria_cnt})")
        df_exibicao = df_exibicao[df_exibicao["tipo"] == "Indústria"]
    else:
        st.subheader(f"📋 Todas as Vagas Disponíveis ({total_ativas})")

if st.session_state.pagina_atual != "Todas":
    if st.button("⬅️ Ver Todas as Vagas Disponíveis"):
        st.session_state.pagina_atual = "Todas"
        st.rerun()

df_exibicao = df_exibicao.sort_values(by="aderencia", ascending=False)

if df_exibicao.empty:
    st.info("Nenhuma vaga encontrada nesta categoria.")
else:
    for _, vaga in df_exibicao.iterrows():
        with st.container():
            icone = "💻" if vaga.get("area") == "Desenvolvimento" else "🛠️"
            st.subheader(f"{icone} {vaga['titulo']}")
            st.markdown(f"**Empresa:** {vaga['empresa']} | 📍 {vaga['local']} | 🏷️ **Área:** {vaga.get('area', 'TI Geral')} | 🏠 {vaga['modalidade']}")
            
            porc = int(vaga['aderencia'] * 100)
            st.progress(float(vaga['aderencia']), text=f"Aderência: {porc}% ({vaga['tags']})")
            
            b1, b2, b3 = st.columns([1, 1.3, 1])
            with b1:
                st.link_button("Ver vaga ↗", vaga["link"])
            with b2:
                if vaga["enviada"]:
                    if st.button("↩️ Reativar", key=f"rec_{vaga['id']}"):
                        df.loc[df["link"] == vaga["link"], "enviada"] = False
                        df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                        st.rerun()
                else:
                    if st.button("Marcar enviada ✔️", key=f"env_{vaga['id']}", type="primary"):
                        df.loc[df["link"] == vaga["link"], "enviada"] = True
                        df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                        st.rerun()
            with b3:
                if st.button("🗑️ Expirada", key=f"del_{vaga['id']}"):
                    df = df[df["link"] != vaga["link"]]
                    df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                    st.rerun()

        st.markdown("---")