# Plan de Implementación — Bot de Telegram PQRS Medellín

## Resumen

Implementar el bounded context `contexts/telegram_bot/` en Python 3.11+ usando `python-telegram-bot` v21 (async/polling), `httpx`, `redis.asyncio`, `hypothesis` y `fakeredis`. El bot expone el sistema PQRS de la Alcaldía de Medellín como canal conversacional en Telegram, sin acceso directo a Postgres.

## Tareas

- [x] 1. Estructura del proyecto y configuración base
  - Crear `contexts/telegram_bot/` con la estructura de paquetes DDD: `telegram_bot/domain/`, `telegram_bot/application/`, `telegram_bot/infrastructure/`
  - Crear `pyproject.toml` con dependencias: `python-telegram-bot>=21`, `httpx>=0.27`, `redis[asyncio]>=5`, `pydantic>=2`
  - Crear `telegram_bot/config.py` que lea las variables de entorno requeridas (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_FUNCIONARIO_SECRET`, `PQRS_API_URL`, `REDIS_URL`, `OLLAMA_URL`) y llame `sys.exit(1)` si `TELEGRAM_BOT_TOKEN` no está definida
  - Crear `telegram_bot/logging_config.py` con logging estructurado JSON (campos `ts`, `chat_id_hash`, `command`, `result`, `duration_ms`)
  - Crear `tests/__init__.py` y `tests/test_config.py` que verifique el `sys.exit(1)` ante token ausente
  - _Requisitos: 9.4, 9.5_

- [x] 2. Modelos de dominio
  - [x] 2.1 Implementar dataclasses de dominio en `telegram_bot/domain/models.py`
    - `UserProfile`, `PqrsSnapshot`, `IngresoState`, `AlertaMessage`, `TelegramUpdate`, `TelegramMessage`, `TelegramCallbackQuery`
    - Incluir método `to_dict` / `from_dict` en cada dataclass para serialización Redis
    - _Requisitos: 1.4, 2.1, 5.2, 6.3, 11.1, 11.7, 10.1_

  - [ ]* 2.2 Test de propiedad: round-trip de TelegramUpdate
    - Crear `tests/test_properties.py`
    - **Propiedad 1: Round-trip de TelegramUpdate**
    - **Valida: Requisito 10.3**

  - [ ]* 2.3 Test de propiedad: persistencia round-trip de UserProfile
    - **Propiedad 12: Persistencia de registro de usuario (round-trip)**
    - **Valida: Requisito 1.4**

- [x] 3. Infraestructura — RedisSessionStore
  - [x] 3.1 Implementar `telegram_bot/infrastructure/redis_session_store.py`
    - Clase `RedisSessionStore` con todos los métodos del diseño: `get_user`, `save_user`, `get_all_funcionarios`, `get_session`, `append_session`, `clear_session`, `get_ingreso`, `save_ingreso`, `clear_ingreso`, `alerta_ya_enviada`, `marcar_alerta_enviada`
    - Respetar esquema de claves Redis y TTLs: `bot:ingreso:{chat_id}` TTL 900 s, `bot:alerta_enviada:{id}:{fecha}` TTL 86400 s, `bot:registro_bloqueado:{chat_id}` TTL 600 s
    - _Requisitos: 1.3, 1.4, 5.2, 6.5, 7.1, 7.2, 11.7, 11.8_

  - [ ]* 3.2 Test de propiedad: deduplicación de alertas (fakeredis)
    - En `tests/test_properties.py`
    - **Propiedad 4: Deduplicación de alertas (round-trip)**
    - **Valida: Requisito 6.5**

  - [ ]* 3.3 Test de propiedad: persistencia y recuperación de sesión IA
    - **Propiedad 6: Persistencia y recuperación de sesión IA**
    - **Valida: Requisito 5.2**

  - [ ]* 3.4 Test de propiedad: IngresoState con TTL correcto
    - **Propiedad 10: Persistencia de IngresoState con TTL correcto**
    - **Valida: Requisito 11.7**

  - [ ]* 3.5 Test de propiedad: bloqueo tras 3 intentos fallidos
    - **Propiedad 11: Bloqueo tras 3 intentos fallidos de registro**
    - **Valida: Requisito 1.3**

  - [ ]* 3.6 Tests unitarios de RedisSessionStore
    - Crear `tests/test_redis_session_store.py` con `fakeredis`
    - Cubrir casos: usuario no encontrado, guardar/recuperar perfil, append sesión hasta 10 mensajes, TTL de ingreso, deduplicación de alertas
    - _Requisitos: 1.4, 5.2, 6.5, 11.7_

- [x] 4. Infraestructura — PqrsApiClient
  - [x] 4.1 Implementar `telegram_bot/infrastructure/pqrs_api_client.py`
    - Clase `PqrsApiClient` con `httpx.AsyncClient`
    - Métodos: `get_pqrs`, `get_pendientes_prioridad`, `get_metricas`, `get_secretarias`, `get_pqrs_por_secretaria`, `crear_pqrs`, `assist_mensaje_gestion`
    - 404 → retorna `None`; 5xx/timeout → lanza `PqrsApiError`
    - Definir excepción `PqrsApiError` en `telegram_bot/domain/exceptions.py`
    - _Requisitos: 2.1, 2.2, 2.3, 3.1, 4.1, 8.1, 8.2, 11.4_

  - [ ]* 4.2 Tests unitarios de PqrsApiClient
    - Crear `tests/test_pqrs_api_client.py` con `respx` para mockear httpx
    - Cubrir: respuesta 200, 404 retorna None, 500 lanza PqrsApiError, timeout lanza PqrsApiError
    - _Requisitos: 2.2, 2.3, 3.1, 4.1_

- [x] 5. Infraestructura — OllamaClient
  - Implementar `telegram_bot/infrastructure/ollama_client.py`
  - Clase `OllamaClient` que delega a `POST /api/v1/assist/ollama/mensaje-gestion` de la PQRS_API
  - Manejar timeout de 30 s (enviar mensaje de espera) y 60 s (error definitivo)
  - _Requisitos: 5.1, 5.3, 5.4_

- [ ] 6. Checkpoint — Infraestructura lista
  - Asegurar que todos los tests de infraestructura pasan. Consultar al usuario si hay dudas sobre contratos de la PQRS_API.

- [x] 7. Aplicación — MessageFormatter
  - [x] 7.1 Implementar `telegram_bot/application/message_formatter.py`
    - Funciones puras: `format_pqrs_detail`, `format_pqrs_list_item`, `format_metricas`, `format_alerta`, `format_secretaria_list`
    - Usar Markdown compatible con Telegram (negrita para etiquetas)
    - Prefijo "🚨 URGENTE:" en `format_alerta` cuando `alerta.es_urgente is True`
    - _Requisitos: 2.5, 3.3, 4.1, 6.3, 6.6, 8.1_

  - [ ]* 7.2 Test de propiedad: formato de detalle PQRS contiene todos los campos
    - En `tests/test_properties.py`
    - **Propiedad 2: Formato de detalle PQRS contiene todos los campos requeridos**
    - **Valida: Requisitos 2.1, 2.5**

  - [ ]* 7.3 Test de propiedad: formato de alerta contiene todos los campos
    - **Propiedad 8: Formato de alerta contiene todos los campos requeridos**
    - **Valida: Requisito 6.3**

  - [ ]* 7.4 Tests unitarios de MessageFormatter
    - Crear `tests/test_message_formatter.py` con ejemplos concretos
    - Cubrir: PQRS con summary, PQRS sin campos opcionales, alerta urgente vs normal, lista vacía
    - _Requisitos: 2.5, 6.3, 6.6_

- [x] 8. Aplicación — CommandHandlers (comandos sin conversación)
  - [x] 8.1 Implementar `telegram_bot/application/command_handlers.py`
    - Handlers async: `start_handler`, `pqrs_handler`, `pendientes_handler`, `metricas_handler`, `secretaria_handler`, `secretarias_handler`, `alertas_handler`, `nueva_consulta_handler`, `cancelar_handler`
    - Verificar rol en handlers restringidos; responder con mensaje de acceso denegado para ciudadanos
    - `start_handler`: flujo de registro con selección de rol y verificación de código de funcionario (hasta 3 intentos, bloqueo 10 min)
    - `pendientes_handler`: botón inline "Ver más" cuando hay más de 10 resultados
    - _Requisitos: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 5.5, 7.1, 7.2, 7.4, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 8.2 Test de propiedad: control de acceso por rol
    - En `tests/test_properties.py`
    - **Propiedad 5: Control de acceso por rol**
    - **Valida: Requisitos 3.2, 4.2, 7.4, 8.4**

  - [ ]* 8.3 Tests unitarios de CommandHandlers
    - Crear `tests/test_command_handlers.py` con utilidades de test de `python-telegram-bot`
    - Cubrir: `/start` ciudadano, `/start` funcionario código correcto, `/start` funcionario código incorrecto ×3, `/pendientes` como ciudadano, `/metricas` como funcionario
    - _Requisitos: 1.1, 1.2, 1.3, 3.2, 4.2_

- [x] 9. Aplicación — FallbackHandler (Asistente IA)
  - Implementar `fallback_handler` en `telegram_bot/application/command_handlers.py`
  - Reenviar texto libre al `OllamaClient`, mantener historial de sesión (últimos 10 mensajes) en Redis
  - Incluir indicador de rol en el contexto para funcionarios
  - Manejar timeout 30 s (mensaje de espera) y 60 s (error)
  - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.6_

- [x] 10. Aplicación — ConversationHandler (flujo /nueva_pqrs)
  - [x] 10.1 Implementar `telegram_bot/application/conversation_handlers.py`
    - `ConversationHandler` con estados: `SELECCIONAR_TIPO → INGRESAR_DESCRIPCION → INGRESAR_NOMBRE → CONFIRMAR → END`
    - Botones inline para selección de tipo (P/Q/R/S/D)
    - Validar que la descripción no sea solo whitespace
    - Mostrar resumen y pedir confirmación antes de llamar `crear_pqrs`
    - Persistir `IngresoState` en Redis (`bot:ingreso:{chat_id}`, TTL 15 min)
    - Manejar `/cancelar` en cualquier paso
    - _Requisitos: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

  - [ ]* 10.2 Test de propiedad: whitespace rechazado como descripción
    - En `tests/test_properties.py`
    - **Propiedad 3: Whitespace rechazado como descripción en ingreso de PQRS**
    - **Valida: Requisito 11.1**

  - [ ]* 10.3 Tests de flujo conversacional
    - Crear `tests/test_ingreso_flow.py`
    - Cubrir: flujo completo exitoso, cancelación en cada paso, descripción whitespace rechazada, error de API al crear PQRS
    - _Requisitos: 11.1, 11.3, 11.4, 11.5, 11.6_

- [ ] 11. Checkpoint — Handlers y conversaciones
  - Asegurar que todos los tests de handlers pasan. Consultar al usuario si hay dudas sobre el flujo de registro o el ConversationHandler.

- [ ] 12. Logging estructurado y endpoint /health
  - [ ] 12.1 Integrar logging JSON en todos los handlers
    - Emitir log por cada update procesado con `ts`, `chat_id_hash` (SHA-256), `command`, `result`, `duration_ms`
    - Registrar errores de PQRS_API y Telegram con payload relevante
    - _Requisitos: 9.3, 2.3, 9.2_

  - [ ]* 12.2 Test de propiedad: log estructurado contiene campos requeridos
    - En `tests/test_properties.py`
    - **Propiedad 9: Log estructurado contiene campos requeridos**
    - **Valida: Requisito 9.3**

- [x] 13. Worker de alertas
  - [x] 13.1 Implementar `telegram_bot/application/alerta_scheduler.py`
    - Función `dispatch_alertas` que consulta `get_pendientes_prioridad`, filtra PQRS con SLA ≤ 24 h, obtiene funcionarios con `alertas_activas=True` de Redis, envía alertas y marca deduplicación
    - Prefijo "🚨 URGENTE:" para PQRS CRITICO con SLA < 4 h
    - Capturar `TelegramError` por destinatario, loguear y continuar
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.3_

  - [x] 13.2 Implementar `worker_alertas.py` en la raíz del contexto
    - Loop `asyncio` con `asyncio.sleep(3600)` que llama `dispatch_alertas`
    - Leer configuración desde variables de entorno
    - _Requisitos: 6.1_

  - [ ]* 13.3 Test de propiedad: despacho solo a funcionarios con alertas activas
    - En `tests/test_properties.py`
    - **Propiedad 7: Despacho de alertas solo a funcionarios con alertas activas**
    - **Valida: Requisitos 6.2, 7.3**

- [x] 14. Punto de entrada principal y endpoint /health
  - Implementar `bot.py` en la raíz del contexto
    - Validar configuración al arrancar (`config.py`)
    - Registrar todos los handlers en la `Application` de `python-telegram-bot`
    - Iniciar polling con `application.run_polling()`
  - Implementar endpoint `GET /health` retornando `{"status": "ok"}` con HTTP 200
    - Usar `aiohttp` o el servidor web integrado de `python-telegram-bot` según convenga
  - _Requisitos: 9.1, 9.2, 9.5, 9.6_

- [x] 15. Checkpoint final — Integración completa
  - Ejecutar la suite completa de tests: `pytest contexts/telegram_bot/tests --asyncio-mode=auto`
  - Asegurar que todos los tests pasan. Consultar al usuario si hay dudas antes de cerrar.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- Cada tarea referencia requisitos específicos para trazabilidad.
- Los tests de propiedades usan `hypothesis` con `@settings(max_examples=100)` y `fakeredis` para Redis.
- El bot corre en modo polling (sin webhook público), adecuado para desarrollo local.
- `worker_alertas.py` y `bot.py` son procesos independientes que comparten la misma librería `telegram_bot/`.
