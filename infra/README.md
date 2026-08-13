# infra/ (Terraform)

Cloudflareゾーン・DNS設定を管理する。GitHub Actions (`.github/workflows/infra.yml`) から
`terraform apply` が実行される。

## 既知の制約: Terraform stateが永続化されていない

`*.tfstate` は `.gitignore` 対象で、リモートbackendも未設定。そのため:

- ローカルで `terraform apply` した内容はローカルの `infra/terraform.tfstate` にのみ記録され、CIには共有されない
- CIの `terraform apply` は毎回**空のstateから開始**する。ローカルで既に作成済みのリソースも「未作成」として扱われ、実際には存在するリソースを新規作成しようとして失敗する(例: `cloudflare_record.root` で発生した `expected DNS record to not already be present but already exists`)

### 暫定対応

`allow_overwrite` を持つリソース(`cloudflare_record` など)には `allow_overwrite = true` を設定し、
既存リソースがあってもエラーにせず上書きする形で回避している(`dns.tf` 参照)。

この対応はこの制約そのものを解決するものではない。`allow_overwrite` を持たないリソースを
今後追加した場合は同じ問題が再発する。また `terraform destroy` はCI上では常に空stateに対して
実行されるため実質的に機能しない。

### 根本対応(未着手)

リモートbackend(Terraform Cloud、S3など)を導入し、ローカル・CIで同一のstateを参照する構成にする。
導入時は既存リソース(`cloudflare_zone_settings_override.ankardo`, `cloudflare_record.root`)を
`terraform import` で新backendのstateに取り込む必要がある。
