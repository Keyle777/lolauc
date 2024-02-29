# 弟弟想隐身玩游戏给他做的

import psutil
import re
import requests
import ctypes
import json
import os
import re
import time
import webbrowser
import requests
import subprocess
import sys
import threading
import tkinter as tk

# 以下代码可避免requests模块运行时报错
requests.packages.urllib3.disable_warnings()
requests.DEFAULT_RETRIES = 1000

# 设置变量区
LCU_API = {
    "current_summoner": "/lol-summoner/v1/current-summoner",
    "game_session": "/lol-gameflow/v1/session",
    "chat_me": "/lol-chat/v1/me"
}
CMD_CHECK_LOL_PROCESS = 'wmic process where name="LeagueClientUx.exe" get processid,executablepath,name'

# LCU API 相关操作封装到类中
class Lcuapi:
    def __init__(self):
        self.requests_session = requests.Session()

    # 查找LCU API的端口和Token
    def find_lcu_prot_and_token(self):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == "LeagueClientUx.exe" and proc.info['cmdline']:
                    cmdline = " ".join(proc.info['cmdline'])
                    # 使用正则表达式提取参数值
                    token_match = re.search(r"--remoting-auth-token=([^\s]+)", cmdline)
                    port_match = re.search(r"--app-port=(\d+)", cmdline)

                    # 获取提取的参数值
                    if token_match and port_match:
                        token = token_match.group(1)
                        port = port_match.group(1)
                        return port, token
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        return None, None
    
    def _send_api_request(self, api, lol_PT, method="GET", data=None):
        port, token = lol_PT
        url = f"https://riot:{token}@127.0.0.1:{port}{api}"
        response = None
        try:
            if method == "GET":
                response = self.requests_session.get(url, verify=False)
            elif method == "PUT":
                response = self.requests_session.put(url, json=data, verify=False)
            if response:
                response.raise_for_status()
                return response.json()
            else:
                print(f"Failed to send {method} request to {url}")
        except Exception as e:
            print(f"发送 {method} 请求到 {url} 时发生错误：{e}")
        return None

    def check_lol_process(self):
        res = subprocess.Popen(CMD_CHECK_LOL_PROCESS,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        res.wait()  
        temp = res.communicate()  
        temp = re.findall('LeagueClientUx.exe', str(temp))
        time.sleep(1)
        return bool(temp)

    def get_current_summoner_info(self, lol_PT):
        return self._send_api_request(LCU_API["current_summoner"], lol_PT)

    def get_game_session_info(self, lol_PT):
        return self._send_api_request(LCU_API["game_session"], lol_PT)

    def get_chat_me_info(self, lol_PT):
        return self._send_api_request(LCU_API["chat_me"], lol_PT)

    def set_chat_me_status(self, lol_PT, status):
        data = {"availability": status}
        return self._send_api_request(LCU_API["chat_me"], lol_PT, method="PUT", data=data)


def main():
    # 创建 Lcuapi 实例
    lcu = Lcuapi()
    
    # 检查是否存在 LOL 进程
    if lcu.check_lol_process():
        # 获取 LCU 的端口和令牌
        lol_PT = lcu.find_lcu_prot_and_token()

        # 获取当前召唤师信息
        current_summoner_info = lcu.get_current_summoner_info(lol_PT)
        
        # 获取游戏会话信息
        game_session_info = lcu.get_game_session_info(lol_PT)
        
        # 获取聊天个人信息
        chat_me_info = lcu.get_chat_me_info(lol_PT)

        # 解析并打印当前召唤师信息
        if current_summoner_info:
            summoner_name = current_summoner_info.get('displayName', 'N/A')
            summoner_level = current_summoner_info.get('summonerLevel', 'N/A')
            puuid = current_summoner_info.get('puuid', 'N/A')
            account_id = current_summoner_info.get('accountId', 'N/A')
            print(f"召唤师名称： {summoner_name}\n"
                  f"召唤师等级： {summoner_level}\n"
                  f"当前PUUID: {puuid}\n"
                  f"当前AccountID: {account_id}")

        # 解析并打印游戏会话信息
        if game_session_info:
            map_name = game_session_info.get("map", {}).get("gameModeName", "N/A")
            print(f"游戏地图：{map_name}")

        # 解析并打印聊天个人信息
        if chat_me_info:
            availability = chat_me_info.get("availability", "N/A")
            print(f"召唤师当前在线状态：{availability}")

            # 修改召唤师状态为隐身
            new_status = "invisible"
            lcu.set_chat_me_status(lol_PT, new_status)
            print(f"召唤师修改后的状态：{new_status}")

    else:
        print("未检测到游戏进程")

if __name__ == "__main__":
    main()
