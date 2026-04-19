# Documento de Requisitos — Bot de Telegram PQRS Medellín

## Introducción

Se requiere un bot de Telegram que actúe como canal de acceso ciudadano y operativo al sistema PQRS de la Alcaldía de Medellín. El bot permite a ciudadanos y funcionarios consultar el estado de PQRS, recibir alertas sobre vencimientos y novedades, y obtener respuestas asistidas por IA (Ollama `llama3.2:3b`) sin necesidad de acceder al frontend web. El bot se integra con la API REST existente (`http://127.0.0.1:8080/api/v1`) y con el modelo Ollama local.

---

## Glosario

- **Bot**: El servicio de Telegram implementado en este contexto (`contexts/telegram_bot/`).
- **Telegram_API**: La API de Telegram Bot (Telegram Bot API v7+).
- **PQRS_API**: La API REST Rust/Axum del proyecto, accesible en `/api/v1`.
- **Asistente_IA**: El módulo de inferencia Ollama (`llama3.2:3b`) expuesto vía `/api/v1/assist/ollama/*`.
- **Ciudadano**: Usuario de Telegram que consulta el estado de sus PQRS.
- **Funcionario**: Usuario de Telegram con rol operativo que recibe alertas y gestiona PQRS.
- **Chat_Id**: Identificador único de conversación en Telegram.
- **Alerta**: Notificación proactiva enviada por el Bot a un Funcionario sobre vencimientos o PQRS críticas.
- **Sesión**: Estado conversacional en memoria (Redis) asociado a un Chat_Id.
- **Webhook**: Endpoint HTTP del Bot que recibe actualizaciones de Telegram.
- **Worker_Alertas**: Proceso periódico que consulta la PQRS_API y despacha Alertas.
- **Nivel_Riesgo**: Clasificación de urgencia de una PQRS: CRITICO, ALTO, MEDIO, BAJO.
- **SLA**: Plazo máximo de respuesta según Ley 1755 de 2015.

---

## Requisitos

### Requisito 1: Registro y autenticación de usuarios

**User Story:** Como ciudadano o funcionario, quiero registrarme en el bot con mi Chat_Id para que el sistema me identifique y personalice mis interacciones.

#### Criterios de Aceptación

1. WHEN un usuario envía el comando `/start`, THE Bot SHALL responder con un mensaje de bienvenida que explique las capacidades disponibles y solicite el rol del usuario (ciudadano o funcionario).
2. WHEN un usuario selecciona el rol "funcionario", THE Bot SHALL solicitar un código de acceso y verificarlo contra la variable de entorno `TELEGRAM_FUNCIONARIO_SECRET`.
3. IF el código de acceso proporcionado por el usuario no coincide con `TELEGRAM_FUNCIONARIO_SECRET`, THEN THE Bot SHALL responder con un mensaje de error y permitir hasta 3 intentos antes de bloquear el registro por 10 minutos.
4. WHEN el registro es exitoso, THE Bot SHALL persistir el Chat_Id, el rol y la marca de tiempo de registro en Redis con clave `bot:user:{chat_id}`.
5. THE Bot SHALL responder en español en todas las interacciones.

---

### Requisito 2: Consulta de PQRS por ID

**User Story:** Como ciudadano, quiero consultar el detalle de una PQRS por su identificador para conocer su estado actual sin acceder al portal web.

#### Criterios de Aceptación

1. WHEN un usuario envía el comando `/pqrs {id}`, THE Bot SHALL consultar `GET /api/v1/pqrs/{id}` y responder con: identificador, tipo, estado de clasificación, nivel de riesgo, secretaría asignada y fecha límite SLA.
2. IF la PQRS_API retorna un código HTTP 404 para el identificador solicitado, THEN THE Bot SHALL responder con el mensaje "No se encontró una PQRS con el identificador indicado."
3. IF la PQRS_API retorna un código HTTP distinto de 200 y 404, THEN THE Bot SHALL responder con el mensaje "El servicio no está disponible en este momento. Intente más tarde." y registrar el error en el log del Bot.
4. WHEN la respuesta de la PQRS_API incluye un resumen IA disponible, THE Bot SHALL incluir el resumen en la respuesta al usuario.
5. THE Bot SHALL formatear la respuesta usando Markdown compatible con Telegram (negrita para etiquetas, valor en texto plano).

