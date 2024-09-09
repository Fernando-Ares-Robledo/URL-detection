# estadisticas.py

import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def estadisticas(extractor):
    st.title("Estadísticas de Características de URLs")

    data = extractor.obtener_datos_caracteristicas()

    country_coordinates = {
        "The Netherlands": (52.3676, 4.9041),
        "Indonesia": (-0.7893, 113.9213),
        "Italy": (41.8719, 12.5674),
        "Venezuela": (6.4238, -66.5897),
        "Sweden": (60.1282, 18.6435),
        "United Kingdom": (55.3781, -3.4360),
        "Dominican Republic": (18.7357, -70.1627),
        "Ireland": (53.1424, -7.6921),
        "Germany": (51.1657, 10.4515),
        "Singapore": (1.3521, 103.8198),
        "Canada": (56.1304, -106.3468),
        "Finland": (61.9241, 25.7482),
        "Portugal": (39.3999, -8.2245),
        "South Korea": (35.9078, 127.7669),
        "United States": (37.0902, -95.7129),
        "India": (20.5937, 78.9629),
        "France": (46.6034, 1.8883),
        "Brazil": (-14.2350, -51.9253),
        "Australia": (-25.2744, 133.7751),
        "Japan": (36.2048, 138.2529),
        "Mexico": (23.6345, -102.5528),
        "Russia": (61.5240, 105.3188),
        "China": (35.8617, 104.1954),
    }

    data['latitude'] = data['pais'].map(lambda x: country_coordinates.get(x, (None, None))[0])
    data['longitude'] = data['pais'].map(lambda x: country_coordinates.get(x, (None, None))[1])

    data = data.dropna(subset=['latitude', 'longitude'])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribución de URLs Malignas y Benignas")
        malignas_benignas = data['maligna'].value_counts()
        fig = px.pie(values=malignas_benignas, names=['Benignas', 'Malignas'], title='Distribución de URLs Malignas y Benignas')
        st.plotly_chart(fig)

    with col2:
        st.subheader("Distribución de URLs que usan HTTPS")
        https_counts = data['usa_https'].value_counts()
        fig = px.pie(values=https_counts, names=['No usan HTTPS', 'Usan HTTPS'], title='Distribución de URLs que usan HTTPS')
        st.plotly_chart(fig)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Distribución de la Longitud de las URLs")
        fig = px.histogram(data, x='longitud', title='Distribución de la Longitud de las URLs', nbins=50)
        st.plotly_chart(fig)

    with col4:
        st.subheader("Cantidad de Dígitos en las URLs")
        fig = px.histogram(data, x='cantidad_digitos', title='Cantidad de Dígitos en las URLs', nbins=50)
        st.plotly_chart(fig)

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Cantidad de Letras en las URLs")
        fig = px.histogram(data, x='cantidad_letras', title='Cantidad de Letras en las URLs', nbins=50)
        st.plotly_chart(fig)

    with col6:
        st.subheader("Entropía del SLD")
        fig = px.histogram(data, x='entropia_sld', title='Entropía del SLD', nbins=50)
        st.plotly_chart(fig)

    col7, col8 = st.columns(2)

    with col7:
        st.subheader("Distribución de TLDs")
        tld_counts = data['tld'].value_counts().head(10)  
        fig = px.bar(x=tld_counts.index, y=tld_counts.values, title='Distribución de TLDs')
        fig.update_layout(xaxis_title='TLD', yaxis_title='Cantidad')
        st.plotly_chart(fig)

    with col8:
        st.subheader("URLs Registradas y No Registradas")
        registered_counts = data['dominio_registrado'].value_counts()
        fig = px.pie(values=registered_counts, names=['No Registradas', 'Registradas'], title='URLs Registradas y No Registradas')
        st.plotly_chart(fig)

    col9, col10 = st.columns(2)

    with col9:
        st.subheader("Edad de los Dominios")
        fig = px.histogram(data, x='edad_dominio', title='Edad de los Dominios', nbins=50)
        st.plotly_chart(fig)

    with col10:
        st.subheader("Mapa de Densidad de URLs Malignas")
        data_malignas = data[data['maligna'] == True]
        if not data_malignas.empty:
            fig = px.density_mapbox(data_malignas, lat='latitude', lon='longitude', radius=10, zoom=1,
                                    mapbox_style="carto-positron", title='Distribución Geográfica de URLs Malignas')
            st.plotly_chart(fig)
        else:
            st.write("No hay datos de URLs Malignas para mostrar en el mapa.")

    col11, col12 = st.columns(2)

    with col11:
        st.subheader("Mapa de Densidad de URLs Benignas")
        data_benignas = data[data['maligna'] == False]
        if not data_benignas.empty:
            fig = px.density_mapbox(data_benignas, lat='latitude', lon='longitude', radius=10, zoom=1,
                                    mapbox_style="carto-positron", title='Distribución Geográfica de URLs Benignas')
            st.plotly_chart(fig)
        else:
            st.write("No hay datos de URLs Benignas para mostrar en el mapa.")

    with col12:
        st.subheader("Nube de Palabras de Palabras Sospechosas")
        palabras_sospechosas = ' '.join(data[data['tiene_palabras_sospechosas'] == True]['palabras_detectadas'])
        if palabras_sospechosas:
            wordcloud = WordCloud(width=800, height=400, background_color ='white').generate(palabras_sospechosas)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        else:
            st.write("No hay palabras sospechosas para mostrar en la nube de palabras.")

    col13, col14 = st.columns(2)

    with col13:
        st.subheader("Cantidad de URLs por País")
        country_counts = data['pais'].value_counts()
        fig = px.bar(x=country_counts.index, y=country_counts.values, title='Cantidad de URLs por País')
        fig.update_layout(xaxis_title='País', yaxis_title='Cantidad')
        st.plotly_chart(fig)

    with col14:
        st.subheader("Tiempo Restante Hasta la Expiración del Dominio")
        fig = px.histogram(data, x='tiempo_restante', title='Tiempo Restante Hasta la Expiración del Dominio', nbins=50)
        st.plotly_chart(fig)
