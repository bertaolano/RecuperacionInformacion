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



def create_folder(folder_name):
    if (not os.path.exists(folder_name)):
        os.mkdir(folder_name)
        
#encontrar búsquedas en el campo título
def find_title(root):
    titles = root.findall('dc:title', ns)
    text = " ".join([title.text for title in titles if title.text is not None])
    return text

#encontrar búsquedas en el campo tema
def find_subject(root):
    subjects = root.findall('dc:subject', ns)
    text = " ".join([subject.text for subject in subjects if subject.text is not None])
    return text

#encontrar búsquedas en el campo descripción
def find_description(root):
    descs = root.findall('dc:description', ns)
    text = " ".join([desc.text for desc in descs if desc.text is not None])
    return text

#encontrar búsquedas en el campo autor
def find_creator(root):
    auths = root.findall('dc:creator', ns)
    text = " ".join([auth.text for auth in auths if auth.text is not None])
    return text  

#encontrar búsquedas en el campo director
def find_contributor(root):
    conts = root.findall('dc:contributor', ns)
    text = " ".join([cont.text for cont in conts if cont.text is not None])
    return text  

def find_Coordinates(root):
    north = None
    south = None
    east = None
    west = None
    
    boundingBox = root.findall('ows:BoundingBox', ns)
    
    for bbox in boundingBox:
        # Extraer UpperCorner (norte y este)
        upperCoord = bbox.find('ows:UpperCorner', ns)
        if upperCoord is not None and upperCoord.text is not None:
            try:
                east, north = map(float, upperCoord.text.split())
            except ValueError:
                east, north = None, None
        
        # Extraer LowerCorner (sur y oeste)
        lowerCoord = bbox.find('ows:LowerCorner', ns)
        if lowerCoord is not None and lowerCoord.text is not None:
            try:
                west, south = map(float, lowerCoord.text.split())
            except ValueError:
                west, south = None, None
    
    return north, south, west, east



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

#encontrar búsquedas en el campo identidicador
def find_identifier(root):
    ids = root.findall('dc:identifier', ns)
    text = " ".join([ident.text for ident in ids if ident.text is not None])
    return text  
 

class MyIndex:
    def __init__(self,index_folder):
        schema = Schema(path=ID(stored=True), content=TEXT(CustomSpanishAnalyzer()), date=STORED,
                        title=TEXT(analyzer=CustomSpanishAnalyzer()), subject=TEXT(analyzer=CustomSpanishAnalyzer()), 
                        description=TEXT(analyzer=CustomSpanishAnalyzer()),creator=TEXT(analyzer=CustomSpanishAnalyzer()),
                        contributor=TEXT(analyzer=CustomSpanishAnalyzer()),
                        publisher=TEXT(analyzer=CustomSpanishAnalyzer()),publishingyear=NUMERIC(numtype=int),identifier=TEXT(stored=True),
                        north=NUMERIC(numtype=float),south=NUMERIC(numtype=float),west=NUMERIC(numtype=float),east=NUMERIC(numtype=float))
        create_folder(index_folder)
        index = create_in(index_folder, schema)
        self.writer = index.writer()

    def index_docs(self,docs_folder):   #indexa documentos
        if (os.path.exists(docs_folder)):
            for file in sorted(os.listdir(docs_folder)):
                # print(file)
                if file.endswith('.xml'):
                    self.index_xml_doc(docs_folder, file)
                elif file.endswith('.txt'):
                    self.index_txt_doc(docs_folder, file)
        self.writer.commit()

    def index_txt_doc(self, foldername,filename):   #para ficheros .txt
        file_path = os.path.join(foldername, filename)
        # print(file_path)
        with open(file_path) as fp:
            text = ' '.join(line for line in fp if line)
        # print(text)
        d=os.path.getmtime(file_path)
        fecha_formateada = email.utils.formatdate(d, usegmt=False)
        self.writer.add_document(path=filename, content=text, date=fecha_formateada)


    def index_xml_doc(self, foldername, filename):  #para ficheros .xml
        file_path = os.path.join(foldername, filename)
        # print(file_path)
        tree = ET.parse(file_path)
        root = tree.getroot()
        raw_text = "".join(root.itertext())
        # break into lines and remove leading and trailing space on each
        text = ' '.join(line.strip() for line in raw_text.splitlines() if line)
        #print(text)
        d=os.path.getmtime(file_path)   #extraemos última fecha de modificación
        fecha_formateada = email.utils.formatdate(d, usegmt=False)  #formateamos la fecha
        north,south,west,east=find_Coordinates(root)
        print(f' Norte: {north}, Sur: {south}, este:{east}, oeste:{west}')
        self.writer.add_document(path=filename, content=text, date=fecha_formateada,title=find_title(root),
                                 subject=find_subject(root),description=find_description(root),creator=find_creator(root),
                                 contributor=find_contributor(root), publisher=find_publisher(root),
                                 publishingyear=find_Publishingyear(root),identifier=find_identifier(root),
                                 north=north,south=south,east=east,west=west)

if __name__ == '__main__':

    index_folder = '../whooshindexZaguanGeo'   #valor por defecto de la carpeta de indexación
    docs_folder = '../dublinCore'         #valor por defecto de la carpeta de documentos
    #docs_folder = '../../recordsdc'         #valor por defecto de la carpeta de documentos
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


