# -*- coding: utf-8 -*-
"""
webAI.py  ——  web 操作模拟系统 · 图形化版本
=================================================
在 web.py（全程手搓的终端版）基础上，重新设计的一个简洁、好看的桌面交互界面。

功能：
    1. 🎫 车票查询  —— 输入任意出发地 / 目的地 / 日期，自动解析车站电报码，
                       借助 Edge 取得登录态后调用 12306 接口拉取余票，结果写入 tickets.csv
    2. 📜 名言采集  —— 抓取 quotes.toscrape.com 的名人名言（支持多页），写入 quotes.csv

设计要点：
    · 纯标准库 tkinter，无需额外安装 UI 框架
    · 深色现代主题 + 侧边导航 + 卡片式表格
    · 所有网络请求都在后台线程执行，界面永不卡死

依赖：requests、beautifulsoup4、selenium（与 web.py 一致）
"""

import os
import csv
import time
import queue
import threading
import datetime
import tkinter as tk
from tkinter import ttk

import requests
from bs4 import BeautifulSoup

# 12306 用的是自签证书 + verify=False，屏蔽烦人的告警
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass


# ──────────────────────────────────────────────────────────────────────────
#  主题配色 & 字体
# ──────────────────────────────────────────────────────────────────────────
BG_MAIN     = "#0f1117"   # 主背景
BG_SIDEBAR  = "#161a24"   # 侧边栏
BG_ACTIVE   = "#1f2535"   # 选中项背景
BG_CARD     = "#171b27"   # 卡片 / 表格背景
BG_INPUT    = "#1d2230"   # 输入框背景
BORDER      = "#2a3142"   # 描边
TEXT        = "#e7eaf3"   # 主文字
TEXT_DIM    = "#8b93a7"   # 次级文字
TEXT_FAINT  = "#5a6175"   # 更淡的文字

ACCENT      = "#5b8cff"   # 主强调色（蓝）
ACCENT_HV   = "#7aa0ff"   # 强调色 hover
GREEN       = "#34d399"   # 成功 / 绿
GREEN_HV    = "#54e0ac"
AMBER       = "#fbbf24"   # 名言模块强调色
AMBER_HV    = "#fcd34d"
RED         = "#f87171"   # 错误
ROW_ODD     = "#171b27"
ROW_EVEN    = "#1b2030"

FONT   = "Microsoft YaHei UI"   # 中文好看
FONT_M = "Consolas"             # 等宽（车次 / 时间）

QUOTES_URL = "https://quotes.toscrape.com"
INIT_URL   = "https://kyfw.12306.cn/otn/leftTicket/init"
QUERY_API  = "https://kyfw.12306.cn/otn/leftTicket/query"
STATION_JS = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"

# 网络取不到车站表时的兜底（主要城市），保证最常用线路也能查
FALLBACK_STATIONS = {
    "北京": "BJP", "上海": "SHH", "广州": "GZQ", "深圳": "SZQ", "杭州": "HZH",
    "南京": "NJH", "成都": "CDW", "重庆": "CQW", "武汉": "WHN", "西安": "XAY",
    "天津": "TJP", "长沙": "CSQ", "郑州": "ZZF", "沈阳": "SYT", "哈尔滨": "HBB",
    "济南": "JNK", "青岛": "QDK", "苏州": "SZH", "厦门": "XMS", "昆明": "KMM",
    "南宁": "NNZ", "合肥": "HFH", "福州": "FZS", "南昌": "NCG", "贵阳": "GIW",
    "兰州": "LZJ", "太原": "TYV", "石家庄": "SJP", "长春": "CCT", "大连": "DLT",
}


class WebAIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.busy = False                # 是否有任务在跑（防重复点击）
        self.station_map = None          # 名称 -> 电报码
        self.ui_queue = queue.Queue()    # 后台线程 -> 主线程 的回调队列
        self.pages = {}                  # 页面 key -> frame
        self.nav_items = {}              # 导航项引用

        self._setup_window()
        self._setup_style()
        self._build_layout()
        self._build_quotes_page()
        self._build_tickets_page()
        self.select_page("tickets")

        self.root.after(60, self._pump)  # 启动 UI 队列轮询

    # ── 窗口 ───────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("web 操作模拟系统 · AI 图形版")
        self.root.configure(bg=BG_MAIN)
        w, h = 1000, 680
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2 - 20}")
        self.root.minsize(900, 600)

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Treeview（表格）
        style.configure(
            "AI.Treeview",
            background=BG_CARD, fieldbackground=BG_CARD, foreground=TEXT,
            bordercolor=BG_CARD, borderwidth=0, rowheight=32, font=(FONT, 10),
        )
        style.configure(
            "AI.Treeview.Heading",
            background=BG_SIDEBAR, foreground=ACCENT, font=(FONT, 10, "bold"),
            relief="flat", borderwidth=0, padding=(6, 8),
        )
        style.map("AI.Treeview.Heading", background=[("active", BG_ACTIVE)])
        style.map(
            "AI.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")],
        )
        # 滚动条
        style.configure(
            "AI.Vertical.TScrollbar",
            background=BG_ACTIVE, troughcolor=BG_MAIN, bordercolor=BG_MAIN,
            arrowcolor=TEXT_DIM, relief="flat",
        )
        style.configure(
            "AI.Horizontal.TScrollbar",
            background=BG_ACTIVE, troughcolor=BG_MAIN, bordercolor=BG_MAIN,
            arrowcolor=TEXT_DIM, relief="flat",
        )

    # ── 整体布局：顶部色条 + 侧边栏 + 内容区 ────────────────────────────────
    def _build_layout(self):
        tk.Frame(self.root, bg=ACCENT, height=3).pack(side="top", fill="x")

        body = tk.Frame(self.root, bg=BG_MAIN)
        body.pack(side="top", fill="both", expand=True)

        # 侧边栏
        sidebar = tk.Frame(body, bg=BG_SIDEBAR, width=216)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # logo
        logo = tk.Frame(sidebar, bg=BG_SIDEBAR)
        logo.pack(side="top", fill="x", pady=(26, 8), padx=20)
        tk.Label(logo, text="◆  WebAI", bg=BG_SIDEBAR, fg=TEXT,
                 font=(FONT, 16, "bold")).pack(anchor="w")
        tk.Label(logo, text="web 操作模拟系统", bg=BG_SIDEBAR, fg=TEXT_FAINT,
                 font=(FONT, 9)).pack(anchor="w", pady=(2, 0))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(14, 10))

        self._add_nav(sidebar, "tickets", "🎫", "车票查询", ACCENT)
        self._add_nav(sidebar, "quotes", "📜", "名言采集", AMBER)

        # 侧边栏底部署名
        tk.Label(sidebar, text="基于手搓版 web.py 重构\nby Lycoris × Claude",
                 bg=BG_SIDEBAR, fg=TEXT_FAINT, font=(FONT, 8), justify="left"
                 ).pack(side="bottom", anchor="w", padx=20, pady=18)

        # 内容容器
        self.content = tk.Frame(body, bg=BG_MAIN)
        self.content.pack(side="left", fill="both", expand=True)

    def _add_nav(self, parent, key, icon, text, color):
        row = tk.Frame(parent, bg=BG_SIDEBAR, cursor="hand2")
        row.pack(side="top", fill="x", padx=12, pady=2)

        bar = tk.Frame(row, bg=BG_SIDEBAR, width=3)
        bar.pack(side="left", fill="y")

        inner = tk.Frame(row, bg=BG_SIDEBAR)
        inner.pack(side="left", fill="x", expand=True)
        lbl = tk.Label(inner, text=f"  {icon}   {text}", bg=BG_SIDEBAR, fg=TEXT_DIM,
                       font=(FONT, 12), anchor="w", padx=8, pady=11)
        lbl.pack(fill="x")

        self.nav_items[key] = {"row": row, "bar": bar, "inner": inner,
                               "lbl": lbl, "color": color}

        for widget in (row, inner, lbl, bar):
            widget.bind("<Button-1>", lambda e, k=key: self.select_page(k))
            widget.bind("<Enter>", lambda e, k=key: self._nav_hover(k, True))
            widget.bind("<Leave>", lambda e, k=key: self._nav_hover(k, False))

    def _nav_hover(self, key, entering):
        item = self.nav_items[key]
        if self._active_page == key:
            return
        bg = BG_ACTIVE if entering else BG_SIDEBAR
        for w in (item["row"], item["inner"], item["lbl"]):
            w.config(bg=bg)

    _active_page = None

    def select_page(self, key):
        self._active_page = key
        for k, item in self.nav_items.items():
            active = (k == key)
            bg = BG_ACTIVE if active else BG_SIDEBAR
            item["bar"].config(bg=item["color"] if active else BG_SIDEBAR)
            for w in (item["row"], item["inner"], item["lbl"]):
                w.config(bg=bg)
            item["lbl"].config(fg=TEXT if active else TEXT_DIM,
                               font=(FONT, 12, "bold" if active else "normal"))

        for k, frame in self.pages.items():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

    # ── 通用小部件工厂 ──────────────────────────────────────────────────────
    def _header(self, parent, title, subtitle, color):
        head = tk.Frame(parent, bg=BG_MAIN)
        head.pack(side="top", fill="x", padx=30, pady=(26, 16))
        tk.Label(head, text=title, bg=BG_MAIN, fg=TEXT,
                 font=(FONT, 20, "bold")).pack(anchor="w")
        tk.Label(head, text=subtitle, bg=BG_MAIN, fg=TEXT_DIM,
                 font=(FONT, 10)).pack(anchor="w", pady=(4, 0))
        tk.Frame(head, bg=color, height=3, width=46).pack(anchor="w", pady=(12, 0))
        return head

    def _entry(self, parent, width=12, justify="left"):
        wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        e = tk.Entry(wrap, width=width, bg=BG_INPUT, fg=TEXT, font=(FONT, 12),
                     relief="flat", insertbackground=ACCENT, justify=justify,
                     disabledbackground=BG_INPUT, disabledforeground=TEXT_FAINT)
        e.pack(ipady=7, ipadx=8)
        e.bind("<FocusIn>",  lambda ev: wrap.config(bg=ACCENT))
        e.bind("<FocusOut>", lambda ev: wrap.config(bg=BORDER))
        return wrap, e

    def _button(self, parent, text, command, bg, hover, fg="#0d1018"):
        b = tk.Label(parent, text=text, bg=bg, fg=fg, font=(FONT, 11, "bold"),
                     padx=22, pady=9, cursor="hand2")
        b._bg, b._hv = bg, hover
        b.bind("<Button-1>", lambda e: command())
        b.bind("<Enter>", lambda e: b.config(bg=b._hv) if b["state"] != "disabled" else None)
        b.bind("<Leave>", lambda e: b.config(bg=b._bg))
        return b

    def _make_table(self, parent, columns, widths, anchors=None):
        wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        wrap.pack(side="top", fill="both", expand=True, padx=30, pady=(4, 6))

        inner = tk.Frame(wrap, bg=BG_CARD)
        inner.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(inner, orient="vertical", style="AI.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(inner, orient="horizontal", style="AI.Horizontal.TScrollbar")
        tree = ttk.Treeview(inner, columns=columns, show="headings",
                            style="AI.Treeview", yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        anchors = anchors or {}
        for col, wdt in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=wdt, anchor=anchors.get(col, "center"),
                        stretch=False)

        tree.tag_configure("odd", background=ROW_ODD, foreground=TEXT)
        tree.tag_configure("even", background=ROW_EVEN, foreground=TEXT)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def _status_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_MAIN)
        bar.pack(side="bottom", fill="x", padx=30, pady=(0, 18))
        dot = tk.Label(bar, text="●", bg=BG_MAIN, fg=TEXT_FAINT, font=(FONT, 9))
        dot.pack(side="left")
        lbl = tk.Label(bar, text="就绪", bg=BG_MAIN, fg=TEXT_DIM, font=(FONT, 10),
                       anchor="w")
        lbl.pack(side="left", padx=(8, 0))
        return {"dot": dot, "lbl": lbl}

    def _set_status(self, status, state, text, color):
        status["dot"].config(fg=color)
        status["lbl"].config(text=text, fg=TEXT if color != TEXT_FAINT else TEXT_DIM)

    # ── 名言采集页 ──────────────────────────────────────────────────────────
    def _build_quotes_page(self):
        page = tk.Frame(self.content, bg=BG_MAIN)
        self.pages["quotes"] = page

        self._header(page, "名言数据采集",
                     "抓取 quotes.toscrape.com 的名人名言，自动写入 quotes.csv", AMBER)

        ctrl = tk.Frame(page, bg=BG_MAIN)
        ctrl.pack(side="top", fill="x", padx=30, pady=(0, 6))

        tk.Label(ctrl, text="采集页数", bg=BG_MAIN, fg=TEXT_DIM,
                 font=(FONT, 11)).pack(side="left")
        self.q_pages = tk.IntVar(value=3)
        spin_wrap = tk.Frame(ctrl, bg=BORDER, padx=1, pady=1)
        spin_wrap.pack(side="left", padx=(10, 18))
        tk.Spinbox(spin_wrap, from_=1, to=10, width=5, textvariable=self.q_pages,
                   bg=BG_INPUT, fg=TEXT, font=(FONT, 12), relief="flat",
                   justify="center", buttonbackground=BG_ACTIVE,
                   insertbackground=ACCENT, readonlybackground=BG_INPUT,
                   highlightthickness=0).pack(ipady=5)

        self.q_btn = self._button(ctrl, "开始采集", self.start_quotes, AMBER, AMBER_HV)
        self.q_btn.pack(side="left")

        self.q_count = tk.Label(ctrl, text="", bg=BG_MAIN, fg=TEXT_DIM,
                                font=(FONT, 10))
        self.q_count.pack(side="right")

        self.q_tree = self._make_table(
            page,
            columns=("#", "作者", "名言", "标签"),
            widths=(48, 150, 540, 180),
            anchors={"#": "center", "作者": "w", "名言": "w", "标签": "w"},
        )

        self.q_status = self._status_bar(page)

    def start_quotes(self):
        if self.busy:
            return
        pages = max(1, min(10, self.q_pages.get()))
        self.busy = True
        self.q_btn.config(bg="#7a6420", state="disabled")
        for i in self.q_tree.get_children():
            self.q_tree.delete(i)
        self.q_count.config(text="")
        self._set_status(self.q_status, "running", "正在采集…", AMBER)
        threading.Thread(target=self._quotes_worker, args=(pages,), daemon=True).start()

    def _quotes_worker(self, pages):
        rows = []
        try:
            for p in range(1, pages + 1):
                url = QUOTES_URL if p == 1 else f"{QUOTES_URL}/page/{p}/"
                self.post(lambda p=p: self._set_status(
                    self.q_status, "running", f"正在抓取第 {p}/{pages} 页…", AMBER))
                resp = requests.get(url, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                quotes = soup.find_all("div", class_="quote")
                if not quotes:
                    break
                for q in quotes:
                    text = q.find("span", class_="text").get_text(strip=True)
                    author = q.find("small", class_="author").get_text(strip=True)
                    tags = [t.get_text(strip=True)
                            for t in q.find_all("a", class_="tag")]
                    row = {"作者": author, "名言": text, "标签": ", ".join(tags)}
                    rows.append(row)
                    idx = len(rows)
                    self.post(lambda r=row, i=idx: self._add_quote_row(i, r))
                time.sleep(0.25)

            # 写文件
            saved_path = ""
            if rows:
                saved_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "quotes.csv")
                with open(saved_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=["作者", "名言", "标签"])
                    writer.writeheader()
                    writer.writerows(rows)

            def done():
                self.busy = False
                self.q_btn.config(bg=AMBER, state="normal")
                self.q_count.config(text=f"共 {len(rows)} 条")
                if rows:
                    self._set_status(self.q_status, "ok",
                                     f"完成 · 共 {len(rows)} 条 · 已保存 quotes.csv", GREEN)
                else:
                    self._set_status(self.q_status, "err", "没有抓到数据", RED)
            self.post(done)

        except Exception as e:
            self.post(lambda e=e: self._quotes_error(str(e)))

    def _add_quote_row(self, idx, row):
        tag = "odd" if idx % 2 else "even"
        self.q_tree.insert("", "end", tags=(tag,),
                           values=(idx, row["作者"], row["名言"], row["标签"]))
        self.q_count.config(text=f"已采集 {idx} 条")

    def _quotes_error(self, msg):
        self.busy = False
        self.q_btn.config(bg=AMBER, state="normal")
        self._set_status(self.q_status, "err", f"出错：{msg}", RED)

    # ── 车票查询页 ──────────────────────────────────────────────────────────
    def _build_tickets_page(self):
        page = tk.Frame(self.content, bg=BG_MAIN)
        self.pages["tickets"] = page

        self._header(page, "车票查询",
                     "输入城市与日期，自动解析电报码并查询 12306 余票，结果写入 tickets.csv",
                     ACCENT)

        # 输入区
        ctrl = tk.Frame(page, bg=BG_MAIN)
        ctrl.pack(side="top", fill="x", padx=30, pady=(0, 4))

        def field(label, default, width=10):
            box = tk.Frame(ctrl, bg=BG_MAIN)
            box.pack(side="left", padx=(0, 14))
            tk.Label(box, text=label, bg=BG_MAIN, fg=TEXT_DIM,
                     font=(FONT, 9)).pack(anchor="w", pady=(0, 4))
            wrap, e = self._entry(box, width=width)
            wrap.pack(anchor="w")
            e.insert(0, default)
            return e

        self.t_from = field("出发地", "北京", 9)

        swap = tk.Label(ctrl, text="⇄", bg=BG_MAIN, fg=ACCENT,
                        font=(FONT, 15, "bold"), cursor="hand2")
        swap.pack(side="left", padx=(0, 14), pady=(16, 0))
        swap.bind("<Button-1>", lambda e: self._swap_stations())

        self.t_to = field("目的地", "上海", 9)

        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        self.t_date = field("出发日期 (YYYY-MM-DD)", tomorrow, 14)

        btn_box = tk.Frame(ctrl, bg=BG_MAIN)
        btn_box.pack(side="left", padx=(2, 0))
        tk.Label(btn_box, text="", bg=BG_MAIN, font=(FONT, 9)).pack(pady=(0, 4))
        self.t_btn = self._button(btn_box, "查询车票", self.start_tickets,
                                  ACCENT, ACCENT_HV, fg="#ffffff")
        self.t_btn.pack(anchor="w")

        # 选项
        opt = tk.Frame(page, bg=BG_MAIN)
        opt.pack(side="top", fill="x", padx=30, pady=(8, 4))
        self.t_headless = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            opt, text="后台静默取登录态（不弹出浏览器窗口）",
            variable=self.t_headless, bg=BG_MAIN, fg=TEXT_DIM,
            selectcolor=BG_INPUT, activebackground=BG_MAIN,
            activeforeground=TEXT, font=(FONT, 9), relief="flat",
            highlightthickness=0, cursor="hand2", bd=0,
        )
        chk.pack(side="left")
        tk.Label(opt, text="（首次查询需调起 Edge 获取 Cookie，请稍候）",
                 bg=BG_MAIN, fg=TEXT_FAINT, font=(FONT, 9)).pack(side="left", padx=(8, 0))

        cols = ("车次", "出发站", "到达站", "出发", "到达", "历时",
                "商务座", "一等座", "二等座", "硬卧", "硬座", "无座", "可订")
        widths = (66, 84, 84, 60, 60, 64, 62, 62, 62, 56, 56, 56, 48)
        self.t_tree = self._make_table(page, cols, widths)

        self.t_status = self._status_bar(page)

    def _swap_stations(self):
        a, b = self.t_from.get(), self.t_to.get()
        self.t_from.delete(0, "end"); self.t_from.insert(0, b)
        self.t_to.delete(0, "end"); self.t_to.insert(0, a)

    def start_tickets(self):
        if self.busy:
            return
        frm = self.t_from.get().strip()
        to = self.t_to.get().strip()
        date = self.t_date.get().strip()
        if not frm or not to or not date:
            self._set_status(self.t_status, "err", "请填写出发地、目的地和日期", RED)
            return

        self.busy = True
        self.t_btn.config(bg="#33415c", state="disabled")
        for i in self.t_tree.get_children():
            self.t_tree.delete(i)
        self._set_status(self.t_status, "running", "准备查询…", ACCENT)
        threading.Thread(target=self._tickets_worker,
                         args=(frm, to, date, self.t_headless.get()),
                         daemon=True).start()

    def _tickets_worker(self, frm_name, to_name, date, headless):
        try:
            # 1) 车站表
            self.post(lambda: self._set_status(
                self.t_status, "running", "加载车站电报码…", ACCENT))
            self._ensure_station_map()
            frm_code = self._resolve_station(frm_name)
            to_code = self._resolve_station(to_name)
            if not frm_code:
                return self.post(lambda: self._tickets_error(f"无法识别出发地：{frm_name}"))
            if not to_code:
                return self.post(lambda: self._tickets_error(f"无法识别目的地：{to_name}"))

            # 2) 调起 Edge，可视化地把出发地/目的地/日期填进去并点击查询
            cookies, ua = self._drive_browser(
                headless, frm_code, to_code, frm_name, to_name, date)

            # 3) 调接口
            self.post(lambda: self._set_status(
                self.t_status, "running", "向 12306 查询余票…", ACCENT))
            params = {
                "leftTicketDTO.train_date": date,
                "leftTicketDTO.from_station": frm_code,
                "leftTicketDTO.to_station": to_code,
                "purpose_codes": "ADULT",
            }
            headers = {"User-Agent": ua}
            resp = requests.get(QUERY_API, params=params, cookies=cookies,
                                headers=headers, verify=False, timeout=20)
            data = resp.json()
            result = (data.get("data") or {}).get("result") or []
            smap = (data.get("data") or {}).get("map") or {}

            rows = []
            for item in result:
                f = item.split("|")
                if len(f) < 33:
                    continue
                rows.append({
                    "车次": f[3],
                    "出发站": smap.get(f[4], f[4]),
                    "到达站": smap.get(f[5], f[5]),
                    "出发": f[8],
                    "到达": f[9],
                    "历时": f[10],
                    "商务座": f[32] or "--",
                    "一等座": f[31] or "--",
                    "二等座": f[30] or "--",
                    "硬卧": f[28] or "--",
                    "硬座": f[29] or "--",
                    "无座": f[26] or "--",
                    "可订": "是" if f[11] == "Y" else "否",
                })

            saved = ""
            if rows:
                saved = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "tickets.csv")
                with open(saved, "w", newline="", encoding="utf-8-sig") as fp:
                    writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)

            self.post(lambda: self._fill_tickets(rows, frm_name, to_name, date))

        except Exception as e:
            self.post(lambda e=e: self._tickets_error(str(e)))

    def _fill_tickets(self, rows, frm, to, date):
        cols = ("车次", "出发站", "到达站", "出发", "到达", "历时",
                "商务座", "一等座", "二等座", "硬卧", "硬座", "无座", "可订")
        for i, r in enumerate(rows, 1):
            tag = "odd" if i % 2 else "even"
            self.t_tree.insert("", "end", tags=(tag,),
                               values=tuple(r[c] for c in cols))
        self.busy = False
        self.t_btn.config(bg=ACCENT, state="normal")
        if rows:
            self._set_status(self.t_status, "ok",
                             f"{frm}→{to} {date} · 共 {len(rows)} 趟 · 已保存 tickets.csv",
                             GREEN)
        else:
            self._set_status(self.t_status, "warn",
                             "查询成功，但该线路当日没有返回车次（换个日期试试）", AMBER)

    def _tickets_error(self, msg):
        self.busy = False
        self.t_btn.config(bg=ACCENT, state="normal")
        self._set_status(self.t_status, "err", f"出错：{msg}", RED)

    # ── 12306 辅助 ──────────────────────────────────────────────────────────
    def _ensure_station_map(self):
        if self.station_map:
            return
        m = {}
        try:
            r = requests.get(STATION_JS, timeout=12, verify=False)
            body = r.text.split("'")[1]
            for rec in body.split("@"):
                if not rec:
                    continue
                p = rec.split("|")
                if len(p) >= 3 and p[1] and p[2]:
                    m[p[1]] = p[2]
        except Exception:
            pass
        if not m:                     # 网络失败 -> 兜底
            m = dict(FALLBACK_STATIONS)
        self.station_map = m

    def _resolve_station(self, name):
        if not self.station_map:
            return None
        name = name.strip()
        if name in self.station_map:                 # 完全匹配
            return self.station_map[name]
        for k, v in self.station_map.items():        # 前缀匹配：北京 -> 北京/北京南…
            if k.startswith(name):
                return v
        return FALLBACK_STATIONS.get(name)

    def _drive_browser(self, headless, frm_code, to_code, frm_name, to_name, date):
        """复用 web.py 的思路：可视化地用 Edge 打开查票页、注入站点与日期、点击查询，
        全程在浏览器里可见；最后顺便取回真实 Cookie 与 UA 给接口用。"""
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.common.by import By

        def step(text):
            self.post(lambda: self._set_status(self.t_status, "running", text, ACCENT))

        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        else:
            opts.add_argument("--start-maximized")
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-gpu")
        try:
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        except Exception:
            pass

        step("调起 Edge 浏览器…")
        driver = webdriver.Edge(options=opts)
        try:
            step("打开 12306 查票页…")
            driver.get(INIT_URL)
            time.sleep(2)

            step(f"① 填入出发地：{frm_name}")
            driver.execute_script(
                f"document.getElementById('fromStationText').value = '{frm_name}';")
            driver.execute_script(
                f"document.getElementById('fromStation').value = '{frm_code}';")
            time.sleep(0.9)

            step(f"② 填入目的地：{to_name}")
            driver.execute_script(
                f"document.getElementById('toStationText').value = '{to_name}';")
            driver.execute_script(
                f"document.getElementById('toStation').value = '{to_code}';")
            time.sleep(0.9)

            step(f"③ 填入出发日期：{date}")
            driver.execute_script(
                f"document.getElementById('train_date').value = '{date}';")
            time.sleep(0.9)

            step("④ 点击「查询」按钮…")
            try:
                driver.find_element(By.ID, "query_ticket").click()
            except Exception:
                pass
            time.sleep(1.5)

            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            ua = driver.execute_script("return navigator.userAgent;")

            if not headless:        # 让用户多看一会儿浏览器里的结果再关闭
                step("浏览器查询完成，正在抓取结构化数据…")
                time.sleep(2.5)
        finally:
            driver.quit()
        return cookies, ua

    # ── 线程 -> UI 队列 ─────────────────────────────────────────────────────
    def post(self, fn):
        self.ui_queue.put(fn)

    def _pump(self):
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.root.after(60, self._pump)


def main():
    root = tk.Tk()
    WebAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
