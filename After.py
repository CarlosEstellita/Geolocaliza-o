import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from time import sleep

#st.set_option('deprecation.showPyplotGlobalUse', False) # comando para remover Warnings

@st.cache_data # guarda o resultado da função em cache.
def carregar_e_geocodificar_dados():
    """
    Carrega os datasets de restaurantes e bares, realiza a geocodificação uma única vez
    e retorna os dataframes prontos para uso.
    """
    df_restaurantes = pd.read_csv('Mapas/restaurante.csv', sep=';')
    df_bares = pd.read_csv('Mapas/bar.csv', sep=";")
    df_restaurantes_geo = df_restaurantes.copy()
    df_bares_geo = df_bares.copy()

    # Adiciona uma coluna para identificar o tipo de estabelecimento
    df_restaurantes_geo['dataset_type'] = 'restaurante'
    df_bares_geo['dataset_type'] = 'bar'
    # Combina os dois dataframes para geocodificar tudo de uma vez
    df_total = pd.concat([df_restaurantes_geo, df_bares_geo], ignore_index=True)
    df_total.dropna(subset=['LOCAL'], inplace=True) # Garante que não há endereços nulos
    # Inicializa o geolocator
    geolocator = Nominatim(user_agent='app_after', timeout=10)
    latitudes = []
    longitudes = []

    # Geocodifica cada endereço (esta parte lenta só roda uma vez eu acho)
    for endereco in df_total['LOCAL']:
        try:
            location = geolocator.geocode(endereco)
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
            else:
                latitudes.append(None)
                longitudes.append(None)
        except Exception as e:
            # Em caso de erro adiciona None e continua na tora
            latitudes.append(None)
            longitudes.append(None)
        sleep(1) # aparentemente precisa da pausa para não sobrecarregar a API???

    df_total['LAT'] = latitudes
    df_total['LON'] = longitudes
    # Remove linhas que não puderam ser geocodificadas
    df_total.dropna(subset=['LAT', 'LON'], inplace=True)
    # Separa os dataframes novamente
    df_restaurantes_geo_final = df_total[df_total['dataset_type'] == 'restaurante']
    df_bar_geo_final = df_total[df_total['dataset_type'] == 'bar']
    return df_restaurantes_geo_final, df_bar_geo_final

# Carrega os dados usando a função cacheada
df_restaurantes_geo, df_bar_geo = carregar_e_geocodificar_dados()
# Carrega os dados completos para as análises (sem geocodificação)
df_restaurantes_analise = pd.read_csv("Mapas/restaurante.csv", sep=";")
df_bar_analise = pd.read_csv("Mapas/bar.csv", sep=";")


with st.sidebar:
    st.text('Alisson Nobre Nogueira: Frontend')
    st.text('Carlos Estellita Neto: Cientista de Dados')
    st.text('Eulidio Regadas de Souza: Cientista de Dados')

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("Mapas/logo.png", width=300)

tab1, tab2, tab3, tab4 = st.tabs(["Apresentação", "Análise dos restaurantes", "Análise dos bares", "Geolocalização"])

with tab1:
    st.header("Apresentação", divider="red")
    st.markdown("Quando o rolê tá bom, ninguém quer parar, né?")
    st.markdown("Com o After, você decide onde sua noite vai terminar — ou começar de novo.")
    st.markdown("E aí? Bora de After?")
    st.header("Detalhes técnicos", divider="red")
    st.markdown("A aplicação se trata de um serviço de geolocalização, onde é possível o usuário filtrar e encontrar quais estabelecimentos estão disponíveis para continuar sua noite.")
    st.markdown("Foram escolhidos os datasets **restaurante** e **bar**.")
    st.markdown("Na seção de análise de dados, foram plotados gráficos a partir dos atributos julgados como mais relevantes - Pontuação e Tipo de estabelecimento.")
    st.markdown("Por fim, na seção de mapa, há a possibilidade de filtrar os estabelcimentos por pontuação, dataset (restaurante ou bar), especialidade do estabelecimento e por proximidade de distância ao pin selecionado")


