from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ==========================================
# 1. Esquemas de datos con Pydantic
# ==========================================
# Esquema de entrada (Validación estricta)

class SolicitudEntrega(BaseModel):
    codigo_pedido: str = Field(min_length=3, max_length=30, description="Código identificador del pedido")
    distancia_km: float = Field(gt=0, le=5000, description="Distancia del envío en kilómetros")
    tipo_envio: Literal["express", "estandar", "economico"] = Field(description="Modalidad de envío contratada")
    horas_desde_pedido: int = Field(ge=0, le=720, description="Horas transcurridas desde que se realizó el pedido")
    es_festivo: bool = Field(default=False, description="Indica si el envío coincide con un día festivo")
    clima_adverso: bool = Field(default=False,  description="Indica si existen condiciones meteorológicas adversas")
    zona_remota: bool = Field(default=False, description="Indica si el destino está en una zona remota")


# Esquema de respuesta tipado
class ResultadoEntrega(BaseModel):
    codigo_pedido: str
    riesgo_retraso: Literal["Bajo", "Medio", "Alto"]
    score_riesgo: float = Field( ge=0,le=100, description="Puntuación heurística de riesgo entre 0 y 100")
    probabilidad_retraso: float = Field(ge=0, le=1, description="Probabilidad simulada entre 0 y 1")
    retraso_estimado_horas: float = Field(ge=0, description="Estimación orientativa del retraso en horas" )
    motivo: str = Field(min_length=1, description="Explicación de los factores evaluados")


# ==========================================
# 2. Servidor FastAPI, CORS y estáticos
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Predictor Inteligente de Retrasos en Entregas",
    description=(
        "API que calcula el riesgo de retraso de un pedido según sus características y las condiciones de entrega."
    ),
        version="1.0.0"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# ==========================================
# 3. Endpoints del servicio y Frontend
# ==========================================

@app.get("/", response_class=FileResponse, tags=["Frontend"])
def inicio():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/api/info", tags=["Información"])
def informacion():
    """Devuelve información general sobre el servicio."""
    return {
        "servicio": "Predictor de retrasos en entregas",
        "estado": "operativo",
        "version": "1.0.0",
        "endpoint_inferencia": "/api/predecir-retraso",
        "documentacion": "/docs",
        "tipo_modelo": "Simulación heurística"
    }


@app.get("/api/health", tags=["Información"])
def comprobar_estado():
    """Comprueba si la API está disponible."""
    return {"estado": "ok"}


# ==========================================
# 4. Endpoint de inferencia
# ==========================================

@app.post(
    "/api/predecir-retraso",
    response_model=ResultadoEntrega,
    tags=["Predicción"],
    summary="Evaluar el riesgo de retraso de un pedido"
)
def predecir_retraso(solicitud: SolicitudEntrega):
    """
    Calcula una puntuación de riesgo a partir de las características
    del envío y devuelve una clasificación y una explicación.
    """

    # Puntuación inicial
    score = 10.0
    factores = []

    # Distancia del envío
    if solicitud.distancia_km > 1500:
        score += 25
        factores.append("distancia muy elevada (+25)")
    elif solicitud.distancia_km > 500:
        score += 15
        factores.append("distancia elevada (+15)")

    # Modalidad contratada
    if solicitud.tipo_envio == "economico":
        score += 20
        factores.append("envío económico (+20)")
    elif solicitud.tipo_envio == "estandar":
        score += 10
        factores.append("envío estándar (+10)")
    else:
        score -= 10
        factores.append("envío exprés (-10)")

    # Tiempo transcurrido desde el pedido
    if solicitud.horas_desde_pedido > 48:
        score += 20
        factores.append("más de 48 horas desde el pedido (+20)")
    elif solicitud.horas_desde_pedido > 24:
        score += 10
        factores.append("más de 24 horas desde el pedido (+10)")

    # Festivos
    if solicitud.es_festivo:
        score += 15
        factores.append("día festivo (+15)")

    # Condiciones meteorológicas
    if solicitud.clima_adverso:
        score += 25
        factores.append("clima adverso (+25)")

    # Ubicación de destino
    if solicitud.zona_remota:
        score += 15
        factores.append("destino en zona remota (+15)")

    # Limitamos la puntuación al intervalo de 0 a 100
    score = max(0.0, min(100.0, round(score, 1)))

    # Clasificación del riesgo
    if score < 30:
        riesgo = "Bajo"
    elif score < 60:
        riesgo = "Medio"
    else:
        riesgo = "Alto"

    # Probabilidad simulada: escala didáctica basada en el score
    probabilidad = round(score / 100, 2)

    # Estimación heurística de horas de retraso
    if score < 30:
        retraso_horas = 0.0
    elif score < 60:
        retraso_horas = round(2 + (score - 30) * 0.2, 1)
    else:
        retraso_horas = round(8 + (score - 60) * 0.3, 1)

    # Explicación del resultado
    if riesgo == "Bajo":
        resumen = "El pedido presenta un riesgo bajo de retraso."
    elif riesgo == "Medio":
        resumen = "El pedido presenta un riesgo moderado de retraso."
    else:
        resumen = "El pedido presenta un riesgo alto de retraso."

    motivo = resumen + " Factores evaluados: " + (
        ", ".join(factores) if factores else "sin factores adicionales"
    ) + "."

    return {
        "codigo_pedido": solicitud.codigo_pedido,
        "riesgo_retraso": riesgo,
        "score_riesgo": score,
        "probabilidad_retraso": probabilidad,
        "retraso_estimado_horas": retraso_horas,
        "motivo": motivo
    }
