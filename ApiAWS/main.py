from typing import List
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from mysql_client import get_connection

app = FastAPI()
router = APIRouter(prefix="/api")

class Pedido(BaseModel):
    id_pedido: int
    nombre_cliente: str
    items: List[str]
    estado: str
    ubicacion_bodega: str

# Modelo para actualizar estado (si quieres agregar PUT después)
class ActualizacionEstado(BaseModel):
    nuevo_estado: str

@router.get("/")
def leer_raiz():
    return {"mensaje": "Bienvenido a la API de Logística de Pedidos"}

# POST para crear varios pedidos
@router.post("/pedidos/", response_model=List[Pedido])
def crear_pedidos(pedidos: List[Pedido]):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for pedido in pedidos:  # iterar cada pedido
            cursor.execute("""
                INSERT INTO pedidos (id_pedido, nombre_cliente, estado, ubicacion_bodega)
                VALUES (%s, %s, %s, %s)
            """, (
                pedido.id_pedido,
                pedido.nombre_cliente,
                pedido.estado,
                pedido.ubicacion_bodega
            ))

            for item in pedido.items:
                cursor.execute("""
                    INSERT INTO pedido_items (id_pedido, nombre_item)
                    VALUES (%s, %s)
                """, (pedido.id_pedido, item))

        conn.commit()
        return pedidos
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# GET para listar todos los pedidos con sus items
@router.get("/pedidos/", response_model=List[Pedido])
def obtener_pedidos():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id_pedido, nombre_cliente, estado, ubicacion_bodega
            FROM pedidos
            ORDER BY id_pedido
        """)
        pedidos_db = cursor.fetchall()

        pedidos = []
        for p in pedidos_db:
            id_pedido, nombre_cliente, estado, ubicacion_bodega = p
            cursor.execute("""
                SELECT nombre_item FROM pedido_items WHERE id_pedido = %s
            """, (id_pedido,))
            items_db = cursor.fetchall()
            items = [item[0] for item in items_db]

            pedidos.append(Pedido(
                id_pedido=id_pedido,
                nombre_cliente=nombre_cliente,
                items=items,
                estado=estado,
                ubicacion_bodega=ubicacion_bodega
            ))

        return pedidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Obtener un pedido por ID
@router.get("/pedidos/{id_pedido}", response_model=Pedido)
def leer_pedido(id_pedido: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        pedido = cursor.fetchone()

        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        cursor.execute("SELECT nombre_item FROM pedido_items WHERE id_pedido = %s", (id_pedido,))
        items = [row['nombre_item'] for row in cursor.fetchall()]

        return Pedido(**pedido, items=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Actualizar estado del pedido
@router.put("/pedidos/{id_pedido}/estado/", response_model=Pedido)
def actualizar_estado_pedido(id_pedido: int, actualizacion: ActualizacionEstado):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE pedidos SET estado = %s WHERE id_pedido = %s", (actualizacion.nuevo_estado, id_pedido))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        conn.commit()

        # Obtener datos actualizados
        cursor.execute("SELECT * FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        pedido = cursor.fetchone()
        cursor.execute("SELECT nombre_item FROM pedido_items WHERE id_pedido = %s", (id_pedido,))
        items = [row['nombre_item'] for row in cursor.fetchall()]

        return Pedido(**pedido, items=items)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Obtener todas las bodegas únicas
@router.get("/bodegas/", response_model=List[str])
def obtener_bodegas():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT ubicacion_bodega FROM pedidos")
        bodegas = [row[0] for row in cursor.fetchall()]
        return bodegas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Obtener pedidos por bodega
@router.get("/bodegas/{ubicacion_bodega}", response_model=List[Pedido])
def obtener_pedidos_en_bodega(ubicacion_bodega: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pedidos WHERE ubicacion_bodega = %s", (ubicacion_bodega,))
        pedidos_data = cursor.fetchall()

        pedidos = []
        for pedido in pedidos_data:
            cursor.execute("SELECT nombre_item FROM pedido_items WHERE id_pedido = %s", (pedido['id_pedido'],))
            items = [row['nombre_item'] for row in cursor.fetchall()]
            pedidos.append(Pedido(**pedido, items=items))

        return pedidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

app.include_router(router)