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
from datetime import datetime


from whoosh.qparser import QueryParser, OrGroup, MultifieldParser
from whoosh import scoring
import whoosh.index as index
from whoosh.query import And,Or
from whoosh.query import NumericRange, Term
import xml.etree.ElementTree as ET

# Array de strings equivalntes a TAZ-TFG para la consulta de tipo de documento
TFG_equivalents = [
    "taz-tfg", "trabajos fin de grado", "trabajo fin de grado", "trabajos de fin de grado", 
    "trabajo de fin de grado", "tfg - trabajo de fin de grado", 
    "tfg (trabajo de fin de grado)", "trabajos fin de estudios", "trabajo fin de estudios", 
    "trabajos de fin de estudios", "trabajo de fin de estudios", "tfg"
]

# Array de strings equivalntes a TAZ-TFM para la consulta de tipo de documento
TFM_equivalents = [
    "taz-tfm", "trabajos fin de master", "trabajo fin de master", "trabajos de fin de master", 
    "trabajo de fin de master", "tfm", "o master", "o de master", "o de máster", "o máster",
    "trabajos fin de máster", "trabajos de fin de máster",
    "trabajo fin de máster", "trabajo de fin de máster"
]

# Array de strings equivalntes a TESIS para la consulta de tipo de documento
Tesis_equivalents = [
    "tesis", "tesis doctoral", "tesinas", "tesina", "tesina doctoral", "tesinas doctorales", "taz-tesis"
]

# Array de strings equivalntes a TAZ-PFC para la consulta de tipo de documento
PFC_equivalents = [
    "taz-pfc", "proyectos fin de carrera", "proyectos de fin de carrera", "proyecto fin de carrera", "proyecto de fin de carrera",
    "pfc"
]

# Array de strings equivalntes a español para la consulta de lenguaje
Spanish_equivalents = [
    "español", "castellano", "spanish"
]

# Array de strings equivalntes a inglés para la consulta de lenguaje
English_equivalents = [
    "inglés", "english"
]

# Array de palabras poco significativas para la búsqueda de palabras clave y búsquedas en el campo title y description
Other_Words = [
    "dirigidos", "dirigido", "años", "año", "departamentos de", "departamento de", "miembros", "miembro", "familia", 
    "publicados", "publicado", "estudios", "estudio", "trabajos", "trabajo", "realizados", "realizado", "tutorizados",
    "tutorizado", "apellido", "preferentemente", "defecto", "relacionados", "relacionado", "existen", "hay", "han", "alguien",
    "busco", "necesito", "ejemplo", "ejemplos", "llamado", "desarrollado", "desarrollada", "deben", "interesado"
]

# Array de strings palabras vacías en español
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

# Sustituye todos los signos de puntuación por puntos, o los elimina si no son necesarios
def cleanQuery(query_text):
    # substituimos signos de puntuación por puntos
    query_text = re.sub(r'[;,!?]', '.', query_text)
    #eliminamos *
    query_text = re.sub(r'[\*,¿,¡]', '', query_text)
    
    return query_text

# Elimina las palabras menos significativas o que pertenecen a consultas en otros campos para la búsqueda de 
# palabras clave, búsquedas en el campo title y búsquedas en el campo description
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

# Búsqueda de palabras clave, en el título y en la descripción. Es decir, 
# búsquedas en los campos subject, title y description
def mainQuery(query_text, searcher):
    lowerCaseQuery = query_text.lower()
    keyWordQueries = []
    titleAndDescQueries = []
    sentences = lowerCaseQuery.split('.')
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    for sentence in sentences:
        aux = deleteUnnecessaryWords(sentence)
        #print(aux)
        parsed = searcher.KeyWordParser.parse(aux)
        parsed.boost *= 2.5
        keyWordQueries.append(parsed)
        parsed = searcher.MainParser.parse(aux)
        parsed.boost *= 1.25
        titleAndDescQueries.append(parsed)
    return Or(keyWordQueries), Or(titleAndDescQueries)

# Búsquedas de tipo de documento: tesis, tfg, tfm, ...
def docTypeQuery(query_text):
    lowerCaseQuery = query_text.lower()
    typeSearched = []
    deleteWords = [TFG_equivalents, TFM_equivalents, Tesis_equivalents, PFC_equivalents]
    for dict in deleteWords:
        for word in dict:
            if word in lowerCaseQuery:
                t = Term("docType", dict[0])
                t.boost *= 1.5
                typeSearched.append(t)
    return Or(typeSearched)

# Búsquedas de lenguaje. Búscamos aparicines de palabras que nos indiquen la preferencia de idioma
# para filtrar los documentos en base a dichas preferencias
def languageQuery(query_text):
    lowerCaseQuery = query_text.lower()
    langSearched = []
    for term in Spanish_equivalents:
        if re.search(r'.*' + term + r'.*', lowerCaseQuery):
            t = Term("language", "es")
            t.boost *= 2.0
            langSearched.append(t)
    
    for term in English_equivalents:
        if re.search(r'.*' + term + r'.*', lowerCaseQuery):
            t = Term("language", "eng")
            t.boost *= 2.0
            langSearched.append(t)
    return Or(langSearched)

