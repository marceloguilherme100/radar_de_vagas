import os
import re
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

ARQUIVO_CSV = "vagas.csv"

# Regex para competências e aderência
SKILLS_REGEX = {
    "Suporte / Helpdesk": r"\bsuporte\b|\bhelpdesk\b|\bservice desk\b|\bn1\b|\bn2\b|\bt[eé]cnico de inform[aá]tica\b",
    "Infraestrutura / Redes": r"\binfraestrutura\b|\bredes\b|\bhardware\b|\bactive directory\b|\bmikrotik\b",
    "Windows / Linux": r"\bwindows\b|\blinux\b|\bsysprep\b|\bclonezilla\b",
    "Python": r"\bpython\b",
    "SQL / Banco de Dados": r"\bsql\b|\bbanco de dados\b|\bmysql\b|\bpostgres\b",
    "Desenvolvimento / Dev": r"\bdesenvolvedor\b|\bprogramador\b|\bsoftware\b|\bdev\b|\bfrontend\b|\bbackend\b|\bfullstack\b",
    "C / C++": r"\bc\+\+\b|\blinguagem c\b",
    "Automação / RPA": r"\bautoma[cç][aã]o\b|\brpa\b"
}

# Termos para identificar o Polo Industrial
POLO_KEYWORDS = [
    "suape", "cabo de santo agostinho", "cabo", "ipojuca", 
    "porto de suape", "complexo de suape", "complexo industrial", 
    "indústria", "industria", "estaleiro", "refinaria"
]

# Regex seguro para cidades e sigla de Pernambuco
PADRAO_PE = re.compile(
    r"\b(recife|jaboat[aã]o|olinda|paulista|cabo de santo agostinho|ipojuca|suape|camaragibe|abreu e lima|igarassu|s[aã]o louren[cç]o|caruaru|petrolina|pernambuco)\b|"
    r"(\bpe\b|[\-_/]pe[\-_/.]|,\s*pe\b)",
    re.IGNORECASE
)

# Regex para detectar explicitamente outros estados
PADRAO_OUTROS_ESTADOS = re.compile(
    r"(\b(sc|sp|rj|mg|rs|pr|ba|ce|df|es|go|ma|mt|ms|pa|pb|pi|rn|ro|rr|se|to|am|ac|al|ap)\b|"
    r"[\-_/](sc|sp|rj|mg|rs|pr|ba|ce|df|es|go|ma|mt|ms|pa|pb|pi|rn|ro|rr|se|to|am|ac|al|ap)[\-_/.])",
    re.IGNORECASE
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def classificar_area(titulo):
    t = titulo.lower()
    dev_keywords = ["desenvolvedor", "programador", "software", "dev", "frontend", "backend", "fullstack", "python", "web"]
    if any(k in t for k in dev_keywords):
        return "Desenvolvimento"
    return "Suporte / TI"

def extrair_modalidade_e_tipo(titulo, local, empresa):
    texto = f"{titulo} {local} {empresa}".lower()
    
    is_remoto = any(k in texto for k in ["remoto", "remote", "home office", "teletrabalho"])
    modalidade = "Remoto" if is_remoto else "Presencial"
    
    pertence_polo = any(k in texto for k in POLO_KEYWORDS)
    tipo = "Polo Industrial" if (pertence_polo and not is_remoto) else ("Remoto" if is_remoto else "Metropolitana / Recife")
    
    return modalidade, tipo

def extrair_tags_e_aderencia(titulo, requisitos):
    texto = f"{titulo} {requisitos}".lower()
    tags = [nome for nome, regex in SKILLS_REGEX.items() if re.search(regex, texto, re.IGNORECASE)]
    score = min(0.98, 0.65 + (len(tags) * 0.08)) if tags else 0.50
    return round(score, 2), ", ".join(tags[:3]) if tags else "TI Geral"

def limpar_link(url_bruta):
    parsed = urllib.parse.urlparse(url_bruta)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def vaga_ainda_ativa(url_vaga):
    try:
        res = requests.get(url_vaga, headers=HEADERS, timeout=6, allow_redirects=True)
        if res.status_code != 200:
            return False
        
        texto_pagina = res.text.lower()
        termos_fechada = [
            "não aceita mais candidaturas",
            "nao aceita mais candidaturas",
            "no longer accepting applications",
            "closed-job",
            "closed_job",
            "topcard__flavor--closed",
            "job-details-jobs-unified-top-card__closed-message"
        ]
        return not any(termo in texto_pagina for termo in termos_fechada)
    except Exception:
        return True

def validar_localidade_pe(modalidade, local_texto, link):
    if modalidade == "Remoto":
        return True
    
    analise = f"{local_texto} {link}".lower()
    tem_pe = bool(PADRAO_PE.search(analise))
    tem_outro = bool(PADRAO_OUTROS_ESTADOS.search(analise))
    
    return tem_pe and not (tem_outro and not tem_pe)

# ==========================================
# FONTE 1: LINKEDIN
# ==========================================
def raspar_linkedin(cargo, localidade, apenas_remoto=False):
    vagas = []
    q_enc = urllib.parse.quote(cargo)
    loc_enc = urllib.parse.quote(localidade)
    
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q_enc}&location={loc_enc}&f_TPR=r259200&start=0"
    if apenas_remoto:
        url += "&f_WT=2"
        
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return vagas
        soup = BeautifulSoup(res.text, "html.parser")
        
        for card in soup.find_all("li"):
            tit_elem = card.find("h3", class_="base-search-card__title")
            emp_elem = card.find("h4", class_="base-search-card__subtitle")
            loc_elem = card.find("span", class_="job-search-card__location")
            lnk_elem = card.find("a", class_="base-card__full-link")
            
            if tit_elem and emp_elem and lnk_elem:
                link = limpar_link(lnk_elem["href"])
                
                if not vaga_ainda_ativa(link):
                    continue
                    
                titulo = tit_elem.get_text(strip=True)
                empresa = emp_elem.get_text(strip=True)
                local = loc_elem.get_text(strip=True) if loc_elem else localidade
                
                modalidade, tipo = extrair_modalidade_e_tipo(titulo, local, empresa)
                if apenas_remoto:
                    modalidade = "Remoto"
                    tipo = "Remoto"
                
                # Bloqueia vagas presenciais fora de PE
                if not validar_localidade_pe(modalidade, local, link):
                    continue
                
                vagas.append({
                    "titulo": titulo,
                    "empresa": empresa,
                    "local": "Remoto (Brasil)" if modalidade == "Remoto" else local,
                    "tipo": tipo,
                    "modalidade": modalidade,
                    "area": classificar_area(titulo),
                    "fonte": "LinkedIn",
                    "link": link
                })
    except Exception as e:
        print(f"Erro LinkedIn ({cargo}): {e}")
    return vagas

