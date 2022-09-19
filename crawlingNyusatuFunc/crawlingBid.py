#coding: UTF-8

import os
import sys
sys.path.append("lib.bs4")
import csv

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import datetime

import glob
import shutil

# exeに固める時のコマンド
# pyinstaller ./crawlingBid.py --onefile --noconsole --add-binary "./driver/chromedriver.exe;./driver"

difference_all = []

if 'on_lambda' in os.environ:
  dpath = '/tmp/'
else:
  dpath = os.getcwd() + '/'

# URL確認対象パス
urlPath = dpath + "url/"
# 前回確認結果パス
beforePath = dpath + "output/before/"
# 差分結果パス
differencePath = dpath + "output/difference/"
#csvファイル名称
csv_file_name = 'difference_all.csv'
#メール配信用フォルダ
setMailPath = dpath + "mail_file/"
#配信用ファイル名称
send_file_name="Hokkaido.csv"
# ログファイルパス
logPath = dpath + "log/"
# ログファイルパス
log_file_name = "execLog.txt"

# 正常終了メッセージ
trueEnd = "正常終了"
# 異常検知メッセージ
badEnd = "異常検知"

def main(args):
    print("start")

    os.makedirs(beforePath, exist_ok=True)
    os.makedirs(differencePath, exist_ok=True)
    os.makedirs(logPath, exist_ok=True)
    os.makedirs(setMailPath, exist_ok=True)

    # 開始ログ出力
    logPut('\n')
    logPut('北海道案件検索処理開始 ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    # URL確認対象の取得
    with open(urlPath + 'url.csv', 'r', encoding='shift_jis') as csvfile:
        url_csv = csv.reader(csvfile, delimiter=',', quotechar='"')
        for uRow in url_csv:
            name = uRow[0] 
            scrapingType = uRow[1]
            url = uRow[2]
            
            # 情報取得
            result = scraping(name, scrapingType, url)

            # 前回の取得時に存在していたかチェック
            differenceList = []
            if os.path.exists(beforePath + scrapingType + '.csv'):
                for nRow in result:
                    # 前回確認結果の取得
                    with open(beforePath + scrapingType + '.csv', 'r', encoding='utf-16') as csvfile2:
                        before_csv = csv.reader(csvfile2, delimiter=',', quotechar='"')
                        if nRow not in before_csv:
                            differenceList.append(nRow)
            else:
                differenceList = result

            # 差分結果パスに書き込み
            with open(differencePath + scrapingType + '.csv', 'w', encoding='utf-16', errors="ignore") as w:
                writer = csv.writer(w, lineterminator='\n')
                writer.writerows(differenceList)

            # サマリ用
            for difference in differenceList:
                difference_all.append([name, url+' ', difference[0], difference[1]])

            # 前回確認結果パスに書き込み
            with open(beforePath + scrapingType + '.csv', 'w', encoding='utf-16', errors="ignore") as w:
                writer = csv.writer(w, lineterminator='\n')
                writer.writerows(result)

    # 差分結果パスに書き込み(サマリ用)
    with open(differencePath + csv_file_name, 'w', encoding='utf-16', errors="ignore") as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerows(difference_all)
    
    #書き込んだcsvファイルを、メール配信用フォルダへ移動
    moveCSVFile(differencePath + csv_file_name)

    # 終了ログ書き込み
    logPut('北海道案件検索処理終了 ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    print("end")

# スクレイピング処理root
def scraping(name, scrapingType, url):
    if scrapingType == "poly":
        return poly(name, url)
    elif scrapingType == "hkd.mlit":
        return hkd(name, url)
    elif scrapingType == "spmdu":
        return spmdu(name, url)
    elif scrapingType == "spkhtknst":
        return spkhtknst(name, url)
    elif scrapingType == "sphsptl":
        return sphsptl(name, url)
    elif scrapingType == "spkyk":
        return spkyk(name, url)
    #elif scrapingType == "spsmk":
    #    return spsmk(name, url)
    #elif scrapingType == "hkdclg":
    #    return hkdclg(name, url)
    #elif scrapingType == "spsdk":
    #    return spsdk(name, url)
    else :
        return noneUrl("")

#画面遷移系の各種URL取得
def getCsvPath(getName):
  with open(urlPath + 'target_url.csv', 'r', encoding='shift_jis') as csvfile:
    url_csv = csv.reader(csvfile, delimiter=',', quotechar='"')
    #Csvファイル一行ずつループ
    for uRow in url_csv:
      scrapingType = uRow[1]
      url = uRow[2]
      #スクレイピング項目が対象ページであった場合、URLを返却する
      if scrapingType == getName:
       target_url = url

  return(target_url)


#メール配信フォルダへ移動
def moveCSVFile(TargetPath):
    
    #配信フォルダにある古いファイルを削除
    file_path = glob.glob(setMailPath + '*' + csv_file_name)
    if len(file_path) > 0:
        for filename in file_path:
            os.remove(filename)
    
    #ファイル名称用本日日付
    now_date = datetime.datetime.now().strftime("%Y%m%d")

    #ファイルリネームコピー
    shutil.copy(TargetPath, setMailPath + now_date + '_' + send_file_name)

# ログファイル書き込み処理
def logPut(strPut):

  # ログファイルオープン
  f = open(logPath + log_file_name, 'a', encoding='UTF-8')

  # 任意文字列の書き込み
  f.write(strPut + '\n')

  # ログファイルクローズ
  f.close()


def noneUrl(url):

  result = []
  result.append(["",""])
  return result

# ポリテクセンター北海道
def poly(name, url):

  result = []
  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.text, "html.parser")

    tables = soup.find_all('table', attrs={'class': 'table1'})
    for table in tables:
      date = table.find_all('td')[0].text
      title = table.find_all('td')[1].text

      result.append([date, title])
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 北海道開発局（本局分）
def hkd(name, url):

  result = []

  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.content, "html.parser")
    # 物品の販売、製造　配下を取得
    section = soup.find(id="s1")
    h5s = section.find_all("h5")
    for h5 in h5s:
      lis = h5.next_element.next_element.next_element.find_all("li")
      for li in lis:
          date = h5.text
          title = li.text

          result.append([date, title])
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 札幌医科大学
def spmdu(name, url):

  result = []

  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.content, "html.parser")

    uls = soup.find('ul', attrs={'class': 'entry'})
    lis = uls.find_all('li')
    for li in lis:
      date = li.find('time').text
      title = li.find('p').text
      result.append([date,title])
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 札幌開発建設部
def spkhtknst(name, url):

  result = []

  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.content, "html.parser")

    uls = soup.find('ul', attrs={'class': 'iPapers'})
    lis = uls.find_all('li')
    date = soup.find('p', attrs={'class': 'lastDate'}).text
    for li in lis:
      title = li.find('a').text
      result.append([date,title])
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 市立札幌病院
def sphsptl(name, url):

  result = []

  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.content, "html.parser")

    tables = soup.find('table', attrs={'cellspacing': '1'})
    trs = tables.find_all('tr')
    cnt = 0
    for tr in trs:
      #ヘッダーを読み飛ばす
      if cnt != 0:
          #状況が募集中のみ
          if tr.find_all('td')[0].text == "募集中":
              date = tr.find_all('td')[1].text
              title = tr.find_all('td')[3].text

              result.append([date,title])
      cnt = cnt + 1
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 札幌市教育委員会
def spkyk(name, url):

  result = []

  try:
    site = requests.get(url)
    soup = BeautifulSoup(site.content, "html.parser")

    divid = soup.find('div',id="tmp_contents")
    uls = divid.find('ul')
    lis = uls.find_all('li')
    date = soup.find(id="tmp_update").text
    for li in lis:
      if li.text == '現在公募中の案件はありません':
        break
      else :
        title = li.find('a').text
        result.append([date,title])
  except:
    execMsg = badEnd
  else:
    execMsg = trueEnd

  finally:
    # ログ書き込み
    logPut(name + " " + execMsg)

  return result

