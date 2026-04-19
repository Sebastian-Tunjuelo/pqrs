from __future__ import annotations
from datetime import date
from telegram_bot.domain.models import PqrsSnapshot, AlertaMessage

TIPO_LABELS = {"P": "Petición", "Q": "Queja", "R": "Reclamo", "S": "Sugerencia", "D": "Denuncia"}


def _tipo(t: str | None) -> str:
    return TIPO_LABELS.get(t or "", t or "—")


def _dias_restantes(fecha_limite: date | None) -> str:
    if not fecha_limite:
        return "—"
    delta = (fecha_limite - date.today()).days
    if delta < 0:
        return f"⚠️ Vencida hace {abs(delta)} día(s)"
    if delta == 0:
        return "⚠️ Vence hoy"
    return f"{delta} día(s)"


def format_pqrs_detail(snap: PqrsSnapshot) -> str:
    lines = [
        f"📋 PQRS {snap.id[:8]}...",
        f"Tipo: {_tipo(snap.tipo)}",
        f"Clasificación: {snap.estado_clasificacion or '—'}",
        f"Gestión: {snap.estado_gestion or '—'}",
        f"Riesgo: {snap.nivel_riesgo or '—'}",
        f"Secretaría: {snap.secretaria_nombre or '—'}",
        f"Fecha límite SLA: {snap.fecha_limite.isoformat() if snap.fecha_limite else '—'}",
        f"Días restantes: {_dias_restantes(snap.fecha_limite)}",
    ]
    if snap.summary_executive:
        lines.append(f"\n📝 Resumen IA:\n{snap.summary_executive[:500]}")
    return "\n".join(lines)


def format_pqrs_list_item(snap: PqrsSnapshot, idx: int) -> str:
    return (
        f"{idx}\\. `{snap.id[:8]}` — {_tipo(snap.tipo)} "
        f"\\| {snap.nivel_riesgo or '—'} "
        f"\\| {snap.secretaria_nombre or '—'} "
        f"\\| {_dias_restantes(snap.fecha_limite)}"
    )


def format_metricas(data: dict) -> str:
    lines = [
        "📊 *Métricas del sistema PQRS*",
        f"*Total PQRS:* {data.get('total_pqrs', '—')}",
        f"*Pendientes:* {data.get('pendientes', '—')}",
        f"*En trámite:* {data.get('en_tramite', '—')}",
        f"*Respondidas:* {data.get('respondidas', '—')}",
        f"*Vencidas:* {data.get('vencidas', '—')}",
    ]
    por_riesgo = data.get("por_riesgo") or data.get("por_nivel_riesgo")
    if por_riesgo and isinstance(por_riesgo, dict):
        lines.append("*Por riesgo:*")
        for k, v in por_riesgo.items():
            lines.append(f"  • {k}: {v}")
    return "\n".join(lines)


def format_alerta(alerta: AlertaMessage) -> str:
    prefix = "🚨 *URGENTE:* " if alerta.es_urgente else "⏰ *Alerta SLA:* "
    lines = [
        f"{prefix}PQRS próxima a vencer",
        f"*ID:* `{alerta.pqrs_id[:8]}...`",
        f"*Tipo:* {_tipo(alerta.tipo)}",
        f"*Riesgo:* {alerta.nivel_riesgo or '—'}",
        f"*Secretaría:* {alerta.secretaria_nombre or '—'}",
        f"*Fecha límite:* {alerta.fecha_limite.isoformat() if alerta.fecha_limite else '—'}",
        f"*Horas restantes:* {alerta.horas_restantes:.1f}h",
    ]
    return "\n".join(lines)


def format_secretaria_list(secretarias: list[dict]) -> str:
    if not secretarias:
        return "No hay secretarías disponibles."
    lines = ["🏛️ *Secretarías disponibles:*"]
    for s in secretarias:
        codigo = s.get("codigo", "")
        nombre = s.get("nombre", "")
        lines.append(f"• `{codigo}` — {nombre}")
    return "\n".join(lines)
