import json
import os
from google.oauth2 import service_account  # pyright: ignore[reportMissingImports]
from google.oauth2.credentials import Credentials  # pyright: ignore[reportMissingImports]
from googleapiclient.discovery import build  # pyright: ignore[reportMissingImports]
from googleapiclient.http import MediaIoBaseUpload  # pyright: ignore[reportMissingImports]
from io import BytesIO

# Configuración de los scopes necesarios para Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

import os
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def _get_drive_service():
    """Selecciona dinámicamente el método de autenticación según la variable de entorno."""
    auth_mode = os.getenv("DRIVE_AUTH_MODE", "service_account").lower()
    
    if auth_mode == "oauth":
        # Modo OAuth (Usuario personal con Refresh Token)
        client_id = os.getenv("DRIVE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("DRIVE_OAUTH_CLIENT_SECRET")
        refresh_token = os.getenv("DRIVE_OAUTH_REFRESH_TOKEN")

        faltantes = []
        if not client_id: faltantes.append("DRIVE_OAUTH_CLIENT_ID")
        if not client_secret: faltantes.append("DRIVE_OAUTH_CLIENT_SECRET")
        if not refresh_token: faltantes.append("DRIVE_OAUTH_REFRESH_TOKEN")
        
        if faltantes:
            raise ValueError(f"Faltan las siguientes variables de entorno para OAuth: {', '.join(faltantes)}")
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
    else:
        creds_json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_json_str:
            raise ValueError("La variable de entorno GOOGLE_SERVICE_ACCOUNT_JSON no está configurada.")
        creds_dict = json.loads(creds_json_str)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


    return build('drive', 'v3', credentials=creds)

def _obtener_o_crear_carpeta(service, nombre_carpeta: str, parent_id: str = None) -> str:
    """Busca una carpeta por nombre dentro de un directorio padre; si no existe, la crea."""
    query = f"name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    
    if files:
        return files[0]['id']
    
    # Si no existe, la creamos
    file_metadata = {
        'name': nombre_carpeta,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
        
    folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
    return folder.get('id')

def _resolver_ruta_vacante(service, vacante_codigo: str) -> str:
    """
    Resuelve la estructura 'Drive/<vacante.codigo>/'.
    Nota: Debes definir una carpeta raíz compartida con tu service account 
    o configurar el ID de la carpeta raíz principal mediante una variable de entorno.
    """
    root_folder_id = os.getenv("DRIVE_ROOT_FOLDER_ID") # ID de la carpeta raíz compartida en tu Drive
    
    # 1. Creamos/Buscamos la carpeta raíz general 'Drive' (o puedes usar la compartida directamente)
    # Aquí asumimos que DRIVE_ROOT_FOLDER_ID es la carpeta compartida donde agrupas todo.
    if not root_folder_id:
        raise ValueError("La variable de entorno DRIVE_ROOT_FOLDER_ID no está configurada.")
    
    # 2. Dentro de la raíz, buscamos o creamos la carpeta con el código de la vacante
    vacante_folder_id = _obtener_o_crear_carpeta(service, vacante_codigo, parent_id=root_folder_id)
    return vacante_folder_id


def guardar_hv(pdf_bytes: bytes, vacante, nombre: str) -> dict:
    """Sube a Drive/<vacante.codigo>/ y devuelve id y url."""
    service = _get_drive_service()
    folder_id = _resolver_ruta_vacante(service, vacante.codigo)
    
    file_metadata = {
        'name': f"{nombre}.pdf",
        'parents': [folder_id]
    }
    
    media = MediaIoBaseUpload(BytesIO(pdf_bytes), mimetype='application/pdf', resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        supportsAllDrives=True,
        fields='id, webViewLink, webContentLink'
    ).execute()
    
    return {
        "id": file.get('id'),
        "url": file.get('webViewLink')
    }


def renombrar_hv(drive_file_id: str, nota: int, nombre: str, cargo: str) -> None:
    """Renombra a '[NOTA] - [NOMBRE] - [CARGO].pdf'."""
    service = _get_drive_service()
    nuevo_nombre = f"[{nota}] - [{nombre}] - [{cargo}].pdf"
    
    file_metadata = {
        'name': nuevo_nombre
    }
    
    service.files().update(
        fileId=drive_file_id,
        body=file_metadata
    ).execute()


def mover_hv(drive_file_id: str, vacante) -> dict:
    """Mueve el PDF a Drive/<vacante.codigo>/ y devuelve id y url (pueden cambiar)."""
    service = _get_drive_service()
    nueva_folder_id = _resolver_ruta_vacante(service, vacante.codigo)
    
    # Para mover el archivo, necesitamos recuperar los padres actuales para removerlos
    file = service.files().get(fileId=drive_file_id, fields='parents, webViewLink').execute()
    previous_parents = ",".join(file.get('parents', []))
    
    # Actualizamos el archivo moviéndolo al nuevo directorio padre
    file = service.files().update(
        fileId=drive_file_id,
        addParents=nueva_folder_id,
        removeParents=previous_parents,
        fields='id, webViewLink'
    ).execute()
    
    return {
        "id": file.get('id'),
        "url": file.get('webViewLink')
    }


def borrar_hv(drive_file_id: str) -> None:
    """Borra el PDF. Si ya no existe se considera éxito (el borrado debe ser reintentable)."""
    service = _get_drive_service()
    try:
        service.files().delete(fileId=drive_file_id).execute()
    except Exception as e:
        # Verificamos si el error es porque el archivo ya no existe (HTTP 404 Not Found)
        error_str = str(e)
        if "404" in error_str or "File not found" in error_str:
            # Se considera éxito si ya fue borrado previamente (idempotencia / reintentable)
            return
        raise e