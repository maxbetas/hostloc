#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hostloc论坛自动访问空间获取积分
环境变量：hostloc(账户&密码)
by：@shalulyq
"""

import os
import sys
import subprocess

def install_dependencies():
    print("正在安装依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "requests-toolbelt", "curl_cffi"])
    print("依赖安装完成")

try:
    import requests
    from bs4 import BeautifulSoup
    from curl_cffi import requests as requests_cffi
except ImportError:
    install_dependencies()
    import requests
    from bs4 import BeautifulSoup
    from curl_cffi import requests as requests_cffi

import re
import random
import time

try:
    from notify import send
except ImportError:
    print("通知服务加载失败，请检查notify.py是否存在")
    exit(1)

class HostlocAPI:
    def __init__(self):
        self.session = requests_cffi.Session()
        # 设置Chrome浏览器指纹
        self.session.impersonate = "chrome110"
        self.session.headers.update({
            'Host': 'hostloc.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Priority': 'u=0, i',
            'Sec-Ch-Ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_formhash(self):
        try:
            r = self.session.get('https://hostloc.com/', impersonate="chrome110")
            
            if r.status_code == 200:
                pattern = r'<input\s+type="hidden"\s+name="formhash"\s+value="([^"]+)"'
                match = re.search(pattern, r.text)
                if match:
                    formhash = match.group(1)
                 #   print(f"获取到formhash: {formhash}")
                    return formhash
            print("未找到formhash")
            return None
        except Exception as e:
            print(f"发生异常: {str(e)}")
            return None

    def login(self, username, password):
        formhash = self.get_formhash()
        if not formhash:
            return False, "获取formhash失败"
            
        data = {
            'fastloginfield': 'username',
            'username': username,
            'password': password,
            'formhash': formhash,
            'quickforward': 'yes',
            'handlekey': 'ls'
        }
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://hostloc.com',
            'referer': 'https://hostloc.com/'
        }
        
        try:
            r = self.session.post(
                'https://hostloc.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1',
                data=data,
                headers=headers,
                impersonate="chrome110"
            )
            if 'window.location.href' in r.text:
                return True, "登录成功"
            elif '登录失败' in r.text:
                return False, f"登录失败: {r.text}"
            else:
                return False, f"未知返回: {r.text}"
        except Exception as e:
            return False, f"登录异常: {str(e)}"

    def visit_space(self, uid):
        try:
            self.session.get(f'https://hostloc.com/home.php?mod=space&uid={uid}', impersonate="chrome110")
            return True
        except:
            return False

    def get_points(self):
        try:
            r = self.session.get('https://hostloc.com/home.php?mod=spacecp&ac=credit&showcredit=1', impersonate="chrome110")
            
            # 匹配金钱
            money_match = re.search(r'金钱: </em>(\d+)', r.text)
            money = money_match.group(1) if money_match else "获取失败"
            
            # 匹配威望
            prestige_match = re.search(r'威望: </em>(\d+)', r.text) 
            prestige = prestige_match.group(1) if prestige_match else "获取失败"
            
            # 匹配总积分
            points_match = re.search(r'<em>积分: </em>(\d+)', r.text)
            points = points_match.group(1) if points_match else "获取失败"
            
            return f"金钱:{money} 威望:{prestige} 总积分:{points}"
        except Exception as e:
            return f"获取积分失败: {str(e)}"

def process_account(account):
    try:
        username, password = account.split('&')
    except:
        return "\n账户格式错误"

    api = HostlocAPI()
    success, msg = api.login(username, password)
    result = f'\n【用户名】{username}\n【登录状态】{msg}'
    
    if not success:
        return result

    # 登录成功后执行积分操作
    # 随机生成10个不重复的uid
    uids = random.sample(range(1, 50000), 10)
    visited = 0
    
    for uid in uids:
        if api.visit_space(uid):
            visited += 1
        time.sleep(random.randint(1, 3))  # 随机延迟1-3秒

    points = api.get_points()
    
    result += f'\n【访问空间】{visited}/10\n【当前积分】{points}'
    return result

def main():
    creds = os.getenv("hostloc")
    if not creds:
        print("错误：未设置hostloc环境变量")
        return

    results = [process_account(acc) for acc in creds.split('#')]
    msg = "-"*45 + "\n".join(results)
    print("###Hostloc积分###\n\n", msg)
    send("Hostloc积分", msg)

if __name__ == '__main__':
    main() 