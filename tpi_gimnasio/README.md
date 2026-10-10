# TPI Gimnasio – API con FastAPI y MongoDB Atlas

CRUD con **baja lógica** sobre tres colecciones: `socios`, `clases` y `reservas`.
Arquitectura en capas: `router → service → repository → MongoDB`.

```
tpi_gimnasio/
├── main.py                      # FastAPI, manejo de errores, /health
├── app/
│   ├── config.py                # lee MONGO_URI y DB_NAME del .env
│   ├── database.py              # conexión única + creación de colecciones e índices
│   ├── validators.py            # los $jsonSchema de las 3 colecciones
│   ├── schemas/                 # modelos Pydantic (entrada y salida)
│   ├── repositories/            # único lugar que habla con MongoDB (baja lógica en base.py)
│   ├── services/                # reglas de negocio
│   └── routers/                 # endpoints HTTP, sin lógica
├── postman/TPI_Gimnasio.postman_collection.json
└── tests/                       # pruebas automáticas (base simulada, no usan Atlas)
```

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# editá .env: reemplazá <usuario> y <password> por los de tu usuario de Atlas

uvicorn main:app --reload
```

- Swagger (para probar a mano): http://127.0.0.1:8000/docs
- Estado de la API y de la conexión: http://127.0.0.1:8000/health

Al arrancar, la API crea las colecciones que falten **con su validador `$jsonSchema`** y los índices.
Si una colección ya existe en Atlas, no la toca.

### Si no conecta
En Atlas → **Network Access** tiene que estar habilitada tu IP actual (o `0.0.0.0/0` solo para pruebas).
Si el arranque falla con `ServerSelectionTimeoutError`, casi siempre es eso o una credencial incorrecta.

## Endpoints

| Operación | Socios | Clases | Reservas |
|---|---|---|---|
| CREATE | `POST /socios` | `POST /clases` | `POST /reservas` |
| READ (lista) | `GET /socios` | `GET /clases` | `GET /reservas?socioId=&claseId=&estado=` |
| READ (uno) | `GET /socios/{id}` | `GET /clases/{id}` | `GET /reservas/{id}` |
| UPDATE parcial | `PATCH /socios/{id}` | `PATCH /clases/{id}` | `PATCH /reservas/{id}` |
| DELETE (baja lógica) | `DELETE /socios/{id}` | `DELETE /clases/{id}` | `DELETE /reservas/{id}` |

Los listados aceptan `skip` y `limit` (por defecto 0 y 50, máximo 200).

### Cómo funciona la baja lógica
- `DELETE` hace `activo = false` y `fechaBaja = ahora`. El documento **sigue en la base**.
- Todas las lecturas, modificaciones y bajas filtran `activo: true`: lo dado de baja devuelve **404** y no aparece en los listados.
- Los modelos de entrada rechazan `activo` y `fechaBaja` (422), así que no se pueden tocar desde afuera.

### Códigos de respuesta
`201` creado · `200` ok · `400` id mal formado o nada para actualizar · `404` no existe o está dado de baja ·
`409` DNI repetido, reserva duplicada o clase sin cupo · `422` datos inválidos o socio/clase de la reserva dados de baja ·
`503` sin conexión con MongoDB.

### Reglas de negocio de reservas
- El socio y la clase deben existir y estar activos.
- Un socio no puede tener dos reservas confirmadas para la misma clase.
- La cantidad de reservas `CONFIRMADA` de una clase no puede superar su `cupoMaximo`.
- La reserva no guarda fecha: solo referencia a la clase (`claseId`), y la fecha vive en `clase.fechaInicio`.

### Modelo de clases
Una **clase es una ocurrencia real**: si hay boxeo hoy y mañana, son dos documentos distintos, cada uno con su cupo, sus reservas y su baja lógica.
- `fechaAlta`: desde cuándo existe la clase. La pone el servidor al crearla y no se puede modificar.
- `fechaInicio`: momento en que inicia la clase. Es obligatorio al crear y se puede modificar con `PATCH`.
- **Cancelar** (`PATCH` con `estado: "CANCELADA"`) libera el cupo y es distinto de la **baja lógica** (`DELETE`).
- Reactivar una reserva cancelada vuelve a validar el cupo.

## Postman
1. Con la API corriendo, importá `postman/TPI_Gimnasio.postman_collection.json`.
2. Si la API no está en `http://127.0.0.1:8000`, cambiá la variable `base_url` de la colección.
3. Ejecutá la colección completa con **Run collection**. Las carpetas van en orden y cada una usa los ids que guardó la anterior:
   Sistema → Socios → Clases → Reservas → Bajas lógicas → Verificar baja lógica.

Cada request tiene tests que validan el código de estado y el contenido. La carpeta 5 comprueba que lo dado de baja ya no se puede leer ni aparece en los listados.
Podés repetir la corrida las veces que quieras: genera DNIs y fechas nuevos.

## Pruebas automáticas
```bash
pip install -r requirements-dev.txt
pytest
```
Usan una base simulada (`mongomock`): **no tocan tu clúster**.

## Decisiones y supuestos (revisalos)
- **Nombre de la base:** `DB_NAME` vale `gimnasio` por defecto. Si tus colecciones están en otra base, cambialo en `.env`.
- **Documentos embebidos:** tu modelo solo dice «documento embebido», así que definí:
  `membresia {plan, precio?, fechaVencimiento?}` e `instructor {nombre, apellido, especialidad?}`.
  Si tenés otros campos, se ajustan en `app/schemas/`.
- **`fechaInicio` obligatorio:** lo agregué a `required` del validador de `clases` (y de la API). `fechaAlta` no es obligatorio en el validador, igual que en `socios`.
- **Sin validación de fechas:** se puede reservar una clase que ya empezó o crear una clase con `fechaInicio` en el pasado. Si querés bloquearlo, es una regla de una línea en los servicios.
- **Validadores:** MongoDB solo los aplica al crear la colección. Si ya la creaste vos con el script, quedó con el tuyo.
- **DNI único solo entre socios activos** (índice parcial): el DNI de un socio dado de baja se puede volver a registrar.
- **`PATCH`:** solo cambia lo que se envía. En `membresia` e `instructor` se modifica subcampo a subcampo.
  Un campo enviado como `null` se ignora. En reservas solo se puede cambiar el `estado`.
- **No hay baja en cascada:** al dar de baja un socio o una clase, sus reservas existentes quedan como están; lo que se bloquea es crear reservas nuevas.
- **Cupo:** se calcula contando reservas al momento de reservar. Con muchas reservas simultáneas sobre la última plaza podría colarse una de más (aceptable para un TPI).
- **Fechas:** se guardan en UTC. Conviene enviar `fechaInicio` con `Z` (ej. `2026-10-20T22:00:00Z`).

## Seguridad
- La cadena de conexión con la contraseña vive solo en `.env`, que está en `.gitignore`. **Nunca la subas al repositorio.**
- Como la contraseña del usuario de Atlas se compartió por chat, conviene **rotarla** en Atlas → Database Access y crear un usuario con permisos solo sobre esta base.
