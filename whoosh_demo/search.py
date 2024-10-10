"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
search.py
Authors: Carlos Giralt and Berta Olano

Program to search a free text query on a previously created inverted index.
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python3 search.py -index <indexPath> -infoNeeds <queryFile> -output <resultsFile>
"""

import sys

from whoosh.qparser import QueryParser
from whoosh.qparser import OrGroup
from whoosh import scoring
import whoosh.index as index

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
        query = self.parser.parse(query_text)
        print(query)
        #limitamos los resultados de cada búsqueda a 100
        results = self.searcher.search(query,limit = 100)
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