# ==========================================
# FONTE 2: INFOJOBS
# ==========================================
def raspar_infojobs(termo_busca, uf="pe"):
    vagas = []
    slug_termo = termo_busca.lower().strip().replace(" ", "-")
    url = f"https://www.infojobs.com.br/vagas-de-emprego-{slug_termo}-em-{uf}.aspx"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return vagas
            
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.find_all("div", class_=lambda c: c and "js_vacancy" in c) or soup.find_all("div", attrs={"data-js": "vacancy-item"})
        
        for card in cards:
            tit_elem = card.find("h2") or card.find("a", class_=lambda c: c and "title" in c)
            emp_elem = card.find("div", class_=lambda c: c and "company" in c) or card.find("a", class_=lambda c: c and "company" in c)
            loc_elem = (
                card.find("span", class_=lambda c: c and "location" in c) or
                card.find("div", class_=lambda c: c and "location" in c) or
                card.find("div", class_=lambda c: c and "city" in c)
            )
            lnk_elem = card.find("a", href=True)
            
            if tit_elem and lnk_elem:
                titulo = tit_elem.get_text(strip=True)
                empresa = emp_elem.get_text(strip=True) if emp_elem else "Empresa Confidencial"
                local_real = loc_elem.get_text(strip=True) if loc_elem else ""
                
                link_rel = lnk_elem["href"]
                link_comp = link_rel if link_rel.startswith("http") else f"https://www.infojobs.com.br{link_rel}"
                link_limpo = limpar_link(link_comp)
                
                modalidade, tipo = extrair_modalidade_e_tipo(titulo, local_real, empresa)
                
                # Bloqueia vagas de fora de PE
                if not validar_localidade_pe(modalidade, local_real, link_limpo):
                    continue
                
                vagas.append({
                    "titulo": titulo,
                    "empresa": empresa,
                    "local": "Remoto (Brasil)" if modalidade == "Remoto" else (local_real if local_real else "Recife e Região, PE"),
                    "tipo": tipo,
                    "modalidade": modalidade,
                    "area": classificar_area(titulo),
                    "fonte": "InfoJobs",
                    "link": link_limpo
                })
    except Exception as e:
        print(f"Erro InfoJobs ({termo_busca}): {e}")
        
    return vagas

