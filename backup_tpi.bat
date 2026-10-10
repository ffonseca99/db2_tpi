@echo off
REM ==========================================================
REM  TPI Bases de Datos II - Script de resguardo (backup)
REM  Descarga la base gimnasio_tpi desde MongoDB Atlas con mongodump
REM  dentro de .\resguardos_tpi\<fecha_actual>\
REM ==========================================================

setlocal

REM Trabajar siempre desde la carpeta donde esta el script (rutas relativas)
cd /d "%~dp0"

REM --- Configuracion ---
REM Se puede sobrescribir definiendo la variable de entorno MONGO_URI
if "%MONGO_URI%"=="" set "MONGO_URI=mongodb+srv://profesor_tpi:WnuKSKpUrE26FmIs@clustertpigimnasio.l3fcykv.mongodb.net/"
set "BASE_DATOS=gimnasio_tpi"

REM Fecha en formato AAAA-MM-DD (independiente de la configuracion regional)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "FECHA=%%i"
set "DESTINO=.\resguardos_tpi\%FECHA%"

REM --- Verificar que mongodump este instalado ---
where mongodump >nul 2>&1
if errorlevel 1 (
  echo ERROR: mongodump no esta instalado o no esta en el PATH.
  echo Descargar MongoDB Database Tools: https://www.mongodb.com/try/download/database-tools
  exit /b 1
)

REM --- Crear la carpeta de destino ---
if not exist "%DESTINO%" mkdir "%DESTINO%"
echo [%FECHA% %TIME%] Iniciando backup de '%BASE_DATOS%' en %DESTINO%

REM --- Ejecutar mongodump contra Atlas ---
mongodump --uri="%MONGO_URI%" --db="%BASE_DATOS%" --out="%DESTINO%"

if errorlevel 1 (
  echo [%FECHA% %TIME%] ERROR: fallo la ejecucion de mongodump.
  exit /b 1
)

echo [%FECHA% %TIME%] Backup finalizado correctamente.
endlocal
exit /b 0
