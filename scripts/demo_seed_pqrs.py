#!/usr/bin/env python3
"""
Inserta PQRS sintéticas para demo (metadata.demo = true, id_externo DEMO-#####).

Las filas aceptadas rotan por las 26 dependencias: cada texto abre de forma distinta
e incluye vocabulario alineado al glosario de ruteo (keywords por secretaría).
Las rechazadas (ilegible u ofensivo) usan muchas variantes distintas de redacción.

Requisitos: Postgres con migración warehouse aplicada y seeds de dim_secretaria
y dim_territorio cargados.

Uso (desde la raíz del repo):
  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable \\
    python scripts/demo_seed_pqrs.py

Opciones:
  --count N   (default 200)
  --purge     Elimina filas demo previas antes de insertar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import unicodedata
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import psycopg

_ROOT = Path(__file__).resolve().parents[1]
_prio = _ROOT / "contexts" / "prioritization"
if str(_prio) not in sys.path:
    sys.path.insert(0, str(_prio))

from prioritization.infrastructure.calendario_colombia import (  # noqa: E402
    fecha_limite_dias_habiles,
)

DEMO_FLAG = {"demo": True}

ACEPTADA = "ACEPTADA"
RECHAZO_O = "RECHAZADA_OFENSIVO"
RECHAZO_NE = "RECHAZADA_NO_ENTENDIBLE"

GESTIONES_ACEPTADAS = ["PENDIENTE", "EN_TRAMITE", "RESPONDIDA", "VENCIDA"]
RIESGOS = ["BAJO", "MEDIO", "ALTO", "CRITICO", None]

# Mismo orden que glosarios/secretarias_routing.yaml (una fila aceptada = un tema rotativo).
ORDEN_SECRETARIAS = [
    "SDE",
    "SED",
    "SSA",
    "SIF",
    "SGC",
    "SMA",
    "SMO",
    "SIS",
    "SMU",
    "SJU",
    "SCU",
    "SGO",
    "SHA",
    "SCO",
    "SID",
    "SGH",
    "SEV",
    "SGE",
    "SNR",
    "STU",
    "DAP",
    "DAGRD",
    "DAS",
    "SAG",
    "SPF",
    "SEJ",
]

def _sin_tildes(s: str) -> str:
    """Minúsculas sin marcas diacríticas (para cruzar palabras clave con texto coloquial)."""
    nf = unicodedata.normalize("NFD", s.casefold())
    return "".join(c for c in nf if unicodedata.category(c) != "Mn")


# Palabras clave por dependencia (alineadas a `glosarios/secretarias_routing.yaml`).
_KEYWORDS_SEC: list[tuple[str, tuple[str, ...]]] = [
    ("SDE", ("empleo", "emprendimiento", "empresa", "negocio", "feria", "mercado", "comercio", "microempresa", "economia", "productividad", "formalizacion")),
    ("SED", ("colegio", "escuela", "estudiante", "profesor", "matricula", "bachillerato", "primaria", "pae", "alimentacion escolar")),
    ("SSA", ("hospital", "eps", "enfermedad", "medico", "vacuna", "dengue", "salud mental", "ambulancia")),
    ("SIF", ("hueco", "anden", "puente", "obra", "pavimento", "malla vial", "infraestructura vial", "cra ")),
    ("SGC", ("predio", "impuesto predial", "licencia", "construccion", "urbanismo", "invasion", "uso de suelo")),
    ("SMA", ("arbol", "tala", "basura", "basurero", "contaminacion", "rio", "quebrada", "fauna", "maleza", "canal", "arroyo")),
    ("SMO", ("semaforo", "trancon", "bus", "metro", "taxi", "comparendo", "infraccion", "parqueo", "trafico", "paradero")),
    ("SIS", ("adulto mayor", "discapacidad", "primera infancia", "habitante de calle", "inclusion")),
    ("SMU", ("violencia", "mujer", "genero", "feminicidio", "acoso", "equidad")),
    ("SJU", ("joven", "adolescente", "parche", "juvenil")),
    ("SCU", ("cultura", "arte", "museo", "biblioteca", "patrimonio", "festival")),
    ("SGO", ("seguridad", "convivencia", "riña", "espacio publico", "vendedor ambulante")),
    ("SHA", ("impuesto", "tributo", "recaudo", "devolucion", "factura", "industria y comercio")),
    ("SCO", ("prensa", "medios", "informacion publica", "transparencia")),
    ("SID", ("tramite en linea", "portal web", "aplicacion", "sistema", "clave ciudadana", "formulario")),
    ("SGH", ("atencion ciudadano", "mas cerca", "punto de atencion", "funcionario", "fila")),
    ("SEV", ("control interno", "auditoria", "corrupcion", "denuncia funcionario", "irregularidad")),
    ("SGE", ("acto administrativo", "resolucion", "decreto", "archivo central")),
    ("SNR", ("paz", "conflicto", "reconciliacion", "victimas", "no violencia")),
    ("STU", ("turista", "hotel", "sitio turistico", "guia turistico")),
    ("DAP", ("pot", "plan ordenamiento", "estratificacion", "uso suelo")),
    ("DAGRD", ("derrumbe", "inundacion", "incendio", "emergencia", "evacuacion", "zona riesgo", "lluvia")),
    ("DAS", ("policia", "delito", "fleteo", "hurto", "microtrafico", "patrullaje")),
    ("SAG", ("campesino", "rural", "cultivo", "corregimiento", "agro", "vereda agricola")),
    ("SPF", ("junta de accion comunal", "presupuesto participativo", "jal", "veeduria")),
    ("SEJ", ("sena", "capacitacion", "certificacion", "oficio", "formacion para el trabajo")),
]


def _inferir_secretaria_desde_texto(texto: str, fallback_i: int) -> str:
    """Simula ruteo IA por coincidencia léxica (PQRS no aceptadas o texto coloquial)."""
    t = _sin_tildes(texto)
    best_cod = "SGH"
    best_score = 0
    for cod, kws in _KEYWORDS_SEC:
        sc = sum(1 for k in kws if _sin_tildes(k) in t)
        if sc > best_score:
            best_score = sc
            best_cod = cod
    if best_score == 0:
        return ORDEN_SECRETARIAS[fallback_i % len(ORDEN_SECRETARIAS)]
    return best_cod


NOMBRES_CIUDADANO = [
    "María Fernanda López",
    "Pedro Andrés Gómez",
    "Lucía Ramírez",
    "Carlos Arturo Mejía",
    "Ana Milena Osorio",
    "Jorge Iván Castaño",
    "Diana Patricia Vélez",
    "Óscar Hernán Duque",
    "Claudia Milena Arango",
    "Santiago Betancur",
    "Valentina Sánchez",
    "Diego León Zapata",
    "Laura Cristina Muñoz",
    "Héctor Fabio Giraldo",
    "Natalia Correa",
    "Andrés Felipe Tobón",
    "Isabel Cristina Ríos",
    "Mauricio Echeverri",
    "Paola Andrea Montoya",
    "Juan David Restrepo",
    "Carolina Londoño",
    "Felipe Henao",
    "Manuela Arias",
    "Sebastián Ocampo",
    "Camila Toro",
    "Roberto Cárdenas",
    "Lina Marcela Franco",
    "Edwin Mauricio Agudelo",
    "Gloria Elena Ruiz",
    "Bernardo Arias",
]


def _hash_contenido(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _slot_aceptada(i: int) -> int:
    """Índice secuencial entre filas aceptadas (i=1,4,7,… → 0,1,2,…)."""
    return (i - 1) // 3


def _codigo_secretaria_demo_aceptada(i: int) -> str:
    return ORDEN_SECRETARIAS[_slot_aceptada(i) % len(ORDEN_SECRETARIAS)]


def _contenido_aceptada(i: int, id_ext: str) -> str:
    """
    Cada PQRS aceptada rota por secretaría; el texto abre distinto e incluye
    vocabulario alineado al glosario de ruteo (keywords temáticas).
    """
    slot = _slot_aceptada(i)
    cod = _codigo_secretaria_demo_aceptada(i)
    rep = slot // len(ORDEN_SECRETARIAS)
    comuna = 10 + (i % 9)
    correg = ["San Cristóbal", "Altavista", "San Antonio de Prado", "Santa Elena", "San Sebastián de Palmitas"][
        slot % 5
    ]
    nom = NOMBRES_CIUDADANO[slot % len(NOMBRES_CIUDADANO)]
    cc = 1_000_000_000 + (slot * 7919 + rep * 503) % 899_999_999
    extra = ["segunda solicitud", "seguimiento a radicado previo", "urgencia vecinal", "acompañamiento comunitario"][
        rep % 4
    ]

    # Frases iniciales distintas por (cod, rep) para que no repitan el mismo arranque.
    def abrir(*frases: str) -> str:
        return frases[rep % len(frases)]

    if cod == "SDE":
        ini = abrir(
            "Me dirijo respetuosamente para solicitar apoyo a mi emprendimiento de comercio local",
            "Requiero orientación sobre ferias de emprendimiento y formalización de empresa",
            "Solicito información sobre microempresa y programas de productividad en la ciudad",
        )
        cuerpo = (
            f"{ini}. Busco acceso a asesoría en economía popular, negocio estable y posibilidades "
            f"de participar en mercados campesinos. Comuna {comuna}. {extra.capitalize()}. "
            f"Solicitante: {nom}, cédula {cc}. Referencia: {id_ext}."
        )
    elif cod == "SED":
        ini = abrir(
            "Como acudiente escribo por la matrícula escolar y el servicio del PAE en el plantel de mi hijo",
            "Preocupa el ambiente en el colegio: estudiantes sin acompañamiento y retrasos en alimentación escolar",
            "Solicito revisión de condiciones de bachillerato y primaria en la institución educativa cercana",
        )
        cuerpo = (
            f"{ini}. Pido información sobre profesores, cronograma de matrícula y mejoras en alimentación escolar. "
            f"Comuna {comuna}. {nom}, CC {cc}. Ref. {id_ext}."
        )
    elif cod == "SSA":
        ini = abrir(
            "Necesito canalizar una consulta sobre vacunación y prevención del dengue en mi barrio",
            "Solicito atención médica coordinada con la EPS por síntomas persistentes y falta de ambulancia",
            "Escribo por salud mental comunitaria y acceso a hospital para valoración especializada",
        )
        cuerpo = (
            f"{ini}. Incluyo datos de enfermedad reportada y pedido de vacuna pendiente. Comuna {comuna}. "
            f"{nom}, identificación {cc}. Radicado {id_ext}."
        )
    elif cod == "SIF":
        ini = abrir(
            "Reporto un hueco profundo en la vía que afecta andenes y pavimento frente a mi vivienda",
            "Solicito inspección de obra pública y malla vial: puente peatonal con daños estructurales visibles",
            "Hay deterioro del pavimento y riesgo en la intersección; requiero cronograma de intervención",
        )
        cuerpo = (
            f"{ini}. Adjunto referencia de ubicación en comuna {comuna}. {nom}, CC {cc}. Documento {id_ext}."
        )
    elif cod == "SGC":
        ini = abrir(
            "Consulto sobre licencia de construcción y trámite de predio en zona de expansión urbana",
            "Solicito orientación de urbanismo y uso de suelo relacionado con impuesto predial",
            "Denuncio posible invasión de predio público y requiero actuación de control territorial",
        )
        cuerpo = (
            f"{ini}. Dirección en comuna {comuna}. {nom}, cédula {cc}. Referencia ciudadana {id_ext}."
        )
    elif cod == "SMA":
        ini = abrir(
            "Solicito poda y revisión de tala no autorizada de árboles en el parque del sector",
            "Hay acumulación de basura junto a la quebrada y olores; pido intervención por contaminación",
            "Preocupa fauna silvestre y vertimiento al río; requiero visita técnica del medio ambiente",
        )
        cuerpo = (
            f"{ini}. Ubicación comuna {comuna}, corregimiento {correg}. {nom}, CC {cc}. Caso {id_ext}."
        )
    elif cod == "SMO":
        ini = abrir(
            "El semáforo permanece en falla y genera trancón; solicito comparendo preventivo y revisión de tráfico",
            "Pido regulación de parqueo informal y orden del transporte público en parada de buses",
            "Hay infracción recurrente de taxis en zona escolar; requiero presencia de movilidad",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, identificación {cc}. Radicación {id_ext}."
        )
    elif cod == "SIS":
        ini = abrir(
            "Solicito apoyo para adulto mayor en situación de habitante de calle cerca de mi casa",
            "Requiero programa de primera infancia y acompañamiento familiar para caso de discapacidad",
            "Pido ruta de inclusión social para víctimas y hogar comunitario en el territorio",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, CC {cc}. Seguimiento {id_ext}."
        )
    elif cod == "SMU":
        ini = abrir(
            "Denuncio acoso callejero recurrente y pido rutas de equidad de género en el sector",
            "Solicito acompañamiento por violencia de género y orientación sobre feminicidio cero",
            "Requiero talleres de prevención de violencia contra las mujeres en la comuna",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, cédula {cc}. Caso {id_ext}."
        )
    elif cod == "SJU":
        ini = abrir(
            "Solicito espacios para adolescentes y parche juvenil con liderazgo juvenil en la biblioteca barrial",
            "Pido mentorías para jóvenes en riesgo y actividades deportivas nocturnas supervisadas",
            "Requiero información sobre convocatorias culturales para jóvenes creadores",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, CC {cc}. Ref. {id_ext}."
        )
    elif cod == "SCU":
        ini = abrir(
            "Solicito apoyo para festival comunitario y exhibición de arte local en museo itinerante",
            "Pido ampliación de horarios de biblioteca y resguardo de patrimonio audiovisual del barrio",
            "Requiero asesoría en cultura ciudadana y participación en agenda cultural municipal",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, identificación {cc}. Evento asociado a {id_ext}."
        )
    elif cod == "SGO":
        ini = abrir(
            "Reporto riña frecuente en espacio público y venta informal que afecta convivencia",
            "Solicito mediación por seguridad en parque y presencia de vendedor ambulante no regulado",
            "Pido plan de convivencia y coordinación con policía para puntos calientes del sector",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, CC {cc}. Radicado {id_ext}."
        )
    elif cod == "SHA":
        ini = abrir(
            "Solicito aclaración de factura de impuesto y trámite de devolución de tributo municipal",
            "Consulto recaudo de industria y comercio y plazos para pago sin sanción",
            "Requiero certificación de paz y salvo y orientación sobre beneficios tributarios",
        )
        cuerpo = (
            f"{ini}. {nom}, cédula {cc}, comuna {comuna}. Referencia {id_ext}."
        )
    elif cod == "SCO":
        ini = abrir(
            "Solicito información pública sobre actas de comité y publicación en medios oficiales",
            "Pido acceso a datos de transparencia y lineamientos de prensa institucional",
            "Requiero respuesta sobre comunicaciones ciudadanas enviadas al canal web",
        )
        cuerpo = (
            f"{ini}. {nom}, identificación {cc}. Solicitud {id_ext}, comuna {comuna}."
        )
    elif cod == "SID":
        ini = abrir(
            "No puedo ingresar al trámite en línea del portal web: solicito restablecimiento de clave ciudadana",
            "La aplicación móvil falla al cargar formularios; pido soporte del sistema de innovación digital",
            "Requiero capacitación para uso del sistema de firma electrónica en trámites digitales",
        )
        cuerpo = (
            f"{ini}. {nom}, CC {cc}. Caso técnico {id_ext}, territorio comuna {comuna}."
        )
    elif cod == "SGH":
        ini = abrir(
            "Fui atendido en MásCerca y la fila fue muy larga; solicito mejor servicio al ciudadano",
            "Pido información sobre horarios de punto de atención y trámite de funcionario de turno",
            "Requiero queja formal por demora en atención ciudadana telefónica",
        )
        cuerpo = (
            f"{ini}. {nom}, cédula {cc}. Comuna {comuna}. Radicación {id_ext}."
        )
    elif cod == "SEV":
        ini = abrir(
            "Solicito investigación de control interno por posible irregularidad en contratación menor",
            "Denuncio a funcionario por trato discriminatorio; pido auditoría y seguimiento",
            "Requiero canal ético para reporte de corrupción con reserva",
        )
        cuerpo = (
            f"{ini}. {nom}, identificación {cc}. Expediente ciudadano {id_ext}."
        )
    elif cod == "SGE":
        ini = abrir(
            "Solicito copia de acto administrativo y resolución archivada en archivo central",
            "Pido notificación de decreto aplicable a mi predio y términos para recurso",
            "Requiero certificación de expediente y estado de decreto municipal",
        )
        cuerpo = (
            f"{ini}. {nom}, CC {cc}. Comuna {comuna}. Ref. {id_ext}."
        )
    elif cod == "SNR":
        ini = abrir(
            "Solicito acompañamiento en proceso de paz escolar y reconciliación entre grupos del aula",
            "Pido ruta psicosocial para víctimas del conflicto en el territorio comunitario",
            "Requiero mediación para conflicto vecinal con enfoque de no violencia",
        )
        cuerpo = (
            f"{ini}. {nom}, cédula {cc}. Comuna {comuna}. Caso {id_ext}."
        )
    elif cod == "STU":
        ini = abrir(
            "Solicito información para hotel boutique y registro de guía turístico en la ciudad",
            "Pido señalización y orden en sitio turístico concurridos por visitantes",
            "Requiero apoyo para ruta turística segura en corregimiento con afluencia de turistas",
        )
        cuerpo = (
            f"{ini}. Corregimiento {correg}, comuna {comuna}. {nom}, CC {cc}. Ref. {id_ext}."
        )
    elif cod == "DAP":
        ini = abrir(
            "Consulto estratificación del predio y su reflejo en plan de ordenamiento territorial",
            "Solicito interpretación de uso de suelo según plan de ordenamiento vigente",
            "Pido certificado de compatibilidad de uso respecto del plan de ordenamiento",
        )
        cuerpo = (
            f"{ini}. Dirección en comuna {comuna}. {nom}, identificación {cc}. Radicado {id_ext}."
        )
    elif cod == "DAGRD":
        ini = abrir(
            "Tras lluvias hubo inundación en mi calle; solicito evaluación de zona de riesgo y evacuación",
            "Reporto derrumbe en ladera y temor de incendio en vegetación seca; pido emergencia",
            "Requiero simulacro y kit informativo para emergencia en el barrio",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}, sector {correg}. {nom}, CC {cc}. Urgencia {id_ext}."
        )
    elif cod == "DAS":
        ini = abrir(
            "Solicito presencia de policía por hurto recurrente y microtráfico en esquina conocida",
            "Denuncio delito de fleteo en paradero; pido patrullaje del departamento de seguridad",
            "Requiero acompañamiento por caso de hurto con violencia en vía pública",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, cédula {cc}. Denuncia {id_ext}."
        )
    elif cod == "SAG":
        ini = abrir(
            "Solicito asistencia técnica en cultivo para productores del corregimiento rural",
            "Pido mejoramiento de vereda agrícola y apoyo a economía campesina",
            "Requiero insumos para proyecto agropecuario familiar en zona rural",
        )
        cuerpo = (
            f"{ini}. Corregimiento {correg}. {nom}, identificación {cc}. Caso {id_ext}."
        )
    elif cod == "SPF":
        ini = abrir(
            "Solicito orientación sobre junta de acción comunal y veeduría ciudadana en obra menor",
            "Pido información sobre presupuesto participativo y convocatoria de JAL",
            "Requiero acompañamiento para veeduría en contratación de servicios en la comuna",
        )
        cuerpo = (
            f"{ini}. Comuna {comuna}. {nom}, CC {cc}. Participación {id_ext}."
        )
    elif cod == "SEJ":
        ini = abrir(
            "Solicito cupo en curso del SENA y certificación de oficio para mejorar empleabilidad",
            "Pido información sobre capacitación laboral y rutas de certificación técnica",
            "Requiero vínculo con formación para el trabajo y prácticas en empresa",
        )
        cuerpo = (
            f"{ini}. {nom}, cédula {cc}, comuna {comuna}. Radicado {id_ext}."
        )
    else:
        cuerpo = (
            f"Solicitud general de servicio municipal. Comuna {comuna}. {nom}, CC {cc}. Ref. {id_ext}."
        )

    return cuerpo


def _contenido_ilegible(i: int, id_ext: str) -> str:
    variantes = [
        (
            "xola k tal esto es sobre eso dk la vía xq ayer pasé y noooo m enendí "
            "y entonces q paso q el señor ese dijo k pa q mañana o pasado xa cuando "
            "vuelva a pasar x hay pero eso no es claro sabe parece k ay un hoyo "
            "o algo x la cra 30 y ndie ha hecho nada desde el año pasado q dije "
            "algo ahora q vuelvo a decir q hagan algo porfa muchas gracias"
        ),
        (
            "buenas tardes es q necesito q me ayuden con eso del parque xq va mal "
            "y no se sabe ni cuando ni pa cuando y yo ya pregunté y nada q me dicen "
            "claro entonces q hago yo si ndie responde y eso lleva meses ya gracias"
        ),
        (
            "hola miren es q hay un problema con el arbol q cayó y eso y entonces "
            "yo llamé y me dijeron k ya pero no vino nadie y sigue igual entonces "
            "xq no hacen nada si eso es peligroso pa los niños del barrio gracias"
        ),
        (
            "eyyy bueno lo q pasa es q eso del trámite no sirve xq puse la cédula "
            "y sale error y yo no se si es la app o q y ya llevamos así toda la semana"
        ),
        (
            "mire yo no soy maluca pero es q nadie explica na del caserío y el arroyo "
            "se tapó y dicen q mañana y mañana nunca y eso huele feísimo ya hagan algo"
        ),
        (
            "buenas noches es q mi vecina dijo k ustedes arreglan eso del poste "
            "y el cable suelto pero es q no vinieron y yo tengo miedo q se caiga encima"
        ),
        (
            "hola hola es q necesito plata pa arreglar la cosa del techo del salón "
            "comunal y no se a quién escribir entonces escribo aquí aver si me dicen"
        ),
        (
            "k tal mira es q el perro de al lado ladra todo el día y eso no deja dormir "
            "y la policía no hace na y ustedes tampoco y ya no se a quien más contarle"
        ),
        (
            "bueno es q yo mandé un papel y no me llegó respuesta y volví a mandar otro "
            "y tampoco y entonces no se si llegó o no llegó o si lo perdieron gracias"
        ),
        (
            "oye es q en el puesto de fruta pusieron un toldo gigante y tapa el sol "
            "a mi ventana y eso no es justo y nadie me avisó y quiero q lo quiten"
        ),
        (
            "hola es q mi papá dijo k ustedes dan carnet pa la discapacidad pero es q "
            "no entiendo el formulario y sale muy difícil y no tengo quien me ayude"
        ),
        (
            "mira es q hay un carro abandonado hace meses y ya tiene maleza y bichos "
            "y los niños juegan ahí y eso es peligroso y nadie lo remolca todavía"
        ),
        (
            "buenas es q el bus pasa llenísimo y no paran y yo voy con mi abuelita "
            "y eso no se puede y necesito q pongan más buses o algo no se"
        ),
        (
            "hola k tal es q el parqueadero del centro cobra lo q quiere y no dan "
            "factura y eso no me parece y quiero saber si eso es legal o no gracias"
        ),
        (
            "es q yo no se escribir bien pero el caso es q el hueco de la esquina "
            "se hizo más grande con la lluvia y ya casi se cae el carro adentro"
        ),
        (
            "mire yo llamé al número y me pasaron pa otro y pa otro y al final cortaron "
            "y no resolví nada y eso es cansón y necesito hablar con alguien de verdad"
        ),
        (
            "bueno es q la cancha está llena de vidrios y los pelados no pueden jugar "
            "y eso lleva así desde el torneo pasado y nadie barrió todavía"
        ),
        (
            "hola es q necesito q me manden el número del señor del arreglo del agua "
            "porque en la cuadra dicen q ustedes saben pero nadie me lo quiere dar"
        ),
        (
            "oye es q el semáforo de acá parpadea raro y los carros se atraviesan "
            "y casi chocan y eso da miedo en las mañanas cuando hay colegio"
        ),
        (
            "k tal es q yo puse la queja por internet y me salió un código raro "
            "y no se si sirvió o no porque no me llegó correo ni nada gracias"
        ),
    ]
    cuerpo = variantes[i % len(variantes)]
    return f"{cuerpo}\n\nRadicado interno: {id_ext}."


def _contenido_ofensivo(i: int, id_ext: str) -> str:
    """Texto de reclamo con lenguaje irrespetuoso (solo entorno demo / clasificador)."""
    variantes = [
        (
            "¡¿QUÉ VAINA ES ESTA?! Ustedes son unos inútiles de mierda, hace tres meses "
            "reporté un problema de agua en la vereda y no han hecho un carajo. "
            "Mientras tanto, el alcalde se lleva la plata robada como siempre y los "
            "trabajadores son unos maricones que no hacen nada. Dejen de ser tan jodidos "
            "y arreglen esto de una vez o voy a hacer un escándalo en redes. "
            "Esto es una porquería de administración, ¡qué patanes son todos!"
        ),
        (
            "Esto es un desastre y ustedes son unos imbéciles que no sirven para nada. "
            "Llevo semanas esperando respuesta y solo dan excusas de mierda. "
            "Si no arreglan el tema del basurero voy a denunciar a todos estos ladrones. "
            "¡Qué jodida es esta vaina!"
        ),
        (
            "No aguanto más esta porquería de servicio. Son unos inútiles, unos patanes, "
            "y el que atendió fue un idiota. Hagan algo de una vez o la vaina se les va "
            "a ir de las manos, carajo."
        ),
        (
            "Asco de alcaldía, puros incompetentes; llevo meses con el mismo reclamo "
            "y solo se hacen los locos. Si no arreglan la vía me van a ver en las noticias "
            "porque ya estoy harto de esta basura."
        ),
        (
            "Son unos corruptos de mierda y el barrio lo sabe; el dinero se lo roban "
            "y a nosotros nos dejan en el lodo. Hagan la obra de una vez o les va a caer "
            "el pueblo encima, carajo."
        ),
        (
            "Qué asco de trato, me atendieron como basura y encima no solucionan nada. "
            "Esto parece una burla y ustedes son unos inútiles que solo saben cobrar impuestos."
        ),
        (
            "Ya estoy podrido de esta administración de mierda; todo sale mal y nadie "
            "asume. Si no mandan a arreglar el parque voy a prender el escándalo en redes."
        ),
        (
            "Esto es una tomada de pelo, unos ladrones y unos ineptos; mi familia está "
            "harto y no vamos a quedarnos callados con tanta vaina mal hecha."
        ),
        (
            "Me tienen jarto con excusas baratas; son unos irresponsables y el que manda "
            "es un payaso. Arreglen el tema del agua o la vaina se les va a devolver peor."
        ),
        (
            "Qué desastre de ciudad con estos funcionarios inútiles; nadie sirve para nada "
            "y el que contesta el teléfono es un grosero de mierda. Quiero solución ya."
        ),
        (
            "Son unos sinvergüenzas, puro show y cero resultados; así cualquiera gobierna. "
            "Si no limpian el canal voy a denunciar públicamente a todos estos corruptos."
        ),
        (
            "Asco total, me niego a seguir aguantando esta porquería; ustedes no tienen "
            "madre ni respeto por la gente trabajadora del barrio."
        ),
        (
            "Esto huele a robo por todos lados; inútiles, ineptos y encima groseros. "
            "Voy a hacer viral esta vaina porque ya no aguanto más."
        ),
        (
            "Qué vergüenza de servicio, puros patanes y nadie asume; mi calle está "
            "destrozada y ustedes ni aparecen, manga de vagos."
        ),
        (
            "Ya basta de tanta mierda, son unos irresponsables y el que diseñó este sistema "
            "es un idiota; no sirve para nada y solo hacen perder el tiempo."
        ),
    ]
    cuerpo = variantes[i % len(variantes)]
    return f"{cuerpo}\n\nIdentificador demo: {id_ext}."


def _validation_status_demo(i: int, estado_clf: str) -> str:
    """Reparto pedido en P8 sobre filas aceptadas; el resto queda pendiente de validación."""
    if estado_clf != ACEPTADA:
        return "PENDING_VALIDATION"
    r = (i - 1) % 200
    if r < 50:
        return "PENDING_VALIDATION"
    if r < 150:
        return "VALIDATED"
    if r < 180:
        return "REJECTED_BY_OFFICER"
    return "CORRECTION_REQUESTED"


def _clasificacion_por_indice(i: int) -> str:
    """Reparto cíclico: aceptada / ilegible / ofensivo (~un tercio cada una)."""
    r = (i - 1) % 3
    if r == 0:
        return ACEPTADA
    if r == 1:
        return RECHAZO_NE
    return RECHAZO_O


def main() -> int:
    p = argparse.ArgumentParser(description="Demo: insertar PQRS sintéticas (arquetipos Medellín).")
    p.add_argument("--count", type=int, default=200, help="Número de filas (default 200).")
    p.add_argument(
        "--purge",
        action="store_true",
        help="Borra pqrs con metadata.demo=true antes de insertar.",
    )
    args = p.parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: defina DATABASE_URL", flush=True)
        return 1
    if args.count < 1 or args.count > 5000:
        print("ERROR: --count debe estar entre 1 y 5000", flush=True)
        return 1

    rng = random.Random(42)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dim_secretaria")
            if cur.fetchone()[0] == 0:
                print("ERROR: dim_secretaria vacía. Cargue data/seed/seed_dim_secretaria.sql", flush=True)
                return 1
            cur.execute("SELECT id FROM dim_territorio ORDER BY id")
            territorios = [r[0] for r in cur.fetchall()]
            if not territorios:
                print("ERROR: dim_territorio vacía. Cargue seed de territorio.", flush=True)
                return 1

        inserted = 0
        with conn.transaction():
            with conn.cursor() as cur:
                if args.purge:
                    cur.execute(
                        """
                        DELETE FROM pqrs_secretaria WHERE pqrs_id IN (
                          SELECT id FROM pqrs WHERE metadata @> %s::jsonb
                        )
                        """,
                        (json.dumps(DEMO_FLAG),),
                    )
                    cur.execute(
                        "DELETE FROM pqrs_historial WHERE pqrs_id IN (SELECT id FROM pqrs WHERE metadata @> %s::jsonb)",
                        (json.dumps(DEMO_FLAG),),
                    )
                    cur.execute(
                        "DELETE FROM pqrs WHERE metadata @> %s::jsonb",
                        (json.dumps(DEMO_FLAG),),
                    )
                    print("Purge: filas demo eliminadas.", flush=True)

                for i in range(1, args.count + 1):
                    pid = uuid.uuid4()
                    id_ext = f"DEMO-{i:05d}"
                    estado_clf = _clasificacion_por_indice(i)

                    if estado_clf == ACEPTADA:
                        tipo = "P"
                        contenido = _contenido_aceptada(i, id_ext)
                        estado_ges = rng.choice(GESTIONES_ACEPTADAS)
                        riesgo = rng.choice(RIESGOS)
                        razon = None
                        conf = round(rng.uniform(0.86, 0.99), 2)
                        sec_demo = _codigo_secretaria_demo_aceptada(i)
                    elif estado_clf == RECHAZO_NE:
                        tipo = rng.choice(["Q", "R"])
                        contenido = _contenido_ilegible(i, id_ext)
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = (
                            "Falta de claridad redaccional, sin estructura, sin datos de "
                            "identificación claros. Texto tipo mensajería difícil de entender (demo)."
                        )
                        conf = round(rng.uniform(0.88, 0.95), 2)
                    else:
                        tipo = "R"
                        contenido = _contenido_ofensivo(i, id_ext)
                        estado_ges = "PENDIENTE"
                        riesgo = None
                        razon = (
                            "Lenguaje vulgar, ofensivo e irrespetuoso. Incumplimiento de normas de "
                            "cortesía en peticiones oficiales (demo)."
                        )
                        conf = round(rng.uniform(0.96, 1.0), 2)

                    if estado_clf == ACEPTADA:
                        sec_asignada = sec_demo
                        motivo_sec = "Demo: texto alineado al tema de la dependencia."
                        score_sec = round(0.82 + (i % 17) * 0.01, 2)
                    else:
                        sec_asignada = _inferir_secretaria_desde_texto(contenido, i)
                        motivo_sec = "Demo: inferencia por palabras clave del texto (simulación de ruteo IA)."
                        score_sec = round(0.72 + (i % 19) * 0.01, 2)

                    h = _hash_contenido(contenido + str(pid))
                    terr_id = rng.choice(territorios)
                    lon = -75.58 + rng.random() * 0.06
                    lat = 6.22 + rng.random() * 0.08
                    rad = datetime.now(UTC) - timedelta(days=rng.randint(0, 120))
                    if estado_clf == ACEPTADA:
                        hoy = date.today()
                        if i <= 12 and _validation_status_demo(i, estado_clf) == "PENDING_VALIDATION":
                            lim = fecha_limite_dias_habiles(hoy, 3)
                        else:
                            lim = hoy + timedelta(days=rng.randint(5, 60))
                    else:
                        lim = None

                    meta = {
                        **DEMO_FLAG,
                        "synthetic_index": i,
                        "arquetipo_demo": (
                            f"aceptada_tema_{sec_demo.lower()}"
                            if estado_clf == ACEPTADA
                            else ("ilegible_chat" if estado_clf == RECHAZO_NE else "ofensivo_reclamo")
                        ),
                    }

                    vstat = _validation_status_demo(i, estado_clf)

                    cur.execute(
                        """
                        INSERT INTO pqrs (
                          id, id_externo, tipo, contenido, contenido_hash,
                          fecha_radicado, fecha_limite, estado_clasificacion,
                          estado_gestion, nivel_riesgo, territorio_id, punto_geo,
                          confianza_clasificacion, razon_rechazo, metadata,
                          validation_status
                        ) VALUES (
                          %(id)s, %(ext)s, %(tipo)s, %(cont)s, %(hash)s,
                          %(rad)s, %(lim)s, %(eclf)s,
                          %(eges)s, %(riesgo)s, %(tid)s,
                          ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                          %(conf)s, %(razon)s, %(meta)s::jsonb,
                          %(vstat)s::validation_status
                        )
                        """,
                        {
                            "id": pid,
                            "ext": id_ext,
                            "tipo": tipo,
                            "cont": contenido,
                            "hash": h,
                            "rad": rad,
                            "lim": lim,
                            "eclf": estado_clf,
                            "eges": estado_ges,
                            "riesgo": riesgo,
                            "tid": terr_id,
                            "lon": lon,
                            "lat": lat,
                            "conf": conf,
                            "razon": razon,
                            "meta": json.dumps(meta),
                            "vstat": vstat,
                        },
                    )
                    cur.execute(
                        """
                        INSERT INTO pqrs_secretaria (pqrs_id, secretaria_codigo, es_lider, score, motivo)
                        VALUES (%s, %s, true, %s, %s)
                        """,
                        (pid, sec_asignada, score_sec, motivo_sec),
                    )
                    inserted += 1

    print(
        f"OK: insertadas {inserted} PQRS demo (secretaría en todas las filas: aceptadas por tema, "
        f"rechazadas por inferencia léxica; id_externo DEMO-#####).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