---

### Requisito 3: Listado de PQRS pendientes priorizadas (Funcionario)

**User Story:** Como funcionario, quiero consultar las PQRS pendientes ordenadas por prioridad para atender primero las más urgentes.

#### Criterios de Aceptación

1. WHEN un Funcionario envía el comando `/pendientes`, THE Bot SHALL consultar `GET /api/v1/pqrs/pendientes/prioridad` y responder con las primeras 10 PQRS ordenadas por Nivel_Riesgo descendente.
2. WHILE el usuario tiene rol "ciudadano", THE Bot SHALL responder al comando `/pendientes` con el mensaje "Este comando está disponible solo para funcionarios."
3. THE Bot SHALL mostrar por cada PQRS: identificador, tipo, Nivel_Riesgo, secretaría asignada y días restantes al vencimiento SLA.
4. IF la lista de PQRS pendientes está vacía, THEN THE Bot SHALL responder con el mensaje "No hay PQRS pendientes en este momento."
5. WHEN la lista supera 10 elementos, THE Bot SHALL incluir un botón inline "Ver más" que consulte la siguiente página de resultados.

---

### Requisito 4: Consulta de métricas del dashboard

**User Story:** Como funcionario, quiero consultar métricas resumidas del sistema para tener visibilidad del estado general sin abrir el dashboard web.

#### Criterios de Aceptación

1. WHEN un Funcionario envía el comando `/metricas`, THE Bot SHALL consultar `GET /api/v1/dashboard/metricas` y responder con: total de PQRS, cantidad por estado de clasificación, cantidad por Nivel_Riesgo y cantidad vencidas.
2. WHILE el usuario tiene rol "ciudadano", THE Bot SHALL responder al comando `/metricas` con el mensaje "Este comando está disponible solo para funcionarios."
3. IF la PQRS_API retorna un error al consultar métricas, THEN THE Bot SHALL responder con el mensaje "No se pudieron obtener las métricas en este momento."

---

### Requisito 5: Interacción con el Asistente IA

**User Story:** Como ciudadano o funcionario, quiero hacer preguntas en lenguaje natural sobre el sistema PQRS para obtener respuestas contextualizadas sin conocer los comandos exactos.

#### Criterios de Aceptación

1. WHEN un usuario envía un mensaje de texto que no corresponde a ningún comando registrado, THE Bot SHALL reenviar el mensaje al Asistente_IA vía `POST /api/v1/assist/ollama/mensaje-gestion` y responder con la respuesta generada.
2. THE Bot SHALL mantener el historial de la Sesión activa (últimos 10 mensajes) en Redis con clave `bot:session:{chat_id}` y enviarlo como contexto al Asistente_IA en cada solicitud.
3. WHEN el Asistente_IA tarda más de 30 segundos en responder, THE Bot SHALL enviar el mensaje "El asistente está procesando tu consulta, por favor espera..." y continuar esperando hasta 60 segundos antes de responder con un error de tiempo de espera.
4. IF el Asistente_IA retorna un error HTTP, THEN THE Bot SHALL responder con el mensaje "El asistente no está disponible en este momento. Puedes usar los comandos directos como /pqrs {id}."
5. THE Bot SHALL limpiar la Sesión de Redis cuando el usuario envíe el comando `/nueva_consulta`.
6. WHERE el usuario tiene rol "funcionario", THE Bot SHALL incluir en el contexto enviado al Asistente_IA el indicador de rol para que las respuestas sean apropiadas al perfil operativo.

---

### Requisito 6: Alertas proactivas de vencimiento SLA (Funcionario)

