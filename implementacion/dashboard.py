import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))



# dashboard.py

import streamlit as st
from streamlit_option_menu import option_menu
from extractor import ExtractorCaracteristicasURL
from analisis_url import analisis_url
from estadisticas import estadisticas

db_config = {
    'dbname': 'url',
    'user': 'postgres',
    'password': '1234',
    'host': 'localhost',
    'port': '5432',
    'options': '-c client_encoding=UTF8'  
}

geoip_db_path = 'D:\\yo\\GeoLite2-City.mmdb'

extractor = ExtractorCaracteristicasURL(db_config, geoip_db_path)

def inject_css():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 90%;
            padding: 4rem 1rem 1rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
inject_css()

selected = option_menu(
    menu_title="Dashboard de URLs",
    options=["Análisis de URL", "Estadísticas"],
    icons=["link", "bar-chart"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal"
)

if selected == "Análisis de URL":
    analisis_url(extractor)
elif selected == "Estadísticas":
    estadisticas(extractor)

extractor.cerrar_conexion()
