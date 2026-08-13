# Cloudflare WorkersのRoute機能はゾーンへの到達済みリクエストをパスパターンでWorkerに振り分けるため、
# 実際の配信先IPを指すオリジンは不要。ただし、リクエストがCloudflareのエッジに到達するには、
# ルートドメインの proxied(オレンジクラウド)なDNSレコードが必要。
resource "cloudflare_record" "root" {
  zone_id = data.cloudflare_zone.ankardo.id
  name    = "@"
  type    = "A"
  content = "192.0.2.1" # プレースホルダー。Workers Routeが全リクエストを処理するため実際に疎通しない
  proxied = true
  comment = "Placeholder origin - traffic is served entirely by Cloudflare Workers routes"

  # CIはterraform stateを永続化していないため、既に存在するレコードでも
  # 常に「新規作成」として扱われる(詳細: infra/README.md)。それによる
  # "already exists" エラーを避けるための暫定対応。
  allow_overwrite = true
}
