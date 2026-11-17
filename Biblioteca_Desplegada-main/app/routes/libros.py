from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.controllers import libro as libro_controller
from app.controllers.libro import OrdenLibro
from app.core.cloudinary import subir_imagen_cloudinary
from app.core.dependencies import get_db, paginacion, requiere_rol
from app.models.usuario import RolUsuario
from app.routes.common import ERROR_RESPONSES
from app.schemas.libro import LibroCreate, LibroResponse, LibroUpdate
from app.schemas.pagina import Pagina

router = APIRouter(
    prefix="/libros",
    tags=["Libros"],
    responses=ERROR_RESPONSES,
)


@router.get(
    "",
    response_model=Pagina[LibroResponse],
    summary="Buscar y listar libros",
)
def listar_libros(
    db: Annotated[Session, Depends(get_db)],
    pag: Annotated[dict, Depends(paginacion)],
    buscar: str | None = None,
    autor: str | None = None,
    categoria_id: int | None = None,
    desde: int | None = None,
    hasta: int | None = None,
    orden: OrdenLibro | None = None,
):
    return libro_controller.get_libros(
        db,
        pag["skip"],
        pag["limit"],
        buscar,
        autor,
        categoria_id,
        desde,
        hasta,
        orden,
    )


@router.get(
    "/autores/{autor_id}/libros",
    response_model=Pagina[LibroResponse],
    summary="Listar libros de un autor",
)
def listar_libros_por_autor(
    autor_id: int,
    db: Annotated[Session, Depends(get_db)],
    pag: Annotated[dict, Depends(paginacion)],
):
    return libro_controller.get_libros_by_autor(
        db, autor_id, pag["skip"], pag["limit"]
    )


@router.get(
    "/{libro_id}",
    response_model=LibroResponse,
    summary="Consultar un libro",
)
def obtener_libro(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return libro_controller.get_libro_by_id(db, libro_id)


@router.post(
    "",
    response_model=LibroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un libro",
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
)
async def crear_libro(
    # Recibimos los datos del libro individualmente mediante Form para permitir el archivo
    titulo: str = Form(..., min_length=1, max_length=150),
    isbn: str = Form(...),
    anio_publicacion: int = Form(...),
    ejemplares: int = Form(...),
    autor_id: int = Form(...),
    categoria_ids: str = Form(...),  # Recibido como string o número desde el formulario
    imagen: UploadFile = File(None),  # Archivo de imagen opcional para Cloudinary
    db: Session = Depends(get_db),
):
    # Subir imagen a Cloudinary si se adjuntó un archivo
    imagen_url = None
    if imagen and imagen.filename:
        imagen_url = subir_imagen_cloudinary(imagen)

    import json
    
    # Procesar categoria_ids de manera robusta para asegurar que siempre sea una lista de enteros
    parsed_categorias = []
    if isinstance(categoria_ids, str):
        try:
            loaded = json.loads(categoria_ids)
            if isinstance(loaded, list):
                parsed_categorias = [int(cat) for cat in loaded]
            else:
                parsed_categorias = [int(loaded)]
        except:
            parsed_categorias = [int(cat.strip()) for cat in categoria_ids.split(",") if cat.strip()]
    elif isinstance(categoria_ids, int):
        parsed_categorias = [categoria_ids]

    libro_data = LibroCreate(
        titulo=titulo,
        isbn=isbn,
        anio_publicacion=anio_publicacion,
        ejemplares=ejemplares,
        autor_id=autor_id,
        categoria_ids=parsed_categorias
    )

    return libro_controller.create_libro_con_imagen(db, libro_data, imagen_url) if hasattr(libro_controller, "create_libro_con_imagen") else libro_controller.create_libro(db, libro_data)


@router.patch(
    "/{libro_id}",
    response_model=LibroResponse,
    summary="Actualizar un libro",
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
)
async def actualizar_libro(
    libro_id: int,
    titulo: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    anio_publicacion: Optional[int] = Form(None),
    ejemplares: Optional[int] = Form(None),
    autor_id: Optional[int] = Form(None),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Subir nueva imagen a Cloudinary si se proporciona una nueva
    imagen_url = None
    if imagen and imagen.filename:
        imagen_url = subir_imagen_cloudinary(imagen)

    # Crear el esquema de actualización
    update_data = {
        k: v for k, v in {
            "titulo": titulo,
            "isbn": isbn,
            "anio_publicacion": anio_publicacion,
            "ejemplares": ejemplares,
            "autor_id": autor_id,
            "imagen_url": imagen_url
        }.items() if v is not None
    }
    
    libro_update = LibroUpdate(**update_data)
    return libro_controller.update_libro(db, libro_id, libro_update)


@router.delete(
    "/{libro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un libro",
    dependencies=[requiere_rol(RolUsuario.admin)],
)
def eliminar_libro(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return libro_controller.delete_libro(db, libro_id)