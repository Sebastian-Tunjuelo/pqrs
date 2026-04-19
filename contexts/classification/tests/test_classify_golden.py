"""20 casos dorados: 10 ofensivos, 5 no entendibles, 5 válidos (LLM mockeado)."""

from __future__ import annotations

import json

import pytest

from classification.application.classify_use_case import ClassifyPqrsUseCase
from shared_kernel.value_objects.enums import EstadoClasificacion


class NoLLM:
    async def chat_json(self, system: str, user: str) -> str:
        raise AssertionError("No debe invocarse Ollama en pre-filtro")


class FixedLLM:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def chat_json(self, system: str, user: str) -> str:
        return json.dumps(self._payload)


@pytest.mark.parametrize(
    "texto",
    [
        "Ciudadano radica PQRS: usted es un estúpido y no entiende el trámite en mi comuna de Medellín.",
        "Reclamo formal: me atendieron como hijueputa y no respetan derechos en la ventanilla.",
        "Queja: ese funcionario es un malparido y no quiere ayudar en el barrio Belén.",
        "Denuncia: si no solucionan esto, te voy a matar y me las van a pagar en la Secretaría.",
        "Mensaje: qué gonorrea de servicio, nadie responde por el hueco en la vía.",
        "Texto inaceptable: negro de mierda me negaron el trámite sin motivo en Laureles.",
        "Amenaza: voy a quemar todo si no arreglan el problema del mercado en Aranjuez.",
        "Insulto: es un sapo y un cerdo, no sirve para nada en la dependencia.",
        "Queja grave: son basura humana y no atienden a la comunidad del corregimiento.",
        "Reproche: es un imbécil inútil y bueno para nada en la línea de atención.",
    ],
)
@pytest.mark.asyncio
async def test_golden_ofensivo_prefiltro(texto: str) -> None:
    uc = ClassifyPqrsUseCase(ollama_client=NoLLM())
    r = await uc.execute(texto)
    assert r.verdict == EstadoClasificacion.RECHAZADA_OFENSIVO
    assert r.source == "prefilter_offensive"


@pytest.mark.parametrize(
    "texto",
    [
        "corto",
        "😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀",
        "1234567890123",
        "aaaaaaaaxyz",
        "abcde",
    ],
)
@pytest.mark.asyncio
async def test_golden_no_entendible_prefiltro(texto: str) -> None:
    uc = ClassifyPqrsUseCase(ollama_client=NoLLM())
    r = await uc.execute(texto)
    assert r.verdict == EstadoClasificacion.RECHAZADA_NO_ENTENDIBLE
    assert r.source == "prefilter_no_entendible"


@pytest.mark.parametrize(
    "texto",
    [
        "Solicitud ciudadana: pido información sobre requisitos para registro de microempresa en Medellín, comuna Laureles.",
        "Queja formal: el semáforo en la calle 30 con carrera 65 lleva semanas fallando y genera riesgo.",
        "Reclamo: la basura no ha sido recogida en mi sector del barrio Robledo durante tres días.",
        "Sugerencia: instalar señalización peatonal adicional cerca al colegio en el Poblado.",
        "Petición: requiero copia del acta administrativa relacionada con mi caso radicado la semana pasada.",
    ],
)
@pytest.mark.asyncio
async def test_golden_aceptada_llm_mock(texto: str) -> None:
    payload = {
        "tipo": "P",
        "es_ofensivo": False,
        "es_entendible": True,
        "confianza": 0.88,
        "razon": "Petición clara y sin lenguaje ofensivo.",
        "palabras_detectadas": ["Medellín"],
    }
    uc = ClassifyPqrsUseCase(ollama_client=FixedLLM(payload))
    r = await uc.execute(texto)
    assert r.verdict == EstadoClasificacion.ACEPTADA
    assert r.source == "llm"
    assert r.tipo is not None
    assert r.tipo.value == "P"
