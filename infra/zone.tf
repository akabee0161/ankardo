# ankardo.com は Cloudflare Registrar で既に登録済み・ゾーンも自動作成済みのため、
# 新規作成ではなく既存ゾーンを data source で参照する
data "cloudflare_zone" "ankardo" {
  name = var.domain
}
