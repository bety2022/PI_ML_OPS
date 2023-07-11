
# IMPORTAMOS LIBRERIAS

import pandas as pd
import numpy  as np

from fastapi import FastAPI

import uvicorn

from sklearn.metrics.pairwise        import cosine_similarity
from sklearn.utils.extmath           import randomized_svd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise        import linear_kernel


app = FastAPI()



# PRESENTACION:
# REALIZAMOS UNA CONSULTA COMO PRESENTACION CON NUESTRO NOMBRE
# UTILIZAMOS UN DECORADOR (@app.get(‘/’) QUE NOS MUESTRA LA RUTA Y EL VERBO EN ESTE CASO GET
@app.get('/')
def presentacion():
    return 'BEATRIZ_CAROLINA_LOPEZ_AMADO'

# IMPORTAMOS LOS DATOS
Data_recomendación = pd.read_csv('./Data_recomendación_peliculas_plataformas_de_streaming.csv')


# FUNCION 1:
# ESTA FUNCION DEVUELVE LA CANTIDAD DE PELICULAS PRODUCIDAS POR ESE IDIOMA
@app.get("/peliculas_idioma/{idioma}")
def peliculas_idioma(idioma:str):
    idioma_filtro = Data_recomendación[Data_recomendación['name_languague'] == idioma]
    cantida_pelis =  idioma_filtro['name_languague'].shape[0]
    return {'idioma:':idioma, 'cantidad peliculas:':cantida_pelis}


# FUNCION 2:
# ESTA FUNCION DEVUELVE LA DURACION Y EL AÑO DE UNA PELICULA
@app.get("/peliculas_duracion/{pelicula}")
def peliculas_duracion(pelicula:str):
    peli_filtro = Data_recomendación[Data_recomendación['title'] == pelicula]
    duracion =  peli_filtro['runtime']
    año = peli_filtro['release_year']
    return {'PELICULA:':pelicula, 'duracion en minutos:':duracion, 'año de estreno:':año } 


# FUNCION 3:
# ESTA FUNCION RETORNA LA CANTIDAD DE PELICULAS, GANANCIA TOTAL Y PROMEDIO AL INGRESAR LA FRANQUICIA
@app.get("/franquicia/{franquicia}")
def franquicia(franquicia:str):
    franquicia_filtro = Data_recomendación[Data_recomendación['name_collection'] == franquicia]
    cantidad_pelis = Data_recomendación['name_collection'].shape[0]
    ganancia = Data_recomendación['revenue'].sum()
    promedio = Data_recomendación['revenue'].mean()
    return {'franquicia:':franquicia, 'ganancias totales generadas:':ganancia, 'ganancia promedio:':promedio}


# FUNCION 4:
# ESTA FUNCION RETORNA LA CANTIDAD DE PELICULAS PRODUCIDAS EN EL MISMO PAIS
@app.get("/peliculas_pais/{pais}")
def peliculas_pais(pais:str):
    pais_filtro = Data_recomendación[Data_recomendación['name_countrie'] == pais]
    cantidad = pais_filtro['name_countrie'].shape[0]
    return{'pais:':pais, 'cantidad de peliculas creadas:':cantidad}


# FUNCION 5:
# ESTA FUNCION AL INGRESAR LA PRODUCTORA ENTREGA EL REVENUE TOTAL Y LA CANTIDAD DE PELICULAS QUE REALIZO
@app.get("/productoras_exitosas/{productora}")
def productoras_exitosas(productora:str):
    productora_filtro = Data_recomendación[Data_recomendación['name_production'] == productora]
    cantidad = productora_filtro['revenue'].sum()
    cantidad_peliculas = productora_filtro['name_production'].shape[0]
    return{'productora:':productora, 'ganancias totales:':cantidad, 'cantidad de peliculas generadas:':cantidad_peliculas}

