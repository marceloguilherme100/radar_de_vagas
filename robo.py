import os
import re
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

ARQUIVO_CSV = "vagas.csv"

# 1. Habilidades com correspondência exata via Regex
SKILLS_REGEX = {
    "Suporte": r"\bsuporte\b|\bhelpdesk\b|\bservice desk\b|\bn1\b|\bn2\b",
    "Infraestrutura": r"\binfraestrutura\b|\bredes\b|\bhardware\b|\bactive directory\b|\bglpi\b|\bmikrotik\b",
    "Windows/Linux": r"\bwindows\b|\blinux\b|\bsysprep\b|\bclonezilla\b",
    "Python": r"\bpython\b",
    "SQL / Banco de Dados": r"\bsql\b|\bbanco de dados\b|\bpostgres\b|\bmysql\b",
    "Automação / RPA": r"\bautoma[cç][aã]o\b|\brpa\b",
    "Desenvolvimento": r"\bdesenvolvedor\b|\bprogramador\b|\bsoftware\b|\bdev\b|\bapi\b",
    "C / C++": r"\bc\+\+\b|\blinguagem c\b|\bprogramador c\b",
    "Excel / BI": r"\bexcel\b|\bbi\b|\bpower bi\b|\bdados\b"
}

# 2. Configurações de busca: Presencial regional + Remoto em todo o Brasil
SEARCH_QUERIES = [
    # --- REGIONAL (Presencial / Polo Industrial) ---
    {"cargo": "Suporte TI", "local": "Recife, Pernambuco, Brazil", "remoto_apenas": False},
    {"cargo": "Analista de Suporte", "local": "Cabo de Santo Agostinho, Pernambuco, Brazil", "remoto_apenas": False},
    {"cargo": "Infraestrutura TI", "local": "Ipojuca, Pernambuco, Brazil", "remoto_apenas": False},
    {"cargo": "TI Suape", "local": "Pernambuco, Brazil", "remoto_apenas": False},
    {"cargo": "Help Desk", "local": "Recife e Regiao, Brasil", "remoto_apenas": False},
    
    # --- BRASIL TODO (100% Remoto) ---
    {"cargo": "Desenvolvedor Python Remoto", "local": "Brazil", "remoto_apenas": True},
    {"cargo": "Analista de Suporte Remoto", "local": "Brazil", "remoto_apenas": True},
    {"cargo": "Desenvolvedor Júnior Remoto", "local": "Brazil", "remoto_apenas": True},
    {"cargo": "Automação Python Remoto", "local": "Brazil", "remoto_apenas": True}
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Cidades permitidas para trabalho presencial / híbrido
CIDADES_LOCAIS = [
    "recife", "cabo", "ipojuca", "suape", "jaboatão", "jaboatao", "olinda", 
    "paulista", "abreu e lima", "igarassu", "camaragibe", "são lourenço", 
    "sao lourenco", "greater recife", "pernambuco"
]

def extrair_tags_e_aderencia(titulo, texto_requisitos):
    texto_completo = f"{titulo} {texto_requisitos}".lower()
    
    tags_encontradas = []
    for nome_skill, padrao in SKILLS_REGEX.items():
        if re.search(padrao, texto_completo, re.IGNORECASE):
            tags_encontradas.append(nome_skill)
            
    aderencia_base = 0.65 if any(t in ["Suporte", "Infraestrutura", "Python", "Desenvolvimento"] for t in tags_encontradas) else 0.40
    score = min(0.98, aderencia_base + (len(tags_encontradas) * 0.07))
    
    tags_formatadas = ", ".join(tags_encontradas[:3]) if tags_encontradas else "TI Geral"
    return round(score, 2), tags_formatadas

def raspar_linkedin(cargo, localidade, apenas_remoto=False):
    vagas_encontradas = []
    query_encoded = urllib.parse.quote(cargo)
    location_encoded = urllib.parse.quote(localidade)
    
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query_encoded}&location={location_encoded}&start=0"
    if apenas_remoto:
        url += "&f_WT=2"  # Filtro oficial de vagas remotas do LinkedIn
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return vagas_encontradas
        
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.find_all("li")
        
        for card in cards:
            titulo_elem = card.find("h3", class_="base-search-card__title")
            empresa_elem = card.find("h4", class_="base-search-card__subtitle")
            local_elem = card.find("span", class_="job-search-card__location")
            link_elem = card.find("a", class_="base-card__full-link")
            
            if titulo_elem and empresa_elem and link_elem:
                titulo = titulo_elem.get_text(strip=True)
                empresa = empresa_elem.get_text(strip=True)
                local = local_elem.get_text(strip=True) if local_elem else localidade
                link = link_elem["href"].split("?")[0]
                
                local_lower = local.lower()
                titulo_lower = titulo.lower()
                
                # Identifica se a vaga é remota
                is_remoto = (
                    apenas_remoto or 
                    any(t in local_lower or t in titulo_lower for t in ["remoto", "remote", "teletrabalho", "home office", "home-office"])
                )
                
                # Identifica se a vaga é presencial na região de interesse
                is_local_pe = any(cidade in local_lower for cidade in CIDADES_LOCAIS)
                
                # REGRA CENTRAL: Aceita se for Remoto (qualquer lugar do Brasil) OU Presencial em PE
                if not (is_remoto or is_local_pe):
                    continue  # Descarta presencial fora de PE (ex: SP, MG, BA)
                    
                # Filtro de relevância de TI
                termos_ti = ["suporte", "ti", "t.i", "infra", "infraestrutura", "desenvolvedor", "programador", "python", "software", "dados", "rpa", "helpdesk", "help desk", "sistemas"]
                if not any(termo in titulo_lower for termo in termos_ti):
                    continue

                # Definições de exibição
                tipo = "Indústria" if any(ind in f"{titulo} {empresa} {local}".lower() for ind in ["suape", "cabo", "ipojuca", "porto", "logística", "indústria", "dislub", "baterias"]) else "Tecnologia / Serviços"
                modalidade = "Remoto" if is_remoto else "Presencial"
                
                vagas_encontradas.append({
                    "titulo": titulo,
                    "empresa": empresa,
                    "local": local if not is_remoto else "Remoto (Brasil)",
                    "tipo": tipo,
                    "modalidade": modalidade,
                    "requisitos": f"{cargo} {titulo}",
                    "link": link
                })
    except Exception as e:
        print(f"⚠️ Erro ao consultar '{cargo}': {e}")
        
    return vagas_encontradas

