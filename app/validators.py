"""Validadores $jsonSchema de las colecciones (idénticos al modelo definido para el TPI).

Se aplican al crear cada colección en MongoDB (ver app/database.py -> init_db).
"""

SOCIOS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["dni", "nombre", "apellido", "email", "membresia", "activo"],
        "properties": {
            "dni": {"bsonType": "string", "description": "Debe ser una cadena y es obligatorio."},
            "nombre": {"bsonType": "string", "description": "Debe ser una cadena y es obligatorio."},
            "apellido": {"bsonType": "string", "description": "Debe ser una cadena y es obligatorio."},
            "email": {"bsonType": "string", "description": "Debe ser una cadena y es obligatorio."},
            "telefono": {"bsonType": "string", "description": "Debe ser una cadena pero no es obligatorio."},
            "fechaAlta": {"bsonType": "date", "description": "Debe ser una fecha."},
            "membresia": {"bsonType": "object", "description": "Documento embebido con el plan; es obligatorio."},
            "activo": {"bsonType": "bool", "description": "Indica si el socio está activo (baja lógica); es obligatorio."},
            "fechaBaja": {"bsonType": ["date", "null"], "description": "Fecha de baja lógica o null."},
        },
    }
}

CLASES_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["nombre", "instructor", "cupoMaximo", "fechaInicio", "activo"],
        "properties": {
            "nombre": {"bsonType": "string", "description": "Debe ser una cadena y es obligatorio."},
            "instructor": {"bsonType": "object", "description": "Documento embebido con los datos del instructor; es obligatorio."},
            "cupoMaximo": {"bsonType": "int", "description": "Debe ser un número entero y es obligatorio."},
            "sala": {"bsonType": "string", "description": "Debe ser una cadena pero no es obligatorio."},
            "fechaAlta": {"bsonType": "date", "description": "Desde cuándo existe la clase."},
            "fechaInicio": {"bsonType": "date", "description": "Momento en que inicia la clase; es obligatorio."},
            "activo": {"bsonType": "bool", "description": "Baja lógica; es obligatorio."},
            "fechaBaja": {"bsonType": ["date", "null"], "description": "Fecha de baja lógica o null."},
        },
    }
}

RESERVAS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["socioId", "claseId", "estado", "activo"],
        "properties": {
            "socioId": {"bsonType": "objectId", "description": "Referencia al socio; es obligatorio."},
            "claseId": {"bsonType": "objectId", "description": "Referencia a la clase; es obligatorio."},
            "estado": {"enum": ["CONFIRMADA", "CANCELADA"], "description": "Solo puede ser CONFIRMADA o CANCELADA."},
            "activo": {"bsonType": "bool", "description": "Baja lógica; es obligatorio."},
            "fechaBaja": {"bsonType": ["date", "null"], "description": "Fecha de baja lógica o null."},
        },
    }
}

VALIDATORS = {
    "socios": SOCIOS_VALIDATOR,
    "clases": CLASES_VALIDATOR,
    "reservas": RESERVAS_VALIDATOR,
}