**User Story:** Como funcionario, quiero recibir alertas automáticas cuando una PQRS esté próxima a vencer su SLA para tomar acción a tiempo.

#### Criterios de Aceptación

1. THE Worker_Alertas SHALL ejecutarse cada 60 minutos y consultar `GET /api/v1/pqrs/pendientes/prioridad` para identificar PQRS con fecha límite SLA dentro de las próximas 24 horas.
2. WHEN el Worker_Alertas identifica una PQRS con SLA vencido o a menos de 24 horas de vencer, THE Worker_Alertas SHALL enviar una Alerta a todos los Chat_Id registrados con rol "funcionario" en Redis.
3. THE Worker_Alertas SHALL incluir en cada Alerta: identificador de la PQRS, tipo, Nivel_Riesgo, secretaría asignada, fecha límite SLA y horas restantes.
4. IF el envío de una Alerta a un Chat_Id falla con error de Telegram, THEN THE Worker_Alertas SHALL registrar el error en el log y continuar con los demás destinatarios.
5. THE Worker_Alertas SHALL registrar en Redis con clave `bot:alerta_enviada:{pqrs_id}:{fecha}` las alertas ya enviadas para evitar duplicados en el mismo día.
6. WHEN una PQRS tiene Nivel_Riesgo CRITICO y su SLA vence en menos de 4 horas, THE Worker_Alertas SHALL enviar la Alerta con el prefijo "🚨 URGENTE:" en el mensaje.

---

### Requisito 7: Suscripción y desuscripción a alertas

**User Story:** Como funcionario, quiero controlar si recibo alertas automáticas para gestionar las notificaciones según mi disponibilidad.

#### Criterios de Aceptación

1. WHEN un Funcionario envía el comando `/alertas on`, THE Bot SHALL actualizar el campo `alertas_activas` a `true` en Redis para el Chat_Id del usuario y confirmar la activación.
2. WHEN un Funcionario envía el comando `/alertas off`, THE Bot SHALL actualizar el campo `alertas_activas` a `false` en Redis para el Chat_Id del usuario y confirmar la desactivación.
3. WHILE el campo `alertas_activas` de un Funcionario es `false`, THE Worker_Alertas SHALL omitir ese Chat_Id al despachar Alertas.
4. WHILE el usuario tiene rol "ciudadano", THE Bot SHALL responder a los comandos `/alertas on` y `/alertas off` con el mensaje "Las alertas automáticas están disponibles solo para funcionarios."

---

### Requisito 8: Consulta de PQRS por secretaría (Funcionario)

**User Story:** Como funcionario, quiero consultar las PQRS asignadas a una secretaría específica para hacer seguimiento por dependencia.

#### Criterios de Aceptación

1. WHEN un Funcionario envía el comando `/secretaria {codigo}`, THE Bot SHALL consultar `GET /api/v1/secretarias/{codigo}/pqrs` y responder con las primeras 10 PQRS de esa secretaría incluyendo: identificador, tipo, estado de gestión y días restantes al SLA.
2. IF la PQRS_API retorna HTTP 404 para el código de secretaría, THEN THE Bot SHALL responder con el mensaje "No se encontró la secretaría con el código indicado."
3. WHEN un Funcionario envía el comando `/secretarias`, THE Bot SHALL consultar `GET /api/v1/secretarias` y responder con la lista de secretarías disponibles (código y nombre).
4. WHILE el usuario tiene rol "ciudadano", THE Bot SHALL responder a los comandos `/secretaria` y `/secretarias` con el mensaje "Este comando está disponible solo para funcionarios."

---

### Requisito 9: Webhook y disponibilidad del servicio

**User Story:** Como operador del sistema, quiero que el bot sea confiable y fácil de desplegar para garantizar disponibilidad continua del canal Telegram.

#### Criterios de Aceptación

