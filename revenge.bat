@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado.
  echo Rode este comando dentro da pasta do projeto:
  echo python -m venv .venv
  pause
  exit /b 1
)

if exist "requirements.txt" (
  ".venv\Scripts\python.exe" -m pip show PyQt5 >nul 2>nul
  if errorlevel 1 (
    echo Instalando dependencias...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
      echo Falha ao instalar dependencias.
      pause
      exit /b 1
    )
  )
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
