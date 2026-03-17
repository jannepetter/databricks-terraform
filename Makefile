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

# source .venv/bin/activate
