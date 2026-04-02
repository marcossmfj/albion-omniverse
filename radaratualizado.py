import streamlit as st
import requests
import pandas as pd
import time
import math
import concurrent.futures

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
h1, h2, h3, h5 { color: #58a6ff !important; font-weight: 800; margin-bottom: -10px; }
.stCaption { color: #8b949e !important; }

.stButton>button {
    background-color: #1f6feb !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: bold !important; transition: all 0.2s ease;
    box-shadow: 0 4px 10px rgba(31, 111, 235, 0.2) !important;
    height: 42px !important; font-size: 1rem !important; margin-top: 27px;
}
.stButton>button:hover { background-color: #15469a !important; transform: translateY(-2px); }

[data-testid="stSidebar"] div.stRadio label{
    background-color: transparent; padding: 8px 12px;
    border-radius: 6px; color: #c9d1d9; font-weight: 600;
    cursor: pointer; transition: 0.2s;
}
[data-testid="stSidebar"] div.stRadio label:hover { background-color: #30363d; }
[data-testid="stSidebar"] div.stRadio label[data-selected="true"] {
    background-color: #1f6feb; color: white;
}

div[data-testid="metric-container"] {
    background-color: #161b22; border: 1px solid #30363d;
    padding: 15px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}
[data-testid="stMetricValue"] { color: #00FF41 !important; font-weight: 900; font-size: 1.8rem; }
div.stDataFrame { border: 1px solid #30363d; border-radius: 8px; background-color: #0d1117; }
</style>
""", unsafe_allow_html=True)

CIDADES_ROYAL = ["Martlock", "Caerleon", "Thetford", "Fort Sterling", "Lymhurst", "Bridgewatch", "Brecilien"]
CIDADES_DESTINO = CIDADES_ROYAL + ["Black Market"]
MAPA_SERVIDORES = { "Américas (West)": "west", "Europa (Europe)": "europe", "Ásia (East)": "east" }

REGRAS_QTD_BRUTO = {4: 2, 5: 3, 6: 4, 7: 5, 8: 5}
ITEM_VALUE_BASE = {4: 16, 5: 32, 6: 64, 7: 128, 8: 256}

MAPA_REFINO = {
    "Minério (Metal)": {"bruto": "ORE", "refinado": "METALBAR", "base_t3": "T3_METALBAR", "bonus": "Thetford", "journal": "JOURNAL_ORE"},
    "Madeira (Tábua)": {"bruto": "WOOD", "refinado": "PLANKS", "base_t3": "T3_PLANKS", "bonus": "Fort Sterling", "journal": "JOURNAL_WOOD"},
    "Pelego (Couro)": {"bruto": "HIDE", "refinado": "LEATHER", "base_t3": "T3_LEATHER", "bonus": "Martlock", "journal": "JOURNAL_HIDE"},
    "Fibra (Tecido)": {"bruto": "FIBER", "refinado": "CLOTH", "base_t3": "T3_CLOTH", "bonus": "Lymhurst", "journal": "JOURNAL_FIBER"},
    "Pedra (Bloco)": {"bruto": "ROCK", "refinado": "STONEBLOCK", "base_t3": "T3_STONEBLOCK", "bonus": "Bridgewatch", "journal": "JOURNAL_STONE"}
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
                if item in recursos: res.append(f"{base}_LEVEL{e}@{e}")
                else: res.append(f"{base}@{e}")
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
# 3. SIDEBAR (SETUP GLOBAL E MENU)
# ==========================================
# NOVA LOGO CLICÁVEL (Redireciona para o início do site limpando tudo)
fogo_svg = '<svg viewBox="0 0 24 24" style="width:26px;height:26px;fill:#ff9a00;margin-right:8px;"><path d="M11.9,1.1c-0.2-0.2-0.6-0.2-0.8,0l-0.8,0.8C6.9,5.2,5.2,8,5.2,11.3c0,3.7,3,6.7,6.7,6.7s6.7-3,6.7-6.7c0-3.3-1.7-6.1-4.1-9.4L11.9,1.1z M12,16.2c-2.7,0-4.9-2.2-4.9-4.9c0-1.2,0.4-2.2,1-3c1.1-1.4,2.8-2.3,4.7-2.3c0.1,0,0.2,0,0.3,0v0c1.7,0.1,3.2,1.1,4.1,2.5c0.6,0.9,0.9,1.9,0.9,3.1C16.9,14,14.7,16.2,12,16.2z"></path></svg>'
st.sidebar.markdown(f"""
    <a href="." target="_self" style="text-decoration: none; color: inherit;">
        <div style="display:flex; align-items:center; margin-bottom:15px; cursor: pointer;">
            {fogo_svg}
            <span style="font-weight:900; font-size:1.4rem; color:white;">Omniverse <span style="color:#58a6ff">PRO</span></span>
        </div>
    </a>
    """, unsafe_allow_html=True)

# Nova aba "Início" adicionada
selecao_app = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "👑 REI DO REFINO", "🌍 Radar Tático Global", "🎯 Black Market Sniper"],
    label_visibility="collapsed"
)

st.sidebar.divider()
st.sidebar.markdown("##### 🌐 Setup Global")
servidor_ui = st.sidebar.selectbox("Servidor:", list(MAPA_SERVIDORES.keys()))
servidor_api = MAPA_SERVIDORES[servidor_ui]

opcoes_montaria = {"🎒 Unitário": 0, "🐂 Boi T5 (1200kg)": 1200, "🐗 Javali (900kg)": 900, "🦣 Mamute (25000kg)": 25000}
montaria_ui = st.sidebar.selectbox("Sua Carga Total:", list(opcoes_montaria.keys()), index=0)
cap_selecionada = opcoes_montaria[montaria_ui]

st.sidebar.divider()
st.sidebar.markdown("##### 💰 Taxas de Mercado")
tem_premium = st.sidebar.toggle("✨ Conta Premium (Taxa 4%)", value=True, help="O Premium reduz a taxa de mercado pela metade.")
taxa_mercado_atual = 0.04 if tem_premium else 0.08

if st.sidebar.button("🔄 Limpar Cache", use_container_width=True):
    st.cache_data.clear()

# ==========================================
# 4. MOTOR MULTI-THREADING (ALTA PERFORMANCE)
# ==========================================
def fetch_url(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=120, show_spinner=False)
def motor_de_busca_transporte(itens, servidor, origem_lista, destinos, cap_montaria, taxa_aplicada):
    chunks = [itens[i:i+100] for i in range(0, len(itens), 100)]
    urls = []
    for chunk in chunks:
        ids = ",".join(chunk)
        urls.append(f"https://{servidor}.albion-online-data.com/api/v2/stats/prices/{ids}?locations={','.join(origem_lista)},{','.join(destinos)}&qualities=1")
        urls.append(f"https://{servidor}.albion-online-data.com/api/v2/stats/history/{ids}?locations={','.join(destinos)}&t=24")
    
    barra = st.progress(0, text="⚡ Disparando Multi-Threads na API do Albion...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for i, res in enumerate(executor.map(fetch_url, urls)):
            results.append(res)
            barra.progress((i+1)/len(urls))
    barra.empty()

    dados_p, dados_v = [], []
    for i in range(0, len(results), 2):
        if results[i]: dados_p.extend(results[i])
        if (i+1) < len(results) and results[i+1]: dados_v.extend(results[i+1])

    precos, hist_analise = {}, {}
    for e in dados_p:
        if (p := e["sell_price_min"] if e["sell_price_min"] > 0 else e["buy_price_max"]) > 0:
            precos.setdefault(e["item_id"], {})[e["city"]] = p

    for h in dados_v:
        iid = h["item_id"]
        dados_reais = h.get("data", [])
        if dados_reais:
            vol_total = sum(d["item_count"] for d in dados_reais)
            precos_medios = [d["avg_price"] for d in dados_reais]
            hist_analise[iid] = {"vol": vol_total, "curva": precos_medios, "media_24h": sum(precos_medios)/len(precos_medios)}

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
                lucro = (venda * (1 - taxa_aplicada)) - compra
                
                if lucro > 0:
                    info_h = hist_analise.get(item, {"vol": 0, "curva": [venda, venda], "media_24h": venda})
                    vol, curva, media_hist = info_h["vol"], info_h["curva"], info_h["media_24h"]
                    
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
                    
                    l_viagem_text, l_viagem_val = "-", 0
                    if cap_montaria > 0:
                        qtd_cabe = math.floor(cap_montaria / peso_kg)
                        l_viagem_val = qtd_cabe * lucro
                        l_viagem_text = formatar_prata(l_viagem_val)

                    resultados.append({
                        "Mercadoria": nome, "Tier": t, "Enc": e,
                        "Logística": f"{cid_compra}➔{cid_venda}{' ☠️' if cid_venda=='Black Market' else ''}",
                        "Score": score, "Compra_f": formatar_prata(compra), "Venda_f": formatar_prata(venda),
                        "Lucro Líquido_f": formatar_prata(lucro), "Lucro_r": lucro, "Lucro/Kg_f": formatar_prata(lucro_kg),
                        "Lucro Viagem": l_viagem_text, "Lucro_Viagem_r": l_viagem_val,
                        "Margem (%)": margem, "Giro/24h": vol, "Gráfico 24h": curva 
                    })
    return pd.DataFrame(resultados)

@st.cache_data(ttl=120, show_spinner=False)
def motor_de_busca_refino(itens, servidor, cidades):
    session = requests.Session()
    ids = ",".join(itens)
    cids = ",".join(cidades)
    barra = st.progress(0, text="⚡ Sincronizando Usinas na Nuvem...")
    try:
        url_p = f"https://{servidor}.albion-online-data.com/api/v2/stats/prices/{ids}?locations={cids}&qualities=1"
        r1 = session.get(url_p, timeout=10)
        url_h = f"https://{servidor}.albion-online-data.com/api/v2/stats/history/{ids}?locations={cids}&t=24"
        r2 = session.get(url_h, timeout=10)
        barra.empty()
        return r1.json() if r1.status_code==200 else [], r2.json() if r2.status_code==200 else []
    except: 
        barra.empty()
        return [], []

# ==========================================
# 5. RENDERIZADORES COMPACTOS DE TOPO E TABELA
# ==========================================
def rendering_top_tatico_filters():
    with st.expander("⚙️ Filtros Avançados (Tier, Encantamento, Margem, SCAM)"):
        st.markdown("<br>", unsafe_allow_html=True)
        fc1, fc2, fc3, fc4 = st.columns([1,1,1,1])
        with fc1: f_tier = st.multiselect("Travar Tier", ["T3", "T4", "T5", "T6", "T7", "T8"], label_visibility="collapsed")
        with fc2: f_enc = st.multiselect("Travar Enc", ["0", "1", "2", "3", "4"], label_visibility="collapsed")
        with fc3: o_scam = st.checkbox("🛡️ Ocultar SCAMs", value=True)
        with fc4: 
            f_nome = st.text_input("Buscar Item", label_visibility="collapsed")
            c_sl = st.columns(2)
            with c_sl[0]: m_min = st.slider("Margem %", 0, 100, 1, label_visibility="collapsed")
            with c_sl[1]: v_min = st.slider("Giro", 0, 50, 1, label_visibility="collapsed")
    return f_tier, f_enc, o_scam, f_nome, m_min, v_min

def renderizar_tabela_transporte(df, f_tier, f_enc, o_scam, f_nome, m_min, v_min):
    if not df.empty:
        if f_nome: df = df[df["Mercadoria"].str.contains(f_nome, case=False)]
        df = df[(df["Margem (%)"] >= m_min) & (df["Giro/24h"] >= v_min)]
        if f_tier: df = df[df["Tier"].isin(f_tier)]
        if f_enc: df = df[df["Enc"].isin(f_enc)]
        if o_scam: df = df[df["Score"] != "🚨 SCAM"]
        
        if not df.empty:
            ordem_col = "Lucro_Viagem_r" if cap_selecionada > 0 else "Lucro_r"
            df = df.sort_values(by=["Score", ordem_col], ascending=[True, False])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📌 Oportunidades", f"{len(df)} itens")
            c2.metric("🚀 Margem Máxima", f"{df['Margem (%)'].max():.1f}%")
            if cap_selecionada > 0: c3.metric("🦣 Pico Lucro/Viagem", formatar_prata(df['Lucro_Viagem_r'].max()))
            else: c3.metric("⚖️ Pico Lucro/Kg", formatar_prata(df['Lucro_r'].max() / 2)) 
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_config = {
                "Mercadoria": st.column_config.TextColumn("Item", width="medium"),
                "Score": st.column_config.TextColumn("Tier", width="small"),
                "Gráfico 24h": st.column_config.LineChartColumn("📈 Tendência 24h", y_min=0, y_max=None),
                "Margem (%)": st.column_config.NumberColumn("Margem %", format="%.1f%%"),
                "Lucro/Kg_f": st.column_config.TextColumn("⚖️ Lucro/Kg"),
                "Compra_f": st.column_config.TextColumn("📥 Compra Imediata"),
                "Venda_f": st.column_config.TextColumn("📤 Venda (Sem Ordem)"),
                "Lucro Líquido_f": st.column_config.TextColumn("💰 Lucro Un."),
            }
            if cap_selecionada == 0: df = df.drop(columns=["Lucro Viagem"])
            else: col_config["Lucro Viagem"] = st.column_config.TextColumn("🦣 Carga Total")

            st.dataframe(df.drop(columns=['Lucro_r', 'Lucro_Viagem_r', 'Tier', 'Enc']), use_container_width=True, hide_index=True, column_config=col_config)
        else: st.warning("⚠️ Nenhum item sobreviveu aos filtros.")
    else: st.error("💀 O mercado está sem liquidez.")

# ==========================================
# 6. CORPO PRINCIPAL
# ==========================================

# ------------------------------------------
# MÓDULO 0: INÍCIO (DASHBOARD)
# ------------------------------------------
if selecao_app == "🏠 Início":
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("💎 Bem-vindo ao Omniverse PRO")
    st.markdown("A plataforma de inteligência de mercado mais avançada e **100% gratuita** para Albion Online.")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**👑 Rei do Refino**\n\nCalcule rotas industriais com precisão absurda. Inclui custo oculto (Item Value), bônus de cidade, e lucro com venda de Diários de Trabalhador.")
    with c2:
        st.success("**🌍 Radar Tático**\n\nEncontre oportunidades de arbitragem entre cidades (comprar barato e vender caro) com proteção inteligente Anti-Scam e Gráficos de Tendência.")
    with c3:
        st.error("**🎯 BM Sniper**\n\nIdentifique flips instantâneos em Caerleon direto para o Black Market. Ative o 'Fast Flip' para lucrar sem sair da cidade.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Use o menu lateral para navegar entre os módulos. Ajuste o servidor e a sua montaria na aba 'Setup Global' para cálculos logísticos exatos.")

# ------------------------------------------
# MÓDULO 1: REI DO REFINO
# ------------------------------------------
elif selecao_app == "👑 REI DO REFINO":
    st.markdown(f"<h2>{selecao_app}</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.2])
    with c1: recurso_nome = st.selectbox("Recurso (Matéria Prima)", list(MAPA_REFINO.keys()), label_visibility="collapsed")
    with c2: taxa_estacao = st.number_input("Tax Fee da Loja", value=500, label_visibility="collapsed")
    with c3: uso_foco = st.selectbox("Modo de Foco", ["✨ Sem Foco (15.2%)", "🔥 Com Foco (43.5%)"], label_visibility="collapsed")
    with c4: btn_refino = st.button("🚀 CALCULAR REFINO", use_container_width=True)

    if btn_refino:
        config = MAPA_REFINO[recurso_nome]
        rrr = 43.5 if "Com Foco" in uso_foco else 15.2
        
        lista_ids = [config['base_t3']]
        for t in range(4, 9):
            lista_ids.extend([f"T{t}_{config['bruto']}", f"T{t}_{config['refinado']}"])
            lista_ids.extend([f"T{t}_{config['journal']}_EMPTY", f"T{t}_{config['journal']}_FULL"])
            for e in range(1, 5):
                sufix = f"_LEVEL{e}@{e}"
                lista_ids.extend([f"T{t}_{config['bruto']}{sufix}", f"T{t}_{config['refinado']}{sufix}"])

        precos_raw, hist_raw = motor_de_busca_refino(lista_ids, servidor_api, CIDADES_ROYAL)
        
        precos = {p['item_id']: {p['city']: p['sell_price_min'] if p['sell_price_min']>0 else p['buy_price_max']} for p in precos_raw if (p['sell_price_min']>0 or p['buy_price_max']>0)}
        vendas_24h = {h['item_id']: sum(d['item_count'] for d in h.get('data', [])) for h in hist_raw}

        refino_data = []
        for t in range(4, 9):
            lucro_diario_txt = "-"
            if t >= 5:
                id_vazio, id_cheio = f"T{t}_{config['journal']}_EMPTY", f"T{t}_{config['journal']}_FULL"
                if id_vazio in precos and id_cheio in precos:
                    p_vazio = min(precos[id_vazio].values())
                    p_cheio = max(precos[id_cheio].values())
                    ld = p_cheio - p_vazio
                    if ld > 0: lucro_diario_txt = f"+{formatar_prata(ld)}/un"
            
            for e in range(0, 5):
                sufix = f"_LEVEL{e}@{e}" if e > 0 else ""
                id_b, id_r = f"T{t}_{config['bruto']}{sufix}", f"T{t}_{config['refinado']}{sufix}"
                id_r_anterior = config['base_t3'] if t == 4 else f"T{t-1}_{config['refinado']}"
                
                if all(i in precos for i in [id_b, id_r, id_r_anterior]):
                    cid_compra_b = min(precos[id_b], key=precos[id_b].get)
                    preco_b = precos[id_b][cid_compra_b]
                    
                    cid_compra_ant = min(precos[id_r_anterior], key=precos[id_r_anterior].get)
                    preco_ant = precos[id_r_anterior][cid_compra_ant]
                    
                    cid_venda = max(precos[id_r], key=precos[id_r].get)
                    preco_r = precos[id_r][cid_venda]
                    
                    custo_material = (preco_b * REGRAS_QTD_BRUTO[t]) + preco_ant
                    iv = ITEM_VALUE_BASE[t] * (2 ** e) if e > 0 else ITEM_VALUE_BASE[t]
                    custo_estacao = iv * 0.1125 * (taxa_estacao / 100) 
                    
                    custo_total = custo_material + custo_estacao
                    lucro = ( (preco_r / (1 - (rrr/100))) * (1 - taxa_mercado_atual) ) - custo_total
                    
                    refino_data.append({
                        "Receita": f"T{t}.{e}", "Logística": f"{cid_compra_b} ➔ {cid_venda}",
                        "Matéria Prima 🥈": formatar_prata(custo_material), "Custo Produção 🥈": formatar_prata(custo_total),
                        "Venda Final 🥈": formatar_prata(preco_r), "Lucro Real / Un 🥈": formatar_prata(lucro),
                        "📖 Intel Diário": lucro_diario_txt,
                        "✨ Lucro Un.": lucro, "Margem %": round((lucro/custo_total)*100, 1) if custo_total > 0 else 0,
                        "Giro 24h": vendas_24h.get(id_r, 0),
                        "Status": "💎 PRO ROTA" if lucro > (custo_total * 0.3) else "✅ OK" if lucro > 0 else "❌ LOSS"
                    })

        if refino_data:
            df_refino = pd.DataFrame(refino_data).sort_values("✨ Lucro Un.", ascending=False)
            st.dataframe(df_refino.drop(columns=['✨ Lucro Un.']), use_container_width=True, hide_index=True)
            st.success(f"📍 Bônus de Produção para {recurso_nome}: **{config['bonus']}**.")
        else: st.warning("Dados indisponíveis na API do Albion no momento.")

# ------------------------------------------
# MÓDULO 2: BLACK MARKET SNIPER
# ------------------------------------------
elif selecao_app == "🎯 Black Market Sniper":
    st.markdown(f"<h2>{selecao_app}</h2>", unsafe_allow_html=True)
    st.info("⚠️ O Sniper verifica lucros rápidos entregando no Black Market (Caerleon).")
    
    is_fast_flip = st.toggle("🔥 Modo Fast Flip (Apenas Caerleon -> Mercado Negro)", value=False, help="Ignora cidades Royal e foca em comprar em Caerleon e andar 2 minutos até o BM.")
    
    c1, c2 = st.columns([2, 1])
    with c1: 
        if is_fast_flip:
            origens = ["Caerleon"]
            st.success("📍 Modo Fast Flip Ativado: Buscando itens nas lojas de Caerleon para venda imediata no Black Market.")
        else:
            origens = st.multiselect("Buscando Oportunidades nas Cidades:", CIDADES_ROYAL, default=["Martlock", "Thetford", "Fort Sterling", "Lymhurst", "Bridgewatch", "Brecilien"])
            
    with c2: btn_sniper = st.button(f"🎯 ATIRAR SNIPER", use_container_width=True)
    
    f_tier, f_enc, o_scam, f_nome, m_min, v_min = rendering_top_tatico_filters()

    if btn_sniper:
        if not origens: st.error("❌ Selecione ao menos uma cidade Royal.")
        else:
            itens_bm = CATEGORIAS["⚔️ Armas Meta"] + CATEGORIAS["⛏️ Roupas Coleta"]
            df_sniper = motor_de_busca_transporte(itens_bm, servidor_api, origens, ["Black Market"], cap_selecionada, taxa_mercado_atual)
            renderizar_tabela_transporte(df_sniper, f_tier, f_enc, o_scam, f_nome, max(15, m_min) if not is_fast_flip else m_min, max(1, v_min))

# ------------------------------------------
# MÓDULO 3: RADAR GLOBAL 
# ------------------------------------------
elif selecao_app == "🌍 Radar Tático Global":
    st.markdown(f"<h2>{selecao_app}</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.5, 1.5, 1.2])
    with c1: origens = st.multiselect("Comprar em:", CIDADES_ROYAL, default=["Martlock"], label_visibility="collapsed")
    with c2: destino = st.selectbox("Vender em:", CIDADES_DESTINO, index=1, label_visibility="collapsed")
    with c3: btn_transporte = st.button(f"🚀 VARRER AGORA", use_container_width=True)

    f_tier, f_enc, o_scam, f_nome, m_min, v_min = rendering_top_tatico_filters()

    if btn_transporte:
        if not origens: st.error("❌ Selecione uma cidade de origem.")
        else:
            df_transporte = motor_de_busca_transporte(TODOS_ITENS, servidor_api, origens, [destino], cap_selecionada, taxa_mercado_atual)
            renderizar_tabela_transporte(df_transporte, f_tier, f_enc, o_scam, f_nome, m_min, v_min)
