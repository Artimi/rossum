test:
	UNIT_TESTS=1 pytest -v

build:
	docker-compose build

run: build
	docker-compose up -V