"""
pytest 配置文件

自动加载环境变量和配置
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 加载 .env 文件
def load_env_file():
    """加载 .env 文件到环境变量"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')

    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 设置环境变量（如果还没设置）
                    if key not in os.environ:
                        os.environ[key] = value

# 在 pytest 启动时加载
load_env_file()

# 禁用代理（避免干扰 API 调用）
for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
                   'all_proxy', 'ALL_PROXY']:
    if proxy_var in os.environ:
        del os.environ[proxy_var]
