"""
RECUPERACIÓN DE INFORMACIÓN:PRACTICA 1
search.py
Authors: Carlos Giralt and Berta Olano

Program to search a free text query on a previously created inverted index.
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python3 evaluation.py -qrels <qrelsFileName> -results <resultsFileName> -output <outputFileName>

"""

import sys
import matplotlib . pyplot as plt
import numpy as np

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
    
    def get_relevant_documents_from_infoNeed(self, need_id: int, infoNeed: InformationNeed):
        res = []
        for doc in self.get_documents_from_infoNeed(need_id):
            if doc in infoNeed.get_relevant_documents():
                res.append(doc)
        return res


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

    
    #def recall(self, info_id: int, results: Results, k: int = None) -> float:
       # return self.tp(info_id, results, k)/(self.tp(info_id, results, k)+self.fn(info_id, results, k))
    def recall(self, info_id, results: Results, at_index):
        relevant_docs = self.information_needs[info_id].get_relevant_documents()
        retrieved_docs = results.get_documents_from_infoNeed(info_id)[:at_index]  # Considerar los primeros 'at_index' documentos
        
        relevant_retrieved = 0
        for doc in retrieved_docs:
            if doc in relevant_docs:
                relevant_retrieved += 1  # Cuenta solo los relevantes recuperados hasta aquí

        # Evitar la división por cero si no hay documentos relevantes
        if len(relevant_docs) == 0:
            return 0.0
        
        # Cálculo del recall
        return relevant_retrieved / len(relevant_docs)

    def f1(self, info_id: int, results: Results) -> float:
        P = self.precision(info_id, results)
        R = self.recall(info_id, results,len(results.get_documents_from_infoNeed(info_id)))
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
            if doc in relevant_docs:
                relevant_retrieved_count += 1
                print(index)
                # Calculamos la precisión hasta este punto
                #precision_at_k = relevant_retrieved_count / (index + 1)
                precision_at_k = self.precision(info_id,results,index+1)
                sum_precisions += precision_at_k
        
        return sum_precisions / relevant_retrieved_count
    
        """
        n_relevant_docs = len(self.information_needs[info_id].get_relevant_documents())
        #print(n_relevant_docs)
        if (len(results.get_relevant_documents_from_infoNeed(info_id, self.information_needs[info_id])) == 0):
            return 0
        sum = 0
        for i in range (n_relevant_docs):
            sum += self.precision(info_id, results, i+1)
            print(sum)
        return sum / n_relevant_docs
        """



    def recall_precision(self, info_id, results: Results):
        precisions = []
        recalls = []
        
        retrieved_docs = results.get_documents_from_infoNeed(info_id)
        relevant_docs = self.information_needs[info_id].get_relevant_documents()

        for index, doc in enumerate(retrieved_docs):
            if doc in relevant_docs:
                precision = self.precision(info_id, results, index + 1)
                recall = self.recall(info_id, results, index + 1)

                print(f"Doc: {doc} | Precision: {precision:.3f} | Recall: {recall:.3f}")
                
                precisions.append(precision)
                recalls.append(recall)

        return precisions, recalls


    def recall_precision_interpolated(self, info_id, results: Results):
        precisions = []
        recalls = []
         
        relevant_docs = self.information_needs[info_id].get_relevant_documents()
        retrieved_docs = results.get_documents_from_infoNeed(info_id)
        
        precision_points = []
        recall_points = []
        
        for index, doc in enumerate(retrieved_docs):
            if doc in relevant_docs:
                precision = self.precision(info_id, results, index + 1) 
                recall = self.recall(info_id, results, index + 1)  
                
                precision_points.append(precision)
                recall_points.append(recall)
                print(f"Doc: {doc} | Precision: {precision:.3f} | Recall: {recall:.3f}")
        
        # Lista de recalls estándar donde interpolaremos las precisiones
        recall_levels = [i / 10.0 for i in range(11)]
        
        # Aplicamos la interpolación de precisión para cada nivel de recall estándar
        interpolated_precisions = []
        
        for recall_level in recall_levels:
            # Encontrar la máxima precisión para el recall >= recall_level
            max_precision = 0.0
            for r, p in zip(recall_points, precision_points):
                if r >= recall_level:
                    max_precision = max(max_precision, p)
            interpolated_precisions.append(max_precision)

        
        return recall_levels, interpolated_precisions
    






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
        total_precision = 0.0
        total_recall = 0.0
        total_f1 = 0.0
        total_prec_at_10 = 0.0
        total_ap = 0.0  # MAP
        all_interpolated_precisions = [0.0] * 11  # Para interpolar en 11 puntos
        count = 1
        num_queries = len(evaluation.information_needs)

        interpolated_precisions = [[0.0 for _ in range(11)] for _ in range(num_queries + 1)]

        for infoNeed in evaluation.information_needs:
            Outputfile.write(f"INFORMATION_NEED {count}\n")
            
            precision = evaluation.precision(infoNeed, results)
            recall = evaluation.recall(infoNeed, results, len(results.get_documents_from_infoNeed(infoNeed)))
            f1 = evaluation.f1(infoNeed, results)
            prec_at_10 = evaluation.prec10(infoNeed, results)
            average_precision = evaluation.average_precision(infoNeed, results)
            
            Outputfile.write(f"precision {precision:.3f}\n")
            Outputfile.write(f"recall {recall:.3f}\n")
            Outputfile.write(f"F1 {f1:.3f}\n")
            Outputfile.write(f"prec@10 {prec_at_10:.3f}\n")
            Outputfile.write(f"average_precision {average_precision:.3f}\n")
            
            # Acumulamos para las métricas totales
            total_precision += precision
            total_recall += recall
            total_f1 += f1
            total_prec_at_10 += prec_at_10
            total_ap += average_precision
            
            # Recall y Precision
            Outputfile.write("recall_precision\n")
            precisions, recalls = evaluation.recall_precision(infoNeed, results)
            for recall_value, precision_value in zip(recalls, precisions):
                Outputfile.write(f"{recall_value:.3f} {precision_value:.3f}\n")
            
            # Interpolación de precisión y recall
            interpolated_recalls, interpolated_precisions[count-1] = evaluation.recall_precision_interpolated(infoNeed, results)
            Outputfile.write("interpolated_recall_precision\n")
            for recall_value, precision_value in zip(interpolated_recalls, interpolated_precisions[count-1]):
                Outputfile.write(f"{recall_value:.3f} {precision_value:.3f}\n")
            
            # Acumulamos las interpolaciones
            for i, precision_value in enumerate(interpolated_precisions[count-1]):
                all_interpolated_precisions[i] += precision_value
            
            #interpolated_precisions[count-1]=all_interpolated_precisions.copy()
            print("a",len(all_interpolated_precisions))
            
            count += 1

        # Calculamos las métricas totales
        total_avg_precision = total_precision / num_queries if num_queries else 0
        total_avg_recall = total_recall / num_queries if num_queries else 0
        total_avg_f1 = total_f1 / num_queries if num_queries else 0
        total_avg_prec_at_10 = total_prec_at_10 / num_queries if num_queries else 0
        total_avg_ap = total_ap / num_queries if num_queries else 0
        interpolated_avg_precisions = [p / num_queries for p in all_interpolated_precisions]
        
        # Escribimos las métricas totales en el archivo
        Outputfile.write("\nTOTAL\n")
        Outputfile.write(f"precision {total_avg_precision:.3f}\n")
        Outputfile.write(f"recall {total_avg_recall:.3f}\n")
        Outputfile.write(f"F1 {total_avg_f1:.3f}\n")
        Outputfile.write(f"prec@10 {total_avg_prec_at_10:.3f}\n")
        Outputfile.write(f"MAP {total_avg_ap:.3f}\n")
        
        # Escribimos la interpolación total
        Outputfile.write("interpolated_recall_precision\n")
        for i, precision_value in enumerate(interpolated_avg_precisions):
            Outputfile.write(f"{i/10:.3f} {precision_value:.3f}\n")
        
    interpolated_precisions[num_queries]=interpolated_avg_precisions.copy()

    x = np . linspace (0.0 , 1.0 , 11)
    print(len(x))
    print(type(interpolated_precisions))
    fig , ax = plt.subplots ()
    for i in range(0,num_queries):
        ax.plot(x, interpolated_precisions[i], label =f'information need  {i+1}')
    ax.plot(x, interpolated_precisions[num_queries], label =f'total')
    ax.set_title('precision - recall curve')
    ax.set_xlabel('recall')
    ax.set_ylabel('precision')
    ax.grid(True, axis='y', linestyle='-', color = 'gray')
    plt.legend(loc ='upper right')
    plt.show ()