# FUNCION 6:
# ESTA FUNCION AL INGRESAR EL NOMBRE DE UN DIRECTOR DEVUELVE EL EXITO DEL MISMO A TRAVES DEL RETORNO /
# DEVUELVE EL NOMBRE DE CADA PELICULA CON LA FECHA DE LANZAMIENTO, RETORNO INDIVIDUAL, COSTO Y GANANCIA DE LA MISMA
@app.get("/get_director/{director}")
def get_director(director:str):
   director_data = Data_recomendación[Data_recomendación['name_director'].apply(lambda x: director in x if isinstance(x, (list, str)) else False)].head(5)
   ganancias_totales = director_data['revenue'].sum()
   peliculas = []
   for _, row in director_data.iterrows():
        titulo = row['title']
        fecha_estreno = row['release_date']
        retorno = row['return']
        costo = row['budget']
        ganancia = row['revenue']
        peliculas.append({'titulo': titulo, 'fecha_estreno': fecha_estreno, 'retorno':retorno, 'ganancia generada:':ganancia, 'coste de la pelicula:': costo})
    
   return {'nombre del director': director, 'retorno total': ganancias_totales, 'peliculas': peliculas}



      # CREACION DEL MODELO DE RECOMENDACIONES  

# UTILIZAMOS SOLO 20 MIL FILAS DEL DATASETS
muestra_aleatoria = Data_recomendación.head(5000) 

# CONVERTIMOS EL TEXTO EN UNA MATRIZ DE CARACTERISTICAS NUMERICAS PARA FACILITAR EL CALCULO DE SIMILITUDES
tfidf = TfidfVectorizer(stop_words='english') 

# REMPLAZAMOS LOS VALORES NULOS POR EL ESPACIO VACIO PARA EVITAR ERRORES
muestra_aleatoria['overview'] = muestra_aleatoria['overview'].fillna('') 

# ANALIZAMOS Y EXTRAEMOS LAS PALABRAS MAS IMPORTANTES CON TF-IDF Y CREAMOS UNA MATRIZ QUE REPRESENTA LA IMPORTANCIA DE LAS PALABRAS EN CADA DESCRIPCION, ESTO NOS SIRVE PARA ENCONTRAR LAS PELICULAS SIMILARES
tdfid_matrix = tfidf.fit_transform(muestra_aleatoria['overview']) 
                                                                        
# CALCULAMOS LA SIMILITUD COSENO ENTRE TODAS LAS DESCRIPCIONES / LA SIMILITUD COSENO ES UNA MEDIDA QUE NOS INDICAN CUANDO SE APARECEN DOS VECTORES
cosine_similarity = linear_kernel( tdfid_matrix, tdfid_matrix) 
                                                               

# CREAMOS LA FUNCION "RECOMENDACION" LA CUAL CONSISTE EN RECOMENDAR 5 PELICULAS  EN BASE AL PARAMETRO TITULO QUE LE PASEMOS
@app.get("/recomendacion/{titulo}")
def recomendacion(titulo: str):
    idx = muestra_aleatoria[muestra_aleatoria['title'] == titulo].index[0] # BUSCAMOS EL INDICE TITULO EN NUESTRO DATASETS
    sim_cosine = list(enumerate(cosine_similarity[idx])) # ACCEDEMOS A LA FILA "idx" DE LA MATRIZ "SIMILITUD COSENO" ENUMERO FILAS, CREAMOS LISTA DE TUPLAS, DONDE CADA TUPLA CONTIENE EL INDICE Y SIMILITUD COSENO DE LA PELICULA
    sim_scores = sorted(sim_cosine, key=lambda x: x[1], reverse=True) # ORDENAMOS LA LISTA DE TUPLAS EN FUNCION DE LA SIMILITUD COSENO DE MANERA DESCENDENTE, GUARDAMOS LOS RESULTADOS EN UNA VARIABLE sim_scores
    similar_indices = [i for i, _ in sim_scores[1:6]] # CREAMOS LA LISTA DE LAS 5 MEJORES PELICULAS 
    similar_movies = muestra_aleatoria['title'].iloc[similar_indices].values.tolist() # SELECCIONAMOS LOS TITULOS SEGUN LOS INDICES Y LOS PASAMOS A UNA LISTA
   
    return similar_movies # RETORNAMOS LA LISTA

### RESUMEN:
### En resumen creamos una funcion que toma el titulo de una pelicula y encuentra las peliculas mas similares basandose en la similitud del coseno 
### de las descripciones de las peliculas devolviendo una lista con 5 peliculas

