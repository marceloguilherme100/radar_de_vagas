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
    st.info("Banco de dados vazio. Clique no botão abaixo para buscar as vagas.")
    if st.button("🔄 Buscar Vagas Agora", type="primary"):
        with st.spinner("Varrendo LinkedIn, Gupy e InfoJobs..."):
            atualizar_banco()
        st.rerun()
    st.stop()

df = pd.read_csv(ARQUIVO_CSV)

# Garante a integridade das colunas
if "area" not in df.columns:
    df["area"] = df["titulo"].apply(
        lambda t: "Desenvolvimento" if any(k in str(t).lower() for k in ["dev", "programador", "software", "python", "frontend", "backend", "fullstack"]) else "Suporte / TI"
    )

if "enviada" not in df.columns:
    df["enviada"] = False
else:
    df["enviada"] = df["enviada"].fillna(False).astype(bool)

if "tipo" not in df.columns:
    df["tipo"] = "Metropolitana / Recife"

if "modalidade" not in df.columns:
    df["modalidade"] = df["local"].apply(
        lambda l: "Remoto" if any(k in str(l).lower() for k in ["remoto", "remote", "home office"]) else "Presencial"
    )

if "tags" not in df.columns:
    df["tags"] = "TI Geral"
if "aderencia" not in df.columns:
    df["aderencia"] = 0.70

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

# FILTRO TERRITORIAL ESTRITO:
# Presenciais devem ser exclusivamente de Pernambuco; vagas de outros estados só entram se forem remotas.
CIDADES_PE = [
    "recife", "jaboatão", "jaboatao", "olinda", "paulista", 
    "cabo de santo agostinho", "cabo", "ipojuca", "suape", 
    "camaragibe", "abreu e lima", "igarassu", "são lourenço", 
    "caruaru", "petrolina", "pernambuco", "pe"
]

def validar_territorio(linha):
    if linha["modalidade"] == "Remoto":
        return True
    local = str(linha["local"]).lower()
    return any(c in local for c in CIDADES_PE)

df = df[df.apply(validar_territorio, axis=1)].copy()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Todas"

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

# SEPARAÇÃO MUTUAMENTE EXCLUSIVA
ativas_df = df[df["enviada"] == False].copy()

# 1. Apenas Remotas
df_remoto = ativas_df[ativas_df["modalidade"] == "Remoto"]

# 2. Apenas Polo Industrial (Cabo, Ipojuca, Suape - Presencial)
df_polo = ativas_df[(ativas_df["tipo"] == "Polo Industrial") & (ativas_df["modalidade"] != "Remoto")]

# 3. Suporte / TI Presencial (Recife e Região Metropolitana, fora Polo)
df_suporte = ativas_df[(ativas_df["area"] == "Suporte / TI") & (ativas_df["modalidade"] != "Remoto") & (ativas_df["tipo"] != "Polo Industrial")]

# 4. Dev / Programação Presencial (Recife e Região)
df_dev = ativas_df[(ativas_df["area"] == "Desenvolvimento") & (ativas_df["modalidade"] != "Remoto")]

# 5. Enviadas
df_enviadas = df[df["enviada"] == True].copy()

# Contadores
total_ativas = len(ativas_df)
suporte_cnt = len(df_suporte)
dev_cnt = len(df_dev)
remoto_cnt = len(df_remoto)
industria_cnt = len(df_polo)
enviadas_cnt = len(df_enviadas)

# Cabeçalho Principal integrado com botão de sincronização
col_titulo, col_btn = st.columns([4, 1.2])

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

# Cards de Categorias no Topo
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

# Lógica de Filtragem e Exibição
if st.session_state.pagina_atual == "Enviadas":
    st.subheader(f"📤 Candidaturas Realizadas ({enviadas_cnt})")
    df_exibicao = df_enviadas
elif st.session_state.pagina_atual == "Suporte":
    st.subheader(f"🛠️ Suporte & Infraestrutura - Presencial Recife / RMR ({suporte_cnt})")
    df_exibicao = df_suporte
elif st.session_state.pagina_atual == "Dev":
    st.subheader(f"💻 Programação & Software - Presencial Recife / RMR ({dev_cnt})")
    df_exibicao = df_dev
elif st.session_state.pagina_atual == "Remoto":
    st.subheader(f"🏠 Oportunidades Estritamente Remotas ({remoto_cnt})")
    df_exibicao = df_remoto
elif st.session_state.pagina_atual == "Indústria":
    st.subheader(f"🏭 Polo Industrial / Suape / Cabo / Ipojuca ({industria_cnt})")
    df_exibicao = df_polo
else:
    st.subheader(f"📋 Todas as Vagas Disponíveis ({total_ativas})")
    df_exibicao = ativas_df

if st.session_state.pagina_atual != "Todas":
    if st.button("⬅️ Ver Todas as Vagas"):
        st.session_state.pagina_atual = "Todas"
        st.rerun()

df_exibicao = df_exibicao.sort_values(by="aderencia", ascending=False)

if df_exibicao.empty:
    st.info("Nenhuma vaga encontrada nesta categoria no momento.")
else:
    for _, vaga in df_exibicao.iterrows():
        fonte = vaga["fonte"]
        classe_fonte = "badge-linkedin" if fonte == "LinkedIn" else ("badge-gupy" if fonte == "Gupy" else "badge-infojobs")
        icone_cargo = "💻" if vaga.get("area") == "Desenvolvimento" else "🛠️"
        
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

        porc = int(vaga['aderencia'] * 100)
        st.progress(float(vaga['aderencia']), text=f"Match com perfil: {porc}% • Tags: {vaga['tags']}")

        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
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