# 札幌市総務局
def spsmk(url):

  site = requests.get(url)
  soup = BeautifulSoup(site.content, "html.parser")

  divid = soup.find('div',id="tmp_contents")
  uls = divid.find('ul')
  lis = uls.find_all('li')
  date = soup.find(id="tmp_update").text
  result = []
  for li in lis:
    if li.text == '現在公募中の案件はありません':
      break
    else :
     title = li.find('a').text
     result.append([date,title])

  return result


# 北海道大学
#def hkdclg(name, url):
#  site = requests.get(url)
#  soup = BeautifulSoup(site.content, "html.parser")

#  tables = soup.find('table', attrs={'class': 'k_teisai'})
#  trs = tables.find_all('tr')
#  result = []s
#  for tr in trs:
#    if tr.find_all('td')[0].find('font').text != "物件番号":
#    date = tr.find_all('td')[1].find('font').text
#    title = tr.find_all('td')[3].find('font').text
#    result.append([date,' '.join(title.splitlines())])

#  return result


#ドライバー読み込み。ブラウザ表示の場合に使用する
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

#ボタン押下処理
def target_click(url,tag_type,target):

  #ChromeDriver読み込み
  driver = webdriver.Chrome(resource_path('./driver/chromedriver.exe'))

  #10秒待機
  driver.implicitly_wait(10) # seconds

  #押下対象画面を開く
  driver.get(url)
  #対象がclass
  if tag_type == 'class':
    element = driver.find_element_by_class_name(target)
    element.click()
  #対象がid
  elif tag_type == 'id':
    element = driver.find_element_by_id(target)
    element.click()
  #href押下
  elif tag_type == 'href':
    pass
  #その他
  else :
    element = driver.find_element_by_name(target)

