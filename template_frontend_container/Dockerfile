# Dockerfile for Frontend (React)
# ファイル名: frontend/Dockerfile

# ベースイメージとしてNode.jsを使用
FROM node:22

# 作業ディレクトリを設定
WORKDIR /app


# プロジェクトのソースコード全体をコピー
COPY . .

# 作業ディレクトリを作成済みのReactRouterプロジェクトに変更して、依存関係をインストール
WORKDIR /app/template_react-router
RUN npm install

# デフォルトのCMDをbashにしておく（デバッグや後の変更用）
# CMD ["bash"]

