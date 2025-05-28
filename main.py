#Para iniciar la api es colocando "fastapi dev main.py"


from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase


#Crear una instancia de la aplicacion FastAPI
app = FastAPI()

#Modelo de datos para un pedido
class Pedido(BaseModel):
    id_pedido: int
    nombre_cliente: str
    items: List[str]                # Lista de de algun posible iems/productos en el pedido
    estado: str                     # Estado del pedido  pendiente o enviado 
    ubicacion_bodega: str           # Lugar de la bodega

#Modelo de datos para una actualizar estado 
class ActualizacionEstado(BaseModel):
    id_pedido: int
    nuevo_estado: str



#Bievenida "improvisada"

@app.get("/")
def leer_raiz():
    return {"mensaje": "Bienvenido a la API de Logística de Pedidos"}




#Crear pedidos 
@app.post("/pedidos/", response_model=Pedido)           #ruta post pa crear pedidos y devuelve el pedido como respuesta    
def crear_pedido(pedido: Pedido):                       #funcion que recibe un pedido como json
    response = supabase.table("pedidos").insert(pedido.dict()).execute()    #Lo guarda en la base de datos de supabase
    error = getattr(response, 'error', None)                                    #agarra el error si hay uno en la respuesta
    if error:      #si hay error lanza un 500
        raise HTTPException(status_code=500, detail=f"Error al crear el pedido: {error}")    
    return pedido   #si todo bien retorna el pedido

@app.get("/pedidos/", response_model=List[Pedido])
def leer_pedidos():
    response = supabase.table("pedidos").select("*").execute()
    if not hasattr(response, "data") or response.data is None:
        raise HTTPException(status_code=500, detail="Error al obtener pedidos")
    return response.data

@app.get("/pedidos/{id_pedido}", response_model=Pedido)
def leer_pedido(id_pedido: int):
    response = supabase.table("pedidos").select("*").eq("id_pedido", id_pedido).maybe_single().execute()
    data = getattr(response, 'data', None) or (response.get('data') if isinstance(response, dict) else None)
    error = getattr(response, 'error', None) or (response.get('error') if isinstance(response, dict) else None)
    if error:
        raise HTTPException(status_code=500, detail=f"Error Supabase: {error}")
    if not data:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return data

@app.put("/pedidos/{id_pedido}/estado/", response_model=Pedido)
def actualizar_estado_pedido(id_pedido: int, actualizacion_estado: ActualizacionEstado):
    response = supabase.table("pedidos").update({"estado": actualizacion_estado.nuevo_estado}).eq("id_pedido", id_pedido).execute()
    if not hasattr(response, "data") or not response.data:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o error al actualizar")
    return response.data[0]



#Bodegas


@app.get("/bodegas/", response_model=List[str])
def obtener_bodegas():
    response = supabase.table("pedidos").select("ubicacion_bodega").execute()
    if not hasattr(response, "data") or response.data is None:
        raise HTTPException(status_code=500, detail="Error al obtener bodegas")
    bodegas = list(set(p["ubicacion_bodega"] for p in response.data if "ubicacion_bodega" in p))
    return bodegas


@app.get("/bodegas/{ubicacion_bodega}", response_model=List[Pedido])
def obtener_pedidos_en_bodega(ubicacion_bodega: str):
    response = supabase.table("pedidos").select("*").eq("ubicacion_bodega", ubicacion_bodega).execute()
    if not hasattr(response, "data") or response.data is None:
        raise HTTPException(status_code=500, detail="Error al obtener pedidos de la bodega")
    return response.data






















#Codigo en caso de usar la api del otro grupo



# Endpoint para comunicarse con el modulo de Ventas
#@app.post("/ventas/modulo/", response_model=Dict[str, str])
#def comunicarse_con_ventas(datos_modulo: Dict[str, str]):
#    return {"mensaje": "Datos recibidos por el Módulo de Ventas", "datos": datos_modulo}

# Endpoint para comunicarse con el modulo de Post-Venta
#@app.post("/post-ventas/modulo/", response_model=Dict[str, str])
#def comunicarse_con_post_ventas(datos_modulo: Dict[str, str]):
#    return {"mensaje": "Datos recibidos por el Módulo de Post-Ventas", "datos": datos_modulo}

# Endpoint para comunicarse con el modulo de Reporteria
#@app.post("/reporting/modulo/", response_model=Dict[str, str])
#def comunicarse_con_reporting(datos_modulo: Dict[str, str]):
#    return {"mensaje": "Datos recibidos por el Módulo de Reporteria", "datos": datos_modulo}



