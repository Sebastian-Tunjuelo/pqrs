"""30 PQRS sintéticas (noticias/temas Medellín) — una por cada secretaría + multidependencia."""

from __future__ import annotations

import pytest

from routing.application.recommend_secretaria_use_case import RecommendSecretariaUseCase


class NoLLM:
    async def chat_json(self, system: str, user: str) -> str:
        raise AssertionError("No se esperaba tie-break LLM en estos casos")


CASOS: list[tuple[str, str]] = [
    (
        "Radico PQRS sobre empleo feria de servicios microempresa y economía productiva en Medellín.",
        "SDE",
    ),
    (
        "Solicitud sobre matrícula escolar PAE alimentación escolar y profesor en colegio de la ciudad.",
        "SED",
    ),
    (
        "Queja por demora en EPS hospital vacuna dengue y salud mental en urgencias de Medellín.",
        "SSA",
    ),
    (
        "Reporte de hueco profundo en la vía pavimento andén y malla vial en mi cuadra del barrio.",
        "SIF",
    ),
    (
        "Consulta sobre predio impuesto predial licencia construcción y urbanismo en un lote de la comuna.",
        "SGC",
    ),
    (
        "Denuncia por tala de árbol basura en quebrada y contaminación del río en zona verde de Medellín.",
        "SMA",
    ),
    (
        "Reclamo por tráfico semáforo trancón bus metro taxi comparendo y parqueo indebido en la vía.",
        "SMO",
    ),
    (
        "Petición de apoyo a habitante calle adulto mayor discapacidad y primera infancia en el territorio.",
        "SIS",
    ),
    (
        "Solicitud de orientación por violencia mujer feminicidio tentativa y acoso en contexto de equidad.",
        "SMU",
    ),
    (
        "PQRS juvenil sobre parche adolescente joven y liderazgo juvenil en comuna popular de Medellín.",
        "SJU",
    ),
    (
        "Invitación a fortalecer cultura ciudadana museo biblioteca patrimonio y festival en el distrito.",
        "SCU",
    ),
    (
        "Reporte de riña en espacio público convivencia seguridad y vendedor ambulante en el parque.",
        "SGO",
    ),
    (
        "Solicitud de devolución tributo recaudo impuesto factura y trámite de hacienda en línea.",
        "SHA",
    ),
    (
        "Petición de información pública transparencia prensa y medios sobre actos administrativos recientes.",
        "SCO",
    ),
    (
        "Reclamo por fallas del portal web trámite en línea app sistema y clave ciudadana en el portal.",
        "SID",
    ),
    (
        "Queja por atención ciudadano funcionario y punto de atención MásCerca sin resolver mi caso.",
        "SGH",
    ),
    (
        "Denuncia por posible corrupción control interno auditoría y denuncia funcionario en dependencia.",
        "SEV",
    ),
    (
        "Solicitud de copia de resolución decreto acto administrativo y archivo central de la entidad.",
        "SGE",
    ),
    (
        "PQRS sobre paz reconciliación conflicto y víctimas en programa de no violencia en la ciudad.",
        "SNR",
    ),
    (
        "Consulta turística sobre hotel guía turístico y sitio turístico para visitantes en Medellín.",
        "STU",
    ),
    (
        "Observación sobre POT plan ordenamiento estratificación y uso suelo en revisión del instrumento.",
        "DAP",
    ),
    (
        "Emergencia por inundación derrumbe evacuación zona riesgo e incendio en ladera del cerro.",
        "DAGRD",
    ),
    (
        "Denuncia penal por hurto fleteo microtráfico delito y presencia policial en el sector urbano.",
        "DAS",
    ),
    (
        "Solicitud rural sobre campesino cultivo corregimiento y apoyo agro en vereda de Medellín.",
        "SAG",
    ),
    (
        "Participación ciudadana JAL junta acción comunal veeduría y presupuesto participativo barrial.",
        "SPF",
    ),
    (
        "PQRS de formación SENA curso capacitación certificación y oficio para empleabilidad en la ciudad.",
        "SEJ",
    ),
    (
        "Caso complejo: colegio cerca de casa y violencia recurrente en entorno escolar del barrio Laureles.",
        "SED",
    ),
    (
        "Reporte: hueco en la vía y niño lesionado al caer en andén sin señalización en la comuna.",
        "SIF",
    ),
    (
        "Emergencia: inundación en barrio bajo creciente de quebrada y riesgo para viviendas aledañas.",
        "DAGRD",
    ),
    (
        "Solo texto genérico sin palabras clave de secretarías ni contexto temático claro en Medellín ciudad.",
        "SGH",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("texto,esperado_lider", CASOS)
async def test_routing_top1_por_caso(texto: str, esperado_lider: str) -> None:
    uc = RecommendSecretariaUseCase(ollama_client=NoLLM())
    r = await uc.execute(texto)
    assert r.secretaria_lider == esperado_lider
    assert r.secretarias_recomendadas[0].codigo == esperado_lider


@pytest.mark.asyncio
async def test_multidependencia_tres_secretarias() -> None:
    texto = (
        "Denuncia por violencia cerca del colegio y peleas recurrentes en el entorno escolar "
        "del barrio en Medellín."
    )
    uc = RecommendSecretariaUseCase(ollama_client=NoLLM())
    r = await uc.execute(texto)
    codigos = {m.codigo for m in r.secretarias_recomendadas}
    assert r.es_multidependencia is True
    assert "SED" in codigos
    assert "SGO" in codigos
    assert "SMU" in codigos
