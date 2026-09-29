#!/bin/bash
REPO_NAME=$1
GITHUB_TOKEN=$2

if [ -z "$REPO_NAME" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "用法: bash upload_to_github.sh <repo_name> <github_token>"
    echo "获取 Token: https://github.com/settings/tokens (需要 repo 权限)"
    exit 1
fi

echo "🚀 正在初始化 Git 并推送到 GitHub..."
git init
git add .
git commit -m "Initial commit: AI Book Classifier"
git branch -M main

# 使用 GitHub API 创建远程仓库
echo "📦 正在创建 GitHub 仓库: $REPO_NAME"
curl -H "Authorization: token $GITHUB_TOKEN" -d "{\"name\":\"$REPO_NAME\", \"private\":false}" https://api.github.com/user/repos

# 添加 remote 并 push
git remote add origin https://$GITHUB_TOKEN@github.com/$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep login | cut -d '"' -f 4)/$REPO_NAME.git
git push -u origin main

echo "✅ 上传完成！请访问: https://github.com/$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep login | cut -d '"' -f 4)/$REPO_NAME"
