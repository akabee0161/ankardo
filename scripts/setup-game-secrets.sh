#!/usr/bin/env bash
# 新しいゲームリポジトリに、Cloudflareデプロイ用のGitHub Secretsを設定する。
# Usage: CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... ./scripts/setup-game-secrets.sh <owner/repo>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... $0 <owner/repo>" >&2
  exit 1
fi

repo="$1"

: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN environment variable is not set}"
: "${CLOUDFLARE_ACCOUNT_ID:?CLOUDFLARE_ACCOUNT_ID environment variable is not set}"

gh secret set CLOUDFLARE_API_TOKEN --repo "$repo" --body "$CLOUDFLARE_API_TOKEN"
gh secret set CLOUDFLARE_ACCOUNT_ID --repo "$repo" --body "$CLOUDFLARE_ACCOUNT_ID"

echo "Secrets configured for $repo"
