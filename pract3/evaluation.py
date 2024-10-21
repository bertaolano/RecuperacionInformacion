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
        return list({doc_id: rel for doc_id, rel in self.documents.items() if rel == 1})
    
    def get_documents(self):
       # return {self.documents.keys()}
        return list(self.documents.keys())

class Results:
    def __init__(self):
        self.information_needs = {}
    
    def add_result(self, need_id, doc_id):
        if need_id not in self.information_needs:
            self.information_needs[need_id] = []
            
        self.information_needs[need_id].append(doc_id)
    
    def get_documents_from_infoNeed(self, need_id):
        return list(self.information_needs[need_id])
        #return list(self.relevant_documents.keys())


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
        fn = 0
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
    
    def average_precision(self, info_id, results):
        sum_precisions = 0.0
        relevant_docs = self.information_needs[info_id].get_relevant_documents()
        retrieved_docs = results.get_documents_from_infoNeed(info_id)
        num_relevant = len(relevant_docs)
        
        if num_relevant == 0:
            return 0.0

        relevant_retrieved_count = 0  # Contador de documentos relevantes recuperados
        for index, doc in enumerate(retrieved_docs):
        #for index, doc in enumerate(retrieved_docs):
            if doc in self.information_needs[info_id].get_documents():
                relevant_retrieved_count += 1
                print(index)
                # Calculamos la precisión hasta este punto
                precision_at_k = relevant_retrieved_count / (index + 1)
                #precision_at_k = self.precision(info_id,results,index+1)
                sum_precisions += precision_at_k
        
        return sum_precisions / relevant_retrieved_count



    def recall_precision(self, results: Results):
        precisions = []
        recalls = []
        
        for query in self.information_needs.keys():  
            relevant_docs = len(self.information_needs[query].get_relevant_documents())  
            retrieved_docs = results.get_documents_from_infoNeed(query)
            
            precision_points = []
            recall_points = []

            for index, doc in enumerate(retrieved_docs):
                tp = self.tp(query, results) 
                precision = self.precision(query, results, index + 1)  
                recall = self.recall(query, results)  

                precision_points.append(precision)
                recall_points.append(recall)
                
        return precisions, recalls

    def recall_precision_interpolated(self, results: Results):
        precisions = []
        recalls = []
        
        for query in self.information_needs.keys(): 
            relevant_docs = len(self.information_needs[query].get_relevant_documents())  
            retrieved_docs = results.get_documents_from_infoNeed(query)
            
            precision_points = []
            recall_points = []
            
            for index, doc in enumerate(retrieved_docs):
                tp = self.tp(query, results)  
                precision = self.precision(query, results, index + 1) 
                recall = self.recall(query, results)  
                
                precision_points.append(precision)
                recall_points.append(recall)
            
            # Aplicamos la interpolación de precisión
            max_precision = 0
            interpolated_precisions = []
            
            for p in reversed(precision_points):
                max_precision = max(max_precision, p)
                interpolated_precisions.insert(0, max_precision)  # Insertar al inicio de la lista para mantener el orden
                
            precisions.append(interpolated_precisions)
            recalls.append(recall_points)
        
        return precisions, recalls





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
    #cargar el archivo qrels.txt
    with open(qrelsFileName, 'r') as Queryfile:
        for line in Queryfile:
            if line.strip():
                information_need, document_id, relevancy = map(int, line.strip().split('\t'))
                print(f"Loading judgment: Need ID: {information_need}, Document ID: {document_id}, Relevancy: {relevancy}")
                evaluation.add_judgment(information_need, document_id, relevancy)
    
    results = Results()
    with open(resultsFileName, 'r') as Resultsfile:
        for line in Resultsfile:
            # Saltar líneas en blanco
            if line.strip():
                # Dividir la línea por tabuladores y convertir a enteros
                information_need, document_id = map(int, line.strip().split('\t'))
                # Añadir los datos a la lista
                print(f"Loading result: Need ID: {information_need}, Document ID: {document_id}")
                results.add_result(information_need,document_id)


with open(outputFileName, 'w') as Outputfile:
    count = 1
    for infoNeed in evaluation.information_needs:
        Outputfile.write(f"INFORMATION_NEED {count}\n")
        Outputfile.write(f"precision {evaluation.precision(infoNeed,results):.3f}\n")
        Outputfile.write(f"recall {evaluation.recall(infoNeed,results):.3f}\n")
        Outputfile.write(f"F1 {evaluation.f1(infoNeed,results):.3f}\n")
        Outputfile.write(f"prec@10 {evaluation.prec10(infoNeed,results):.3f}\n")
        Outputfile.write(f"average_precision {evaluation.average_precision(infoNeed,results):.3f}\n")
        precisions, recalls = evaluation.recall_precision(results)
        Outputfile.write("recall_precision\n")
        for recall, precision in zip(recalls, precisions):
            for r, p in zip(recall, precision): 
                Outputfile.write(f"{r:.3f} {p:.3f}\n")
        
        interpolated_precisions, interpolated_recalls = evaluation.recall_precision_interpolated(results)
        Outputfile.write("interpolated_recall_precision\n")
        for recall, precision in zip(interpolated_recalls, interpolated_precisions):
            for r, p in zip(recall, precision): 
                Outputfile.write(f"{r:.3f} {p:.3f}\n")
        count += 1
