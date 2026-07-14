"""Servicio de ingestión de encuestas al esquema real (Supabase).

Lee un CSV de ArcGIS Survey123 y lo escribe en las tablas normalizadas:
    encuestas → respuestas_encuesta → detalle_respuestas → resultados_competencia
calculando los scores con `digcomp_scoring` (escala Likert 1–4).

También permite borrar TODAS las encuestas (cascade elimina respuestas, detalle y
resultados, conservando el catálogo competencias/preguntas/respuestas_correctas).
"""
from __future__ import annotations

import io
import logging
from datetime import datetime

import pandas as pd
from supabase import Client

from infrastructure.adapters.ingestion.digcomp_scoring import Pregunta, score_row

logger = logging.getLogger(__name__)

_GENEROS_VALIDOS = {"Masculino", "Femenino", "Otro"}


class SupabaseSurveyIngestion:
    """Carga y borra encuestas en el esquema real de Supabase."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self._empresa_id: str | None = None
        self._usuario_id: str | None = None
        self._preguntas: list[Pregunta] | None = None

    # ------------------------------------------------------------------ #
    # Catálogo (cacheado)
    # ------------------------------------------------------------------ #
    def _load_catalog(self) -> None:
        if self._preguntas is not None:
            return
        comps = self._client.table("competencias").select("*").execute().data
        if not comps:
            raise RuntimeError("No hay competencias cargadas en la base de datos.")
        id2cod = {c["id_competencia"]: c["codigo"] for c in comps}
        self._empresa_id = comps[0]["id_empresa"]

        usuarios = (
            self._client.table("usuarios")
            .select("id_usuario")
            .eq("id_empresa", self._empresa_id)
            .limit(1)
            .execute()
            .data
        )
        if not usuarios:
            raise RuntimeError("No hay usuarios en la empresa para registrar la carga.")
        self._usuario_id = usuarios[0]["id_usuario"]

        correct = {
            r["id_pregunta"]: r["letra_correcta"]
            for r in self._client.table("respuestas_correctas").select("*").execute().data
        }
        self._preguntas = [
            Pregunta(
                id_pregunta=p["id_pregunta"],
                id_competencia=p["id_competencia"],
                codigo_competencia=id2cod[p["id_competencia"]],
                id_tipo=p["id_tipo"],
                codigo_columna=p["codigo_columna"],
                letra_correcta=correct.get(p["id_pregunta"]),
            )
            for p in self._client.table("preguntas").select("*").execute().data
        ]

    # ------------------------------------------------------------------ #
    # Carga
    # ------------------------------------------------------------------ #
    def ingest(
        self, file_content: bytes, nombre: str, archivo_origen: str = "survey.csv"
    ) -> dict:
        """Procesa el CSV y persiste encuesta + respuestas + detalle + resultados."""
        self._load_catalog()
        assert self._preguntas is not None

        try:
            df = pd.read_csv(io.BytesIO(file_content), dtype=str, keep_default_na=False)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"No se pudo leer el CSV: {exc}") from exc

        df = df[[c for c in df.columns]]  # conserva orden
        df = df.dropna(how="all")
        # Descarta filas totalmente vacías (p. ej. línea final del CSV).
        df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]

        # 1. Crea la encuesta (estado 'procesando').
        enc = (
            self._client.table("encuestas")
            .insert({
                "id_empresa": self._empresa_id,
                "id_usuario": self._usuario_id,
                "nombre": nombre,
                "archivo_origen": archivo_origen,
                "estado": "procesando",
                "total_respuestas": 0,
            })
            .execute()
            .data[0]
        )
        id_encuesta = enc["id_encuesta"]

        procesadas = 0
        errores: list[str] = []

        for pos, (_, row) in enumerate(df.iterrows(), start=1):
            data = {k: (v if str(v).strip() != "" else None) for k, v in row.to_dict().items()}
            try:
                self._ingest_row(id_encuesta, data)
                procesadas += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error en fila %d", pos)
                errores.append(f"Fila {pos}: {exc}")

        # 2. Cierra la encuesta.
        estado = "completado" if not errores else ("completado" if procesadas else "error")
        self._client.table("encuestas").update({
            "estado": estado,
            "total_respuestas": procesadas,
            "filas_procesadas": procesadas,
            "filas_con_error": len(errores),
            "log_procesamiento": {"errores": errores} if errores else None,
        }).eq("id_encuesta", id_encuesta).execute()

        logger.info("Encuesta %s: %d procesadas, %d errores.", id_encuesta, procesadas, len(errores))
        return {
            "id_encuesta": id_encuesta,
            "total": procesadas + len(errores),
            "procesadas": procesadas,
            "errores": len(errores),
            "errores_list": errores,
        }

    def _ingest_row(self, id_encuesta: str, data: dict) -> None:
        """Inserta una respuesta y su detalle/resultados."""
        genero_raw = data.get("Genero")
        if genero_raw in _GENEROS_VALIDOS:
            genero, genero_otro = genero_raw, data.get("Otro - Genero")
        elif genero_raw:
            genero, genero_otro = "Otro", genero_raw
        else:
            genero, genero_otro = None, None

        respuesta = (
            self._client.table("respuestas_encuesta")
            .insert({
                "id_encuesta": id_encuesta,
                "fecha_respuesta": _parse_fecha(data.get("Fecha")),
                "genero": genero,
                "genero_otro": genero_otro,
                "edad_rango": data.get("Edad"),
                "origen_id": _parse_int(data.get("ObjectID")),
                "origen_global_id": data.get("GlobalID"),
                "datos_raw": data,
            })
            .execute()
            .data[0]
        )
        id_respuesta = respuesta["id_respuesta"]

        detalle, resultados = score_row(data, self._preguntas)  # type: ignore[arg-type]

        if detalle:
            self._client.table("detalle_respuestas").insert([
                {
                    "id_respuesta": id_respuesta,
                    "id_pregunta": d.id_pregunta,
                    "valor_likert": d.valor_likert,
                    "valor_texto": d.valor_texto,
                    "es_correcta": d.es_correcta,
                }
                for d in detalle
            ]).execute()

        if resultados:
            self._client.table("resultados_competencia").insert([
                {
                    "id_encuesta": id_encuesta,
                    "id_respuesta": id_respuesta,
                    "id_competencia": r.id_competencia,
                    "score_autoevaluacion": r.score_autoevaluacion,
                    "score_conocimiento": r.score_conocimiento,
                    "nivel": r.nivel,
                }
                for r in resultados
            ]).execute()

    # ------------------------------------------------------------------ #
    # Borrado
    # ------------------------------------------------------------------ #
    def delete_all(self) -> dict:
        """Borra TODAS las encuestas (cascade elimina respuestas/detalle/resultados)."""
        total = self._client.table("encuestas").select("id_encuesta", count="exact").execute().count or 0
        # Filtro siempre verdadero (Supabase exige un filtro para DELETE).
        self._client.table("encuestas").delete().neq(
            "id_encuesta", "00000000-0000-0000-0000-000000000000"
        ).execute()
        logger.info("Encuestas borradas: %d", total)
        return {"encuestas_borradas": total}

    def delete_encuesta(self, id_encuesta: str) -> None:
        """Borra una encuesta concreta (para limpieza de pruebas)."""
        self._client.table("encuestas").delete().eq("id_encuesta", id_encuesta).execute()

    def list_encuestas(self) -> list[dict]:
        """Lista las encuestas cargadas (más recientes primero)."""
        return (
            self._client.table("encuestas")
            .select("id_encuesta,nombre,archivo_origen,estado,total_respuestas,created_at")
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def count_respuestas(self) -> int:
        """Total de respuestas (encuestados) almacenadas."""
        return (
            self._client.table("respuestas_encuesta")
            .select("id_respuesta", count="exact")
            .execute()
            .count
            or 0
        )


def _parse_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_fecha(value: object) -> str | None:
    """Convierte 'M/D/YYYY h:mm:ss AM/PM' a fecha ISO (YYYY-MM-DD)."""
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None