# Búsqueda de autores y directores de los trabajos
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
            n = searcher.ContrNameParser.parse(name)
            n.boost *= 1.5
            contributorQueries.append(n)
        elif (not re.search(r'.*sobre' + name + r'.*', query_text)):
            n = searcher.AuthorNameParser.parse(name)
            n.boost *= 2.0
            authorQueries.append(n)
    
    return Or(authorQueries), Or(contributorQueries)

# Búsquedas de departamentos a los que están adscritos los trabajos 
def departmentQuery(query_text, searcher):
    query_text = query_text.lower()
    pattern = r'\b(departamento|departmentos) de\s+([a-z\s]+)'
    
    # Search for the first match
    match = re.search(pattern, query_text, re.IGNORECASE)
    
    if match:
        # Return the department name (second group in the regex)
        d = searcher.PubliParser.parse(match.group(2).strip())
        d.boost *= 2.0
        return d
    
    return None

# Función auxiliar para detectar rangos de fechas
def find2Dates(stringDate1, stringDate2, sentence, query):
    pattern = r'.*' + re.escape(stringDate1) + r'.*([0-9]{4}).*' + re.escape(stringDate2) + r'.*([0-9]{4})'
    match = re.search(pattern, sentence)
    if match:
        year1 = int(match.group(1))
        year2 = int(match.group(2))
        fecha_range_query = NumericRange("publishingyear", min(year1, year2), max(year1, year2))
        fecha_range_query.boost *= 2.0
        query.append(fecha_range_query)

# Función auxiliar para detectar rangos de fechas definidos por una única fecha
def find1Date(stringDate1, stringDate2, sentence, query):
    pattern = r'.*' + re.escape(stringDate1) + r'.*' + r'([1-9][0-9]{0,3})' + r'.*' + re.escape(stringDate2)
    match = re.search(pattern, sentence)
    if match:
        years = match.group(1)
        currentYear = datetime.now().year
        if (stringDate2 == "años"):
            minYear = currentYear - int(years)
        else:
            minYear = years
        
        fecha_range_query = NumericRange("publishingyear", minYear, currentYear)
        fecha_range_query.boost *= 2.0
        query.append(fecha_range_query)

# Función para filtrar fechas de publicación
def publishingYearQuery(query_text):
    query_text = query_text.lower()
    yQuery = []
    sentences = query_text.split('.')
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    for sentence in sentences:
        # dos fechas
        find2Dates("entre", "y", sentence, yQuery)
        find2Dates("desde", "hasta", sentence, yQuery)
        # una única fecha
        find1Date("últimos", "años", sentence, yQuery)
        find1Date("desde hace", "años", sentence, yQuery)
        find1Date("desde", "hasta hoy", sentence, yQuery)
        find1Date("desde", "en adelante", sentence, yQuery)
        match = re.search(r'.*' + "el año" + r'[0-9]{4}', sentence)
        if match:
            year = match.group(1)
            y = Term("publishingyear", year)
            y.boost *= 2.0
            yQuery.append(y)
    return Or(yQuery)

# Devuelve la query obtenida como conjunción de disyunciones obtenida al procesar la necesidad
# información
def parseQuery(query_text, searcher):
    # Eliminamos interrogantes y otros signos de puntuación distintos del punto
    query = cleanQuery(query_text)
    keyWordQuery, titleAndDescQuery = mainQuery(query, searcher)
    docQuery = docTypeQuery(query)
    lanQuery = languageQuery(query)
    authorQuery, contributorQuery = namesQuery(query, searcher)
    depQuery = departmentQuery(query, searcher)
    tempQuery = publishingYearQuery(query)

    queries = [query for query in [keyWordQuery, titleAndDescQuery, docQuery, lanQuery, authorQuery, contributorQuery, depQuery, tempQuery] if query]
    finalQuery = And(queries)
    #print(finalQuery)
    return finalQuery


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

    def search(self, query, query_id, output_file):
        print("Búsqueda de la Query procesada: ", query)
        results = self.searcher.search(query, limit = 100)
        print('Returned documents:')
        i = 1
        for result in results:
            identifier = result.get("identifier")
            print(f'{i} - File path: {result.get("path")}, Similarity score: {result.score}, identifier:{result.get("identifier")}')
            # Escribir el número de consulta y el identificador en el archivo de resultados
            output_file.write(f"{query_id}\t{identifier}\n")
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
        with open(resultsFile, 'w', encoding='utf-8') as output_file:
            tree = ET.parse(queryFile)
            root = tree.getroot()
            for child in root.findall('informationNeed'):
                query_count = child.find('identifier').text
                query=child.find('text').text
                print(f"\nEjecutando búsqueda para la query {query_count}: '{query}'")
                    # Obtener los resultados de la búsqueda
                processedQuery = parseQuery(query, searcher)
                results = searcher.search(processedQuery, query_count, output_file)
    except FileNotFoundError:
        print(f"El archivo {queryFile} no se encontró.")
    except Exception as e:
        print(f"Se produjo un error: {e}")