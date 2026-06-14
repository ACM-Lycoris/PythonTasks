import requests
from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# 一阶段：爬虫试验
x = input("点击任意键启动")
print("第一部分：爬虫与写入文件试验")
print("请不要操作，我们会爬取url = https://quotes.toscrape.com上的名人名言数据")
url = "https://quotes.toscrape.com"
response = requests.get(url)

print("服务器状态：", response.status_code)
if response.status_code == 200:
    print("服务器正常")
else:
    print("异常error,Wrong Code:", response.status_code, "Please Repair")

soup = BeautifulSoup(response.text, "html.parser")

quotes = soup.find_all("div", class_="quote")
print("当页的名言数量", len(quotes))


# print (quotes[0])
# 跑出来的html如下
"""
<div class="quote" itemscope="" itemtype="http://schema.org/CreativeWork">
<span class="text" itemprop="text">“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”</span>
<span>by <small class="author" itemprop="author">Albert Einstein</small>
<a href="/author/Albert-Einstein">(about)</a>
</span>
<div class="tags">
            Tags:
            <meta class="keywords" content="change,deep-thoughts,thinking,world" itemprop="keywords"/>
<a class="tag" href="/tag/change/page/1/">change</a>
<a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
<a class="tag" href="/tag/thinking/page/1/">thinking</a>
<a class="tag" href="/tag/world/page/1/">world</a>
</div>
</div>
"""
print("打印数据...并写入本地quote.txt")
with open("quotes.txt", "w", encoding="utf-8") as f:
    for quote in quotes:
        text = quote.find("span", class_="text").text
        author = quote.find("small", class_="author").text
        print(f"作者：{author:<20} 名言：{text}")
        f.write(f"{author:<20} {text}\n")


# 第二阶段：web控制，以12306为例

time.sleep(0.5)
print("\n")
print("爬虫部分结束，已经将数据集写入quotes.txt")
print("\n")
time.sleep(0.8)
input("第二阶段查票脚本,按任意键启动")

driver = webdriver.Edge()
driver.get("https://kyfw.12306.cn/otn/leftTicket/init")  # 打开查票页
time.sleep(2)
# driver.quit()

"""爬到的核心输入段html如下"""

"""<div class="s-info" id="place_area"><ul><li><span class="label"><label id="fromStationText_label">出发地</label>
</span>
<div class="inp-w"><input id="fromStation" type="hidden" value="" name="leftTicketDTO.from_station">
<input autocomplete="off" type="text" id="fromStationText" class="inp-txt" value="" name="leftTicketDTO.from_station_name" aria-label="请输入或选择出发站，按回车确认输入">
</div>
</li>
<li class="i-change i-change2" id="change_station" style="background-position: -67px -96px; cursor: pointer;"><a href="javascript:" title="将出发地与目的地互换" style="width:1px;height:1px;position:absolute;display:block;"></a></li>
<li><span class="label"><label id="toStationText_label"> 目的地</label>
</span>
<div class="inp-w"><input id="toStation" type="hidden" value="" name="leftTicketDTO.to_station">
<input autocomplete="off" type="text" id="toStationText" class="inp-txt" value="" name="leftTicketDTO.to_station_name" aria-label="请输入或选择目的地站，按回车确认输入">
</div>
</li>
<li><span class="label"> 出发日</span>
<div class="inp-w" style="z-index:1200"><input aria-label="请输入日期，例如2021杠01杠01" autocomplete="off" type="text" class="inp_selected" name="leftTicketDTO.train_date" id="train_date" value="2013-06-07 周五">
<span id="date_icon_1" class="i-date"></span>
</div>
</li>
<li class="no-change"><span class="label"> 返程日</span>
<div class="inp-w" id="back_div" style="z-index:1100"><input autocomplete="off" aria-label="请输入日期，例如2021杠01杠01" type="text" class="inp-txt" name="back_train_date" id="back_train_date" value="" disabled="disabled">
<!--	<div id="back_train_date_" style="position: absolute; height: 250px;z-index:1100;left:0; top:30px;"></div>-->
<span id="date_icon_2" class="i-date"></span>
</div>
<!--<div class="inp-w" id="back_div">
								<input th:value="${back_train_date}" type="text" class="inp-txt" name="back_train_date" id="back_train_date"
									value="2013-06-16 周日" readonly="readonly"></input> <span id="date_icon_2" class="i-date"></span>
							</div>-->
</li>
</ul>
</div>
"""

