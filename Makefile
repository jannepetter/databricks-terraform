include .env
export

init_terraform:
	terraform -chdir=terraform/dev init

plan_terraform:
	terraform -chdir=terraform/dev plan

apply_terraform:
	terraform -chdir=terraform/dev apply

destroy_terraform:
	terraform -chdir=terraform/dev destroy

fmt:
	terraform -chdir=terraform fmt --recursive
# source .venv/bin/activate
