# Blueprint Downloader API - Release Documentation

## 📋 Información General

**Repositorio:** Pablo-Rods/blueprint_downloader  
**Descripción:** API desplegada en servidor Linux para la gestión de archivos necesarios para las toolbars de Civil 3D y Revit  
**Autenticación:** Azure OAuth2 (Tenant de Ayesa)

## 🚀 Características Principales

### Funcionalidades Core
- **Gestión de Plantillas**: Descarga y distribución de plantillas para Civil 3D y Revit
- **Control de Versiones**: Manejo automático de versiones de archivos y componentes
- **Distribución de Toolbars**: Provisión de archivos necesarios para ejecutar toolbars especializadas
- **Autenticación Segura**: Integración con Azure OAuth2 para control de acceso

### Arquitectura
- **Plataforma**: Linux Server
- **Tipo**: RESTful API
- **Autenticación**: Azure OAuth2 (Tenant Ayesa)
- **Aplicaciones Objetivo**: Autodesk Civil 3D, Autodesk Revit

## 🔐 Autenticación y Seguridad

### Requisitos de Autenticación
- Los usuarios deben estar autenticados en el tenant de Ayesa
- Implementación de Azure OAuth2 para control de acceso
- Tokens de acceso requeridos para todas las llamadas a la API

### Flujo de Autenticación
1. El usuario se autentica contra Azure AD (Tenant Ayesa)
2. Se obtiene el token de acceso OAuth2
3. El token se incluye en las solicitudes HTTP a la API
4. La API valida el token antes de procesar la solicitud

## 📁 Estructura de Archivos Gestionados

### Tipos de Archivos
- **Plantillas (.dwt, .rte)**: Templates base para proyectos
- **Archivos de Versión**: Control de versiones de componentes
- **Configuraciones de Toolbar**: Archivos de configuración para interfaces
- **Recursos Adicionales**: Bibliotecas, símbolos y recursos complementarios

### Organización
```
/templates
  ├── civil3d/
  │   ├── templates/
  │   ├── config/
  │   └── versions/
  └── revit/
      ├── templates/
      ├── families/
      ├── config/
      └── versions/
```

## 🛠️ Endpoints de la API

### Autenticación
```http
POST /auth/login
Content-Type: application/json
Authorization: Bearer {azure_token}
```

### Gestión de Plantillas
```http
GET /api/templates
GET /api/templates/{software}/{category}
GET /api/templates/{id}/download
```

### Control de Versiones
```http
GET /api/versions
GET /api/versions/{software}/latest
GET /api/versions/{software}/{version}
```

### Toolbars
```http
GET /api/toolbars/{software}
GET /api/toolbars/{software}/config
POST /api/toolbars/{software}/update
```

## 📦 Instalación y Despliegue

### Prerrequisitos del Sistema
- Servidor Linux (distribución compatible)
- Python 3.x o runtime correspondiente
- Conexión a Azure AD configurada
- Certificados SSL para HTTPS

### Variables de Entorno
```bash
AZURE_TENANT_ID=<tenant_id_ayesa>
AZURE_CLIENT_ID=<client_id>
AZURE_CLIENT_SECRET=<client_secret>
API_PORT=<puerto_api>
LOG_LEVEL=<nivel_logging>
FILE_STORAGE_PATH=<ruta_archivos>
```

### Proceso de Despliegue
1. Clonar el repositorio en el servidor
2. Configurar variables de entorno
3. Instalar dependencias
4. Configurar proxy/load balancer si es necesario
5. Iniciar el servicio
6. Verificar endpoints de salud

## 🔧 Configuración

### Configuración de Azure OAuth2
```json
{
  "azure": {
    "tenant_id": "tenant-ayesa-id",
    "client_id": "app-client-id",
    "client_secret": "app-secret",
    "authority": "https://login.microsoftonline.com/{tenant_id}"
  }
}
```

### Configuración de Software Soportado
```json
{
  "supported_software": {
    "civil3d": {
      "versions": ["2022", "2023", "2024"]
    },
    "revit": {
      "versions": ["2022", "2023", "2024"]
    }
  }
}
```

## 📊 Monitoreo y Logging

### Métricas de Monitoreo
- Tiempo de respuesta de endpoints
- Número de descargas por software/plantilla
- Errores de autenticación
- Uso de ancho de banda
- Disponibilidad del servicio

### Logging
- Eventos de autenticación
- Descargas de archivos
- Errores y excepciones
- Actualizaciones de versión
- Accesos denegados

## 🐛 Troubleshooting

### Problemas Comunes

#### Error de Autenticación
**Síntoma**: HTTP 401 Unauthorized
**Solución**: 
- Verificar token de Azure válido
- Confirmar permisos en tenant de Ayesa
- Revisar configuración de cliente OAuth2

#### Archivos No Encontrados
**Síntoma**: HTTP 404 Not Found
**Solución**:
- Verificar estructura de directorios
- Confirmar existencia de versión solicitada
- Revisar permisos de lectura en archivos

#### Problemas de Red
**Síntoma**: Timeouts o conexiones rechazadas
**Solución**:
- Verificar conectividad de red
- Revisar configuración de firewall
- Confirmar estado del servidor

---

*Esta documentación se actualiza con cada release. Para la versión más actual, consulte el repositorio en GitHub.*
