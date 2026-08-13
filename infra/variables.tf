variable "domain" {
  description = "Ankardoのルートドメイン"
  type        = string
  default     = "ankardo.com"
}

variable "cloudflare_api_token" {
  description = "Cloudflare APIトークン(infra/secrets.auto.tfvarsで設定する。CIではTF_VAR_cloudflare_api_token環境変数から自動供給される)"
  type        = string
  sensitive   = true
}
