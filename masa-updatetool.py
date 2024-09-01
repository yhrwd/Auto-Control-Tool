import os
import requests
import sys
import yaml
from datetime import datetime
from tqdm import tqdm

# 获取用户桌面路径
desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

# 定义masa-update文件夹路径
masa_update_dir = os.path.join(desktop_dir, "masa-update")

# 确保masa-update文件夹存在
if not os.path.exists(masa_update_dir):
    os.makedirs(masa_update_dir)

# 配置文件路径
config_file = os.path.join(masa_update_dir, "config.yaml")

# 定义默认配置
default_config = {
    "root_dir": masa_update_dir,
    "version_file": os.path.join(masa_update_dir, "repos_versions.yaml"),
    "download_folder": os.path.join(masa_update_dir, "download"),
    "token": "",
    "repos": [
        "sakura-ryoko/litematica", 
        "sakura-ryoko/minihud", 
        "sakura-ryoko/tweakeroo", 
        "sakura-ryoko/syncmatica", 
        "sakura-ryoko/itemscroller", 
        "sakura-ryoko/litematica-printer"
    ],
    "timeout": 10
}

# 配置文件注释
config_comments = f"""# GitHub访问令牌，用于API认证
# 将你的个人访问令牌放在这里。你可以在 https://github.com/settings/tokens 创建一个。
# 注意：请不要将令牌分享给其他人。
# 示例: token: "your_github_token"

# 要监控的GitHub仓库列表
# 在这里添加你想要监控的GitHub仓库，每个仓库使用 "用户名/仓库名" 的格式。
# 示例: repos: ["用户名/仓库名", "another_user/another_repo"]

# 请求超时时间（以秒为单位）
# 设置HTTP请求的超时时间，单位是秒。建议设置为一个合理的值，以避免长时间的等待。
# 示例: timeout: 10

# 各种路径配置
# 项目根目录: {masa_update_dir}
# 版本信息文件路径: {default_config['version_file']}
# 下载文件夹路径: {default_config['download_folder']}
"""

def load_config():
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"读取配置文件时发生错误: {e}")
            choice = input("是否重新生成默认配置文件？(y/n): ")
            if choice.lower() == 'y':
                create_default_config()
                return default_config
            else:
                print("请检查配置文件格式是否正确。")
                sys.exit(1)
    else:
        # 如果配置文件不存在，创建默认配置文件
        create_default_config()
        return default_config

def create_default_config():
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_comments)
        yaml.safe_dump(default_config, f, allow_unicode=True)
    print(f"已生成默认配置文件: {config_file}")

def save_config(config):
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_comments)
        yaml.safe_dump(config, f, allow_unicode=True)

def get_token(config):
    token = config.get("token", "")
    if not token:
        print("请输入GitHub访问令牌。")
        token = input()
        if not token:
            print("请正确输入令牌。")
            sys.exit()
        config["token"] = token
        save_config(config)
    return token

def get_latest_release(repo, token, timeout):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # 检查请求是否成功
        release_info = response.json()
        latest_release = release_info["tag_name"]
        release_time = datetime.strptime(release_info["published_at"], "%Y-%m-%dT%H:%M:%SZ")
        download_url = release_info["assets"][0]["browser_download_url"]
        file_name = download_url.split("/")[-1]
        return latest_release, release_time, file_name
    except requests.RequestException as e:
        print(f"请求失败：{e}")
        return None, None, None

def load_version_info(config):
    version_file = config.get("version_file", "")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return {}

def save_version_info(config, version_info):
    version_file = config.get("version_file", "")
    with open(version_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(version_info, f)

def check_local_version(config, repo):
    version_info = load_version_info(config)
    
    if repo in version_info:
        local_version = version_info[repo]["version"]
        local_time = datetime.strptime(version_info[repo]["time"], "%Y-%m-%d %H:%M:%S.%f")
    else:
        local_version = "0.0.0"
        local_time = datetime.now()
        create_local_version_file(config, repo, local_version, local_time)
        
    return local_version, local_time

def create_local_version_file(config, repo, version, time=None):
    version_info = load_version_info(config)
    version_info[repo] = {
        "version": version,
        "time": (time or datetime.now()).strftime("%Y-%m-%d %H:%M:%S.%f")
    }
    save_version_info(config, version_info)

def download_latest_release(config, repo, token, file_name, timeout):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # 检查请求是否成功
        release_info = response.json()
        download_url = release_info["assets"][0]["browser_download_url"]

        download_folder = config.get("download_folder", "")
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        file_path = os.path.join(download_folder, file_name)

        # 下载文件并显示进度条
        with requests.get(download_url, headers=headers, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(file_path, "wb") as f, tqdm(
                total=total_size, unit='B', unit_scale=True, desc=file_name, ncols=100
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        print(f"{repo}的最新版本已下载。")
    except requests.RequestException as e:
        print(f"下载失败：{e}")

def delete_old_file(config, file_name):
    download_folder = config.get("download_folder", "")
    file_path = os.path.join(download_folder, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"{file_name} 已删除。")

# 加载配置
config = load_config()

# 获取 GitHub 令牌
token = get_token(config)

# 获取仓库列表和超时时间
repos = config.get("repos", [])
timeout = config.get("timeout", 10)

updates = []

# 检查所有仓库
for repo in repos:
    latest_release, release_time, file_name = get_latest_release(repo, token, timeout)
    if latest_release:
        print(f"{repo}的最新版本是{latest_release}，发布时间是{release_time}")
        local_version, local_time = check_local_version(config, repo)
        if local_version != latest_release or local_time < release_time:
            updates.append((repo, file_name, latest_release))
        else:
            print(f"{repo}已经是最新版本。")
    else:
        print(f"无法获取{repo}的最新版本")

# 统一确认是否下载
if updates:
    print("\n以下仓库有新版本可用：")
    for i, (repo, file_name, latest_release) in enumerate(updates, start=1):
        print(f"{i}. {repo} 最新版本：{latest_release}")

    choice = input("\n是否下载所有这些仓库的最新版本？(y/n): ")
    if choice.lower() == "y":
        for repo, file_name, latest_release in updates:
            delete_old_file(config, file_name)
            download_latest_release(config, repo, token, file_name, timeout)
            create_local_version_file(config, repo, latest_release)
    else:
        print("已取消下载。")
else:
    print("所有仓库都是最新版本。")
