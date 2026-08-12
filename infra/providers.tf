# トークンは var.cloudflare_api_token から取得する(ローカルはinfra/secrets.auto.tfvars、
# CIはTF_VAR_cloudflare_api_token環境変数で供給する)
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
