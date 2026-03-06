# Nginx 反向代理

FROM nginx:alpine

# 复制配置
COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