# 札幌市水道局
def spsdk(name, url):

  #ChromeDriver読み込み
  driver = webdriver.Chrome(resource_path('./driver/chromedriver.exe'))

  #10秒待機
  driver.implicitly_wait(10) # seconds

  #トップページを開く
  driver.get(url)

  #トップページが開いた状態から、電子入札ボタンを押下
  dns_click = getCsvPath('spsdk_dns1')
  driver.get(dns_click)

  #メニューフレームに操作を移行する
  iframe = driver.find_element_by_name('menu_Frm')
  driver.switch_to.frame(iframe)
  
  #案件画面から、メニューフレームの物品タグを開く
  element_bpn = driver.find_element_by_id('menuObj_1')
  element_bpn.click()

  #案件画面から、物販入札リスト画面への繊維タブ情報を取得し、疑似的に押下する
  element = driver.find_element_by_id('menuObj_4')
  element.click()

  # もとのフレームに戻る
  driver.switch_to.default_content()

  #20秒待機
  driver.implicitly_wait(20) # seconds

  #表示された画面から、メインフレームに操作を移行する
  nframe = driver.find_element_by_name('mainfrm')
  driver.switch_to.frame(nframe)


  #案件ページへのリンクが貼られた要素一覧を取得
  ankn_tags = driver.find_elements_by_class_name('SUBSTANCE_ROW_NB')
  result = []
  aa_cnt = 1
  for ankn_tag in ankn_tags:
   #aタグが埋め込まれている場合
   if aa_cnt == 1 :
    aas = ankn_tag.find_elements_by_tag_name('a')

    if len(aas) != 0:
     #aタグをクリック
     ankn_tag.find_element_by_tag_name('a').click()

     #10秒待機
     driver.implicitly_wait(10) # seconds

     # もとのフレームに戻る
     driver.switch_to.default_content()

     #表示された画面から、メインフレームに操作を移行する
     pframe = driver.find_element_by_name('mainfrm')
     driver.switch_to.frame(pframe)

     #案件一覧が表示されているテーブルを取得
     table = driver.find_element_by_class_name('borderTable.group')

     #テーブルから、案件が記載された行一覧を取得
     rows = table.find_elements_by_tag_name('tr')
     cnt = 1
     for row in rows:
       #3行目まではヘッダー
      if row.text != '':
        if cnt > 2:
          if cnt % 2 != 0 : #奇数行から案件番号、案件名を取得
            tds = row.find_elements_by_tag_name('td')
            ankn_no = tds[1].text
            ankn_nm = tds[2].text
          else : #偶数行から公示日を取得
            tds = row.find_elements_by_tag_name('td')
            date = tds[3].text
            result.append([date,ankn_no + '_' + ankn_nm])
        cnt = cnt + 1
     aa_cnt = aa_cnt + 1

  return result


if __name__ == '__main__':
    try:
        args = sys.argv 
        if 1 <= len(args):
            main(args)
        else:
            print('Arguments are too short')        
    except Exception as e:
        print(e)