1. THE Bot SHALL exponer un endpoint HTTP `POST /webhook` que reciba actualizaciones de la Telegram_API y responda con HTTP 200 en menos de 3 segundos.
2. IF el procesamiento de una actualización de Telegram tarda más de 3 segundos, THEN THE Bot SHALL responder HTTP 200 a Telegram inmediatamente y procesar la actualización de forma asíncrona.
3. THE Bot SHALL registrar en log estructurado (JSON) cada mensaje recibido con: Chat_Id anonimizado (hash SHA-256), tipo de comando, marca de tiempo y resultado (éxito/error).
4. THE Bot SHALL leer su configuración exclusivamente desde variables de entorno: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_FUNCIONARIO_SECRET`, `PQRS_API_URL`, `REDIS_URL`, `OLLAMA_URL`.
5. IF la variable de entorno `TELEGRAM_BOT_TOKEN` no está definida al iniciar, THEN THE Bot SHALL terminar con código de salida 1 y un mensaje de error descriptivo en stderr.
6. THE Bot SHALL incluir un endpoint `GET /health` que retorne HTTP 200 con `{"status": "ok"}` cuando el servicio esté operativo.

---

### Requisito 11: Ingreso de nueva PQRS desde el bot

**User Story:** Como ciudadano, quiero poder radicar una nueva PQRS directamente desde Telegram para reportar una petición, queja, reclamo o sugerencia sin necesidad de acceder al portal web.

#### Criterios de Aceptación

1. WHEN un usuario envía el comando `/nueva_pqrs`, THE Bot SHALL iniciar un flujo conversacional guiado que solicite paso a paso: tipo de PQRS (Petición / Queja / Reclamo / Sugerencia / Denuncia), descripción del caso y nombre del solicitante.
2. THE Bot SHALL presentar el tipo de PQRS mediante botones inline para que el usuario seleccione una opción válida sin necesidad de escribir texto libre.
3. WHEN el usuario completa todos los campos requeridos, THE Bot SHALL mostrar un resumen de la PQRS a radicar y solicitar confirmación antes de enviarla.
4. WHEN el usuario confirma el envío, THE Bot SHALL realizar `POST /api/v1/pqrs` con los datos recopilados y responder con el identificador asignado y la fecha límite SLA calculada.
5. IF la PQRS_API retorna un error al crear la PQRS, THEN THE Bot SHALL responder con el mensaje "No se pudo radicar la PQRS. Intente nuevamente o contacte al administrador." y registrar el error en el log.
6. WHEN el usuario envía el comando `/cancelar` durante el flujo de ingreso, THE Bot SHALL cancelar el proceso y limpiar el estado de la sesión en Redis.
7. THE Bot SHALL almacenar el estado del flujo de ingreso en Redis con clave `bot:ingreso:{chat_id}` para tolerar interrupciones y permitir retomar el proceso.
8. IF el usuario no completa el flujo en 15 minutos, THEN THE Bot SHALL limpiar automáticamente el estado `bot:ingreso:{chat_id}` de Redis y notificar al usuario que el proceso expiró.

---

### Requisito 10: Parseo y serialización de mensajes Telegram

**User Story:** Como desarrollador, quiero que el bot parsee y serialice correctamente los mensajes de Telegram para garantizar la integridad de las interacciones.

#### Criterios de Aceptación

1. WHEN el Bot recibe una actualización de la Telegram_API, THE Bot SHALL parsear el JSON de la actualización en una estructura interna `TelegramUpdate`.
2. THE Bot SHALL serializar las respuestas salientes al formato JSON requerido por la Telegram_API antes de enviarlas.
3. FOR ALL mensajes de texto válidos recibidos, parsear y luego serializar la estructura `TelegramUpdate` SHALL producir un objeto equivalente al original (propiedad round-trip).
4. IF el JSON de una actualización recibida no cumple el esquema esperado de la Telegram_API, THEN THE Bot SHALL registrar el error con el payload recibido y responder HTTP 200 a Telegram para evitar reintentos.
