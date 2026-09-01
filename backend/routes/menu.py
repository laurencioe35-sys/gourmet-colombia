from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
import unicodedata
from ..database import get_db
from ..models import Categoria, Producto
from ..schemas import (
    CategoriaCreate, CategoriaUpdate, CategoriaOut,
    ProductoCreate, ProductoUpdate, ProductoOut
)

router = APIRouter()
PRECIO_ALMUERZO_CORRIENTE = 18000


def _precio_base_corriente(precio: object | None, nombre: str | None = None) -> float:
    precio_num = float(precio or 0)
    nombre_limpio = (nombre or "").strip().lower()
    if precio_num > 0:
        return precio_num
    if "almuerzo" in nombre_limpio or "corriente" in nombre_limpio:
        return float(PRECIO_ALMUERZO_CORRIENTE)
    return float(PRECIO_ALMUERZO_CORRIENTE if precio_num == 0 else precio_num)


def _normalizar_categoria(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", (nombre or "")).encode("ascii", "ignore").decode().lower()
    texto = " ".join(texto.replace("menus", "menu").split())
    if "corriente" in texto or "almuerzo general" in texto or texto == "almuerzo":
        return "almuerzos corrientes"
    return texto


# ── CATEGORÍAS ────────────────────────────────────────────────────────────────

@router.get("/categorias", response_model=List[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).filter(Categoria.activo == True).order_by(Categoria.orden).all()


@router.post("/categorias", response_model=CategoriaOut)
def crear_categoria(data: CategoriaCreate, db: Session = Depends(get_db)):
    cat = Categoria(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categorias/{cat_id}", response_model=CategoriaOut)
def actualizar_categoria(cat_id: int, data: CategoriaUpdate, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categorias/{cat_id}")
def eliminar_categoria(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    cat.activo = False
    db.commit()
    return {"ok": True}


# ── PRODUCTOS ─────────────────────────────────────────────────────────────────

@router.get("/productos", response_model=List[ProductoOut])
def listar_productos(
    categoria_id: Optional[int] = None,
    disponible: Optional[bool] = None,
    destacado: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Producto).options(joinedload(Producto.categoria))
    if categoria_id:
        q = q.filter(Producto.categoria_id == categoria_id)
    if disponible is not None:
        q = q.filter(Producto.disponible == disponible)
    if destacado is not None:
        q = q.filter(Producto.destacado == destacado)
    return q.all()


@router.get("/productos/{prod_id}", response_model=ProductoOut)
def obtener_producto(prod_id: int, db: Session = Depends(get_db)):
    prod = db.query(Producto).options(joinedload(Producto.categoria)).filter(Producto.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@router.post("/productos", response_model=ProductoOut)
def crear_producto(data: ProductoCreate, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == data.categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    prod = Producto(**data.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@router.put("/productos/{prod_id}", response_model=ProductoOut)
def actualizar_producto(prod_id: int, data: ProductoUpdate, db: Session = Depends(get_db)):
    prod = db.query(Producto).filter(Producto.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(prod, k, v)
    db.commit()
    db.refresh(prod)
    return prod


@router.delete("/productos/{prod_id}")
def eliminar_producto(prod_id: int, db: Session = Depends(get_db)):
    prod = db.query(Producto).filter(Producto.id == prod_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    prod.disponible = False
    db.commit()
    return {"ok": True}


@router.post("/activar-dia")
def activar_menu_dia(items: List[dict] = Body(...), db: Session = Depends(get_db)):
    """
    Activa los platos elegidos para el día de hoy.
    Desactiva todos los demás productos en la BD.
    Crea el producto si no existe, o actualiza precio/datos si ya existe.
    """
    # Desactivar todo
    db.query(Producto).update({Producto.disponible: False})
    db.flush()

    activados = 0
    vistos = set()
    for item in items:
        categoria_normalizada = _normalizar_categoria(item.get("categoria"))
        nombre = (item.get("nombre") or "").strip()
        clave = (categoria_normalizada, nombre.casefold())
        if not nombre or clave in vistos:
            continue
        vistos.add(clave)
        cat = db.query(Categoria).filter(
            Categoria.nombre.ilike("%Almuerzos Corrientes%" if categoria_normalizada == "almuerzos corrientes" else f"%{item.get('categoria', '').split('&')[0].strip()}%")
        ).first()
        if not cat:
            continue

        prod = db.query(Producto).filter(
            Producto.categoria_id == cat.id,
            func.lower(Producto.nombre) == nombre.casefold()
        ).first()

        precio_final = float(item.get("precio", prod.precio if prod else 0) or 0)
        if categoria_normalizada == "almuerzos corrientes":
            precio_final = _precio_base_corriente(precio_final, nombre)
        if prod:
            prod.precio      = precio_final
            prod.disponible  = True
            prod.descripcion = item.get("descripcion", prod.descripcion) or prod.descripcion
            prod.emoji       = item.get("emoji", prod.emoji) or prod.emoji
            prod.tiempo_prep = int(item.get("tiempo_prep", prod.tiempo_prep) or 15)
        else:
            prod = Producto(
                categoria_id = cat.id,
                nombre       = nombre,
                descripcion  = item.get("descripcion", ""),
                precio       = precio_final,
                emoji        = item.get("emoji", "🍽️"),
                tiempo_prep  = int(item.get("tiempo_prep", 15)),
                disponible   = True,
            )
            db.add(prod)
        activados += 1

    db.commit()
    return {"ok": True, "activados": activados}


@router.get("/completo")
def menu_completo(db: Session = Depends(get_db)):
    """Devuelve el menú completo organizado por categorías."""
    categorias = db.query(Categoria).filter(Categoria.activo == True).order_by(Categoria.orden).all()
    resultado = []
    for cat in categorias:
        productos = db.query(Producto).filter(
            Producto.categoria_id == cat.id,
            Producto.disponible == True
        ).all()
        productos_normalizados = []
        for p in productos:
            precio = float(p.precio or 0)
            if "almuerzos corrientes" in (cat.nombre or "").lower():
                precio = _precio_base_corriente(precio, p.nombre)
            productos_normalizados.append({
                "id": p.id,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "precio": precio,
                "emoji": p.emoji,
                "imagen_url": p.imagen_url,
                "destacado": p.destacado,
                "tiempo_prep": p.tiempo_prep,
            })
        resultado.append({
            "id": cat.id,
            "nombre": cat.nombre,
            "emoji": cat.emoji,
            "color": cat.color,
            "productos": productos_normalizados,
        })
    return resultado
