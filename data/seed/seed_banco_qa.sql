-- Catálogo semilla banco_qa (alineado con glosarios/banco_qa.yaml).
-- Requisito: dim_secretaria con SGH, SDE, SSA (seed_dim_secretaria.sql).
TRUNCATE banco_qa RESTART IDENTITY;

INSERT INTO banco_qa (pregunta, respuesta, secretaria_codigo, tags) VALUES
(
  '¿Qué es una PQRS?',
  'PQRS son Peticiones, Quejas, Reclamos y Sugerencias. Es el canal oficial para que la ciudadanía se comunique con la administración municipal sobre trámites, servicios y participación.',
  NULL,
  ARRAY['conceptos', 'ciudadanía']::text[]
),
(
  '¿Cuántos días hábiles tengo para una petición de información?',
  'Según la Ley 1755 de 2015, las peticiones de documentos e información suelen atenderse en plazos de 10 días hábiles; otras peticiones pueden tener 15 días hábiles. Los plazos exactos dependen del tipo de solicitud y del riesgo asociado.',
  'SGH',
  ARRAY['ley 1755', 'plazos', 'información']::text[]
),
(
  '¿Dónde radico una PQRS en Medellín?',
  'Puede hacerlo por canales digitales oficiales de la Alcaldía de Medellín o presencialmente en puntos de atención habilitados. Verifique siempre el sitio web institucional para enlaces vigentes y requisitos.',
  'SGH',
  ARRAY['radicación', 'canales']::text[]
),
(
  '¿Qué secretaría atiende temas de emprendimiento y negocios?',
  'La Secretaría de Desarrollo Económico (SDE) orienta políticas de desarrollo económico, emprendimiento y competitividad en el municipio.',
  'SDE',
  ARRAY['secretarías', 'economía']::text[]
),
(
  '¿Quién responde por salud pública municipal?',
  'La Secretaría de Salud (SSA) es la dependencia competente en políticas de salud pública y prestación de servicios de salud a nivel municipal, según su mandato.',
  'SSA',
  ARRAY['salud', 'secretarías']::text[]
),
(
  '¿Qué hago si mi PQRS fue clasificada como no entendible?',
  'Redacte el texto con datos concretos (qué pasó, cuándo, dónde, qué solicita). Evite mensajes demasiado cortos o sin contexto. Si necesita orientación, acérquese a atención ciudadana (SGH) para ayuda en el formulario.',
  'SGH',
  ARRAY['clasificación', 'rechazo']::text[]
),
(
  '¿Qué es una multidependencia en el ruteo de PQRS?',
  'Cuando varias secretarías tienen competencias relacionadas con el mismo caso, el sistema puede marcar multidependencia y proponer una secretaría líder con coordinación entre dependencias.',
  NULL,
  ARRAY['ruteo', 'secretarías']::text[]
),
(
  '¿Cómo se prioriza una PQRS con riesgo alto?',
  'Se combinan factores de riesgo poblacional y personal definidos en glosarios oficiales, reglas de la Ley 1755 y evaluación asistida; las PQRS de mayor riesgo reciben plazos más exigentes y seguimiento prioritario.',
  NULL,
  ARRAY['riesgo', 'priorización', 'ley 1755']::text[]
);
