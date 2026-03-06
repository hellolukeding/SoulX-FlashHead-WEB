#!/bin/bash
# 创建 Docker 网络用于数字人平台服务

set -e

NETWORK_NAME="digital-human-network"

echo "==================================="
echo "  创建 Docker 网络"
echo "==================================="
echo ""

if docker network inspect ${NETWORK_NAME} &> /dev/null; then
    echo "✅ 网络已存在: ${NETWORK_NAME}"
    echo ""
    docker network inspect ${NETWORK_NAME} --format '{{json .}}' | python3 -m json.tool
else
    echo "创建网络: ${NETWORK_NAME}"
    docker network create ${NETWORK_NAME}
    echo "✅ 网络创建成功"
fi

echo ""
echo "网络中的容器:"
docker network inspect ${NETWORK_NAME} --format '{{range .Containers}}{{.Name}} {{end}}'
if [ -z "$(docker network inspect ${NETWORK_NAME} --format '{{range .Containers}}{{.Name}} {{end}}')" ]; then
    echo "  (暂无容器)"
fi
