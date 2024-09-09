# extractor.py

import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
from collections import Counter
import math
import geoip2.database
import re
import whois
import ssl
import socket
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import urllib.parse
class ExtractorCaracteristicasURL:
    def __init__(self, db_config, geoip_db_path):
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()
        self.geoip_reader = geoip2.database.Reader(geoip_db_path)
        
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS CaracteristicasURL (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            longitud INTEGER,
            cantidad_digitos INTEGER,
            cantidad_letras INTEGER,
            count_punto INTEGER,
            count_guion INTEGER,
            count_guion_bajo INTEGER,
            count_slash INTEGER,
            count_interrogacion INTEGER,
            count_igual INTEGER,
            count_arroba INTEGER,
            count_ampersand INTEGER,
            count_exclamacion INTEGER,
            count_espacio INTEGER,
            count_tilde INTEGER,
            count_coma INTEGER,
            count_mas INTEGER,
            count_asterisco INTEGER,
            count_numeral INTEGER,
            count_dolar INTEGER,
            count_porcentaje INTEGER,
            domain TEXT,
            domain_length INTEGER,
            cantidad_vocales_dominio INTEGER,
            dominio_resuelve_a_ip BOOLEAN,
            directory TEXT,
            directory_length INTEGER,
            file TEXT,
            file_length INTEGER,
            parameters TEXT,
            parameters_length INTEGER,
            tld TEXT,
            tld_present BOOLEAN,
            numero_parametros INTEGER,
            email_presente BOOLEAN,
            tls_version TEXT,
            tld_type TEXT,
            tld_manager TEXT,
            whois_registrar TEXT,
            whois_creation_date TIMESTAMP,
            whois_expiration_date TIMESTAMP,
            whois_updated_date TIMESTAMP,
            whois_status TEXT,
            es_acortada BOOLEAN,
            numero_subdominios INTEGER,
            entropia_sld FLOAT,
            ciudad TEXT,
            pais TEXT,
            dominio_benigno INTEGER,
            tiene_palabras_sospechosas BOOLEAN,
            palabras_detectadas TEXT,
            tiene_hexadecimal BOOLEAN,
            redirige BOOLEAN,
            esta_registrada BOOLEAN,
            esta_online BOOLEAN,
            tiene_directorios BOOLEAN,
            tiene_file BOOLEAN,
            edad_dominio INTEGER,
            tiempo_restante INTEGER,
            queries_buenas BOOLEAN,
            queries_malas BOOLEAN,
            maligna BOOLEAN,
            tiene_puerto BOOLEAN,
            dominio_es_ip BOOLEAN,
            usa_https BOOLEAN,
            indexada_en_google BOOLEAN,
            tiene_tls BOOLEAN,
            dominio_registrado BOOLEAN,
            contiene_scripts BOOLEAN,
            contiene_caracteres_no_decodificables BOOLEAN
        )
        """)
        self.conn.commit()
        
    def asegurar_http(self, url):
        if not url.startswith(('http://', 'https://')):
            return 'http://' + url
        return url
    
    def contar_caracteres(self, texto):
        return Counter(texto)

    def calcular_entropia(self, texto):
        probabilidad = [float(texto.count(c)) / len(texto) for c in dict.fromkeys(list(texto))]
        return -sum(p * math.log(p) / math.log(2.0) for p in probabilidad)

    def obtener_ip_de_dominio(self, url):
        try:
            dominio = urlparse(url).netloc
            return socket.gethostbyname(dominio)
        except socket.gaierror as e:
            print(f"Error al obtener la IP del dominio: {e}")
            return None

    def obtener_ubicacion_de_ip(self, ip):
        try:
            respuesta = self.geoip_reader.city(ip)
            return {
                "ciudad": respuesta.city.name,
                "pais": respuesta.country.name,
                "latitude": respuesta.location.latitude,
                "longitude": respuesta.location.longitude
            }
        except Exception as e:
            print(f"Error al obtener la ubicación de la IP: {e}")
            return {'ciudad': None, 'pais': None, 'latitude': None, 'longitude': None}

    def verificar_dominio(self, dominio):
        self.cur.execute("SELECT benigno FROM dominios WHERE domain = %s OR domain = %s", (dominio, dominio.replace('www.', '')))
        result = self.cur.fetchone()
        if result is None:
            dominio_sin_tld = '.'.join(dominio.split('.')[:-1])
            self.cur.execute("SELECT benigno FROM dominios WHERE domain = %s OR domain = %s", (dominio_sin_tld, dominio_sin_tld.replace('www.', '')))
            result = self.cur.fetchone()
            if result is None:
                return 0
        return 1 if result[0] else -1

    def tiene_palabras_sospechosas(self, url, dominio):
        palabras_sospechosas = set()
        self.cur.execute("SELECT palabra FROM palabras")
        palabras = [row[0] for row in self.cur.fetchall()]

        url_sin_protocolo = re.sub(r'^https?://', '', url)
        partes_url = re.split(r'\W+', url_sin_protocolo)
        partes_dominio = re.split(r'\W+', dominio)

        for palabra in palabras:
            if palabra in partes_url or palabra in partes_dominio:
                palabras_sospechosas.add(palabra)

        return bool(palabras_sospechosas), list(palabras_sospechosas)

    def es_hexadecimal(self, url):
        return bool(re.search(r'0x[0-9a-fA-F]+', url))

    def verificar_online_y_redirigida(self, url):
        try:
            respuesta = requests.head(url, allow_redirects=True, timeout=2)
            esta_online = respuesta.status_code == 200
            es_redirigida = respuesta.url != url
            return esta_online, es_redirigida
        except requests.RequestException as e:
            print(f"Error al comprobar la URL: {e}")
            return False, False

    def verificar_registro(self, dominio):
        try:
            w = whois.whois(dominio)
            return bool(w.creation_date)
        except Exception as e:
            return False

    def calcular_edad_dominio(self, creation_date, expiration_date):
        if creation_date and expiration_date:
            return (expiration_date - creation_date).days
        return 0

    def calcular_tiempo_restante(self, expiration_date):
        if expiration_date:
            return (expiration_date - datetime.datetime.now()).days
        return 0

    def extraer_query(self, url):
        parsed_url = urlparse(url)
        return parsed_url.path + '?' + parsed_url.query if parsed_url.query else parsed_url.path

    def comprobar_query_en_db(self, query):
        self.cur.execute("SELECT * FROM queries WHERE query = %s", (query,))
        resultado = self.cur.fetchone()
        return bool(resultado), resultado

    def buscar_en_db(self, query):
        existe, resultado = self.comprobar_query_en_db(query)
        if existe:
            return query, resultado

        parts = query.split('/')
        for i in range(1, len(parts)):
            subquery = '/' + '/'.join(parts[i:])
            existe, resultado = self.comprobar_query_en_db(subquery)
            if existe:
                return subquery, resultado

        for i in range(len(parts) - 1, 0, -1):
            subquery = '/'.join(parts[:i])
            existe, resultado = self.comprobar_query_en_db(subquery)
            if existe:
                return subquery, resultado

        return None, None

    def tiene_puerto(self, dominio):
        return bool(re.search(r':[0-9]+', dominio))
    
    def dominio_es_ip(self, url):
        parsed_url = urlparse(url)
        dominio = parsed_url.hostname

        if dominio is None:
            return False

        partes_dominio = dominio.split('.')

        if len(partes_dominio) >= 4:
            posible_ip = '.'.join(partes_dominio[-4:])
            patron_ip = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        
            if patron_ip.match(posible_ip):
                segmentos = posible_ip.split('.')
                if all(0 <= int(segmento) <= 255 for segmento in segmentos):
                    return True

        return False

    def verificar_indice_google(self, url):
        consulta = f"site:{url}"
        url_busqueda_google = f"https://www.google.com/search?q={urllib.parse.quote(consulta)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            respuesta = requests.get(url_busqueda_google, headers=headers)
            if respuesta.status_code == 200:
                sopa = BeautifulSoup(respuesta.text, 'html.parser')
                resultados = sopa.find_all('div', class_='g')
                
                indexado = any(url in resultado.find('a')['href'] for resultado in resultados)
                return indexado
        except Exception as e:
            print(f"Error al obtener resultados de búsqueda: {e}")
        return False

    def check_scripts_in_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return len(soup.find_all('script')) > 0
        except requests.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return False

    def check_non_decodable_characters(self, url):
        try:
            respuesta = requests.get(url)
            respuesta.raise_for_status()
            respuesta.content.decode('utf-8')
            return False
        except (requests.RequestException, UnicodeDecodeError) as e:
            print(f"Error fetching or decoding the URL: {e}")
            return True

    def extraer_caracteristicas(self, url, maligna):
        url = self.asegurar_http(url)
        parsed_url = urlparse(url)
        dominio = parsed_url.netloc
        ruta = parsed_url.path
        archivo = parsed_url.path.split('/')[-1] if '/' in parsed_url.path else ''
        parametros = parsed_url.query

        url_counter = self.contar_caracteres(url)
        dominio_counter = self.contar_caracteres(dominio)
        ruta_counter = self.contar_caracteres(ruta)
        archivo_counter = self.contar_caracteres(archivo)
        parametros_counter = self.contar_caracteres(parametros)

        tld_info = self.verificar_tld(dominio.split('.')[-1] if '.' in dominio else '')

        whois_info = self.obtener_info_whois(dominio)

        sld = dominio.split('.')[-2] if '.' in dominio else dominio
        entropia_sld = self.calcular_entropia(sld)

        esta_online, redirige = self.verificar_online_y_redirigida(url)
        usa_https = url.startswith('https://')
        tiene_tls = self.obtener_version_tls(url) is not None
        esta_registrada = self.verificar_registro(dominio)
        contiene_scripts = self.check_scripts_in_url(url)
        contiene_caracteres_no_decodificables = self.check_non_decodable_characters(url)
        
        caracteristicas = {
            'url': url,
            'longitud': len(url),
            'cantidad_digitos': sum(c.isdigit() for c in url),
            'cantidad_letras': sum(c.isalpha() for c in url),
            'count_punto': url_counter['.'],
            'count_guion': url_counter['-'],
            'count_guion_bajo': url_counter['_'],
            'count_slash': url_counter['/'],
            'count_interrogacion': url_counter['?'],
            'count_igual': url_counter['='],
            'count_arroba': url_counter['@'],
            'count_ampersand': url_counter['&'],
            'count_exclamacion': url_counter['!'],
            'count_espacio': url_counter[' '],
            'count_tilde': url_counter['~'],
            'count_coma': url_counter[','],
            'count_mas': url_counter['+'],
            'count_asterisco': url_counter['*'],
            'count_numeral': url_counter['#'],
            'count_dolar': url_counter['$'],
            'count_porcentaje': url_counter['%'],
            'domain': dominio,
            'domain_length': len(dominio),
            'cantidad_vocales_dominio': sum(c in 'aeiouAEIOU' for c in dominio),
            'directory': ruta,
            'directory_length': len(ruta),
            'file': archivo,
            'file_length': len(archivo),
            'parameters': parametros,
            'parameters_length': len(parametros),
            'tld': (dominio.split('.')[-1] if '.' in dominio else ''),
            'numero_parametros': len(parametros.split('&')) if parametros else 0,
            'email_presente': bool(re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', url, re.I)),
            'tld_type': tld_info['type'],
            'tld_manager': tld_info['tld_manager'],
            'whois_registrar': whois_info['registrar'],
            'whois_creation_date': whois_info['creation_date'],
            'whois_expiration_date': whois_info['expiration_date'],
            'whois_updated_date': whois_info['updated_date'],
            'whois_status': whois_info['status'],
            'es_acortada': self.es_url_acortada_combinada(url),
            'numero_subdominios': len(dominio.split('.')) - 2,
            'entropia_sld': entropia_sld,
            'dominio_benigno': self.verificar_dominio(dominio),
            'tiene_palabras_sospechosas': False,
            'palabras_detectadas': '',
            'tiene_hexadecimal': self.es_hexadecimal(url),
            'redirige': redirige,
            'esta_registrada': esta_registrada,
            'esta_online': esta_online,
            'edad_dominio': self.calcular_edad_dominio(whois_info['creation_date'], whois_info['expiration_date']),
            'tiempo_restante': self.calcular_tiempo_restante(whois_info['expiration_date']),
            'tiene_directorios': bool(parsed_url.path and parsed_url.path != '/'),
            'tiene_file': bool(archivo),
            'queries_buenas': False,
            'queries_malas': False,
            'maligna': maligna,
            'tiene_puerto': self.tiene_puerto(dominio),
            'dominio_es_ip': self.dominio_es_ip(url),
            'usa_https': usa_https,
            'indexada_en_google': self.verificar_indice_google(url),
            'tiene_tls': tiene_tls,
            'dominio_registrado': esta_registrada,
            'contiene_scripts': contiene_scripts,
            'contiene_caracteres_no_decodificables': contiene_caracteres_no_decodificables
        }

        if esta_online:
            ip = self.obtener_ip_de_dominio(url)
            ubicacion = self.obtener_ubicacion_de_ip(ip) if ip else {'ciudad': None, 'pais': None}
            caracteristicas.update({
                'dominio_resuelve_a_ip': bool(ip),
                'ciudad': ubicacion['ciudad'],
                'pais': ubicacion['pais'],
                'latitude': ubicacion['latitude'],
                'longitude': ubicacion['longitude'],
                'tls_version': self.obtener_version_tls(url),
            })
        else:
            caracteristicas.update({
                'dominio_resuelve_a_ip': False,
                'ciudad': None,
                'pais': None,
                'latitude': None,
                'longitude': None,
                'tls_version': None,
            })

        tiene_palabras_sospechosas, palabras_detectadas = self.tiene_palabras_sospechosas(url, dominio)
        caracteristicas.update({
            'tiene_palabras_sospechosas': tiene_palabras_sospechosas,
            'palabras_detectadas': ', '.join(palabras_detectadas),
        })

        query = self.extraer_query(url)
        subquery, resultado_query = self.buscar_en_db(query)

        if subquery and resultado_query:
            caracteristicas.update({
                'queries_buenas': resultado_query[2],
                'queries_malas': not resultado_query[2],
            })

        return caracteristicas

    def verificar_tld(self, tld):
        self.cur.execute("SELECT type, tld_manager FROM tlds WHERE domain = %s", ('.' + tld,))
        result = self.cur.fetchone()
        return {
            'type': result[0] if result else None,
            'tld_manager': result[1] if result else None
        }

    def obtener_info_whois(self, dominio):
        try:
            w = whois.whois(dominio)
            return {
                'registrar': w.registrar,
                'creation_date': w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date,
                'expiration_date': w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date,
                'updated_date': w.updated_date[0] if isinstance(w.updated_date, list) else w.updated_date,
                'status': w.status
            }
        except Exception as e:
            return {
                'registrar': None,
                'creation_date': None,
                'expiration_date': None,
                'updated_date': None,
                'status': None
            }

    def obtener_version_tls(self, url):
        try:
            parsed_url = urlparse(url)
            contexto = ssl.create_default_context()
            with socket.create_connection((parsed_url.netloc, 443)) as sock:
                with contexto.wrap_socket(sock, server_hostname=parsed_url.netloc) as ssock:
                    return ssock.version()
        except Exception as e:
            return None

    def es_url_acortada(self, url):
        self.cur.execute("SELECT url_provider FROM shorturl")
        short_url_providers = [row[0] for row in self.cur.fetchall()]
        dominio = urlparse(url).netloc
        return dominio in short_url_providers

    def es_url_redirigida(self, url):
        try:
            respuesta = requests.head(url, allow_redirects=True)
            return respuesta.url != url
        except requests.RequestException as e:
            print(f"Error al comprobar la URL: {e}")
            return False

    def es_url_acortada_combinada(self, url):
        return self.es_url_acortada(url) or self.es_url_redirigida(url)

    def insertar_caracteristicas(self, caracteristicas):
        columns = sql.SQL(', ').join(map(sql.Identifier, caracteristicas.keys()))
        values = sql.SQL(', ').join(sql.Placeholder() * len(caracteristicas))
        insert_query = sql.SQL("INSERT INTO CaracteristicasURL ({}) VALUES ({})").format(
            columns, values
        )
        self.cur.execute(insert_query, list(caracteristicas.values()))
        self.conn.commit()

    def cerrar_conexion(self):
        self.cur.close()
        self.conn.close()

    def obtener_datos_caracteristicas(self):
        query = "SELECT * FROM CaracteristicasURLs"
        return pd.read_sql(query, self.conn)