with tab2:
    st.header("Análise dos restaurantes")
    # PRIMEIRO GRAFICO RESTAURANTES
    st.markdown("$\;\;\;$ O gráfico abaixo mostra a *contagem de restaurantes por tipo*, destacando que a maioria é classificada genericamente como Restaurante (87 ocorrências), seguido por estabelecimentos com faixas de preço \$\$ (57) e \$\$\$ (28). Tipos específicos como *self-service, **frutos do mar, e **comida brasileira* aparecem em menor número, assim como os tipos raros, como *restaurantes peruanos*, *de sushi* e *pastelarias*, têm apenas 1 ocorrência cada. Isso indica uma grande concentração em categorias genéricas e de médio custo.")
    
    df_limpo = df_restaurantes_analise.dropna(subset=['NOME', 'PONTUACAO', 'TIPO']).copy()
    contagem = df_limpo['TIPO'].value_counts()
    
    rotulos_escapados = [str(s).replace('$', r'\$') for s in contagem.index]
    
    plt.figure(figsize=(12, 7))
    ax1 = sns.barplot(x=rotulos_escapados, y=contagem.values, palette='mako', edgecolor="black")
    
    for i, v in enumerate(contagem.values):
        ax1.text(i, v + 0.5, str(v), ha='center')
    for label in ax1.get_xticklabels():
        label.set_text(label.get_text().replace('\\', ''))
    
    plt.title('Contagem de Restaurantes por Tipo', fontsize=16)
    plt.xlabel('Tipo de Restaurante', fontsize=12)
    plt.ylabel('Quantidade (Frequência)', fontsize=12)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    plt.grid(alpha=0.2)
    plt.tight_layout()
    st.pyplot()
    st.write("####")
    
    #SEGUNDO GRAFICO RESTAURANTES
    st.markdown("$\;\;\;$ Este gráfico exibe os 50 locais com as melhores pontuações, variando de 4,0 a quase 5,0. A maioria pertence às faixas de preço $ e $$, mas há também estabelecimentos mais caros ($$$ e $$$$) com alta avaliação. Isso mostra que tanto locais acessíveis quanto sofisticados podem oferecer excelente qualidade, segundo a opinião dos clientes.")
    faixas_de_preco = ['$', '$$', '$$$', '$$$$']
    
    df_filtrado_por_preco = df_limpo[df_limpo['TIPO'].isin(faixas_de_preco)].copy()
    df_para_plotar = df_filtrado_por_preco.sort_values(by='PONTUACAO', ascending=False).head(50)
    df_para_plotar['TIPO'] = df_para_plotar['TIPO'].apply(lambda s: str(s).replace('$', r'\$'))
    ordem_da_legenda = [r'\$', r'\$\$', r'\$\$\$', r'\$\$\$\$']
    
    plt.figure(figsize=(15, 14), dpi = 500)
    
    sns.barplot(x='PONTUACAO',y='NOME',hue='TIPO',data=df_para_plotar,palette='Blues',edgecolor = "black",hue_order= ordem_da_legenda)
    plt.title('Locais por Pontuação e Faixa de Preço (Top 50)', fontsize=16)
    plt.xlabel('Pontuação', fontsize=12)
    plt.ylabel('Local', fontsize=12)
    plt.xlim(4, 5)
    plt.grid(axis='x', alpha=0.2)
    plt.tight_layout()
    st.pyplot()
    st.write("####")
    
    #TERCEIRO GRAFICO RESTAURANTES
    st.markdown("$\;\;\;$ Este gráfico apresenta os *50 restaurantes mais bem avaliados* por pontuação, destacando também seus *tipos* (como comida caseira, self-service, fast-food, frutos do mar etc.). As notas variam entre *4,5 e 5,0, com forte presença de restaurantes do tipo **genérico*, *comida brasileira* e *caseira. Também aparecem bem avaliados restaurantes **japoneses*, *self-service* e de *faixa de preço variada* (\$ até \$\$\$\$). O gráfico indica que **a alta qualidade é reconhecida em diferentes estilos e preços**, com destaque para os mais tradicionais.")
    df_ordenado = df_limpo.sort_values(by='PONTUACAO', ascending=False)
    df_ordenado['TIPO'] = df_ordenado['TIPO'].apply(lambda s: str(s).replace('$', r'\$'))
    top_50_restaurantes = df_ordenado.head(50)
    plt.figure(figsize=(12, 14))
    sns.barplot(x='PONTUACAO', y='NOME', hue='TIPO', data=top_50_restaurantes, palette='tab10', edgecolor = "black")
    plt.title('Restaurantes por Pontuação e Tipo(Top 50)', fontsize=16)
    
    plt.xlabel('Pontuação', fontsize=12)
    plt.ylabel('Local', fontsize=12)
    plt.xlim(4.5, 5)
    plt.grid(axis='x', alpha = 0.2)
    plt.tight_layout()
    st.pyplot()


