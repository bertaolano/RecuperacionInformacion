"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
search.py
Authors: Carlos Giralt and Berta Olano

Program to search a free text query on a previously created inverted index.
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python3 search.py -index <indexPath> -infoNeeds <queryFile> -output <resultsFile>
"""

import re
import sys
import spacy


from whoosh.qparser import QueryParser
from whoosh.qparser import OrGroup
from whoosh import scoring
import whoosh.index as index
from whoosh.query import And,Or
from whoosh.query import NumericRange
import xml.etree.ElementTree as ET

def parser(query_text):
    nlp = spacy.load ("es_core_news_sm")
    doc = nlp ( query_text )
    # Find named entities , phrases and concepts
    posFechas=[]
    parsed_query_parts = []  # Aquí almacenaremos las diferentes partes de la consulta
    parsed_query=""
    for entity in doc.ents:
        #print(entity.text, entity.label_)
        if entity.label_ == "PER":
            # Añadir cada término relacionado a un campo en Whoosh
            parsed_query_parts.append(f"creator:{entity.text}")
            parsed_query_parts.append(f"contributor:{entity.text}")
            parsed_query_parts.append(f"publisher:{entity.text}")
        elif entity.label_ == "LOC":
            parsed_query_parts.append(f"description:{entity.text}")
            parsed_query_parts.append(f"title:{entity.text}")
            parsed_query_parts.append(f"subject:{entity.text}")
        elif entity.label_ == "ORG":
            parsed_query_parts.append(f"description:{entity.text}")
            parsed_query_parts.append(f"publisher:{entity.text}")

    # Construir la consulta final combinando las diferentes partes
    parsed_query = " OR ".join(parsed_query_parts)  # Concatenamos con OR para que sea válido

    # Expresión regular para detectar años (asumiendo que los años están entre 1000 y 2999)
    year_pattern = re.compile(r"\b(1[0-9]{3}|2[0-9]{3})\b")

    # Buscar años en el texto con expresiones regulares
    years = year_pattern.findall(query_text)
    posFechas = [int(year) for year in years]

    # Manejar las fechas
    if len(posFechas) >= 2:
        start_year = min(posFechas)
        end_year = max(posFechas)
        fecha_range_query = NumericRange("publishingyear", start_year, end_year)
        parsed_query += f" OR {fecha_range_query}"
    elif len(posFechas) == 1:
        year = posFechas[0]
        fecha_query = "publishingyear:{year}"
        parsed_query += f" OR {fecha_query}"
    return parsed_query



def findCoord(query_text):
    pattern = r"spatial:([\-\d\.]+),([\-\d\.]+),([\-\d\.]+),([\-\d\.]+)"
    
    # Buscar las coordenadas en el string usando la expresión regular
    match = re.search(pattern, query_text)
    
    if match:
        not_espacial_query = re.sub(pattern, '', query_text)
        west = match.group(1)
        east = match.group(2)
        south = match.group(3)
        north = match.group(4)
        return west, east, south, north,not_espacial_query
    else:
        return None, None, None, None, query_text

class MySearcher:
    def __init__(self, index_folder, model_type = 'tfidf'):
        ix = index.open_dir(index_folder)
        if model_type == 'tfidf':
            # Apply a vector retrieval model as default
            self.searcher = ix.searcher(weighting=scoring.TF_IDF())
        else:
            # Apply the probabilistic BM25F model, the default model in searcher method
            self.searcher = ix.searcher()
        self.parser = QueryParser("content", ix.schema, group = OrGroup)

        
    def search(self, query_text, query_count,output_file):
        spatial_query = None
        west, east, south, north, not_spacial_query=findCoord(query_text)
        if west is not None and east is not None and north is not None and south is not None:
            westRangeQuery = NumericRange ("west", start = None , end = east )
            eastRangeQuery = NumericRange ("east", start = west , end = None )
            northRangeQuery = NumericRange ("north", start = south , end = None )
            southRangeQuery = NumericRange ("west", start = None , end = north )
            spatial_query = And([westRangeQuery,eastRangeQuery,southRangeQuery,northRangeQuery ])
            #query=not_spacial_query
        #búsqueda sin las coordenadas
        #
       # parsed_query=parser(query)
        #query=parser(query_text)
        #query= Or([spatial_query,parsed_query])
        #limitamos los resultados de cada búsqueda a 100
        query = self.parser.parse(not_spacial_query)
        if spatial_query is not None: 
            query = Or([query, spatial_query])
        print("Búsqueda de la Query procesada: ",query)
        results = self.searcher.search(query, limit = 100)
        print('Returned documents:')
        i = 1
        for result in results:
            identifier = result.get("identifier")
            print(f'{i} - File path: {result.get("path")}, Similarity score: {result.score}, identifier:{result.get("identifier")}')
            # Escribir el número de consulta y el identificador en el archivo de resultados
            output_file.write(f"{query_count}\t{identifier}\n")
            i += 1

if __name__ == '__main__':
    index_folder = '../whooshindexZaguan' #indice por defecto
    i = 1
    infor=False
    while (i < len(sys.argv)):
        if sys.argv[i] == '-index': #guarda el indice donde va a hacer la búsqueda
            index_folder = sys.argv[i+1]
            i = i + 1
        if sys.argv[i] == '-infoNeeds':
            queryFile = sys.argv[i+1]   #guarda el fichero que contiene las consultas
            i += 1
        if sys.argv[i] == '-output':
            resultsFile = sys.argv[i+1] #guarda el fichero de resultados
            i += 1
        i = i + 1

    searcher = MySearcher(index_folder)

     # Procesar las consultas y guardar los resultados
    try:
        with open(queryFile, 'r', encoding='utf-8') as query_file, open(resultsFile, 'w', encoding='utf-8') as output_file:
            query_count = 1
            for query in query_file:
                query = query.strip()  # Elimina saltos de línea y espacios adicionales
                if query:
                    print(f"\nEjecutando búsqueda para la query {query_count}: '{query}'")
                    # Obtener los resultados de la búsqueda
                    results = searcher.search(query,query_count,output_file)
                    query_count += 1
    except FileNotFoundError:
        print(f"El archivo {queryFile} no se encontró.")
    except Exception as e:
        print(f"Se produjo un error: {e}")