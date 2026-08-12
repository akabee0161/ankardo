variable "domain" {
  description = "Ankardoのルートドメイン"
  type        = string
  default     = "ankardo.com"
}

variable "cloudflare_api_token" {
  description = "Cloudflare APIトークン(infra/secrets.auto.tfvarsで設定する。CIではCLOUDFLARE_API_TOKEN環境変数から自動供給される)"
  type        = string
  sensitive   = true
}
