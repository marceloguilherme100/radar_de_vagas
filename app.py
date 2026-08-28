import streamlit as st
import pandas as pd
import os
from robo import atualizar_banco

# 1. Configuração da página
st.set_page_config(page_title="Radar de Vagas", page_icon="🎯", layout="centered")

# 2. Carrega estilo CSS externo
def carregar_css(caminho_css):
    if os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

# 3. Gerenciamento de Estado da Navegação (Páginas)
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Geral"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

# 4. Leitura do Banco de Dados
ARQUIVO_CSV = "vagas.csv"

if os.path.exists(ARQUIVO_CSV):
    df = pd.read_csv(ARQUIVO_CSV)
else:
    st.info("Nenhuma vaga cadastrada ainda. Atualize o banco na barra lateral!")
    st.stop()

# 5. Barra Lateral
with st.sidebar:
    st.header("⚙️ Ações")
    if st.button("🔄 Atualizar Vagas Agora", type="primary", use_container_width=True):
        with st.spinner("Buscando novas vagas na web..."):
            atualizar_banco()
        st.success("Vagas atualizadas com sucesso!")
        st.rerun()

    st.divider()
    ocultar_enviadas = st.checkbox("Ocultar vagas enviadas", value=False)

# 6. Cabeçalho Principal
st.title("🎯 Radar de Vagas - Marcelo")
st.markdown("**Filtro diário:** Remoto (Brasil todo) | Presencial (Recife, Região Metropolitana, Cabo, Ipojuca e Suape)")
st.divider()

# 7. Contadores Globais para os Cards
total_vagas = len(df)
industria_cnt = len(df[df['tipo'] == 'Indústria'])
remoto_cnt = len(df[df['modalidade'] == 'Remoto'])
alta_aderencia_cnt = len(df[df['aderencia'] >= 0.85])
enviadas_cnt = len(df[df['enviada'] == True])

# 8. Painel de Cards Clicáveis (Navegação)
st.subheader("Categorias de Vagas")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button(f"🆕 Novas\n\n### {total_vagas}", use_container_width=True, on_click=mudar_pagina, args=("Geral",)):
        pass
with col2:
    if st.button(f"🏭 Indústria\n\n### {industria_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Indústria",)):
        pass
with col3:
    if st.button(f"🏠 Remoto\n\n### {remoto_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Remoto",)):
        pass
with col4:
    if st.button(f"⭐ Alta Ader.\n\n### {alta_aderencia_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Alta Aderência",)):
        pass
with col5:
    if st.button(f"📤 Enviadas\n\n### {enviadas_cnt}", use_container_width=True, on_click=mudar_pagina, args=("Enviadas",)):
        pass

st.divider()

# 9. Lógica de Filtragem de Acordo com a Página Selecionada
df_exibicao = df.copy()

if st.session_state.pagina_atual == "Geral":
    st.subheader(f"📋 Todas as Oportunidades ({total_vagas})")
elif st.session_state.pagina_atual == "Indústria":
    st.subheader(f"🏭 Vagas no Polo Industrial / Suape / Cabo ({industria_cnt})")
    df_exibicao = df_exibicao[df_exibicao['tipo'] == 'Indústria']
elif st.session_state.pagina_atual == "Remoto":
    st.subheader(f"🏠 Vagas Remotas - Brasil Todo ({remoto_cnt})")
    df_exibicao = df_exibicao[df_exibicao['modalidade'] == 'Remoto']
elif st.session_state.pagina_atual == "Alta Aderência":
    st.subheader(f"⭐ Vagas de Alta Compatibilidade >= 85% ({alta_aderencia_cnt})")
    df_exibicao = df_exibicao[df_exibicao['aderencia'] >= 0.85]
elif st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Histórico de Vagas Enviadas ({enviadas_cnt})")
    df_exibicao = df_exibicao[df_exibicao['enviada'] == True]

# Botão para resetar a visualização caso não esteja na tela Geral
if st.session_state.pagina_atual != "Geral":
    if st.button("⬅️ Ver Todas as Vagas", type="secondary"):
        st.session_state.pagina_atual = "Geral"
        st.rerun()

# Aplica filtro de ocultar enviadas se estiver ativado
if ocultar_enviadas and st.session_state.pagina_atual != "Enviadas":
    df_exibicao = df_exibicao[df_exibicao['enviada'] == False]

# 10. Renderização das Vagas
df_exibicao = df_exibicao.sort_values(by="aderencia", ascending=False)

if df_exibicao.empty:
    st.info("Nenhuma vaga encontrada nesta categoria.")
else:
    for index, vaga in df_exibicao.iterrows():
        with st.container():
            icone = "💻" if any(k in str(vaga['titulo']).lower() for k in ["python", "dev", "programador", "software", "rpa", "ia"]) else "🛠️"
            
            st.subheader(f"{icone} {vaga['titulo']}")
            st.markdown(f"**Empresa:** {vaga['empresa']} | 📍 {vaga['local']} | 🏭 {vaga['tipo']} | 🏠 {vaga['modalidade']}")
            
            porcentagem = int(vaga['aderencia'] * 100)
            cor_bolinha = "🟢" if porcentagem >= 80 else "🟡"
            
            st.progress(float(vaga['aderencia']), text=f"{cor_bolinha} {porcentagem}% de Aderência ({vaga['tags']})")
            
            btn_col1, btn_col2, _ = st.columns([1, 1.5, 3])
            with btn_col1:
                st.link_button("Ver vaga", vaga['link'])
                
            with btn_col2:
                if vaga['enviada']:
                    st.button("Enviada ✔️", key=f"env_{vaga['id']}", disabled=True)
                else:
                    if st.button("Marcar enviada", key=f"env_{vaga['id']}", type="primary"):
                        df.loc[df['id'] == vaga['id'], 'enviada'] = True
                        df.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
                        st.rerun()

        st.markdown("---")