with tab3:
    st.header("Análise dos bares")

    #PRIMEIRO GRAFICO BARES
    st.markdown("$\;\;\;$ Este gráfico mostra a *quantidade de bares por tipo*. A maioria é classificada simplesmente como *Bar* (72), seguida por estabelecimentos de faixa de preço *\$\$* (54) e *\$* (25). Tipos mais específicos, como *Bar e Grill*, *Casa noturna* e *Bar de cervejas*, aparecem em números bem menores. Isso indica que os bares são majoritariamente genéricos ou de preço acessível, com **pouca diversidade de categorias especializadas**.")
    
    df_limpo2 = df_bar_analise.dropna(subset=['NOME', 'PONTUACAO', 'TIPO']).copy()
    contagem2 = df_limpo2['TIPO'].value_counts()
    
    rotulos_escapados2 = [str(s).replace('$', r'\$') for s in contagem2.index]
    
    plt.figure(figsize=(12, 7))
    ax2 = sns.barplot(x=rotulos_escapados2, y=contagem2.values, palette='mako', edgecolor="black")
    
    for i, v in enumerate(contagem2.values):
        ax2.text(i, v + 0.5, str(v), ha='center')
    for label in ax2.get_xticklabels():
        label.set_text(label.get_text().replace('\\', ''))
    
    plt.title('Contagem de Bares por Tipo', fontsize=16)
    plt.xlabel('Tipo de Bar', fontsize=12)
    plt.ylabel('Quantidade (Frequência)', fontsize=12)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    plt.grid(alpha=0.2)
    plt.tight_layout()
    st.pyplot()
    
    #SEGUNDO GRAFICO BARES
    st.markdown("$\;\;\;$ Este gráfico mostra os *50 bares mais bem avaliados*, com notas entre *4,0 e 5,0. A maioria está nas faixas de preço *\$* e *\$\$**, com poucos representando categorias mais caras (*\$\$\$ e \$\$\$\$). Isso indica que bares **acessíveis ao público* conseguem atingir *altas pontuações*, demonstrando boa qualidade independente do custo. As avaliações mais altas concentram-se principalmente entre os bares com *preço médio ou popular*.")
    faixas_de_preco = ['$', '$$', '$$$', '$$$$']
    
    df_filtrado_por_preco2 = df_limpo2[df_limpo2['TIPO'].isin(faixas_de_preco)].copy()
    df_para_plotar2 = df_filtrado_por_preco2.sort_values(by='PONTUACAO', ascending=False).head(50)
    df_para_plotar2['TIPO'] = df_para_plotar2['TIPO'].apply(lambda s: str(s).replace('$', r'\$'))
    ordem_da_legenda = [r'\$', r'\$\$', r'\$\$\$', r'\$\$\$\$']
    
    plt.figure(figsize=(15, 14), dpi = 500)
    
    sns.barplot(x='PONTUACAO',y='NOME',hue='TIPO',data=df_para_plotar2,palette='Reds',edgecolor = "black",hue_order=ordem_da_legenda)
    plt.title('Bares por Pontuação e Faixa de Preço (Top 50)', fontsize=16)
    plt.xlabel('Pontuação', fontsize=12)
    plt.ylabel('Local', fontsize=12)
    plt.xlim(4, 5)
    plt.grid(axis='x', alpha=0.2)
    st.pyplot()
    
    #TERCEIRO GRAFICO BARES
    st.markdown("$\;\;\;$ Este gráfico apresenta os 50 bares mais bem avaliados, com pontuações variando de 4,5 a 5,0. A maioria dos locais é classificada como Bar, mas também há presença de bares com música ao vivo, bares e grills, restaurantes, churrascarias e até bares de cerveja.")
    df_ordenado2 = df_limpo2.sort_values(by='PONTUACAO', ascending=False)
    df_ordenado2['TIPO'] = df_ordenado2['TIPO'].apply(lambda s: str(s).replace('$', r'\$'))
    top_50_bares = df_ordenado2.head(50)
    plt.figure(figsize=(12, 14))
    sns.barplot(x='PONTUACAO', y='NOME', hue='TIPO', data=top_50_bares, palette='tab10', edgecolor = "black")
    plt.title('Bares por Pontuação e Tipo(Top 50)', fontsize=16)
    
    plt.xlabel('Pontuação', fontsize=12)
    plt.ylabel('Local', fontsize=12)
    plt.xlim(4.5, 5)
    plt.grid(axis='x', alpha = 0.2)
    plt.tight_layout()
    st.pyplot()


