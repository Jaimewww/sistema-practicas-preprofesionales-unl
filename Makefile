# Comandos del proyecto. El venv vive en la raiz (.venv).
VENV ?= .venv

install:            ## Crear el venv e instalar dependencias de runtime
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements.txt

install-dev:        ## Instalar tambien las dependencias de desarrollo (stubs de typing)
	$(VENV)/bin/pip install -r backend/requirements-dev.txt

run:                ## Arrancar el servidor (un solo comando)
	cd backend && ../$(VENV)/bin/python manage.py runserver

test:               ## Correr la suite de tests
	cd backend && ../$(VENV)/bin/python manage.py test