# ==========================================
# FONTE 3: GUPY
# ==========================================
def raspar_gupy(termo_busca):
    vagas = []
    url = f"https://portal.api.gupy.io/api/v1/jobs?jobName={urllib.parse.quote(termo_busca)}&limit=25"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return vagas
            
        dados = res.json()
        for item in dados.get("data", []):
            titulo = item.get("name", "")
            empresa = item.get("careerPageName", "Empresa via Gupy")
            cidade = item.get("city", "")
            estado = item.get("state", "")
            is_remoto = item.get("isRemoteWork", False)
            link = item.get("jobUrl", "")
            
            local_str = f"{cidade} - {estado}" if cidade else ("Remoto" if is_remoto else "Brasil")
            modalidade, tipo = extrair_modalidade_e_tipo(titulo, local_str, empresa)
            if is_remoto:
                modalidade = "Remoto"
                tipo = "Remoto"
            
            # Bloqueia vagas presenciais fora de PE
            if not validar_localidade_pe(modalidade, local_str, link):
                continue

            vagas.append({
                "titulo": titulo,
                "empresa": empresa,
                "local": "Remoto (Brasil)" if modalidade == "Remoto" else local_str,
                "tipo": tipo,
                "modalidade": modalidade,
                "area": classificar_area(titulo),
                "fonte": "Gupy",
                "link": link
            })
    except Exception as e:
        print(f"Erro Gupy ({termo_busca}): {e}")
    return vagas

# ==========================================
# COORDENADOR GERAL
# ==========================================


def atualizar_banco():
    todas = []
    print("🚀 Buscando vagas em múltiplas plataformas...")

    buscas_linkedin = [
        {"cargo": "Tecnico de Suporte", "local": "Pernambuco, Brazil", "remoto": False},
        {"cargo": "Tecnico de Informatica", "local": "Pernambuco, Brazil", "remoto": False},
        {"cargo": "Suporte TI", "local": "Recife, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Analista de Suporte", "local": "Recife, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Suporte Tecnico", "local": "Cabo de Santo Agostinho, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Suporte", "local": "Ipojuca, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Desenvolvedor", "local": "Recife, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Tecnico de Suporte Remoto", "local": "Brazil", "remoto": True},
        {"cargo": "Analista de Suporte Remoto", "local": "Brazil", "remoto": True},
        {"cargo": "Desenvolvedor Python", "local": "Brazil", "remoto": True},
        {"cargo": "Desenvolvedor Junior", "local": "Brazil", "remoto": True}
    ]
    for b in buscas_linkedin:
        todas.extend(raspar_linkedin(b["cargo"], b["local"], b["remoto"]))

    termos_gupy = ["Suporte TI", "Analista TI", "Técnico de Informática", "Desenvolvedor", "Python", "Redes"]
    for termo in termos_gupy:
        todas.extend(raspar_gupy(termo))

    termos_infojobs = ["suporte ti", "tecnico informatica", "analista suporte", "analista ti", "desenvolvedor"]
    for termo in termos_infojobs:
        todas.extend(raspar_infojobs(termo, uf="pe"))

    colunas_padrao = [
        "id", "titulo", "empresa", "local", "tipo",
        "modalidade", "area", "fonte", "aderencia", "tags", "link", "enviada"
    ]

    enviadas_prev = {}
    if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
        try:
            df_old = pd.read_csv(ARQUIVO_CSV)
            if "link" in df_old.columns and "enviada" in df_old.columns:
                enviadas_prev = df_old.set_index("link")["enviada"].to_dict()
        except Exception:
            pass

    vistas = set()
    processadas = []
    id_n = 1

    for v in todas:
        chave = f"{v['titulo'].lower().strip()}_{v['empresa'].lower().strip()}"
        if chave in vistas or v["link"] in vistas:
            continue
        vistas.add(chave)
        vistas.add(v["link"])

        aderencia, tags = extrair_tags_e_aderencia(v["titulo"], v["titulo"])
        processadas.append({
            "id": id_n,
            "titulo": v["titulo"],
            "empresa": v["empresa"],
            "local": v["local"],
            "tipo": v["tipo"],
            "modalidade": v["modalidade"],
            "area": v["area"],
            "fonte": v.get("fonte", "Outros"),
            "aderencia": aderencia,
            "tags": tags,
            "link": v["link"],
            "enviada": bool(enviadas_prev.get(v["link"], False))
        })
        id_n += 1

    if not processadas:
        print("⚠️ Nenhuma vaga nova capturada nos filtros. Preservando banco existente.")
        if not os.path.exists(ARQUIVO_CSV) or os.path.getsize(ARQUIVO_CSV) == 0:
            pd.DataFrame(columns=colunas_padrao).to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
        return

    df_novo = pd.DataFrame(processadas)
    df_novo.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
    print(f"✅ Banco consolidado com {len(df_novo)} vagas ativas e categorizadas.")

if __name__ == "__main__":
    atualizar_banco()