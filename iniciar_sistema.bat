@echo off
title Radar Obras MT - Sistema de Inteligencia em Licitacoes
color 0b
echo ============================================================
echo   RADAR OBRAS MT - SISTEMA DE INTELIGENCIA DE LICITACOES
echo ============================================================
echo.
echo   Iniciando servidor local...
echo   Abrindo o sistema no seu navegador...
echo.
echo   Para encerrar o sistema, basta fechar esta janela.
echo ============================================================
echo.
start "" http://localhost:8080
python -m http.server 8080
