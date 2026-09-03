import os
import re
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

ARQUIVO_CSV = "vagas.csv"

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def classificar_area(titulo):
    t = titulo.lower()
    dev_keywords = ["desenvolvedor", "programador", "software", "dev", "frontend", "backend", "fullstack", "python", "web"]
    if any(k in t for k in dev_keywords):
        return "Desenvolvimento"
    return "Suporte / TI"

def extrair_tags_e_aderencia(titulo, requisitos):
    texto = f"{titulo} {requisitos}".lower()
    tags = [nome for nome, regex in SKILLS_REGEX.items() if re.search(regex, texto, re.IGNORECASE)]
    score = min(0.98, 0.65 + (len(tags) * 0.08)) if tags else 0.50
    return round(score, 2), ", ".join(tags[:3]) if tags else "TI Geral"

def limpar_link(url_bruta):
    parsed = urllib.parse.urlparse(url_bruta)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

# ==========================================
# FONTE 1: LINKEDIN
# ==========================================
def raspar_linkedin(cargo, localidade, apenas_remoto=False):
    vagas = []
    q_enc = urllib.parse.quote(cargo)
    loc_enc = urllib.parse.quote(localidade)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q_enc}&location={loc_enc}&start=0"
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
                titulo = tit_elem.get_text(strip=True)
                empresa = emp_elem.get_text(strip=True)
                local = loc_elem.get_text(strip=True) if loc_elem else localidade
                link = limpar_link(lnk_elem["href"])
                
                is_remoto = apenas_remoto or any(k in f"{local} {titulo}".lower() for k in ["remoto", "remote", "home office"])
                tipo = "Indústria" if any(k in f"{local} {empresa}".lower() for k in ["suape", "cabo", "ipojuca", "porto", "indústria"]) else "Geral"
                
                vagas.append({
                    "titulo": titulo,
                    "empresa": empresa,
                    "local": local if not is_remoto else "Remoto (Brasil)",
                    "tipo": tipo,
                    "modalidade": "Remoto" if is_remoto else "Presencial",
                    "area": classificar_area(titulo),
                    "link": link
                })
    except Exception as e:
        print(f"Erro LinkedIn ({cargo}): {e}")
    return vagas

# ==========================================
# FONTE 2: GUPY (API Pública da Gupy)
# ==========================================
def raspar_gupy(termo_busca):
    vagas = []
    # A Gupy possui um endpoint aberto de busca que retorna JSON direto
    url = f"https://portal.api.gupy.io/api/v1/jobs?jobName={urllib.parse.quote(termo_busca)}&limit=20"
    
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
            
            # Filtro de localidade: Remoto OU Pernambuco/RMR
            local_lower = f"{local_str} {cidade} {estado}".lower()
            valido_local = any(c in local_lower for c in ["recife", "cabo", "ipojuca", "suape", "pernambuco", "pe", "jaboatão"])
            
            if not (is_remoto or valido_local):
                continue

            tipo = "Indústria" if any(k in f"{local_str} {empresa}".lower() for k in ["suape", "cabo", "ipojuca", "indústria"]) else "Geral"

            vagas.append({
                "titulo": titulo,
                "empresa": empresa,
                "local": "Remoto (Brasil)" if is_remoto else local_str,
                "tipo": tipo,
                "modalidade": "Remoto" if is_remoto else "Presencial",
                "area": classificar_area(titulo),
                "link": link
            })
    except Exception as e:
        print(f"Erro Gupy ({termo_busca}): {e}")
    return vagas

# ==========================================
# COORDENADOR DE ATUALIZAÇÃO
# ==========================================
def atualizar_banco():
    todas = []
    print("🚀 Buscando vagas em múltiplas plataformas...")

    # 1. Buscas no LinkedIn
    buscas_linkedin = [
        {"cargo": "Suporte TI", "local": "Recife, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Analista de TI", "local": "Recife, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Técnico de Informática", "local": "Pernambuco, Brazil", "remoto": False},
        {"cargo": "Suporte TI", "local": "Cabo de Santo Agostinho, Pernambuco, Brazil", "remoto": False},
        {"cargo": "Desenvolvedor Python", "local": "Brazil", "remoto": True},
        {"cargo": "Desenvolvedor Júnior", "local": "Brazil", "remoto": True}
    ]
    for b in buscas_linkedin:
        todas.extend(raspar_linkedin(b["cargo"], b["local"], b["remoto"]))

    # 2. Buscas na Gupy
    termos_gupy = ["Suporte TI", "Analista TI", "Técnico de Informática", "Desenvolvedor", "Python"]
    for termo in termos_gupy:
        todas.extend(raspar_gupy(termo))

    # Recupera enviadas anteriores
    enviadas_prev = {}
    if os.path.exists(ARQUIVO_CSV):
        try:
            df_old = pd.read_csv(ARQUIVO_CSV)
            enviadas_prev = df_old.set_index("link")["enviada"].to_dict()
        except Exception:
            pass

    # Deduplicação
    vistas = set()
    processadas = []
    id_n = 1

    for v in todas:
        chave = f"{v['titulo'].lower()}_{v['empresa'].lower()}"
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
            "aderencia": aderencia,
            "tags": tags,
            "link": v["link"],
            "enviada": bool(enviadas_prev.get(v["link"], False))
        })
        id_n += 1

    df_novo = pd.DataFrame(processadas)
    df_novo.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
    print(f"✅ Banco consolidado com {len(df_novo)} vagas ativas (LinkedIn + Gupy).")

if __name__ == "__main__":
    atualizar_banco()