def atualizar_banco():
    todas_vagas = []
    print("🚀 Caçando vagas: Remoto (Brasil) + Presencial (Recife, Cabo, Ipojuca, Suape)...")
    
    for busca in SEARCH_QUERIES:
        print(f"🔎 Buscando: {busca['cargo']}...")
        vagas = raspar_linkedin(busca["cargo"], busca["local"], busca["remoto_apenas"])
        todas_vagas.extend(vagas)
    
    if not todas_vagas:
        print("⚠️ Nenhuma vaga retornada.")
        return

    lista_processada = []
    links_vistos = set()
    id_counter = 1
    
    for item in todas_vagas:
        if item["link"] in links_vistos:
            continue
        links_vistos.add(item["link"])
        
        aderencia, tags = extrair_tags_e_aderencia(item["titulo"], item["requisitos"])
        
        lista_processada.append({
            "id": id_counter,
            "titulo": item["titulo"],
            "empresa": item["empresa"],
            "local": item["local"],
            "tipo": item["tipo"],
            "modalidade": item["modalidade"],
            "aderencia": aderencia,
            "tags": tags,
            "link": item["link"],
            "enviada": False
        })
        id_counter += 1

    df_novas = pd.DataFrame(lista_processada)
    
    # Preserva histórico de vagas enviadas
    if os.path.exists(ARQUIVO_CSV):
        try:
            df_antigo = pd.read_csv(ARQUIVO_CSV)
            enviadas_map = df_antigo.set_index("link")["enviada"].to_dict()
            df_novas["enviada"] = df_novas["link"].map(enviadas_map).fillna(False)
        except Exception:
            pass

    df_novas.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8")
    print(f"✅ Concluído! {len(df_novas)} vagas consolidadas em '{ARQUIVO_CSV}'.")

if __name__ == "__main__":
    atualizar_banco()