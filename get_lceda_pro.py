import datetime
import shutil
import requests
from lxml import etree
import os
from tqdm import tqdm  # 进度条库
import re

# 定义下载页面的URL
url = "https://lceda.cn/page/download"

# 发送HTTP请求获取页面内容
response = requests.get(url)
if response.status_code != 200:
    print("无法访问下载页面，请检查网络或URL是否正确。")
    exit()

# 解析HTML内容
html_content = response.content
tree = etree.HTML(html_content)

# 查找所有符合条件的下载链接
nodes = tree.xpath("/html/body//a[@class='downloadLink']")

# 筛选出Linux版本的下载链接
linux_pro_links = []
for node in nodes:
    href = node.attrib.get('href', '')
    text = node.text.strip() if node.text else ''
    if 'lceda-pro-linux' in text and 'x64' in text:
        linux_pro_links.append((text, href))

# 如果没有找到任何链接，退出脚本
if not linux_pro_links:
    print("未找到任何lceda pro linux版本的下载链接。")
    exit()

# 提取版本号（假设版本号格式为数字）
latest_version = None
latest_link = None
for link_info in linux_pro_links:
    text, href = link_info
    # 使用正则表达式提取版本号
    version_pattern = r"(\d+(\.\d+)+)"  # 匹配一个或多个数字及小数点的组合
    match = re.search(version_pattern, text)

    if match:
        version = match.group(0)  # 获取匹配到的版本号
        print(f"提取的版本号是: {version}")

        if latest_version is None or version > latest_version:
            latest_version = version
            latest_link = href
    else:
        print("未找到版本号")

# 如果没有找到有效的版本号，退出脚本
if latest_link is None:
    print("无法确定最新版本的下载链接。")
    exit()
else:
    print(f"最新版本的lceda pro linux下载链接为: {latest_link}")
    print(f"最新版本为: {latest_version}")

# 新建tmp
if not os.path.exists("tmp"):
    os.mkdir("tmp")
else:
    # Delete and recreate the tmp directory
    for filename in os.listdir("tmp"):
        file_path = os.path.join("tmp", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

# 下载文件
print(f"最新版本的lceda pro linux下载链接为: {latest_link}")
file_name = "tmp/" + latest_link.split('/')[-1]
print(f"正在下载文件: {file_name}")

# 下载文件并输出下载进度

response = requests.get(latest_link, stream=True)
if response.status_code == 200:
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 8192  # 设置块大小
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:  # 确保chunk不是空的
                progress_bar.update(len(chunk))  # 更新进度条
                f.write(chunk)
    progress_bar.close()  # 关闭进度条

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("下载过程中出现错误，文件可能不完整。")
    else:
        print(f"文件 {file_name} 已成功下载。")
else:
    print(f"下载失败，状态码: {response.status_code}")

# 自动解压文件，利用unzip命令,解压到 lceda-pro 目录下
print(f"正在解压文件: {file_name}")
os.system(f"unzip -o {file_name} -d tmp/lceda-pro")
print(f"文件 {file_name} 已成功解压到 lceda-pro 目录下。")


"""
Generate a debian changelog in following form
lceda-pro (2.2.36.5-1) UNRELEASED; urgency=medium

  * Update from official release.

 -- Auto CI Pack <autoci@pack-using-github-ci.example.com>  Sun, 23 Feb 2025 10:48:22 +0800
"""
# Generate changelog
#mkdir tmp/lceda-pro/DEBIAN/
os.system("mkdir -p tmp/lceda-pro/DEBIAN/")
with open("tmp/lceda-pro/DEBIAN/changelog", "w") as f:
    f.write(f"lceda-pro ({latest_version}-1) UNRELEASED; urgency=medium\n\n")
    f.write(f"  * Update from official release.\n\n")
    # Get date for changelog
    f.write(f" -- Auto CI Pack <autoci@pack-using-github-ci.example.com>  {datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')}\n")

# move to debian directory
os.system("mv -f tmp/lceda-pro/DEBIAN/changelog debian/")

# build deb package
os.system("dpkg-buildpackage -us -uc -b -tc")

# Move the package to the output directory
os.system("mkdir -p output/")
os.system("mv -f ../lceda-pro_*_amd64.deb output/")

# Clean up
os.system("rm -rf tmp")
os.system("rm -rf debian/changelog")