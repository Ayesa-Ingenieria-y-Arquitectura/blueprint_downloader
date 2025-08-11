from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests
import os
import mimetypes
import uvicorn
from typing import Optional
import json

app = FastAPI(title="File Server API - Azure AD Auth", version="1.0.0")

# Configuración Azure AD
TENANT_ID = os.getenv("TENANT_ID", "b245367b-55a3-4d61-92d0-992b771e1d1f")
CLIENT_ID = os.getenv("CLIENT_ID", "59141cc0-7dc6-4c5d-bfdb-1ebb8b1c4910")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio base
BASE_DIR = os.getenv("BASE_DIR", "/home/digital_engineering/Documents/Toolbar")

# Configurar HTTPBearer
security = HTTPBearer()

async def verify_azure_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar que el token de Azure AD sea válido usando Microsoft Graph API"""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Validar el token llamando a Microsoft Graph API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Hacer una llamada a Microsoft Graph para validar el token
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado o inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Error validando token: {response.status_code}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = response.json()
        
        return {
            "user_id": user_data.get("id"),
            "user_name": user_data.get("displayName"),
            "email": user_data.get("userPrincipalName"),
            "given_name": user_data.get("givenName"),
            "surname": user_data.get("surname"),
            "job_title": user_data.get("jobTitle"),
            "office_location": user_data.get("officeLocation")
        }
        
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando con Microsoft Graph: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except json.JSONDecodeError:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validando token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Endpoints principales
@app.get("/")
async def root():
    return {
        "message": "File Server API - Azure AD Auth is running",
        "version": "1.0.0",
        "auth": "Azure AD Bearer Token required",
        "tenant_id": TENANT_ID,
        "client_id": CLIENT_ID,
        "endpoints": {
            "me": "GET /me",
            "list_files": "GET /files/",
            "get_file": "GET /file/{path}",
            "download": "GET /download/{path}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/me")
async def get_current_user(user_info: dict = Depends(verify_azure_token)):
    """Obtener información del usuario actual"""
    return {
        "user": user_info,
        "message": "Usuario autenticado correctamente"
    }

@app.get("/file/{file_path:path}")
async def get_file(file_path: str, user_info: dict = Depends(verify_azure_token)):
    """Obtiene un archivo específico por su ruta"""
    full_path = os.path.join(BASE_DIR, file_path)
    
    # Validaciones de seguridad
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail="La ruta no es un archivo")
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Acceso denegado: ruta fuera del directorio permitido")
    
    # Obtener tipo MIME
    mime_type, _ = mimetypes.guess_type(full_path)
    
    return FileResponse(
        path=full_path,
        media_type=mime_type,
        filename=os.path.basename(full_path)
    )

@app.get("/files/")
async def list_files(directory: str = "", user_info: dict = Depends(verify_azure_token)):
    """Lista archivos en un directorio específico"""
    target_dir = os.path.join(BASE_DIR, directory)
    
    # Validaciones de seguridad
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Directorio no encontrado")
    
    if not os.path.isdir(target_dir):
        raise HTTPException(status_code=400, detail="La ruta no es un directorio")
    
    if not os.path.abspath(target_dir).startswith(os.path.abspath(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Acceso denegado: ruta fuera del directorio permitido")
    
    try:
        files = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            stat_info = os.stat(item_path)
            
            files.append({
                "name": item,
                "is_directory": os.path.isdir(item_path),
                "size": stat_info.st_size if os.path.isfile(item_path) else None,
                "path": os.path.join(directory, item).replace("\\", "/"),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "permissions": oct(stat_info.st_mode)[-3:]
            })
        
        return {
            "files": sorted(files, key=lambda x: (not x["is_directory"], x["name"].lower())),
            "directory": directory,
            "total_items": len(files),
            "user": user_info["user_name"]  # Incluir info del usuario
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="Sin permisos para acceder al directorio")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar archivos: {str(e)}")

@app.get("/download/{file_path:path}")
async def download_file(file_path: str, user_info: dict = Depends(verify_azure_token)):
    """Descarga un archivo forzando la descarga"""
    full_path = os.path.join(BASE_DIR, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail="La ruta no es un archivo")
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return FileResponse(
        path=full_path,
        filename=os.path.basename(full_path),
        headers={
            "Content-Disposition": f"attachment; filename=\"{os.path.basename(full_path)}\""
        }
    )

if __name__ == "__main__":
    print("🚀 Iniciando File Server API - Azure AD Auth")
    print(f"📁 Directorio base: {BASE_DIR}")
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"🔑 Client ID: {CLIENT_ID}")
    print("🔐 Autenticación: Azure AD Bearer Token")
    print("✅ Validación: Microsoft Graph API")
    uvicorn.run(app, host="0.0.0.0", port=8000)