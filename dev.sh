#!/bin/bash
# Запуск бэкенда и фронта одной командой
# Ctrl+C останавливает оба процесса

trap 'kill 0' SIGINT SIGTERM

python3 -m uvicorn main:app --port 8000 --reload &
cd frontend && npm run dev &

wait
