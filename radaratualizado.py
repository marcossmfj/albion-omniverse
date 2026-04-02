import streamlit as st
import requests
import pandas as pd
import time
import math

# ==========================================
# 1. CONFIGURAÇÕES - DARK MODE TERMINAL ELITE
# ==========================================
st.set_page_config(
    page_title="Albion Omniverse Ultimate PRO",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Dicionários de Regras Reais de Refino (Albion Online Oficial)
REGRAS_QTD_BRUTO = {4: 2, 5: 3, 6: 4, 7: 5, 8: 5}
ITEM_VALUE_BASE = {4: 16, 5: 32, 6: 64, 7: 128, 8: 256}

MAPA_REFINO = {
    "Minério (Metal)": {"bruto": "ORE", "refinado": "METALBAR", "base_t3": "T3_METALBAR", "bonus": "Thetford"},
    "Madeira (Tábua)": {"bruto": "WOOD", "refinado": "PLANKS", "base_t3": "T3_PLANKS", "bonus": "Fort Sterling"},
    "Pelego (Couro)": {"bruto": "HIDE", "refinado": "LEATHER", "base_t3": "T3_LEATHER", "bonus": "Martlock"},
    "Fibra (Tecido)": {"bruto": "FIBER", "refinado": "CLOTH", "base_t3": "T3_CLOTH", "bonus": "Lymhurst"},
    "Pedra (Bloco)": {"bruto": "ROCK", "refinado": "STONEBLOCK", "base_t3": "T3_STONEBLOCK", "bonus": "Bridgewatch"}
}

# ==========================================
# 2. FUNÇÕES BASE E DICIONÁRIOS
# ==========================================
def formatar_prata(valor):
    try:
        valor = float(valor)
        if valor >= 1_000_000: return f"{valor/1_000_000:.2f}M 🥈"
        if valor >= 1_000: return f"{valor/1000:.1f}K 🥈"
        return f"{int(valor)} 🥈"
    except: return str(valor)

def calcular_peso_item(item_id):
    tier_str = item_id.split("_")[0].replace("T", "")
    tier = int(tier_str) if tier_str.isdigit() else 4
    if "MOUNT_MAMMOTH" in item_id: return 134.0
    if "MOUNT_OX" in item_id: return tier * 5.0
    if "MOUNT" in item_id: return tier * 3.0
    if any(x in item_id for x in ["WOOD", "ROCK", "ORE", "HIDE", "FIBER", "PLANKS", "METALBAR", "LEATHER", "CLOTH"]):
        return tier * 0.5
    return tier * 1.2

def rendering_sidebar_header():
    fogo_svg = '<svg viewBox="0 0 24 24" style="width:28px;height:28px;fill:#ff9a00;margin-right:8px;"><path d="M11.9,1.1c-0.2-0.2-0.6-0.2-0.8,0l-0.8,0.8C6.9,5.2,5.2,8,5.2,11.3c0,3.7,3,6.7,6.7,6.7s6.7-3,6.7-6.7c0-3.3-1.7-6.1-4.1-9.4L11.9,1.1z M12,16.2c-2.7,0-4.9-2.2-4.9-4.9c0-1.2,0.4-2.2,1-3c1.1-1.4,2.8-2.3,4.7-2.3c0.1,0,0.2,0,0.3,0v0c1.7,0.1,3.2,1.1,4.1,2.5c0.6,0.9,0.9,1.9,0.9,3.1C16.9,14,14.7,16.2,12,16.2z"></path></svg>'
    st.sidebar.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:15px; border-bottom:1px solid #30363d; padding-bottom:15px;">
            {fogo_svg}
            <span style="font-weight:900; font-size:1.5rem; color:white;">Omniverse <span style="color:#58a6ff">GOD MODE</span></span>
        </div>
        """, unsafe_allow_html=True)

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
    item_base = item_id.split("@")[0].replace(f"{tier}_", "", 1).split("_LEVEL")[0]
    nome_pt = DICIONARIO_PTBR.get(item_base, item_base.replace("_", " "))
    return f"{nome_pt} {tier}.{enc}", tier, enc

def gerar_matriz(lista, min_t=4, max_t=8, max_e=4):
    res = []
    recursos = ["WOOD", "ROCK", "ORE", "HIDE", "FIBER", "CLOTH", "METALBAR", "PLANKS", "LEATHER", "STONEBLOCK"]
    for item in lista:
        for t in range(min_t, max_t + 1):
            base = f"T{t}_{item}"
            res.append(base)
            for e in range(1, max_e + 1):
                if item in recursos:
                    res.append(f"{base}_LEVEL{e}@{e}")
                else:
                    res.append(f"{base}@{e}")
    return res

CATEGORIAS = {
    "🐎 Montarias": [f"T{t}_MOUNT_HORSE" for t in range(3,9)] + [f"T{t}_MOUNT_OX" for t in range(3,9)] + ["T5_MOUNT_COUGAR_KEEPER", "T6_MOUNT_DIREWOLF", "T8_MOUNT_MAMMOTH_TRANSPORT"],
    "⚔️ Armas Meta": gerar_matriz(["MAIN_DAGGER_MAGIC", "2H_DUALAXE_KEEPER", "MAIN_CURSEDSTAFF_AVALON", "2H_BOW_KEEPER", "MAIN_NATURESTAFF_KEEPER"], 4, 8, 4),
    "⛏️ Roupas Coleta": gerar_matriz(["HEAD_GATHERER_WOOD", "ARMOR_GATHERER_WOOD", "SHOES_GATHERER_WOOD", "HEAD_GATHERER_ROCK", "ARMOR_GATHERER_ROCK", "SHOES_GATHERER_ROCK"], 4, 8, 0),
    "🧱 Brutos": gerar_matriz(["WOOD", "ROCK", "ORE", "HIDE", "FIBER"], 4, 8, 4),
    "🛡️ Capas & Refinados": gerar_matriz(["CAPE", "BAG", "CLOTH", "METALBAR", "PLANKS", "LEATHER", "STONEBLOCK"], 4, 8, 4)
}

TODOS_ITENS = sum(CATEGORIAS.values(), [])

# ==========================================
# 3. MOTORES DE BUSCA DA API (TCP POOLING)
# ==========================================
@st.cache_data(ttl=120, show_spinner=False)
def motor_de_busca_transporte(itens, servidor, origem_lista, destinos, cap_montaria):
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
                    if not curva: curva = [venda, venda] 
                    
                    margem = (lucro/compra)*100
                    peso_kg = calcular_peso_item(item)
                    lucro_kg = lucro / peso_kg if peso_kg > 0 else lucro
                    
                    nome, t, e = formatar_nome_item(item)
                    
                    if venda > (media_hist * 2.5) and media_hist > 0: score = "🚨 SCAM"
                    else:
                        if vol >= 30 and margem >= 20: score = "S 💎"
                        elif vol >= 15 and margem >= 10: score = "A ⭐"
                        elif vol >= 5 and margem >= 5: score = "B 🟢"
                        else: score = "C 🟡"
                    
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
                        "Gráfico 24h": curva 
                    })
    return pd.DataFrame(resultados)

@st.cache_data(ttl=120, show_spinner=False)
def motor_de_busca_refino(itens, servidor, cidades):
    session = requests.Session()
    ids = ",".join(itens)
    cids = ",".join(cidades)
    try:
        url_p = f"https://{servidor}.albion-online-data.com/api/v2/stats/prices/{ids}?locations={cids}&qualities=1"
        url_h = f"https://{servidor}.albion-online-data.com/api/v2/stats/history/{ids}?locations={cids}&t=24"
        r1 = session.get(url_p, timeout=10)
        r2 = session.get(url_h, timeout=10)
        return r1.json() if r1.status_code==200 else [], r2.json() if r2.status_code==200 else []
    except: return [], []

# ==========================================
# 4. RENDERIZADORES DE DASHBOARD
# ==========================================
def renderizar_ultimate_dashboard(df):
    if not df.empty:
        if busca_nome: df = df[df["Mercadoria"].str.contains(busca_nome, case=False)]
        df = df[(df["Margem (%)"] >= margem_min) & (df["Giro/24h"] >= giro_min)]
        if filtro_tier: df = df[df["Tier"].isin(filtro_tier)]
        if filtro_enc: df = df[df["Enc"].isin(filtro_enc)]
        if ocultar_scam: df = df[df["Score"] != "🚨 SCAM"]
        
        if not df.empty:
            ordem_col = "Lucro_Viagem_r" if cap_selecionada > 0 else "Lucro_r"
            df = df.sort_values(by=["Score", ordem_col], ascending=[True, False])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📌 Rotas Encontradas", f"{len(df)} itens")
            c2.metric("🚀 Pico de Margem", f"{df['Margem (%)'].max():.1f}%")
            if cap_selecionada > 0:
                c3.metric("🦣 Maior Lucro/Viagem", formatar_prata(df['Lucro_Viagem_r'].max()))
            else:
                c3.metric("⚖️ Maior Lucro/Kg", formatar_prata(df['Lucro_r'].max() / 2)) 
            
            st.markdown("<br>", unsafe_allow_html=True)
            
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
# 5. UI - SIDEBAR DE CONTROLE TÁTICO
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
# 6. CORPO PRINCIPAL - ABAS E RENDERIZAÇÃO
# ==========================================
st.title("💎 Terminal Omniverse GOD MODE")
st.caption("A plataforma definitiva para Arbitragem de Transporte e Refino Industrial no Albion.")

abas = st.tabs(["👑 REI DO REFINO (NOVO)", "🌍 Radar Tático Global"] + list(CATEGORIAS.keys()))

# --- ABA 1: REI DO REFINO (MÓDULO INDUSTRIAL PRO) ---
with abas[0]:
    st.markdown("### 🏭 O Rei do Refino: Inteligência Industrial Avançada")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        recurso = st.selectbox("O que vamos refinar hoje?", list(MAPA_REFINO.keys()))
        config = MAPA_REFINO[recurso]
    with col_b:
        taxa_uso = st.number_input("Taxa da Estação / Tax Fee (ex: 500)", value=500, help="Valor cobrado por 100 de nutrição na cidade.")
    with col_c:
        uso_foco = st.toggle("✨ Usar Foco de Produção", value=True)
        rrr = 43.5 if uso_foco else 15.2
        st.info(f"Taxa de Retorno (RRR): **{rrr}%**")

    if st.button(f"🚀 PROCESSAR ROTA INDUSTRIAL: {recurso.upper()}", use_container_width=True, type="primary"):
        lista_ids = [config['base_t3']] # Precisa do T3 flat para fazer T4
        for t in range(4, 9):
            lista_ids.append(f"T{t}_{config['bruto']}")
            lista_ids.append(f"T{t}_{config['refinado']}") 
            for e in range(1, 5):
                sufix = f"_LEVEL{e}@{e}"
                lista_ids.append(f"T{t}_{config['bruto']}{sufix}")
                lista_ids.append(f"T{t}_{config['refinado']}{sufix}")

        precos_raw, hist_raw = motor_de_busca_refino(lista_ids, servidor_api, CIDADES_ROYAL)
        
        precos = {}
        for p in precos_raw:
            val = p['sell_price_min'] if p['sell_price_min'] > 0 else p['buy_price_max']
            if val > 0: precos.setdefault(p['item_id'], {})[p['city']] = val
            
        vendas_24h = {h['item_id']: sum(d['item_count'] for d in h.get('data', [])) for h in hist_raw}

        refino_data = []
        for t in range(4, 9):
            for e in range(0, 5):
                sufix = f"_LEVEL{e}@{e}" if e > 0 else ""
                id_b = f"T{t}_{config['bruto']}{sufix}"
                id_r = f"T{t}_{config['refinado']}{sufix}"
                
                # Regra de Craft: T5 precisa de Refinado T4 flat (.0). T4 precisa do T3.
                id_r_anterior = config['base_t3'] if t == 4 else f"T{t-1}_{config['refinado']}"
                
                if id_b in precos and id_r in precos and id_r_anterior in precos:
                    cid_compra_b = min(precos[id_b], key=precos[id_b].get)
                    preco_b = precos[id_b][cid_compra_b]
                    
                    cid_compra_ant = min(precos[id_r_anterior], key=precos[id_r_anterior].get)
                    preco_ant = precos[id_r_anterior][cid_compra_ant]
                    
                    cid_venda = max(precos[id_r], key=precos[id_r].get)
                    preco_r = precos[id_r][cid_venda]
                    
                    # MATEMÁTICA REAL DE PRODUÇÃO
                    qtd_bruto = REGRAS_QTD_BRUTO[t]
                    custo_material = (preco_b * qtd_bruto) + preco_ant
                    
                    # Cálculo de Taxa Oculta (Item Value * 0.1125 * (TaxFee/100))
                    iv = ITEM_VALUE_BASE[t] * (2 ** e) if e > 0 else ITEM_VALUE_BASE[t]
                    custo_estacao = iv * 0.1125 * (taxa_uso / 100) 
                    
                    custo_total = custo_material + custo_estacao
                    
                    receita_com_rrr = preco_r / (1 - (rrr/100))
                    lucro = (receita_com_rrr * (1 - TAXA_MERCADO)) - custo_total
                    
                    vol = vendas_24h.get(id_r, 0)
                    
                    refino_data.append({
                        "Receita": f"T{t}.{e}",
                        "Logística": f"{cid_compra_b} ➔ {cid_venda}",
                        "Matéria Prima": formatar_prata(custo_material),
                        "Custo Produção": formatar_prata(custo_total),
                        "Venda Final": formatar_prata(preco_r),
                        "Lucro Real / Un": formatar_prata(lucro),
                        "✨ Lucro Real / Un": lucro, 
                        "Margem %": round((lucro/custo_total)*100, 1) if custo_total > 0 else 0,
                        "Giro 24h": vol,
                        "Status": "💎 PRO ROTA" if lucro > (custo_total * 0.3) else "✅ OK" if lucro > 0 else "❌ LOSS"
                    })

        if refino_data:
            df_refino = pd.DataFrame(refino_data).sort_values("✨ Lucro Real / Un", ascending=False)
            
            st.dataframe(
                df_refino.drop(columns=['✨ Lucro Real / Un']), 
                use_container_width=True, 
                hide_index=True
            )
            
            c1, c2 = st.columns(2)
            c1.success(f"📍 **Dica:** Refinar em **{config['bonus']}** maximiza o retorno (Bônus de Cidade). A tabela já assume a melhor rota de compra.")
            c2.info("📊 **Matemática PRO:** O *Custo de Produção* agora calcula o Refinado da Tier anterior exato + Taxa Baseada em Item Value!")
        else:
            st.warning("Dados insuficientes para calcular o refino no momento. O mercado pode estar sem ofertas para estes itens.")

# --- ABA 2: RADAR GLOBAL (TRANSPORTE) ---
with abas[1]:
    if st.button("🚀 INICIAR VARREDURA TÁTICA GLOBAL", use_container_width=True, type="primary"):
        if not origens: st.error("❌ Escolha pelo menos uma origem na barra lateral.")
        else:
            df_global = motor_de_busca_transporte(TODOS_ITENS, servidor_api, origens, CIDADES_ROYAL, cap_selecionada)
            renderizar_ultimate_dashboard(df_global)

# --- ABAS 3 EM DIANTE: CATEGORIAS CLÁSSICAS ---
for i, nome in enumerate(CATEGORIAS):
    with abas[i+2]: 
        if st.button(f"🚀 VARRER {nome.upper()}", key=f"btn_{i}", use_container_width=True, type="primary"):
            if not origens: st.error("❌ Escolha pelo menos uma origem na barra lateral.")
            else:
                df_cat = motor_de_busca_transporte(CATEGORIAS[nome], servidor_api, origens, [destino], cap_selecionada)
                renderizar_ultimate_dashboard(df_cat)

# ==========================================
# 7. MANUAL DO HEDGE FUND
# ==========================================
st.divider()
with st.expander("📖 Manual de Instruções (Segredos do God Mode & Rei do Refino)"):
    st.markdown("""
    **1. 👑 REI DO REFINO (Logística Industrial Avançada):**
    * **Receita Exata do Jogo:** O custo da matéria-prima agora soma os Brutos (ex: 3x T5) + 1 Refinado da tier anterior (ex: 1x T4 Bar).
    * **Taxa Item Value:** O *Custo de Produção* calcula exatamente o que a loja cobra, usando o peso oculto (*Item Value*) que a Sandbox Interactive usa no servidor.
    * **Formatação Monetária:** Valores formatados com *K (Mil)* e *M (Milhão)* acompanhados do selo 🥈 para evitar confusões visuais.
    
    **2. 🚚 RADAR DE TRANSPORTE (Arbitragem Pura):**
    * **⚖️ Lucro por Kg:** Melhor métrica para quem anda de Boi ou a pé. Evita viagens lentas e pesadas para pouco lucro.
    * **📈 Gráfico 24h:** A linha sobe? O preço está encarecendo. A linha cai? Fuja, o mercado está inundado.
    * **🚨 SCAM:** Se marcado com SCAM, alguém monopolizou o item e listou por um valor irreal para inflar preços. **NÃO COMPRE**.
    """)
