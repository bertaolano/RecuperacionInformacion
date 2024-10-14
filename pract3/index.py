"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
index.py
Authors: Carlos Giralt and Berta Olano


Simple program to create an inverted index with the contents of text/xml files contained in a docs folder
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python3 index.py -docs <docsPath> ../dublinCore -index <indexPath>
"""

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import LanguageAnalyzer
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter, StemFilter
from custom_filters import CustomSpanishStemmingFilter


import os

import xml.etree.ElementTree as ET
import email.utils
#LANGUAGE = 'english'
LANGUAGE = 'spanish'

ns= {'dc':'http://purl.org/dc/elements/1.1/','ows':'http://www.opengis.net/ows'}   #definimos el espacio de nombres


#creamos nuestro propio analizador de texto en español
def CustomSpanishAnalyzer():
    return (RegexTokenizer(r"\w+(\.?\w+)*") |  # Paso 1: Tokenización
            LowercaseFilter() |               # Paso 2: Convertir a minúsculas
            StopFilter(lang="es") |            # Paso 3: Filtro de palabras vacías en español
            CustomSpanishStemmingFilter())     # Paso 4: Stemming personalizado

# crea un directorio si no existe ya
def create_folder(folder_name):
    if (not os.path.exists(folder_name)):
        os.mkdir(folder_name)

# busca en el campo especificado en parameter
def find_parameter(root, parameter):
    aux = root.findall('dc:'+parameter, ns)
    matches = " ".join([match.text for match in aux if match.text is not None])
    return matches

#encontrar búsquedas en el campo departamento
def find_publisher(root):
    publishers = root.findall('dc:publisher', ns)
    departments = [] # Lista para almacenar los departamentos encontrados
    for publisher in publishers:
        if publisher.text:
            # Dividir el texto por ';' para separar las partes
            parts = publisher.text.split(';')
            for part in parts:
                part = part.strip()  # Eliminar espacios alrededor de cada parte
                if part.startswith("Departamento"):
                    departments.append(part)  # Agregar el departamento a la lista   
    # Concatenar todos los departamentos encontrados, uno por línea
    return " ".join(departments)

#encontrar búsquedas en el campo año de publicación
def find_Publishingyear(root):
    dates = root.findall('dc:date', ns)
    if dates and dates[0].text is not None:
        try:
            # Intentamos extraer solo el año si es un valor numérico
            return int(dates[0].text[:4])
        except ValueError:
            return None  # Si no es un número válido, devolvemos None
    return None  # Si no se encuentra un año
 

class MyIndex:
    def __init__(self, index_folder):
        schema = Schema(path=ID(stored=True), date=STORED, title=TEXT(analyzer=CustomSpanishAnalyzer()), 
                        subject=TEXT(analyzer=CustomSpanishAnalyzer()), description=TEXT(analyzer=CustomSpanishAnalyzer()), 
                        creator=TEXT(analyzer=CustomSpanishAnalyzer()), contributor=TEXT(analyzer=CustomSpanishAnalyzer()),
                        publisher=TEXT(analyzer=CustomSpanishAnalyzer()), 
                        publishingyear=NUMERIC(numtype=int), identifier=TEXT(stored=True), docType=KEYWORD(lowercase=True), language=KEYWORD)
        create_folder(index_folder)
        index = create_in(index_folder, schema)
        self.writer = index.writer()

    def index_docs(self, docs_folder):   #indexa documentos
        if (os.path.exists(docs_folder)):
            for file in sorted(os.listdir(docs_folder)):
                # print(file)
                if file.endswith('.xml'):
                    self.index_xml_doc(docs_folder, file)
                elif file.endswith('.txt'):
                    self.index_txt_doc(docs_folder, file)
        self.writer.commit()

    def index_txt_doc(self, foldername, filename):   #para ficheros .txt
        file_path = os.path.join(foldername, filename)
        # print(file_path)
        d=os.path.getmtime(file_path)
        fecha_formateada = email.utils.formatdate(d, usegmt=False)
        self.writer.add_document(path=filename, date=fecha_formateada)


    def index_xml_doc(self, foldername, filename):  #para ficheros .xml
        file_path = os.path.join(foldername, filename)
        # print(file_path)
        tree = ET.parse(file_path)
        root = tree.getroot()
        d=os.path.getmtime(file_path)   #extraemos última fecha de modificación
        fecha_formateada = email.utils.formatdate(d, usegmt=False)  #formateamos la fecha
        self.writer.add_document(path=filename, date=fecha_formateada, title=find_parameter(root, 'title'),
                                 subject=find_parameter(root, "subject"), description=find_parameter(root, "description"), creator=find_parameter(root, "creator"),
                                 contributor=find_parameter(root, "contributor"), publisher=find_publisher(root),
                                 publishingyear=find_Publishingyear(root), identifier=find_parameter(root, "identifier"), docType=find_parameter(root, "type"),
                                 language=find_parameter(root, "language"))

if __name__ == '__main__':

    index_folder = '../whooshindexZaguan'   #valor por defecto de la carpeta de indexación
    #docs_folder = '../dublinCore'         #valor por defecto de la carpeta de documentos DublinCore
    docs_folder = '../../recordsdc'         #valor por defecto de la carpeta de documentos del repertorio de Zaguan
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-index':
            index_folder = sys.argv[i + 1]
            i = i + 1
        elif sys.argv[i] == '-docs':
            docs_folder = sys.argv[i + 1]
            i = i + 1
        i = i + 1

    my_index = MyIndex(index_folder)
    my_index.index_docs(docs_folder)


