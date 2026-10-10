#!/bin/bash
# ==========================================================
#  TPI Bases de Datos II - Script de resguardo (backup)
#  Descarga la base gimnasio_tpi desde MongoDB Atlas con mongodump
#  dentro de ./resguardos_tpi/<fecha_actual>/
# ==========================================================

# PATH con las rutas de Homebrew (necesario si se ejecuta desde cron)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Trabajar siempre desde la carpeta donde está el script (rutas relativas)
cd "$(dirname "$0")" || exit 1

# --- Configuración ---
# Se puede sobrescribir con la variable de entorno MONGO_URI
MONGO_URI="${MONGO_URI:-mongodb+srv://profesor_tpi:WnuKSKpUrE26FmIs@clustertpigimnasio.l3fcykv.mongodb.net/}"
BASE_DATOS="gimnasio_tpi"
FECHA=$(date +%Y-%m-%d)
DESTINO="./resguardos_tpi/$FECHA"

# --- Verificar que mongodump esté instalado ---
if ! command -v mongodump > /dev/null 2>&1; then
  echo "ERROR: mongodump no está instalado."
  echo "Instalar con: brew tap mongodb/brew && brew install mongodb-database-tools"
  exit 1
fi

# --- Crear la carpeta de destino ---
mkdir -p "$DESTINO"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup de '$BASE_DATOS' en $DESTINO"

# --- Ejecutar mongodump contra Atlas ---
mongodump --uri="$MONGO_URI" --db="$BASE_DATOS" --out="$DESTINO"

if [ $? -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup finalizado correctamente."
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: falló la ejecución de mongodump."
  exit 1
fi
