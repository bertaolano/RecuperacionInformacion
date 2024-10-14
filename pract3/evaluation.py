"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
search.py
Authors: Carlos Giralt and Berta Olano

Program to search a free text query on a previously created inverted index.
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python3 evaluation.py -qrels <qrelsFileName> -results <resultsFileName> -output <outputFileName>

"""

import sys

class InformationNeed:
    def __init__(self, need_id):
        self.need_id = need_id
        # Diccionario que asocia el documento con su relevancia (0 o 1)
        self.documents = {}

    def add_document(self, doc_id, relevancy):
        self.documents[doc_id] = relevancy

    def get_relevant_documents(self):
        # Filtra y devuelve solo los documentos relevantes
        return {doc_id: rel for doc_id, rel in self.documents.items() if rel == 1}
    
    def get_documents(self):
        return {self.documents.keys()}

class Results:
    def __init__(self):
        self.information_needs = []
    
    def add_result(self, need_id, doc_id):
        if need_id not in self.information_needs:
            self.information_needs[need_id] = []
            
        self.information_needs[need_id].append(doc_id)
    
    def get_documents_from_infoNeed(self, need_id):
        return self.information_needs[need_id]


class Evaluation:
    def __init__(self):
        # Diccionario que asocia cada necesidad de información con un objeto InformationNeed
        self.information_needs = {}

    def add_judgment(self, information_need_id, document_id, relevancy):
        # Si la necesidad de información no existe, crearla
        if information_need_id not in self.information_needs:
            self.information_needs[information_need_id] = InformationNeed(information_need_id)
        
        # Agregar el documento y su relevancia
        self.information_needs[information_need_id].add_document(document_id, relevancy)

    def tp(self, info_id: int, results: Results, k: int = None) -> int:
        tp = 0
        if k is None:
            k = len(results.get_documents_from_infoNeed(info_id))
        for docid in results.get_documents_from_infoNeed(info_id)[:k]:
            if docid in self.information_needs[info_id].get_relevant_documents():
                tp += 1
        return tp

    def fp(self, info_id: int, results: Results, k: int = None) -> int:
        fp=0
        if k is None:
            k = len(results.get_documents_from_infoNeed(info_id))
        for docid in results.get_documents_from_infoNeed(info_id)[:k]:
            if docid not in self.information_needs[info_id].get_relevant_documents():
                fp += 1
        return fp
    
    def fn(self, info_id: int, results: Results, k: int = None) -> int:
        fn=0
        if k is None:
            k = len(results.get_documents_from_infoNeed(info_id))
        for docid in self.information_needs[info_id].get_relevant_documents()[:k]:
            if docid not in results.get_documents_from_infoNeed(info_id):
                fn += 1
        return fn 

    
    def precision(self, info_id: int, results: Results, k: int = None) -> float:
        return self.tp(info_id, results,k)/(self.tp(info_id, results, k)+self.fp(info_id, results, k))

    
    def recall(self, info_id: int, results: Results, k: int = None) -> float:
        return self.tp(info_id, results, k)/(self.tp(info_id, results, k)+self.fn(info_id, results, k))

    def f1(self, info_id: int, results: Results) -> float:
        P = self.precision(info_id, results)
        R = self.recall(info_id, results)
        return (2 * P * R) / (P + R)
    
    def prec10(self, info_id: int, results: Results) -> float:
        if len(results.get_documents_from_infoNeed(info_id)) < 10:
            return self.tp(info_id, Results) / 10
        else:
            return self.precision(info_id,results,10)
    
    def average_precision(self, results: Results) -> float:
        sum=0
        for query in self.information_needs.keys():
            sum2=0
            index=0
            for doc in self.information_needs[query].get_documents():
                if doc in self.information_needs[query].get_relevant_documents():
                    sum2 += self.precision(query, results, index)
                index +=1
            sum2=sum2/len(self.information_needs[query].get_relevant_documents())
            sum+=sum2
        sum=sum/len(self.information_needs.keys())

    def recall_precision(self):



if __name__ == '__main__':
    i = 1
    infor=False
    while (i < len(sys.argv)):
        if sys.argv[i] == '-qrels': #guarda el indice donde va a hacer la búsqueda
            qrelsFileName = sys.argv[i+1]
            i = i + 1
        if sys.argv[i] == '-results':
            resultsFileName = sys.argv[i+1]   #guarda el fichero que contiene las consultas
            i += 1
        if sys.argv[i] == '-output':
            outputFileName = sys.argv[i+1] #guarda el fichero de resultados
            i += 1
        i = i + 1

    evaluation =Evaluation()
    with open(qrelsFileName, 'r') as Queryfile:
        for line in Queryfile:
            # Saltar líneas en blanco
            if line.strip():
                # Dividir la línea por tabuladores y convertir a enteros
                information_need, document_id, relevancy = map(int, line.strip().split('\t'))
                # Añadir los datos a la lista
                evaluation.add_judgment(information_need,document_id,relevancy)
    
    results = Results()
    with open(resultsFileName, 'r') as Resultsfile:
        for line in Resultsfile:
            # Saltar líneas en blanco
            if line.strip():
                # Dividir la línea por tabuladores y convertir a enteros
                information_need, document_id = map(int, line.strip().split('\t'))
                # Añadir los datos a la lista
                results.add_result(information_need,document_id)


    with open(outputFileName, 'w') as Outputfile:
        count=1
        for infoNeed in evaluation.information_needs:
            Outputfile.writelines("INFORMATION_NEED ",count)
            Outputfile.writelines("precision ",evaluation.precision(infoNeed,results))
            Outputfile.writelines("recall",evaluation.recall(infoNeed,results))
            Outputfile.writelines("F1",evaluation.f1(infoNeed,results))
            Outputfile.writelines("prec@10",evaluation.prec10(infoNeed,results))
            Outputfile.writelines("average_precision",evaluation.average_precision(infoNeed,results))