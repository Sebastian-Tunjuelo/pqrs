# pqrs-shared-kernel

Tipos de dominio compartidos y esquemas JSON de eventos para los bounded contexts Python.

## Instalación local (editable)

Desde la raíz del monorepo:

```bash
pip install -e ./shared-kernel
```

O desde un contexto:

```bash
pip install -e ../../shared-kernel
```

Luego en cada contexto que declare `pqrs-shared-kernel` en dependencias, resuelve contra el entorno virtual donde lo instalaste.
