import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from processador import tratar_base_rh

# Função para carregar o CSS externo
def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Chama o arquivo
local_css("style.css")

# --- 1. CONFIGURAÇÕES  ---
st.set_page_config(page_title="Alma Perfumada", layout="wide", initial_sidebar_state="expanded")

# --- INICIALIZAÇÃO DA LINA ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Definição da URL e Token (Coloque aqui no topo para não dar erro de conexão)
API_URL = "https://cloud.flowiseai.com/api/v1/prediction/7aed7671-8c9e-4cc8-839a-5b4f43d207fc"
API_TOKEN = st.secrets["LINA_TOKEN"]

M2_AZUL_ESCURO = "#1E3A8A"
M2_AZUL_CLARO = "#3B82F6"
M2_LARANJA = "#F97316"
M2_FUNDO = "#F8FAFC"


# --- 3. LÓGICA DE DADOS ---
with st.sidebar:
    try:
        from PIL import Image
        logo_img = Image.open("logo_almaperfumada.png")
        st.image(logo_img, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Se não achar a logo, mostra o texto como backup
        st.markdown("<h2 style='color:white;'>ALMA PERFUMADA</h2>", unsafe_allow_html=True)
        st.warning("⚠️ Arquivo 'logo_almaperfumada.png' não encontrado.")

    uploaded_file = st.file_uploader("", type=["csv"])
    

if uploaded_file:
    #df = pd.read_csv(uploaded_file, sep=None, engine='python')
    df = tratar_base_rh(uploaded_file)
    
    # --- 3. IDENTIFICAÇÃO DINÂMICA DE COLUNAS ---
    col_nome = next((c for c in df.columns if 'nome' in c.lower()), df.columns[0])
    
    col_setor = next((c for c in df.columns if 'setor' in c.lower() or 'unidade' in c.lower() or 'loja' in c.lower()), 
                     df.columns[1] if len(df.columns) > 1 else df.columns[0])
    
    col_cargo = next((c for c in df.columns if 'cargo' in c.lower() or 'função' in c.lower()), df.columns[0])
    
    # Busca a coluna de idade, mas CHECA se ela realmente contém números
    col_idade = None
    for c in df.columns:
        if 'idade' in c.lower() or 'age' in c.lower():
            # Só aceita se a coluna for numérica
            if pd.api.types.is_numeric_dtype(df[c]):
                col_idade = c
                break
    
    col_data_adm = next((c for c in df.columns if 'admissão' in c.lower() or 'adm' in c.lower()), None)
    col_nasc = next((c for c in df.columns if 'nascimento' in c.lower() or 'nasc' in c.lower()), None)
    col_email = next((c for c in df.columns if 'email' in c.lower() or 'email' in c.lower()), None)

# --- 4. FILTROS DINÂMICOS NA SIDEBAR ---
    st.sidebar.markdown("### 🔍 Filtros de Análise")
    
    # Filtro 1: Unidade
    sel_unidade = st.sidebar.selectbox("Filtrar por Unidade:", ["Todas"] + sorted(df[col_setor].unique().tolist()))
    
    # Filtro 2: Cargo (Adicionado conforme solicitado)
    sel_cargo = st.sidebar.selectbox("Filtrar por Cargo:", ["Todos"] + sorted(df[col_cargo].unique().tolist()))
    
    # Filtro 3: Mês de Aniversário
    meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    sel_mes = st.sidebar.selectbox("Mês de Aniversário:", meses)

    # Aplicação dos Filtros Cruzados
    df_filtrado = df.copy()

    # --- LÓGICA DE ANIVERSARIANTES (SEGURA) ---
    hoje = datetime.now()
    dia_mes_hoje = hoje.strftime('%d/%m')
    mes_atual = hoje.month

    aniv_hoje = pd.DataFrame()
    aniv_mes = pd.DataFrame()

    if col_nasc:
        # Criamos uma cópia para trabalhar as datas sem afetar o DF principal
        df_niver = df_filtrado.copy()
        df_niver[col_nasc] = pd.to_datetime(df_niver[col_nasc], errors='coerce')
        
        # Removemos quem tiver data inválida apenas para essa análise
        df_niver = df_niver.dropna(subset=[col_nasc])
        
        if not df_niver.empty:
            df_niver['dia_mes'] = df_niver[col_nasc].dt.strftime('%d/%m')
            df_niver['mes'] = df_niver[col_nasc].dt.month
            
            # Filtramos as duas listas
            aniv_hoje = df_niver[df_niver['dia_mes'] == dia_mes_hoje]
            aniv_mes = df_niver[df_niver['mes'] == mes_atual].sort_values(by='dia_mes')
    
    if sel_unidade != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_setor] == sel_unidade]
    
    if sel_cargo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_cargo] == sel_cargo]
    
    if col_nasc and sel_mes != "Todos":
        df_filtrado[col_nasc] = pd.to_datetime(df_filtrado[col_nasc], errors='coerce')
        indice_mes = meses.index(sel_mes)
        df_filtrado = df_filtrado[df_filtrado[col_nasc].dt.month == indice_mes]

