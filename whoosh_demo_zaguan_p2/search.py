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


from whoosh.qparser import QueryParser, OrGroup, MultifieldParser
from whoosh import scoring
import whoosh.index as index
from whoosh.query import And,Or
from whoosh.query import NumericRange, Term
import xml.etree.ElementTree as ET

TFG_equivalents = [
    "taz-tfg", "trabajos fin de grado", "trabajo fin de grado", "trabajos de fin de grado", 
    "trabajo de fin de grado", "tfg - trabajo de fin de grado", 
    "tfg (trabajo de fin de grado)", "trabajos fin de estudios", "trabajo fin de estudios", 
    "trabajos de fin de estudios", "trabajo de fin de estudios", "tfg"
]

TFM_equivalents = [
    "taz-tfm", "trabajos fin de master", "trabajo fin de master", "trabajos de fin de master", 
    "trabajo de fin de master", "tfm", "o master", "o de master", "o de máster", "o máster",
    "trabajos fin de máster", "trabajos de fin de máster",
    "trabajo fin de máster", "trabajo de fin de máster"
]

Tesis_equivalents = [
    "tesis", "tesis doctoral", "tesinas", "tesina", "tesina doctoral", "tesinas doctorales", "taz-tesis"
]

PFC_equivalents = [
    "taz-pfc", "proyectos fin de carrera", "proyectos de fin de carrera", "proyecto fin de carrera", "proyecto de fin de carrera",
    "pfc"
]

Spanish_equivalents = [
    "español", "castellano", "spanish"
]

English_equivalents = [
    "inglés", "english"
]

Other_Words = [
    "dirigidos", "dirigido", "años", "año", "departamentos de", "departamento de", "miembros", "miembro", "familia", 
    "publicados", "publicado", "estudios", "estudio", "trabajos", "trabajo", "realizados", "realizado", "tutorizados",
    "tutorizado", "apellido", "preferentemente", "defecto", "relacionados", "relacionado", "existen", "hay", "han", "alguien",
    "busco", "necesito", "ejemplo", "ejemplos", "llamado", "desarrollado", "desarrollada", "deben", "interesado"
]

Stop_words = [
    "los", "las", "unos", "unas",
    "el", "la", "un", "una",
    "nosotros", "vosotros", "ellos",
    "yo", "tú", "él", "ella", "me", "te", "se", "lo", "la",
    "y", "o", "pero", "porque", "ni",
    "a", "de", "en", "con", "por", "para", "sobre",
    "muy", "poco", "ya", "siempre", "nunca",
    "ser", "estar", "tener", "hacer", "ir", "poder",
    "que", "quien", "donde", "como", "qué", "estos", 
    "estas", "son", "es", "si", "entre", "hacia", "hasta", 
    "para", "por", "según", "sin", "sobre", "tras", "su", "desde",
    "durante", "este", "otro", "otra", "estoy", "quiero"
]


def cleanQuery(query_text):
    # substituimos signos de puntuación por puntos
    query_text = re.sub(r'[;,!?]', '.', query_text)
    #eliminamos *
    query_text = re.sub(r'[\*,¿,¡]', '', query_text)
    
    return query_text


def deleteUnnecessaryWords(sentence):
    lowerCase = sentence.lower()
    # eliminamos palabras relacionadas con el tipo de proyecto, lenguaje y palabras comunes sobre autoría, dirección, etc
    # eliminamos también palabras que no aporten demasiada información en los campos en los que buscamos
    deleteWords = [TFG_equivalents, TFM_equivalents, Tesis_equivalents, PFC_equivalents, 
                    Spanish_equivalents, English_equivalents, Other_Words]
    for dict in deleteWords:
        for word in dict:
             lowerCase = re.sub(r'\b' + re.escape(word) + r'\b', '', lowerCase)
    
    # eliminamos stop words en español
    for stop in Stop_words:
        lowerCase = re.sub(r'\b' + re.escape(stop) + r'\b', '', lowerCase)

    lowerCase = re.sub(r'\s+', ' ', lowerCase).strip()
    return lowerCase    
    


