"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
custom_filters.py
Authors: Carlos Giralt and Berta Olano


Program to create a filter based on the Snowball stemmer
"""
from whoosh.analysis import Filter
from nltk.stem.snowball import SnowballStemmer

class CustomSpanishStemmingFilter(Filter):
    def __init__(self):
        #Definimos un stemmer en español basado en el metodo Snowball
        self.stemmer = SnowballStemmer('spanish')
    
    def __call__(self, tokens):
        #tokenizamos el texto obtenido
        for token in tokens:
            token.text = self.stemmer.stem(token.text)
            yield token