# --- 5. DASHBOARD PRINCIPAL ---
    st.markdown('<h1 class="titulo-dashboard">Dashboard</h1>', unsafe_allow_html=True)    
    
    # Métricas Superiores
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid {M2_AZUL_CLARO};"><p class="metric-label">COLABORADORES</p><p class="metric-value">{len(df_filtrado)}</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid {M2_AZUL_CLARO};"><p class="metric-label">CARGO</p><p class="metric-value" style="font-size:18px;">{sel_cargo}</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card" style="border-top: 4px solid {M2_AZUL_CLARO};"><p class="metric-label">UNIDADE</p><p class="metric-value" style="font-size:18px;">{sel_unidade}</p></div>', unsafe_allow_html=True)
    with m4:
            # Cálculo Seguro da Média de Idade
            if col_idade and not df_filtrado.empty:
                media_etaria = df_filtrado[col_idade].mean()
                val_media = f"{media_etaria:.1f}"
            else:
                val_media = "N/A"
            st.markdown(f'<div class="metric-card" style="border-top: 4px solid {M2_AZUL_CLARO};"><p class="metric-label">MÉDIA DE IDADE</p><p class="metric-value">{val_media}</p></div>', unsafe_allow_html=True)
        
   
    # --- SEÇÃO DE CELEBRAÇÕES (COM POPUP) ---
    st.markdown("---")

    col_tit, col_pop = st.columns([3, 1])

    with col_tit:
        st.markdown(f"<h1 class='titulo-dashboard'>🎂 Aniversariantes de Hoje ({dia_mes_hoje})</h1>", unsafe_allow_html=True)    
    with col_pop:
        with st.popover("📅 Ver todos do mês", use_container_width=True):
            # Tradução manual para evitar dependência de biblioteca de sistema
            meses_pt = {
                "January": "Janeiro", "February": "Fevereiro", "March": "Março",
                "April": "Abril", "May": "Maio", "June": "Junho",
                "July": "Julho", "August": "Agosto", "September": "Setembro",
                "October": "Outubro", "November": "Novembro", "December": "Dezembro"
            }
            mes_nome_pt = meses_pt.get(hoje.strftime('%B'), hoje.strftime('%B'))
            
            st.markdown(f"#### Aniversariantes de {mes_nome_pt}")

            if not aniv_mes.empty:
                col_data = 'dia_mes' if 'dia_mes' in aniv_mes.columns else 'DD/MM'
                df_exibir = aniv_mes[[col_nome, col_data, col_setor]].copy()
                df_exibir.columns = ['Nome', 'Data', 'Unidade']
                st.dataframe(df_exibir, use_container_width=True, hide_index=True)
            else:
                st.write("Sem registros para este mês.")

    # Exibição dos cards de hoje (Alinhado fora do 'with col_pop')
    if not aniv_hoje.empty:
        cols = st.columns(len(aniv_hoje) if len(aniv_hoje) < 4 else 3)
        for i, (_, row) in enumerate(aniv_hoje.iterrows()):
            with cols[i % len(cols)]:
                st.success(f"✨ **{row[col_nome]}**\n\n{row[col_cargo]} - {row[col_setor]}")
    else:
        st.info("Nenhum aniversariante hoje.")

    st.markdown("---")

# --- 6. GRÁFICOS DINÂMICOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("📊 Distribuição por Unidade")
        fig_barra = px.bar(
            df_filtrado[col_setor].value_counts(),
            color_discrete_sequence=[M2_AZUL_CLARO],
            template="plotly_white",
            labels={'index': 'Unidade', 'value': 'Qtd'}
        )
        fig_barra.update_layout(height=300,showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_barra, use_container_width=True)

    with g2:
        st.subheader("⏳ Tempo de Empresa (Anos)")
        
        if col_data_adm:
            # Cálculo dos anos (mesma lógica anterior)
            df_filtrado[col_data_adm] = pd.to_datetime(df_filtrado[col_data_adm], errors='coerce')
            hoje = datetime.now()
            df_filtrado['Anos_Empresa'] = df_filtrado[col_data_adm].apply(
                lambda x: (hoje - x).days / 365.25 if pd.notnull(x) else 0
            )
            
            # Categorização
            def categorizar_tempo(anos):
                if anos < 1: return "<1 ano"
                elif 1 <= anos < 3: return "1-3 anos"
                elif 3 <= anos < 5: return "3-5 anos"
                else: return ">5 anos"
            
            df_filtrado['Faixa_Tempo'] = df_filtrado['Anos_Empresa'].apply(categorizar_tempo)
            contagem_tempo = df_filtrado['Faixa_Tempo'].value_counts()

            # Gráfico de Pizza/Rosca
            fig_pizza_tempo = px.pie(
                values=contagem_tempo.values, 
                names=contagem_tempo.index,
                hole=0.5, # Transforma em rosca (mais elegante)
                color_discrete_sequence=[M2_AZUL_ESCURO, M2_AZUL_CLARO, "#F97316", "#E2E8F0"],
                template="plotly_white"
            )
            
            fig_pizza_tempo.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pizza_tempo, use_container_width=True)
        else:
            st.warning("Coluna de Admissão não encontrada.")

