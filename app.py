import streamlit as st
import pandas as pd
import joblib
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="FC Porto Data Office", page_icon="🔵", layout="wide")

# Estilização
st.markdown("<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #004494; }</style>", unsafe_allow_html=True)

# CORREÇÃO AQUI: Adicionado o '@' e removido o espaço para funcionar como decorador
@st.cache_resource
def load_assets():
    model = joblib.load('modelo_fc_porto.pkl')
    data = pd.read_csv('dados_limpos_porto.csv')
    
    # Definindo as colunas que o modelo espera
    features = ['ovr', 'pac', 'sho', 'pas', 'dri', 'def', 'phy', 'rank']
    
    # Criar uma coluna de 'Potencial de Valorização'
    data['valor_previsto'] = model.predict(data[features])
    data['oportunidade'] = data['valor_previsto'] - data['value_eur']
    return model, data

# Chamada da função
modelo, df = load_assets()

# --- SIDEBAR ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/pt/e/ed/FC_Porto.png", width=80)
st.sidebar.title("Menu de Scouting")
aba = st.sidebar.radio("Escolha uma visão:", ["Análise Individual", "Exploração de Mercado"])

# --- ABA 1: ANÁLISE INDIVIDUAL ---
if aba == "Análise Individual":
    st.title("🔵 Análise Detalhada do Atleta")
    nome_jogador = st.selectbox("Selecione o Atleta", df['name'].unique())
    player_data = df[df['name'] == nome_jogador].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("OVR", player_data['ovr'])
    col2.metric("PAC", player_data['pac'])
    col3.metric("PAS", player_data['pas'])
    col4.metric("Valor Estimado", f"€{player_data['valor_previsto']:,.0f}")

    st.divider()
    c_left, c_right = st.columns(2)
    
    # Lista de atributos para os gráficos
    attrs = ['pac', 'sho', 'pas', 'dri', 'def', 'phy']
    
    with c_left:
        st.write("### Perfil Técnico")
        fig = px.line_polar(r=player_data[attrs].values, theta=attrs, line_close=True)
        fig.update_traces(fill='toself', line_color='#004494')
        st.plotly_chart(fig, use_container_width=True)
        
    with c_right:
        st.write("### Comparação com a Média do Mercado")
        # Garantir que todos os valores são decimais (float) para o Plotly
        avg_stats = df[attrs].mean().values.astype(float)
        player_values = player_data[attrs].values.astype(float)
        
        comp_df = pd.DataFrame({
            'Atributo': attrs, 
            'Jogador': player_values, 
            'Média Geral': avg_stats
        })
        
        fig_bar = px.bar(comp_df, x='Atributo', y=['Jogador', 'Média Geral'], 
                         barmode='group',
                         color_discrete_map={'Jogador': '#004494', 'Média Geral': '#CCCCCC'})
        st.plotly_chart(fig_bar, use_container_width=True)


# --- ABA 2: EXPLORAÇÃO DE MERCADO ---
else:
    st.title("📊 Exploração de Mercado (Scouting)")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        min_ovr = st.slider("Mínimo de OVR", 50, 99, 75)
    with col_f2:
        max_price = st.number_input("Orçamento Máximo (€)", value=50000000)

    # Filtrar jogadores que parecem "baratos" pela IA
    negocios = df[(df['ovr'] >= min_ovr) & (df['value_eur'] <= max_price)].sort_values(by='oportunidade', ascending=False)

    st.write(f"### Melhores Oportunidades (OVR >= {min_ovr})")
    st.dataframe(negocios[['name', 'ovr', 'value_eur', 'valor_previsto', 'oportunidade']].head(15))

    st.divider()
    st.write("### Visão Geral: Performance vs Valor")
    # Top 500 para performance do gráfico
    fig_scatter = px.scatter(df.head(500), x='ovr', y='value_eur', hover_name='name', color='pac',
                             size='ovr', title="Top 500 Jogadores: OVR vs Preço",
                             color_continuous_scale=px.colors.sequential.Blues)
    st.plotly_chart(fig_scatter, use_container_width=True)