import tkinter as tk
from tkinter import scrolledtext
import threading
import datetime
from lolacu import Lcuapi 

class LolApp:
    def __init__(self, master):
        self.master = master
        master.title("League of Legends 数据查询")

        self.label = tk.Label(master, text="输入召唤师名称:")
        self.label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.entry = tk.Entry(master, width=30)
        self.entry.grid(row=0, column=1, padx=10, pady=5)

        self.button = tk.Button(master, text="查询", command=self.query)
        self.button.grid(row=0, column=2, padx=10, pady=5)

        self.result_text = scrolledtext.ScrolledText(master, width=60, height=20)
        self.result_text.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # 设置标签的颜色
        self.result_text.tag_config("win", foreground="#32CD32")
        self.result_text.tag_config("lose", foreground="#FF6347")

        # 配置网格布局使文本框随窗口大小变化而自适应
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)

        # 绑定窗口大小变化事件
        master.bind("<Configure>", self.adjust_font_size)

        # 初始字体大小
        self.font_size = 12

    def query(self):
        self.result_text.delete(1.0, tk.END)  # 清空文本框
        summoner_name = self.entry.get()  # 获取输入的召唤师名称
        # 创建 Lcuapi 实例
        lcu = Lcuapi()
        
        # 查询数据的函数
        def query_data():
            # 获取 LCU 的端口和令牌
            lol_PT = lcu.find_lcu_prot_and_token()
            # 检查是否成功获取了端口和令牌，如果没有，则显示相应的消息
            if lol_PT is None:
                self.result_text.insert(tk.END, "未能获取到端口和令牌，请确保游戏客户端已启动并登录。\n")
                return
            
            # 获取召唤师匹配历史
            match_history = lcu.get_match_history(lol_PT, summoner_name)
            # 检查是否成功获取了匹配历史，如果没有，则显示相应的消息
            if match_history is None:
                self.result_text.insert(tk.END, f"未能获取到召唤师 {summoner_name} 的匹配历史。\n")
                return
            
            for i in match_history['games']['games']:
                start_time = datetime.datetime.strptime(i['gameCreationDate'][:19],
                                                        '%Y-%m-%dT%H:%M:%S')
                start_time = start_time + datetime.timedelta(hours=8)
                start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                champion_name = lcu.get_grid_champions(lol_PT, data=i)
                champion_name = champion_name['name']
                # 根据胜负添加颜色
                tag = "win" if i['participants'][0]['stats']['win'] else "lose"
                self.result_text.insert(tk.END, start_time + " ", "normal")
                self.result_text.insert(tk.END, "败 " if not i['participants'][0]['stats']['win'] else "胜 ", tag)
                self.result_text.insert(tk.END, f"[{champion_name}] {i['participants'][0]['stats']['kills']}-"
                                                    f"{i['participants'][0]['stats']['deaths']}-"
                                                    f"{i['participants'][0]['stats']['assists']} {i['gameMode']}\n", "normal")
        
        # 使用线程来执行查询，避免在主线程中阻塞界面
        query_thread = threading.Thread(target=query_data)
        query_thread.start()

    def adjust_font_size(self, event):
        # 获取当前窗口高度
        height = self.master.winfo_height()
        # 根据窗口高度动态调整字体大小
        self.font_size = max(12, height // 40)
        self.result_text.configure(font=("Courier New", self.font_size))

root = tk.Tk()
app = LolApp(root)
root.mainloop()