# --- 7. EXPLORAÇÃO DE TALENTOS (SIMPLIFICADO) ---
    st.markdown('<h1 class="titulo-dashboard">👥 Exploração de Talentos</h1>', unsafe_allow_html=True)   
    nomes_finais = sorted(df_filtrado[col_nome].unique().tolist())

    if nomes_finais:
        # 1. Campo de seleção ocupando a largura total ou uma largura controlada
        escolha_nome = st.selectbox("Selecione um colaborador para ver a ficha:", ["-- Escolha um nome --"] + nomes_finais)
        
        # 2. Exibição da Ficha (Apenas se um nome for selecionado)
        if escolha_nome != "-- Escolha um nome --":
            pessoa = df[df[col_nome] == escolha_nome].iloc[0]
            
# --- CORREÇÃO DA DATA AQUI ---
    # Convertemos para datetime e formatamos para o padrão brasileiro
            data_nasc_raw = pd.to_datetime(pessoa[col_nasc], errors='coerce')
            data_nasc_formatada = data_nasc_raw.strftime('%d/%m/%Y') if pd.notnull(data_nasc_raw) else "Não informada"
            
            st.markdown(f"""
                <div class="detail-box">
                    <h3 style='color:#1E3A8A; margin-top:0;'>📄 Ficha: {escolha_nome}</h3>
                    <p><b>Cargo Atual:</b> {pessoa[col_cargo]}</p>
                    <p><b>Unidade:</b> {pessoa[col_setor]}</p>
                    <p><b>Data de Nascimento:</b> {data_nasc_formatada}</p>
                    <p><b>E-mail:</b> <a href="mailto:{pessoa[col_email]}" style="color: {M2_AZUL_CLARO}; text-decoration: none;">{pessoa[col_email]}</a></p>
                </div>
            """, unsafe_allow_html=True)
            
            if col_data_adm:
                data_adm = pd.to_datetime(pessoa[col_data_adm], errors='coerce')
                if pd.notnull(data_adm):
                    anos = (datetime.now() - data_adm).days // 365
                    st.info(f"⏳ Tempo de casa: {anos} anos.")
    else:
        st.warning("Nenhum registro encontrado para esta combinação de filtros.")

# --- 8. LINA ---
if uploaded_file:
    st.markdown("---")
    st.markdown('<h1 class="titulo-dashboard">🤖 Fale com a Lina - Assistente IA</h1>', unsafe_allow_html=True)

    # Quadro do chat
    with st.container(border=True):
        area_chat = st.container(height=400, border=False)
        
        # Exibe as mensagens existentes
        with area_chat:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # Input de texto centralizado
        if prompt := st.chat_input("Ex: Qual a unidade com mais colaboradores?", key="input_final_lina"):
            # 1. CRIAR O CONTEXTO REAL (O que a Lina deve ler)
            amostra_dados = df_filtrado[[col_nome, col_setor, col_cargo, col_nasc]].head(30).to_json(orient='records')

            contexto_rh = f"""
            VOCÊ É A LINA, ANALISTA DE RH DA ALMA PERFUMADA.
            Sua base de dados atual contém {len(df_filtrado)} registros.

            DADOS REAIS PARA CONSULTA (JSON):
            {amostra_dados}

            INSTRUÇÕES:
            1. Use os dados acima para responder perguntas específicas sobre nomes, datas e setores.
            2. Se a pergunta for sobre totais, considere que o total no dashboard é {len(df_filtrado)}.
            3. Mês atual: {datetime.now().strftime('%B')}.
            4. Se a informação não estiver no JSON acima, responda com base na sua experiência geral de RH, mas avise que não localizou o dado exato na planilha.

            Pergunta: {prompt}
            """
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with area_chat:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            try:
                # 2. ENVIAR O CONTEXTO + PERGUNTA
                payload = {"question": contexto_rh} 
                headers = {"Authorization": f"Bearer {API_TOKEN}"}
                
                with st.spinner("Lina analisando dados reais..."):
                    r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
                    if r.status_code == 200:
                        resposta = r.json().get('text', "Lina não conseguiu processar.")
                    else:
                        resposta = "⚠️ O cérebro da Lina está lento. Tente novamente."
            except Exception as e:
                resposta = "⚠️ Erro de conexão com a base de conhecimento."
            
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            st.rerun()
else:
    st.info("Aguardando upload do CSV para iniciar a análise.")