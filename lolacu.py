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
import datetime
import threading
import tkinter as tk

# 以下代码可避免requests模块运行时报错
requests.packages.urllib3.disable_warnings()
requests.DEFAULT_RETRIES = 1000

# 设置变量区
LCU_API = {
    "current_summoner": "/lol-summoner/v1/current-summoner",  # 获取当前召唤师信息的API路径
    "game_session": "/lol-gameflow/v1/session",  # 获取游戏会话信息的API路径
    "chat_me": "/lol-chat/v1/me",  # 获取聊天个人信息的API路径
    "match_history": "/lol-match-history/v1/products/lol",  # 获取召唤师匹配历史的API路径
    "summoner_names": "/lol-summoner/v2/summoners/names",  # 获取召唤师名称的API路径
    "grid_champions": "/lol-champ-select/v1/grid-champions",  # 获取英雄选择界面的API路径
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
        
    def _send_api_request(self, api, lol_PT, method="GET", params=None, data=None):
        port, token = lol_PT
        url = f"https://riot:{token}@127.0.0.1:{port}{api}"
        response = None
        try:
            if method == "GET":
                response = self.requests_session.get(url, params=params, verify=False)
            elif method == "PUT":
                response = self.requests_session.put(url, json=data, verify=False)
            elif method == "POST":
                response = self.requests_session.post(url, json=data, verify=False)
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
    
    def get_grid_champions(self, lol_PT, data):
        return self._send_api_request(LCU_API["grid_champions"]+ f"/{data['participants'][0]['championId']}", lol_PT)
    
    def get_match_history(self, lol_PT, name):
        data = [name]
        summoner = self._send_api_request(LCU_API["summoner_names"], lol_PT, method="POST", data=data)
        summoner = summoner[0]['puuid']
        return self._send_api_request(LCU_API["match_history"] + f"/{summoner}/matches", lol_PT)

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

        # 查询某英雄战绩
        name = '白夜天雨'  # 在这里修改名字，要登录一个同区的账号
        match_history = lcu.get_match_history(lol_PT, name)
        if match_history:
            for i in match_history['games']['games']:
                    start_time = datetime.datetime.strptime(i['gameCreationDate'][:19],
                                                            '%Y-%m-%dT%H:%M:%S')
                    start_time = start_time + datetime.timedelta(hours=8)
                    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    champion_name = lcu.get_grid_champions(lol_PT,data=i)
                    champion_name = champion_name['name']
                    print(start_time, ('\033[31m败\033[0m', '\033[34m胜\033[0m')[i['participants'][0]['stats']['win']],
                        '[' + champion_name + ']', str(i['participants'][0]['stats']['kills'])
                        + '-' + str(i['participants'][0]['stats']['deaths'])
                        + '-' + str(i['participants'][0]['stats']['assists']), i['gameMode'])

    else:
        print("未检测到游戏进程")

if __name__ == "__main__":
    main()
