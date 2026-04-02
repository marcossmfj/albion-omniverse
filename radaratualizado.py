import streamlit as st
import requests
import pandas as pd
import time
import math

# ==========================================
# 1. CONFIGURAÇÕES - DARK MODE TERMINAL ELITE
# ==========================================
st.set_page_config(
    page_title="Albion Omniverse God Mode",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Customizado (Design Moderno, Leve, Premium) ---
st.markdown("""
<style>
.main { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
h1, h2, h3, h5 { color: #58a6ff !important; font-weight: 800; }
.stCaption { color: #8b949e !important; }
.stButton>button {
    background-color: #1f6feb !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: bold !important; transition: all 0.2s ease;
    box-shadow: 0 4px 10px rgba(31, 111, 235, 0.3) !important;
    width: 100% !important; height: 50px !important; font-size: 1.1rem !important;
}
.stButton>button:hover { background-color: #15469a !important; transform: translateY(-2px); box-shadow: 0 6px 15px rgba(31, 111, 235, 0.4) !important; }
[data-testid="stSidebar"] .stButton>button { height: 35px !important; font-size: 0.9rem !important; margin-top: 15px; }
div[data-testid="metric-container"] {
    background-color: #161b22; border: 1px solid #30363d;
    padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.4);
}
[data-testid="stMetricLabel"] { color: #8b949e; font-size: 0.9rem; font-weight: 500; }
[data-testid="stMetricValue"] { color: #00FF41 !important; font-weight: 900; font-size: 2.2rem; }
div.stDataFrame { border: 1px solid #30363d; border-radius: 8px; overflow: hidden; background-color: #0d1117; }
</style>
""", unsafe_allow_html=True)

TAXA_MERCADO = 0.08
CIDADES_ROYAL = ["Martlock", "Caerleon", "Thetford", "Fort Sterling", "Lymhurst", "Bridgewatch", "Brecilien"]
CIDADES_DESTINO = CIDADES_ROYAL + ["Black Market"]
MAPA_SERVIDORES = { "Américas (West)": "west", "Europa (Europe)": "europe", "Ásia (East)": "east" }

# ==========================================
# 2. INTELIGÊNCIA ARTIFICIAL: PESO E PRATA
# ==========================================
def formatar_prata(valor):
    try:
        valor = float(valor)
        if valor >= 1_000_000: return f"{valor/1_000_000:.2f}M"
        if valor >= 1_000: return f"{valor/1000:.0f}K"
        return str(int(valor))
    except: return str(valor)

# Inteligência de Peso por Kg
def calcular_peso_item(item_id):
    tier_str = item_id.split("_")[0].replace("T", "")
    tier = int(tier_str) if tier_str.isdigit() else 4
    if "MOUNT_MAMMOTH" in item_id: return 134.0
    if "MOUNT_OX" in item_id: return tier * 5.0
    if "MOUNT" in item_id: return tier * 3.0
    if any(x in item_id for x in ["WOOD", "ROCK", "ORE", "HIDE", "FIBER", "PLANKS", "METALBAR", "LEATHER", "CLOTH"]):
        return tier * 0.5
    return tier * 1.2 # Armas, Roupas e Capas

def rendering_sidebar_header():
    fogo_svg = '<svg viewBox="0 0 24 24" style="width:28px;height:28px;fill:#ff9a00;margin-right:8px;"><path d="M11.9,1.1c-0.2-0.2-0.6-0.2-0.8,0l-0.8,0.8C6.9,5.2,5.2,8,5.2,11.3c0,3.7,3,6.7,6.7,6.7s6.7-3,6.7-6.7c0-3.3-1.7-6.1-4.1-9.4L11.9,1.1z M12,16.2c-2.7,0-4.9-2.2-4.9-4.9c0-1.2,0.4-2.2,1-3c1.1-1.4,2.8-2.3,4.7-2.3c0.1,0,0.2,0,0.3,0v0c1.7,0.1,3.2,1.1,4.1,2.5c0.6,0.9,0.9,1.9,0.9,3.1C16.9,14,14.7,16.2,12,16.2z"></path></svg>'
    st.sidebar.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:15px; border-bottom:1px solid #30363d; padding-bottom:15px;">
            {fogo_svg}
            <span style="font-weight:900; font-size:1.5rem; color:white;">Omniverse <span style="color:#58a6ff">GOD MODE</span></span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. DICIONÁRIO & MATRIZ T4-T8.4
# ==========================================
DICIONARIO_PTBR = {
    "MOUNT_COUGAR_KEEPER":"Garra-ligeira", "MOUNT_DIREWOLF":"Lobo-vil", "MOUNT_WILD_BOAR":"Javali Selado",
    "MOUNT_MAMMOTH_TRANSPORT":"Mamute", "MOUNT_HORSE":"Cavalo", "MOUNT_OX":"Boi", "WOOD":"Madeira",
    "ROCK":"Pedra", "ORE":"Minério", "HIDE":"Pelego", "FIBER":"Fibra", "CLOTH":"Tecido",
    "METALBAR":"Barra", "PLANKS":"Tábua", "LEATHER":"Couro", "STONEBLOCK":"Bloco", "CAPE":"Capa",
    "BAG":"Bolsa", "MAIN_DAGGER_MAGIC":"Sangra-letal", "MAIN_CURSEDSTAFF_AVALON":"Inv. Sombras",
    "2H_BOW_KEEPER":"Arco Badon", "2H_HALBERD_MORGANA":"Foice", "MAIN_NATURESTAFF_KEEPER":"Cajado Praga"
}

def formatar_nome_item(item_id):
    tier = item_id.split("_")[0] if "_" in item_id else "T?"
    enc = item_id.split("@")[1] if "@" in item_id else "0"
    item_base = item_id.split("@")[0].replace(f"{tier}_", "", 1)
    nome_pt = DICIONARIO_PTBR.get(item_base, item_base.replace("_", " "))
    return f"{nome_pt} {tier}.{enc}", tier, enc

def gerar_matriz(lista, min_t=4, max_t=8, max_e=4):
    res = []
    for item in lista:
        for t in range(min_t, max_t + 1):
            base = f"T{t}_{item}"
            res.append(base)
            for e in range(1, max_e + 1): res.append(f"{base}@{e}")
    return res

# ==========================================
# 4. CATEGORIAS DE ARBITRAGEM
# ==========================================
CATEGORIAS = {
    "🐎 Montarias": [f"T{t}_MOUNT_HORSE" for t in range(3,9)] + [f"T{t}_MOUNT_OX" for t in range(3,9)] + ["T5_MOUNT_COUGAR_KEEPER", "T6_MOUNT_DIREWOLF", "T8_MOUNT_MAMMOTH_TRANSPORT"],
    "⚔️ Armas Meta": gerar_matriz(["MAIN_DAGGER_MAGIC", "2H_DUALAXE_KEEPER", "MAIN_CURSEDSTAFF_AVALON", "2H_BOW_KEEPER", "MAIN_NATURESTAFF_KEEPER"], 4, 8, 4),
    "⛏️ Roupas Coleta": gerar_matriz(["HEAD_GATHERER_WOOD", "ARMOR_GATHERER_WOOD", "SHOES_GATHERER_WOOD", "HEAD_GATHERER_ROCK", "ARMOR_GATHERER_ROCK", "SHOES_GATHERER_ROCK"], 4, 8, 0),
    "🧱 Brutos": gerar_matriz(["WOOD", "ROCK", "ORE", "HIDE", "FIBER"], 4, 8, 4),
    "🛡️ Capas & Refinados": gerar_matriz(["CAPE", "BAG", "CLOTH", "METALBAR", "PLANKS", "LEATHER", "STONEBLOCK"], 4, 8, 4),
    "♻️ Rotas de Refino": gerar_matriz(["WOOD", "PLANKS", "ORE", "METALBAR", "HIDE", "LEATHER", "FIBER", "CLOTH"], 4, 8, 4) # NOVA ABA
}

TODOS_ITENS = sum(CATEGORIAS.values(), [])

# ==========================================
# 5. MOTOR SUPER-QUÂNTICO (TCP + ANTI-SCAM + GRÁFICOS)
# ==========================================
@st.cache_data(ttl=120, show_spinner=False)
def motor_de_busca(itens, servidor, origem_lista, destinos, cap_montaria):
    chunks = [itens[i:i+100] for i in range(0, len(itens), 100)]
    dados_p, dados_v = [], []
    session = requests.Session()
    barra = st.progress(0, text="⚡ Analisando Histórico e Pesos (Wall Street Mode)...")
    destinos_str = ",".join(destinos)
    origens_str = ",".join(origem_lista)

    for i, chunk in enumerate(chunks):
        barra.progress((i+1)/len(chunks))
        ids = ",".join(chunk)
        try:
            r1 = session.get(f"https://{servidor}.albion-online-data.com/api/v2/stats/prices/{ids}?locations={origens_str},{destinos_str}&qualities=1", timeout=8)
            r2 = session.get(f"https://{servidor}.albion-online-data.com/api/v2/stats/history/{ids}?locations={destinos_str}&t=24", timeout=8)
            if r1.status_code == 200: dados_p.extend(r1.json())
            if r2.status_code == 200: dados_v.extend(r2.json())
        except: pass
        time.sleep(0.05)
    barra.empty()

    precos = {}
    for e in dados_p:
        if (p := e["sell_price_min"] if e["sell_price_min"] > 0 else e["buy_price_max"]) > 0:
            precos.setdefault(e["item_id"], {})[e["city"]] = p

    # Histórico Avançado: Volume e Curva de Preço (Para Sparkline e Anti-Scam)
    hist_analise = {}
    for h in dados_v:
        iid = h["item_id"]
        dados_reais = h.get("data", [])
        if dados_reais:
            vol_total = sum(d["item_count"] for d in dados_reais)
            precos_medios = [d["avg_price"] for d in dados_reais]
            media_24h = sum(precos_medios) / len(precos_medios)
            hist_analise.setdefault(iid, {"vol": 0, "curva": [], "media_24h": 0})
            hist_analise[iid]["vol"] += vol_total
            hist_analise[iid]["curva"].extend(precos_medios)
            hist_analise[iid]["media_24h"] = media_24h

    resultados = []
    for item in itens:
        p_compra = {c: p for c, p in precos.get(item, {}).items() if c in origem_lista}
        if p_compra:
            cid_compra = min(p_compra, key=p_compra.get)
            compra = p_compra[cid_compra]
            p_venda = {c: p for c, p in precos.get(item, {}).items() if c in destinos}
            
            if compra > 0 and p_venda:
                cid_venda = max(p_venda, key=p_venda.get)
                venda = p_venda[cid_venda]
                lucro = (venda * (1 - TAXA_MERCADO)) - compra
                
                if lucro > 0:
                    info_h = hist_analise.get(item, {"vol": 0, "curva": [venda, venda], "media_24h": venda})
                    vol, curva, media_hist = info_h["vol"], info_h["curva"], info_h["media_24h"]
                    if not curva: curva = [venda, venda] # Fallback gráfico
                    
                    margem = (lucro/compra)*100
                    peso_kg = calcular_peso_item(item)
                    lucro_kg = lucro / peso_kg if peso_kg > 0 else lucro
                    
                    nome, t, e = formatar_nome_item(item)
                    
                    # 🚨 ESCUDO ANTI-SCAM 🚨
                    if venda > (media_hist * 2.5) and media_hist > 0:
                        score = "🚨 SCAM"
                    else:
                        if vol >= 30 and margem >= 20: score = "S 💎"
                        elif vol >= 15 and margem >= 10: score = "A ⭐"
                        elif vol >= 5 and margem >= 5: score = "B 🟢"
                        else: score = "C 🟡"
                    
                    # 🦣 SIMULADOR DE COMBOIO
                    lucro_viagem_text = "-"
                    lucro_viagem_val = 0
                    if cap_montaria > 0:
                        qtd_cabe = math.floor(cap_montaria / peso_kg)
                        lucro_viagem_val = qtd_cabe * lucro
                        lucro_viagem_text = formatar_prata(lucro_viagem_val)

                    resultados.append({
                        "Mercadoria": nome, "Tier": t, "Enc": e,
                        "Logística": f"{cid_compra}➔{cid_venda}{' ☠️' if cid_venda=='Black Market' else ''}",
                        "Score": score, 
                        "Compra_f": formatar_prata(compra), "Venda_f": formatar_prata(venda),
                        "Lucro Líquido_f": formatar_prata(lucro), "Lucro_r": lucro,
                        "Lucro/Kg_f": formatar_prata(lucro_kg),
                        "Lucro Viagem": lucro_viagem_text, "Lucro_Viagem_r": lucro_viagem_val,
                        "Margem (%)": margem, "Giro/24h": vol,
                        "Gráfico 24h": curva # Dado Bruto para o Sparkline
                    })
    return pd.DataFrame(resultados)

# ==========================================
# 6. DASHBOARD RENDERER (WALL STREET)
# ==========================================
def renderizar_ultimate_dashboard(df):
    if not df.empty:
        if busca_nome: df = df[df["Mercadoria"].str.contains(busca_nome, case=False)]
        df = df[(df["Margem (%)"] >= margem_min) & (df["Giro/24h"] >= giro_min)]
        if filtro_tier: df = df[df["Tier"].isin(filtro_tier)]
        if filtro_enc: df = df[df["Enc"].isin(filtro_enc)]
        
        # Oculta SCAMS se o usuário quiser segurança
        if ocultar_scam: df = df[df["Score"] != "🚨 SCAM"]
        
        if not df.empty:
            # Se usar montaria, ordena pelo maior Lucro da Viagem. Se não, ordena por Margem.
            ordem_col = "Lucro_Viagem_r" if cap_selecionada > 0 else "Lucro_r"
            df = df.sort_values(by=["Score", ordem_col], ascending=[True, False])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📌 Rotas Encontradas", f"{len(df)} itens")
            c2.metric("🚀 Pico de Margem", f"{df['Margem (%)'].max():.1f}%")
            if cap_selecionada > 0:
                c3.metric("🦣 Maior Lucro/Viagem", formatar_prata(df['Lucro_Viagem_r'].max()))
            else:
                c3.metric("⚖️ Maior Lucro/Kg", formatar_prata(df['Lucro_r'].max() / 2)) # Approx
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Configuração das Colunas e Sparklines
            col_config = {
                "Mercadoria": st.column_config.TextColumn("Mercadoria", width="medium"),
                "Score": st.column_config.TextColumn("Avaliação", width="small"),
                "Gráfico 24h": st.column_config.LineChartColumn("📈 Tendência 24h", y_min=0, y_max=None),
                "Margem (%)": st.column_config.NumberColumn("Margem %", format="%.1f%%"),
                "Lucro/Kg_f": st.column_config.TextColumn("⚖️ Lucro/Kg"),
                "Compra_f": st.column_config.TextColumn("📥 Compra"),
                "Venda_f": st.column_config.TextColumn("📤 Venda"),
                "Lucro Líquido_f": st.column_config.TextColumn("💰 Lucro Un."),
            }
            
            if cap_selecionada == 0: df = df.drop(columns=["Lucro Viagem"])
            else: col_config["Lucro Viagem"] = st.column_config.TextColumn("🦣 Carga Total")

            st.dataframe(
                df.drop(columns=['Lucro_r', 'Lucro_Viagem_r', 'Tier', 'Enc']), 
                use_container_width=True, hide_index=True, column_config=col_config
            )
        else: st.warning("⚠️ Nenhum item sobreviveu aos filtros.")
    else: st.error("💀 O mercado está sem liquidez nestas rotas.")

# ==========================================
# 7. UI - SIDEBAR "GOD MODE"
# ==========================================
rendering_sidebar_header()
servidor_ui = st.sidebar.selectbox("Região Global", list(MAPA_SERVIDORES.keys()))
servidor_api = MAPA_SERVIDORES[servidor_ui]

origens = st.sidebar.multiselect("Comprar em:", CIDADES_ROYAL, default=["Martlock"])
destino = st.sidebar.selectbox("Vender em:", CIDADES_DESTINO, index=1)

st.sidebar.divider()
st.sidebar.markdown("### 🦣 Simulador de Carga")
opcoes_montaria = {"🎒 Apenas Unitário": 0, "🐂 Boi T5 (1200kg)": 1200, "🐗 Javali (900kg)": 900, "🦣 Mamute (25000kg)": 25000}
montaria_ui = st.sidebar.selectbox("Qual sua montaria?", list(opcoes_montaria.keys()))
cap_selecionada = opcoes_montaria[montaria_ui]

st.sidebar.divider()
st.sidebar.markdown("### 🏹 Defesas & Filtros")
ocultar_scam = st.sidebar.checkbox("🛡️ Ocultar SCAMs (Manipulação)", value=True)
busca_nome = st.sidebar.text_input("Buscar Item (ex: Sangra)")
margem_min = st.sidebar.slider("Margem Mínima (%)", 0, 100, 1)
giro_min = st.sidebar.slider("Vendas Mínimas (24h)", 0, 50, 1)

filtro_tier = st.sidebar.multiselect("Travar Tier", ["T3", "T4", "T5", "T6", "T7", "T8"])
filtro_enc = st.sidebar.multiselect("Travar Encantamento", ["0", "1", "2", "3", "4"])

if st.sidebar.button("🔄 Resetar Cache", use_container_width=True):
    st.cache_data.clear()

# ==========================================
# 8. CORPO PRINCIPAL
# ==========================================
st.title("💎 Terminal Omniverse GOD MODE")
st.caption("Análise de Peso, Previsão Gráfica e Escudo Anti-Scam ativados.")

abas = st.tabs(["🌍 Radar Tático Global"] + list(CATEGORIAS.keys()))

with abas[0]:
    if st.button("🚀 INICIAR VARREDURA TÁTICA GLOBAL", use_container_width=True, type="primary"):
        if not origens: st.error("❌ Escolha pelo menos uma origem.")
        else:
            df_global = motor_de_busca(TODOS_ITENS, servidor_api, origens, CIDADES_ROYAL, cap_selecionada)
            renderizar_ultimate_dashboard(df_global)

for i, nome in enumerate(CATEGORIAS):
    with abas[i+1]:
        if st.button(f"🚀 VARRER {nome.upper()}", key=f"btn_{i}", use_container_width=True, type="primary"):
            if not origens: st.error("❌ Escolha pelo menos uma origem.")
            else:
                df_cat = motor_de_busca(CATEGORIAS[nome], servidor_api, origens, [destino], cap_selecionada)
                renderizar_ultimate_dashboard(df_cat)

st.divider()
with st.expander("📖 Manual do Hedge Fund (Segredos do God Mode)"):
    st.markdown("""
    **1. ⚖️ Lucro por Kg:** Melhor métrica para quem não tem Mamute. Focar nisso evita viagens lentas e perigosas.
    **2. 📈 Gráfico 24h:** A linha sobe? O preço está encarecendo. A linha cai? Fuja, o mercado está inundado.
    **3. 🚨 SCAM:** Se o sistema marcar SCAM, significa que alguém comprou tudo e listou 1 item por um valor absurdo. **NÃO COMPRE**.
    **4. 🦣 Carga Total:** Escolha o Mamute na lateral. O Radar vai te dizer exatamente quantos milhões você faz enchendo a bolsa 100%.
    """)