# Comandos del proyecto. El venv vive en la raiz (.venv).
VENV ?= .venv

install:            ## Crear el venv e instalar dependencias de runtime
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements.txt

install-dev:        ## Instalar tambien las dependencias de desarrollo (stubs de typing)
	$(VENV)/bin/pip install -r backend/requirements-dev.txt

run:                ## Arrancar el servidor (un solo comando; migra la base local para las sesiones)
	cd backend && DJANGO_DEBUG=True ../$(VENV)/bin/python manage.py migrate --noinput
	cd backend && DJANGO_DEBUG=True ../$(VENV)/bin/python manage.py runserver

test:               ## Correr la suite de tests
	cd backend && DJANGO_DEBUG=True ../$(VENV)/bin/python manage.py test

web:                ## Frontend en :4200 con datos simulados (sin backend ni login)
	cd frontend && npm start

web-real:           ## Frontend en :4200 contra la API real (servidor en :8000)
	cd frontend && npm run start:real

up:                 ## Docker: backend + PostgreSQL (API en :8000)
	docker compose up --build

up-front:           ## Docker: backend + PostgreSQL + frontend (:4200)
	docker compose --profile front up --build
