# analisis_url.py

import streamlit as st
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os
from extractor import ExtractorCaracteristicasURL

def take_screenshot(url, save_path="screenshot.png"):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(url)
    driver.set_window_size(1920, 1080)
    driver.save_screenshot(save_path)
    driver.quit()

def analisis_url(extractor):
    st.title("Análisis de URL")

    query_params = st.query_params
    url_input = query_params.get("url", [""])
    if not url_input[0] or url_input[0] == "":
        url_input = ""
    url_input = st.text_input("Introduce la URL a analizar", value=url_input)

    if url_input:
        maligna = st.checkbox("¿Es maligna?")
        with st.spinner("Extrayendo características..."):
            try:
                caracteristicas = extractor.extraer_caracteristicas(url_input, maligna)
                st.success("Características extraídas con éxito")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="Longitud de la URL", value=caracteristicas['longitud'])
                    st.metric(label="Cantidad de dígitos", value=caracteristicas['cantidad_digitos'])
                    st.metric(label="Cantidad de letras", value=caracteristicas['cantidad_letras'])
                    st.metric(label="Número de subdominios", value=caracteristicas['numero_subdominios'])
                    st.metric(label="Entropía del SLD", value=f"{caracteristicas['entropia_sld']:.2f}")
                
                with col2:
                    st.metric(label="¿Usa HTTPS?", value="Sí" if caracteristicas['usa_https'] else "No")
                    st.metric(label="¿Está indexada en Google?", value="Sí" if caracteristicas['indexada_en_google'] else "No")
                    st.metric(label="¿Está online?", value="Sí" if caracteristicas['esta_online'] else "No")
                    st.metric(label="¿Redirige?", value="Sí" if caracteristicas['redirige'] else "No")
                    st.metric(label="¿Es acortada?", value="Sí" if caracteristicas['es_acortada'] else "No")
                
                with col3:
                    st.metric(label="¿Es maligna?", value="Sí" if caracteristicas['maligna'] else "No")
                    st.metric(label="Ciudad", value=caracteristicas['ciudad'] if caracteristicas['ciudad'] else "Desconocido")
                    st.metric(label="País", value=caracteristicas['pais'] if caracteristicas['pais'] else "Desconocido")

                if caracteristicas.get('latitude') and caracteristicas.get('longitude'):
                    m = folium.Map(location=[caracteristicas['latitude'], caracteristicas['longitude']], zoom_start=5)
                    folium.Marker(
                        location=[caracteristicas['latitude'], caracteristicas['longitude']],
                        popup=f"{caracteristicas['ciudad']}, {caracteristicas['pais']}",
                    ).add_to(m)
                    st_folium(m, width=700, height=500)
                else:
                    st.warning("No se pudo obtener la localización de esta URL")

                lexicas = {
                    'Punto': caracteristicas['count_punto'],
                    'Guion': caracteristicas['count_guion'],
                    'Guion bajo': caracteristicas['count_guion_bajo'],
                    'Slash': caracteristicas['count_slash'],
                    'Interrogacion': caracteristicas['count_interrogacion'],
                    'Igual': caracteristicas['count_igual'],
                    'Arroba': caracteristicas['count_arroba'],
                    'Ampersand': caracteristicas['count_ampersand'],
                    'Exclamacion': caracteristicas['count_exclamacion'],
                    'Espacio': caracteristicas['count_espacio'],
                    'Tilde': caracteristicas['count_tilde'],
                    'Coma': caracteristicas['count_coma'],
                    'Mas': caracteristicas['count_mas'],
                    'Asterisco': caracteristicas['count_asterisco'],
                    'Numeral': caracteristicas['count_numeral'],
                    'Dolar': caracteristicas['count_dolar'],
                    'Porcentaje': caracteristicas['count_porcentaje']
                }
                lexicas = {k: v for k, v in lexicas.items() if v > 0}

                if lexicas:
                    fig, ax = plt.subplots()
                    ax.bar(lexicas.keys(), lexicas.values())
                    ax.set_xlabel('Característica')
                    ax.set_ylabel('Conteo')
                    ax.set_title('Características Léxicas de la URL')
                    st.pyplot(fig)
                
                try:
                    screenshot_path = "screenshot.png"
                    take_screenshot(url_input, screenshot_path)
                    st.image(screenshot_path, caption="Vista previa de la página", use_column_width=True)
                except Exception as e:
                    st.warning(f"No se pudo obtener una vista previa de la página: {e}")

            except Exception as e:
                st.error(f"Error al procesar la URL: {e}")
