resource "cloudflare_zone_settings_override" "ankardo" {
  zone_id = data.cloudflare_zone.ankardo.id

  settings {
    ssl = "full"
  }
}
