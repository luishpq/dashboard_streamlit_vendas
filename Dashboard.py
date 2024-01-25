import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'

#Realizando o filtro antes de ler a utl no .get (pois a API de dados fornece essa opção)
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

#Criando o select box no Streamlit
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

#Criando dicionario que ira modificar o url
    
query_string = {'regiao':regiao.lower(),
                'ano':ano}


#Usando método get da biblioteca requests para fazer a requisição da API
response = requests.get(url, params=query_string)


dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

#Criando filtro de MULTISELECT para vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
    

#DataFrame por vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count']))

###########TABELAS##########

#GroupBy de Total da Receita (soma) por Estado (local de compra)
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()

#Criar uma tabela com a informação de latitude e longitude e realizar o merge com a informação acima
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

#Criando receita mensal
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
#Coletar o nome do mês para cada registro
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

#Criar tabela para agrupar receita por estado (TOP 5)
receitas_estados_groupby = dados.groupby('Local da compra')[['Preço']].sum().sort_values(by='Preço', ascending=False).head(5)

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values(by='Preço', ascending=False)

###########GRÁFICOS##############################

fig_mapa_receita = px.scatter_geo(receita_estados, 
                                  lat = 'lat', 
                                  lon = 'lon', 
                                  scope = 'south america', 
                                  size = 'Preço', 
                                  template = 'seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat':False, 'lon': False},
                                  title='Receita por estado')


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y=(receita_mensal.min(), receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_por_estado = px.bar(receitas_estados_groupby,
                                text_auto=True,
                                title = 'Top estados (Receita)')

fig_receita_por_estado.update_layout(yaxis_title = 'Receita')


fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title = 'Top estados (Receita)')

fig_receita_categorias.update_layout(yaxis_title = 'Receita')

########### FUNÇÕES ###################

#Criando uma função para formatar números
def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

##########ABAS DO STREAMLIT ###################
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])


##########VISUALIZAÇÃO NO STREAMLIT##############

#Agora usando a variavel dados conseguimos buscar o arquivo Json como DataFrame
#Criando o layout em formato de colunas

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
    #Para criar cartões (métricas) deve-se executar o código abaixo:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))
        #Passando o gráfico criado anteriormente com o mapa
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_por_estado)
    with coluna2:
        
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        #Passando o gráfico com a receita mensal
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
    #Para criar cartões (métricas) deve-se executar o código abaixo:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))

    with coluna2:
        
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))


with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
    #Para criar cartões (métricas) deve-se executar o código abaixo:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))
        tabela_vendedores = vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores)
        fig_receita_vendedores = px.bar(tabela_vendedores,
                                        x = 'sum',
                                        y=tabela_vendedores.index,
                                        text_auto = True,
                                        title = f'Top{qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))



#Para fazer o DataFrame ser melhor apresentado no Streamlit pode-se utilizar:

#Dados
#st.dataframe(dados)


