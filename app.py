import streamlit as st
import pandas as pd
import os
from robo import atualizar_banco

st.set_page_config(page_title="Radar de Vagas", page_icon="🎯", layout="wide")

def carregar_css(caminho_css):
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Todas"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

ARQUIVO_CSV = "vagas.csv"

if os.path.exists(ARQUIVO_CSV):
    df = pd.read_csv(ARQUIVO_CSV)
    if "area" not in df.columns:
        df["area"] = df["titulo"].apply(lambda t: "Desenvolvimento" if any(k in str(t).lower() for k in ["dev", "programador", "software", "python"]) else "Suporte / TI")
else:
    st.info("Banco de dados vazio. Clique em 'Atualizar Vagas Agora' na barra lateral.")
    st.stop()

# Barra lateral
with st.sidebar:
    st.header("⚙️ Ações")
    if st.button("🔄 Atualizar Vagas Agora", type="primary", use_container_width=True):
        with st.spinner("Buscando novas oportunidades..."):
            atualizar_banco()
        st.success("Vagas atualizadas!")
        st.rerun()

# Contadores para os Cards
ativas_df = df[df["enviada"] == False]
suporte_cnt = len(ativas_df[ativas_df["area"] == "Suporte / TI"])
dev_cnt = len(ativas_df[ativas_df["area"] == "Desenvolvimento"])
remoto_cnt = len(ativas_df[ativas_df["modalidade"] == "Remoto"])
industria_cnt = len(ativas_df[ativas_df["tipo"] == "Indústria"])
total_ativas = len(ativas_df)
enviadas_cnt = len(df[df["enviada"] == True])

st.title("🎯 Radar de Vagas")
st.markdown("**Monitoramento Estratégico:** Suporte / Redes / Infra (RMR e Polo) & Dev / Programação (Remoto e Local)")
st.divider()

# Grid de Cards Clicáveis (Navegação)
st.subheader("Categorias de Oportunidades")
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    if st.button(f"📋 Todas\n\n### {total_ativas}", use_container_width=True, on_click=mudar_pagina, args=("Todas",)):
        pass
with c2:
    if st.button(f"🛠️ Suporte & TI\n\n### {suporte_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Suporte",)):
        pass
with c3:
    if st.button(f"💻 Dev / Software\n\n### {dev_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Dev",)):
        pass
with c4:
    if st.button(f"🏠 Remoto\n\n### {remoto_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Remoto",)):
        pass
with c5:
    if st.button(f"🏭 Indústria / Cabo\n\n### {industria_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Indústria",)):
        pass
with c6:
    if st.button(f"📤 Enviadas\n\n### {enviadas_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Enviadas",)):
        pass

st.divider()

# Lógica de Exibição
if st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Histórico de Candidaturas Realizadas ({enviadas_cnt})")
    df_exibicao = df[df["enviada"] == True].copy()
else:
    # Nas demais páginas, vagas já enviadas não poluem a visualização
    df_exibicao = df[df["enviada"] == False].copy()
    
    if st.session_state.pagina_atual == "Suporte":
        st.subheader(f"🛠️ Vagas de Suporte, Analista TI, Helpdesk e Redes ({suporte_cnt})")
        df_exibicao = df_exibicao[df_exibicao["area"] == "Suporte / TI"]
    elif st.session_state.pagina_atual == "Dev":
        st.subheader(f"💻 Vagas de Programação, Desenvolvimento e Software ({dev_cnt})")
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
            icone = "💻" if vaga["area"] == "Desenvolvimento" else "🛠️"
            st.subheader(f"{icone} {vaga['titulo']}")
            st.markdown(f"**Empresa:** {vaga['empresa']} | 📍 {vaga['local']} | 🏷️ **Área:** {vaga['area']} | 🏠 {vaga['modalidade']}")
            
            porc = int(vaga['aderencia'] * 100)
            st.progress(float(vaga['aderencia']), text=f"Aderência: {porc}% ({vaga['tags']})")
            
            btn_c1, btn_c2, _ = st.columns([1, 1.5, 3])
            with btn_c1:
                st.link_button("Ver vaga ↗", vaga["link"])
                
            with btn_c2:
                if vaga["enviada"]:
                    if st.button("↩️ Reativar vaga", key=f"rec_{vaga['id']}"):
                        df.loc[df["id"] == vaga["id"], "enviada"] = False
                        df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                        st.rerun()
                else:
                    if st.button("Marcar enviada ✔️", key=f"env_{vaga['id']}", type="primary"):
                        df.loc[df["id"] == vaga["id"], "enviada"] = True
                        df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                        st.rerun()

        st.markdown("---")