include .env

init_terraform:
	terraform -chdir=terraform init

plan_terraform:
	terraform -chdir=terraform plan

apply_terraform:
	terraform -chdir=terraform apply

destroy_terraform:
	terraform -chdir=terraform destroy

# source .venv/bin/activate