# 核心输入端：出发地
"""
<input autocomplete="off" 
type="text" 
id="fromStationText" 
class="inp-txt" 
value="" <------------------------------------------------要插入的value
name="leftTicketDTO.from_station_name" 
aria-label="请输入或选择出发站，按回车确认输入">
"""
# 上面那个是显式填入，下面的是隐式查询代码
"""<input id="fromStation" type="hidden" value="" name="leftTicketDTO.from_station">"""

# 出发地
driver.execute_script("document.getElementById('fromStationText').value = '北京';")
driver.execute_script(
    "document.getElementById('fromStation').value = 'BJP';"  # 北京的代号
)
time.sleep(1)

# 到达地
driver.execute_script("document.getElementById('toStationText').value = '上海';")
driver.execute_script(
    "document.getElementById('toStation').value = 'SHH';"  # 上海的代号
)

time.sleep(1)
# 哪一天
driver.execute_script("document.getElementById('train_date').value = '2026-06-15';")

#time.sleep(2)  # 肉眼确认是否填好了


# 然后点查询按钮
"""<a style="margin-top: 12px;" href="javascript:" id="query_ticket" class="btn92s" shape="rect">查询</a>"""

driver.find_element(By.ID, "query_ticket").click()

while True:
    x = input(
        "查好了吗？这一步需要手动确定,\n输入1表示查出正确的东西了，输入0表示没有\n请不要胡乱输入："
    )
    if not (x == "1" or x == "0"):
        print("你输入了个啥？ --来自sjt的质问")
        print("请好好输入！")
        time.sleep(1)
    elif x == "0":
        # 理论不会出现，不做处理
        print("What are you 弄啥嘞？！")
        exit(0)
    else:
        # 核心爬取数据的部分
        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
        # print(cookies)

        api = "https://kyfw.12306.cn/otn/leftTicket/query"
        params = {
            "leftTicketDTO.train_date": "2026-06-15",  # 日期
            "leftTicketDTO.from_station": "BJP",  # 出发电报码
            "leftTicketDTO.to_station": "SHH",  # 到达电报码
            "purpose_codes": "ADULT",  # 成人票
        }
        headers = {"User-Agent": driver.execute_script("return navigator.userAgent;")}

        resp = requests.get(
            api, params=params, cookies=cookies, headers=headers, verify=False
        )
        data = resp.json()
        trains = data["data"]["result"]  # 这是一个列表，每个元素是一趟车
        station_map = data["data"]["map"]

        """f = trains[0].split("|")
        for i, val in enumerate(f):
            print(i, val)
            """

        rows = []
        for item in trains:
            f = item.split("|")
            rows.append({
                
                "车次":   f[3],
                "出发站": station_map.get(f[4], f[4]),   # 用 map 翻成中文，查不到就退回电报码
                "到达站": station_map.get(f[5], f[5]),
                "出发":   f[8],
                "到达":   f[9],
                "历时":   f[10],
                "商务座": f[32] or "--",
                "一等座": f[31] or "--",
                "二等座": f[30] or "--",
                "硬卧":   f[28] or "--",
                "硬座":   f[29] or "--",
                "无座":   f[26] or "--",
                "可预订": "是" if f[11] == "Y" else "否",
            })

        with open("tickets.csv", "w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        print(f"搞定，共 {len(rows)} 趟车，已写入 tickets.csv")
        input("按任意键退出")
        exit(0)
        break

        
