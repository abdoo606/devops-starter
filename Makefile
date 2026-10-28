.PHONY: build run test scan

build:
	docker build -t devops-starter:local .

run:
	docker compose up --build

test:
	python -m pytest ../../projects/30-devops-starter -q

scan:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image devops-starter:local
