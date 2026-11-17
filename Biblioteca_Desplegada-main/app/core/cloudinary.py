import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import get_settings

# Obtenemos la configuración mediante la función con caché
settings = get_settings()

# Configuramos Cloudinary con los datos de tu archivo .env leídos por Pydantic
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)

def subir_imagen_cloudinary(file: UploadFile) -> str:
    """
    Sube una imagen de tipo UploadFile a Cloudinary y retorna la URL segura (secure_url).
    """
    try:
        # Lee el contenido del archivo recibido desde FastAPI
        contenido = file.file.read()
        
        # Sube la imagen a Cloudinary usando el método de carga por lotes/bytes
        resultado = cloudinary.uploader.upload(contenido)
        
        # Retorna la URL segura de la imagen alojada en la nube
        return resultado.get("secure_url")
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir la imagen a Cloudinary: {str(e)}"
        )