with tab4:
    st.header("Procure seu After aqui!")
    
    # Filtro RANGE SLIDER para encontrar o range de pontuação desejada
    values = st.slider("Selecione o range de pontuação", 0.0, 5.0, (0.0, 5.0), step=0.1)
    
    # Filtro de seleção de tipo de estabelecimento
    tipo_selecionado = st.radio("Escolha o tipo de estabelecimento:", ['Todos', 'Restaurantes', 'Bares'])
    
    # Combina os dataframes já geocodificados
    df_total = pd.concat([df_restaurantes_geo, df_bar_geo], ignore_index=True)

    # Aplica filtro por tipo (restaurante ou bar)
    if tipo_selecionado == 'Restaurantes':
        df_filtrado_tipo = df_total[df_total['dataset_type'] == 'restaurante'].copy()
    elif tipo_selecionado == 'Bares':
        df_filtrado_tipo = df_total[df_total['dataset_type'] == 'bar'].copy()
    else:
        df_filtrado_tipo = df_total.copy()

    # Filtro por especialidade
    if not df_filtrado_tipo.empty:
        especialidades = sorted(df_filtrado_tipo['TIPO'].dropna().unique())
        especialidades.insert(0, "Todos")
        tipo_especialidade = st.selectbox("Escolha a especialidade do local:", especialidades)

        if tipo_especialidade != "Todos":
            df_filtrado_especialidade = df_filtrado_tipo[df_filtrado_tipo['TIPO'] == tipo_especialidade].copy()
        else:
            df_filtrado_especialidade = df_filtrado_tipo.copy()
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")
        df_filtrado_especialidade = pd.DataFrame() # DataFrame vazio se não houver dados

    # Filtro final por pontuação
    if not df_filtrado_especialidade.empty:
        df_final_filtrado = df_filtrado_especialidade[
            (df_filtrado_especialidade['PONTUACAO'] >= values[0]) &
            (df_filtrado_especialidade['PONTUACAO'] <= values[1])
        ].copy()
    else:
        df_final_filtrado = df_filtrado_especialidade
    
    # Caixa de seleção com endereços únicos
    enderecos = df_final_filtrado['LOCAL'].unique().tolist()
    local_referencia = st.selectbox("Escolha um local como referência:", ['Nenhum'] + enderecos)

    if local_referencia != 'Nenhum':
        raio_km = st.slider("Selecione o raio de distância (km):", 1.0, 10.0, 2.0, step=0.1)
        
        # Pega lat/lon do ponto de referência
        ref_row = df_final_filtrado[df_final_filtrado['LOCAL'] == local_referencia].iloc[0]
        ref_coord = (ref_row['LAT'], ref_row['LON'])
        
        # Filtra locais dentro do raio
        df_proximos = df_final_filtrado[
            df_final_filtrado.apply(lambda row: geodesic(ref_coord, (row['LAT'], row['LON'])).km <= raio_km, axis=1)
        ]
        
        # Mapa com destaque
        if not df_proximos.empty:
            mapa = folium.Map(location=ref_coord, zoom_start=15)
            folium.Marker(
                location=ref_coord,
                popup=f"{local_referencia} (Referência)",
                icon=folium.Icon(color='green', icon='star')
            ).add_to(mapa)

            for _, row in df_proximos.iterrows():
                cor = 'red' if row['dataset_type'] == 'bar' else 'blue'
                folium.Marker(
                    location=[row['LAT'], row['LON']],
                    popup=f"{row['NOME']} ({row['PONTUACAO']})",
                    icon=folium.Icon(color=cor)
                ).add_to(mapa)
            folium_static(mapa)
        else:
            st.warning("Nenhum estabelecimento encontrado dentro do raio selecionado.")

    else:
        # Mapa padrão com todos os pontos filtrados
        if not df_final_filtrado.empty:
            # Centraliza o mapa na média das coordenadas
            mapa = folium.Map(location=[df_final_filtrado['LAT'].mean(), df_final_filtrado['LON'].mean()], zoom_start=13)
            for _, row in df_final_filtrado.iterrows():
                cor = 'red' if row['dataset_type'] == 'bar' else 'blue'
                folium.Marker(
                    location=[row['LAT'], row['LON']],
                    popup=f"{row['NOME']} ({row['PONTUACAO']})",
                    icon=folium.Icon(color=cor)
                ).add_to(mapa)
            folium_static(mapa)
        else:
            st.info("Selecione os filtros desejados para ver os estabelecimentos no mapa.")