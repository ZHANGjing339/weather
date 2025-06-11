import requests
from bs4 import BeautifulSoup
import csv
import json
import re


def getHTMLtext(url):
    """请求获得网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        print("成功访问")
        return r.text
    except:
        print("访问错误")
        return ""


def get_content(html):
    """处理得到有用信息保存数据文件"""
    final = []  # 初始化一个列表保存数据
    bs = BeautifulSoup(html, "html.parser")  # 创建BeautifulSoup对象
    body = bs.body
    data = body.find('div', {'id': '7d'})  # 找到div标签且id = 7d

    # 尝试新的方法获取当天数据
    final_day = []
    try:
        # 查找包含小时级预报的script标签
        scripts = body.find_all('script')
        for script in scripts:
            if script.string and 'hour3data' in script.string:
                script_text = script.string
                # 使用正则表达式提取小时级预报数据
                pattern = r'hour3data = ({.*?});'
                match = re.search(pattern, script_text, re.DOTALL)
                if match:
                    hour_data = json.loads(match.group(1))
                    # 提取当天的小时数据
                    if '1d' in hour_data:
                        day_data = hour_data['1d']
                        for hour in day_data:
                            temp = []
                            temp.append(hour.get('time', ''))
                            temp.append(hour.get('temp', ''))
                            temp.append(hour.get('wnd', {}).get('dir', ''))
                            temp.append(hour.get('wnd', {}).get('sc', ''))
                            temp.append(hour.get('rain', ''))
                            temp.append(hour.get('sd', ''))
                            temp.append(hour.get('aqi', ''))
                            final_day.append(temp)
                        break
    except Exception as e:
        print(f"获取当天数据时出错: {e}")

    # 下面爬取7天的数据
    ul = data.find('ul')  # 找到所有的ul标签
    li = ul.find_all('li')  # 找到左右的li标签
    i = 0  # 控制爬取的天数
    for day in li:
        if i < 7:
            temp = []  # 临时存放每天的数据
            date = day.find('h1').string  # 得到日期
            temp.append(date)
            inf = day.find_all('p')  # 找出li下面的p标签,提取第一个p标签的值，即天气

            # 处理天气信息
            if inf and len(inf) > 0:
                temp.append(inf[0].string)
            else:
                temp.append("")

            # 处理温度信息
            if inf and len(inf) > 1:
                tem_low = inf[1].find('i').string  # 找到最低气温
                temp.append(tem_low.replace('℃', ''))

                if inf[1].find('span') is None:  # 天气预报可能没有最高气温
                    tem_high = ""
                else:
                    tem_high = inf[1].find('span').string  # 找到最高气温
                    temp.append(tem_high.replace('℃', ''))
            else:
                temp.extend(["", ""])

            # 处理风力信息
            if inf and len(inf) > 2:
                wind = inf[2].find_all('span')  # 找到风向
                for j in wind:
                    if j.get('title'):
                        temp.append(j['title'])
                    else:
                        temp.append(j.string)
                wind_scale = inf[2].find('i').string  # 找到风级
                index1 = wind_scale.index('级')
                temp.append(int(wind_scale[index1 - 1:index1]))
            else:
                temp.extend(["", "", ""])

            final.append(temp)
            i = i + 1
    return final_day, final


def get_content2(html):
    """处理得到有用信息保存数据文件"""
    final = []  # 初始化一个列表保存数据
    bs = BeautifulSoup(html, "html.parser")  # 创建BeautifulSoup对象
    body = bs.body
    data = body.find('div', {'id': '15d'})  # 找到div标签且id = 15d
    ul = data.find('ul')  # 找到所有的ul标签
    li = ul.find_all('li')  # 找到左右的li标签
    i = 0
    for day in li:
        if i < 8:
            temp = []  # 临时存放每天的数据
            date = day.find('span', {'class': 'time'}).string  # 得到日期
            if '（' in date and '）' in date:
                date = date[date.index('（') + 1: date.index('）')]  # 取出日期号
            temp.append(date)

            weather = day.find('span', {'class': 'wea'})  # 找到天气
            if weather:
                temp.append(weather.string)
            else:
                temp.append("")

            tem = day.find('span', {'class': 'tem'})  # 找到温度
            if tem:
                tem_text = tem.text
                if '/' in tem_text:
                    temp.append(tem_text[tem_text.index('/') + 1:].strip().replace('℃', ''))  # 找到最低气温
                    temp.append(tem_text[:tem_text.index('/')].strip().replace('℃', ''))  # 找到最高气温
                else:
                    temp.extend(["", ""])
            else:
                temp.extend(["", ""])

            wind = day.find('span', {'class': 'wind'})  # 找到风向
            if wind:
                wind_text = wind.string
                if '转' in wind_text:  # 如果有风向变化
                    temp.append(wind_text[:wind_text.index('转')])
                    temp.append(wind_text[wind_text.index('转') + 1:])
                else:  # 如果没有风向变化，前后风向一致
                    temp.append(wind_text)
                    temp.append(wind_text)
            else:
                temp.extend(["", ""])

            wind_scale = day.find('span', {'class': 'wind1'})  # 找到风级
            if wind_scale and '级' in wind_scale.string:
                index1 = wind_scale.string.index('级')
                temp.append(int(wind_scale.string[index1 - 1:index1]))
            else:
                temp.append("")

            final.append(temp)
            i = i + 1
    return final


def write_to_csv(file_name, data, day=14):
    """保存为csv文件"""
    with open(file_name, 'w', errors='ignore', newline='', encoding='utf-8') as f:
        if day == 14:
            header = ['日期', '天气', '最低气温', '最高气温', '风向1', '风向2', '风级']
        else:
            header = ['小时', '温度', '风力方向', '风级', '降水量', '相对湿度', '空气质量']
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(data)


def main():
    """主函数"""
    print("weather test")
    # 珠海
    url1 = 'http://www.weather.com.cn/weather/101280701.shtml'  # 7天天气中国天气网
    url2 = 'http://www.weather.com.cn/weather15d/101280701.shtml'  # 8-15天天气中国天气网

    html1 = getHTMLtext(url1)
    data1, data1_7 = get_content(html1)  # 获得当天和1-7天的数据

    html2 = getHTMLtext(url2)
    data8_14 = get_content2(html2)  # 获得8-14天数据
    data14 = data1_7 + data8_14

    write_to_csv('weather14.csv', data14, 14)  # 保存为csv文件
    if data1:
        write_to_csv('weather1.csv', data1, 1)


if __name__ == '__main__':
    main()
