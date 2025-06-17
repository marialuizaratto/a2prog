import os
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Quiz de Raças Caninas", page_icon="🐕")

CSV_PATH = 'dogs.csv'
WIKI_BASE_URL = "https://pt.wikipedia.org/wiki/"

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8')
        colunas_obrigatorias = ['Nome', 'Porte', 'Tipo', 'Amigavel (1-10)', 
            'Dificuldade de Treino (1-10)', 'Necessidade de Tosa', 'Bom com Crianças',
            'Inteligência (1-10)', 'Nível de Queda de Pelo']
        if not all(col in df.columns for col in colunas_obrigatorias):
            st.error(f"Erro: Colunas obrigatórias faltando: {set(colunas_obrigatorias) - set(df.columns)}")
            st.stop()
        df.set_index('Nome', inplace=True)
        return df.to_dict(orient='index')
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{CSV_PATH}' não encontrado.")
        st.stop()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {str(e)}")
        st.stop()

def buscar_conteudo_wikipedia(nome_raca):
    url = f"{WIKI_BASE_URL}{nome_raca.replace(' ', '_')}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox'})
        foto = f"https:{infobox.find('img').get('src')}" if infobox and infobox.find('img') else None
        resumo = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 50]
        return {'foto_url': foto, 'resumo': '\n\n'.join(resumo)[:800] + ('...' if len(resumo) > 1 else ''), 'link': url}
    except Exception as e:
        st.warning(f"Não foi possível acessar Wikipedia: {str(e)}")
        return None

def mostrar_resultado(raca, dados):
    st.success(f"✨ A raça que mais combina com você é: **{raca.upper()}**")
    st.subheader("🐾 Características da raça:")
    for chave, valor in dados.items():
        st.write(f"- **{chave}**: {valor}")
    wiki_info = buscar_conteudo_wikipedia(raca)
    if wiki_info:
        if wiki_info['foto_url']:
            st.image(wiki_info['foto_url'], caption=raca, use_container_width=True)
        st.subheader("📚 Sobre a raça (Wikipedia):")
        st.write(wiki_info['resumo'])
        st.markdown(f"[Leia mais na Wikipedia]({wiki_info['link']})")
    else:
        st.warning("Não foram encontradas informações adicionais sobre esta raça.")

def quiz():
    st.title("🐶 Quiz: Qual é a raça de cachorro ideal para você?")
    st.write("Responda às perguntas abaixo e descubra a raça que mais combina com seu estilo de vida!")
    racas = carregar_dados()
    with st.form("quiz_form"):
        porte = st.selectbox("Porte do cachorro:", ["Pequeno", "Pequeno-Médio", "Médio", "Grande"])
        tipo = st.selectbox("Tipo de cachorro:", ["Caça", "Trabalhador", "Terrier", "Pastor", "Esportista", "Não esportista", "Standart", "Toy"])
        amigavel = st.slider("Nível de amigabilidade:", 1, 5, 3)
        treinamento = st.slider("Importância do treinamento:", 1, 5, 3)
        tosa = st.selectbox("Necessidade de tosa:", ["Pequena", "Média", "Grande", "Muito grande"])
        criancas = st.radio("Bom com crianças:", ["Sim", "Não", "Sim, mesmo que precise treinar"])
        inteligencia = st.slider("Nível de inteligência:", 1, 5, 3)
        pelo = st.selectbox("Processo de troca de pelo:", ["Pequeno", "Médio", "Grande", "Muito grande"])
        submitted = st.form_submit_button("🔍 Descobrir minha raça ideal")

    if submitted:
        melhor_raca, melhor_pontos = None, -1
        for nome_raca, dados in racas.items():
            pontos = 0
            if dados.get('Porte', '').strip().lower() == porte.lower(): pontos += 2
            if dados.get('Tipo', '').strip().lower() == tipo.lower(): pontos += 1
            if abs(dados.get('Amigavel (1-10)', 0) - amigavel) <= 1: pontos += 1
            if dados.get('Dificuldade de Treino (1-10)', 0) >= treinamento: pontos += 1
            if dados.get('Necessidade de Tosa', '').strip().lower() == tosa.lower(): pontos += 2
            if (criancas == 'Sim' and dados.get('Bom com Crianças') == 'Sim') or \
               (criancas == 'Sim, mesmo que precise treinar' and dados.get('Bom com Crianças') in ['Sim', 'Caso treinado']): pontos += 2
            if dados.get('Inteligência (1-10)', 0) >= inteligencia: pontos += 1
            if dados.get('Nível de Queda de Pelo', '').strip().lower() == pelo.lower(): pontos += 1
            if pontos > melhor_pontos:
                melhor_pontos, melhor_raca = pontos, nome_raca
        if melhor_raca:
            mostrar_resultado(melhor_raca, racas[melhor_raca])
        else:
            st.warning("Não encontramos uma raça que corresponda às suas preferências. Tente ajustar seus critérios.")

if __name__ == "__main__":
    quiz()