def mainQuery(query_text, searcher):
    lowerCaseQuery = query_text.lower()
    keyWordQueries = []
    titleAndDescQueries = []
    sentences = lowerCaseQuery.split('.')
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    for sentence in sentences:
        aux = deleteUnnecessaryWords(sentence)
        #print(aux)
        keyWordQueries.append(searcher.KeyWordParser.parse(aux))
        titleAndDescQueries.append(searcher.MainParser.parse(aux))
    return Or(keyWordQueries), Or(titleAndDescQueries)


def docTypeQuery(query_text):
    lowerCaseQuery = query_text.lower()
    typeSearched = []
    deleteWords = [TFG_equivalents, TFM_equivalents, Tesis_equivalents, PFC_equivalents]
    for dict in deleteWords:
        for word in dict:
            if word in lowerCaseQuery:
                typeSearched.append(Term("docType", dict[0]))
    return Or(typeSearched)


def languageQuery(query_text):
    lowerCaseQuery = query_text.lower()
    langSearched = []
    for term in Spanish_equivalents:
        if re.search(r'.*' + term + r'.*', lowerCaseQuery):
            langSearched.append(Term("language", "es"))
    
    for term in English_equivalents:
        if re.search(r'.*' + term + r'.*', lowerCaseQuery):
            langSearched.append(Term("language", "eng"))
    return Or(langSearched)


def namesQuery(query_text, searcher):
    query_text = query_text.lower()
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(query_text)
    names = []
    authorQueries = []
    contributorQueries = []

    for entity in doc.ents:
        if entity.label_ == "PER":
            names.append(entity.text)
    
    for name in names:
        if re.search(r'.*dirigid. por .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*dirigid.s por .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*tutorizad. por .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*turorizad.s por .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*tutor.s .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*tutora .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*tutor .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*director.s .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*director .*' + re.escape(name) + r'.*', query_text) \
        or re.search(r'.*directora .*' + re.escape(name) + r'.*', query_text):
            contributorQueries.append(searcher.ContrNameParser.parse(name))
        elif (not re.search(r'.*sobre' + name + r'.*', query_text)):
            authorQueries.append(searcher.AuthorNameParser.parse(name))
    
    return Or(authorQueries), Or(contributorQueries)

def departmentQuery(query_text):
    query_text = query_text.lower()





def parseQuery(query_text, searcher):
    # Eliminamos interrogantes y otros signos de puntuación distintos del punto
    #query = cleanQuery(query_text)
    #keyWordQuery, titleAndDescQuery = mainQuery(query, searcher)
    #docQuery = docTypeQuery(query)
    #lanQuery = languageQuery(query)
    #authorQuery, contributorQuery = namesQuery(query, searcher)
    departmentQuery(query)
    #print(keyWordQuery, titleAndDescQuery, docQuery, lanQuery, authorQuery, contributorQuery)

class MySearcher:
    def __init__(self, index_folder, model_type = 'tfidf'):
        ix = index.open_dir(index_folder)
        if model_type == 'tfidf':
            # Apply a vector retrieval model as default
            self.searcher = ix.searcher(weighting=scoring.TF_IDF())
        else:
            # Apply the probabilistic BM25F model, the default model in searcher method
            self.searcher = ix.searcher()
        self.KeyWordParser = QueryParser("subject", ix.schema, group = OrGroup)
        self.MainParser = MultifieldParser(["description", "title"], ix.schema, group = OrGroup)
        self.AuthorNameParser = QueryParser("creator", ix.schema, group = OrGroup)
        self.ContrNameParser = QueryParser("contributor", ix.schema, group = OrGroup)
        self.PubliParser = QueryParser("publisher", ix.schema, group = OrGroup)

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
        with open(resultsFile, 'w', encoding='utf-8') as output_file:
            tree = ET.parse(queryFile)
            root = tree.getroot()
            for child in root.findall('informationNeed'):
                query_count = child.find('identifier').text
                query=child.find('text').text
                print(f"\nEjecutando búsqueda para la query {query_count}: '{query}'")
                    # Obtener los resultados de la búsqueda
                processedQuery = parseQuery(query, searcher)
                #results = searcher.search(processedQuery, query_count, output_file)
    except FileNotFoundError:
        print(f"El archivo {queryFile} no se encontró.")
    except Exception as e:
        print(f"Se produjo un error: {e}")