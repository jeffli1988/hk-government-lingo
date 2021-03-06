import json
import urllib.request
import mysql.connector
import re
import time
import io
#import chinese_converter
import urllib
from bs4 import BeautifulSoup

def __main__():
    print("Carries says ... - build 25 Feb PRC branch")
    print()
    print("op")
    print("1 - scrape HKSARG GIA system for URLs")
    print("2 - populate speech bodies")
    print("3 - aggregate results")
    op = input("Select op - ")
    if op == "1":
        print()
        langInt = input("Select lang -")
        langUrlModifier = ""
        if langInt == "1":
            lang = "zh"
            langUrlModifier = "c"
        elif langInt == "2":
            lang = "en"
        year = int(input("Start year - "))
        month = int(input("Start month - "))
        day = 1
        user = input("MySQL user name - ")
        password = input("MySQL password - ")
        mydb = mysql.connector.connect(host="localhost", user=user, password=password, database="carrie-says",auth_plugin='mysql_native_password')
        mycursor = mydb.cursor()
        print()
        startIndex = 1
        nextPage = True
        while (year < 2022):
            if month < 10:
                urlMonth = "0" + str(month)
            else:
                urlMonth = month
            if day < 10:
                urlDay = "0" + str(day)
            else:
                urlDay = day
            tocContent_temp = urllib.request.urlopen("http://www.info.gov.hk/gia/general/" + str(year) + str(urlMonth) + "/" + str(urlDay) + str(langUrlModifier) + ".htm")
            tocContent = BeautifulSoup(tocContent_temp.read(), "html.parser").decode("unicode")
            time.sleep(1)
            tocContentPattern = re.compile("((?:http://www.info.gov.hk/)?gia\/general\/[0-9]{6}\/[0-9]{2}\/P[0-9]{12,}.htm)")
            for tocLinks in re.findall(tocContentPattern, str(tocContent)):
                if "http://www.info.gov.hk/" not in tocLinks:
                    linkToInsert = "http://www.info.gov.hk/" + tocLinks
                else:
                    linkToInsert = tocLinks
                query = "insert into `main` (`url`, `title`, `body`, `lang`, `date`, `author`, `source`, `type`) values ('" + linkToInsert + "', '', '', '" + lang + "', '1960-01-01', '', '', '');"
                mycursor.execute(query)
                mydb.commit()
            print("Processing " + str(urlDay) + " " + str(urlMonth) + " " + str(year) + " http://www.info.gov.hk/gia/general/" + str(year) + str(urlMonth) + "/" + str(urlDay) + str(langUrlModifier) + ".htm", end='\r', flush=True)
            day += 1
            if day == 29:
                if month == 2:
                    if year != 2020 or year != 2016 or year != 2012:
                        month += 1
                        day = 1
            if day == 30:
                if month == 2:
                    if year == 2020 or year == 2016 or year == 2012:
                        month += 1
                        day = 1
            if day == 31:
                if month == 4 or month == 6 or month == 9 or month == 11:
                    month += 1
                    day = 1
            if day == 32:
                if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
                    month += 1
                    day = 1
            if month == 13:
                year += 1
                month = 1

    elif op == "2":
        user = input("MySQL user name - ")
        password = input("MySQL password - ")
        mydb = mysql.connector.connect(host="localhost", user=user, password=password, database="carrie-says",auth_plugin='mysql_native_password')
        mycursor = mydb.cursor()
        lang = input("Lang to process, en or zh - ")
        mycursor.execute("select `url`, `type` from `main` where (`body` = '' or `title` = '') and `lang` = '" + lang + "';")
        result_set = mycursor.fetchall()
        nRow = str(mycursor.rowcount)
        m = 1
        nError = 0
        author = ""
        textToInsert = ""
        dateToInsert = "1970-01-01"
        source = ""
        titleToInsert = ""
        print("")
        for result in result_set:
            mycursor2 = mydb.cursor()
            try:
                pageBody_temp = urllib.request.urlopen(result[0])
                soup = BeautifulSoup(pageBody_temp.read(), "html.parser")
                time.sleep(1)

                textToInsert = ""
                if "doj.gov.hk" in result[0]:
                    titleToInsert = str(soup.title.string).replace(chr(34), "").replace(chr(39), "")
                    if soup.find('div', {'class': 'pressContent'}):
                        textToInsert = str(soup.find('div', {'class': 'pressContent'}).get_text()).replace(chr(34), "").replace(chr(39), "").replace(chr(13), "").replace(chr(10), "")
                    else:
                        textToInsert = ""
                    author = "???????????????"
                    getDayRegex = re.compile("([0-9]{4})([0-9]{2})([0-9]{2})")
                    year = str(getDayRegex.search(result[0]).group(1))
                    month = str(getDayRegex.search(result[0]).group(2))
                    day = str(getDayRegex.search(result[0]).group(3))
                    source = "HK"
                elif "cmab.gov.hk" in result[0]:
                    titleToInsert = ""
                    textToInsert = str(soup.find('td', {'class': 'in'}).get_text()).replace(chr(34), "").replace(chr(39), "").replace(chr(13), "").replace(chr(10), "")
                    author = "??????????????????????????????"
                    source = "HK"
                elif "fmprc.gov.cn" in result[0]:
                    source = "CN"
                    getDayRegex = re.compile("([0-9]{4})-([0-9]{2})-([0-9]{2})")
                    if soup.find('p', {'class': 'time'}):
                        dateSoup = soup.find('p', {'class': 'time'}).text
                        year = str(getDayRegex.search(dateSoup).group(1))
                        month = str(getDayRegex.search(dateSoup).group(2))
                        day = str(getDayRegex.search(dateSoup).group(3))
                    elif soup.find('span', {'id': 'News_Body_Time'}):
                        dateSoup = soup.find('span', {'id': 'News_Body_Time'}).text
                        year = str(getDayRegex.search(dateSoup).group(1))
                        month = str(getDayRegex.search(dateSoup).group(2))
                        day = str(getDayRegex.search(dateSoup).group(3))
                    else:
                        year = "1970"
                        month = "01"
                        day = "01"
                    if soup.find('h1'):
                        titleToInsert = str(soup.find('h1').text).replace(chr(34), "").replace(chr(39), "")
                    elif soup.find('div', {'id': 'News_Body_Title'}):
                        titleToInsert = str((soup.find('div', {'id': 'News_Body_Title'}).text).replace(chr(34), "").replace(chr(39), ""))
                    else:
                        titleToInsert = ""
                    if soup.find('div', {'id': 'News_Body_Txt_A'}):
                        bodySoup = soup.find('div', {'id': 'News_Body_Txt_A'})
                        bodySoup = str(bodySoup).replace("<p", "#####<p") # insert artifical delimiter
                        bodySoupArray = str(bodySoup).split("#####")
                        textToInsert = ""
                        for line in bodySoupArray:
                            if "<b>" not in line and "</strong>" not in line:
                                textToInsert += BeautifulSoup(line, "html.parser").get_text().replace(chr(13), "").replace(chr(10), "")
                    authorRegex = re.compile("??????????????????(.{2,3})(?:???|??????)")
                    if authorRegex.search(titleToInsert) is not None:
                        author = str(authorRegex.search(titleToInsert).group(1))
                    else:
                        author = ""
                else:
                    getDayRegex = re.compile("([0-9]{4})([0-9]{2})\/([0-9]{2})\/")  # parse date of the article from the URL
                    year = str(getDayRegex.search(result[0]).group(1))
                    month = str(getDayRegex.search(result[0]).group(2))
                    day = str(getDayRegex.search(result[0]).group(3))
                    author = ""
                    span = str(soup.find(id="pressrelease")).replace(chr(13), "").replace(chr(10), "")
                    if soup.find(id="PRHeadlineSpan"):
                        titleToInsert = str(soup.find(id="PRHeadlineSpan").text).replace(chr(39), "").replace(chr(34), "")
                    else:
                        # older version of the GIA does not separate the title in a separate span
                        titleToInsert = str(soup.title.string).replace(chr(34), "").replace(chr(39), "")
                        span = span.replace(titleToInsert, "")
                    lineArray = span.split("<br/>")
                    source = "HK"
                    startInserting = False
                    for line in lineArray:
                        if "?????????" in titleToInsert and "??????" in titleToInsert:
                            if "?????????" in line or "?????????" in line or "??????:" in line or "?????????" in line and "?????????" in line:
                                startInserting = True
                            if startInserting == True:
                                textToInsert += BeautifulSoup(line, "html.parser").get_text()
                        elif "LCQ" in titleToInsert:
                            if "President," in line or "President:" in line:
                                startInserting = True
                            if startInserting == True:
                                textToInsert += BeautifulSoup(line, "html.parser").get_text()
                        elif "Reporter: " not in line and "?????????" not in line and "?????????" not in line:
                            if "Ends/" in line and len(lineArray) > 2:
                                break
                            textToInsert += BeautifulSoup(line, "html.parser").get_text()
                dateToInsert = str(year) + "-" + str(month) + "-" + str(day)
                print("Processing " + str(m) + " of " + str(nRow) + ", " + str(nError) + " error - " + titleToInsert + " " + result[0])
                m += 1
                authorRegex = re.compile("?????????(?:.{3,})???(.{3})(?:.*)????(?:.*(?:???|???))(.*)")
                if author == "" and "fmprc" not in result[0]:
                    if "??????????????????" in titleToInsert:
                        author = "??????????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "????????????" in titleToInsert:
                        author = "????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "??????????????????????????????" in titleToInsert:
                        author = "??????????????????????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "?????????????????????" in titleToInsert:
                        author = "?????????????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "???????????????" in titleToInsert:
                        author = "???????????????"
                    elif "?????????????????????????????????" in titleToInsert:
                        author = "?????????????????????????????????"
                    elif "??????????????????" in titleToInsert:
                        author = "??????????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "????????????????????????" in titleToInsert:
                        author = "????????????????????????"
                    elif "???????????????????????????" in titleToInsert:
                        author = "???????????????????????????"
                    elif "??????????????????" in titleToInsert:
                        author = "??????????????????"
                    elif "???????????????????????????" in titleToInsert:
                        author = "???????????????????????????"
                    elif "???????????????????????????" in titleToInsert:
                        author = "???????????????????????????"
                    elif "??????????????????" in titleToInsert:
                        author = "??????????????????"
                    elif "??????????????????" in titleToInsert:
                        author = "??????????????????"
                    elif authorRegex.search(span) is not None:
                        author = str(authorRegex.search(span).group(1))
                    elif "???????????????" in span:
                        author = "???????????????"
                    elif "Transcript of remarks by CE" in titleToInsert:
                        author = "Chief Executive"
                    elif "Acting Chief Executive" in titleToInsert:
                        author = "Acting Chief Executive"
                    elif "Transcript of remarks by CS" in titleToInsert:
                        author = "Chief Secretary for Administration"
                    elif "Financial Secretary" in titleToInsert:
                        author = "Financial Secretary"
                    elif "Secretary for Constitutional and Mainland Affairs" in titleToInsert:
                        author = "Secretary for Constitutional and Mainland Affairs"
                    elif "Commissioner of Police" in titleToInsert:
                        author = "Commissioner of Police"
                    elif "Secretary for Security" in titleToInsert or "Transcript of remarks by S for S" in titleToInsert:
                        author = "Secretary for Security"
                    elif "Secretary of Home Affairs" in titleToInsert:
                        author = "Secretary of Home Affairs"
                    elif "government spokesperson" in titleToInsert or "spokesperson for the government" in titleToInsert or "spokesperson for the HKSAR" in titleToInsert:
                        author = "Government spokesman"
                    else:
                        author = ""
                if ("??????" in titleToInsert or ("?????????" in titleToInsert and "???" in titleToInsert) or "????????????" in titleToInsert or "??????" in titleToInsert or "????????????" in titleToInsert) or "fmprc" in result[0]:
                    type = "remarks"
                else:
                    type = "statement"

                if result[1] == "5": # do not overwrite author field if this is a HKSARG spokesman
                    mycursor2.execute("update `main` set `source` = '" + source + "', `date` = '" + dateToInsert + "', `body` = '" + textToInsert.replace(chr(39), "").replace(chr(34), "").replace(chr(13), "").replace(chr(10), "") + "', `title` = '" + titleToInsert + "' where `url` = '" + result[0] + "';")
                elif "????????????" in titleToInsert and "????????????" in titleToInsert: # delete entry and do not fill if it s a full text of the CE Policy address
                    pass
                else:
                    mycursor2.execute("update `main` set `source` = '" + source + "', `author` = '" + author + "', `date` = '" + dateToInsert + "', `body` = '" + textToInsert.replace(chr(39), "").replace(chr(34), "") + "', `title` = '" + titleToInsert + "' where `url` = '" + result[0] + "';")
                mydb.commit()
            except:
                mycursor2.execute("update `main` set `body` = 'error' where `url` = '" + result[0] + "';")
                nError += 1
                author = ""
                textToInsert = ""
                dateToInsert = "1970-01-01"
                source = ""
                titleToInsert = ""
    elif op == "3":
        print()
        targetFile = input("Path to target - ")
        originalFile = open(targetFile, "r", encoding="utf-8")
        outputFile = input("Path to output - ")
        output = open(outputFile, "w")
        user = input("MySQL user name - ")
        password = input("MySQL password - ")
        mydb = mysql.connector.connect(host="localhost", user=user, password=password, database="carrie-says", auth_plugin='mysql_native_password')
        mycursor = mydb.cursor()
        year = 2012
        month = 7
        txtMonth = ""
        output.write("date,")
        while (year < 2022):
            if month < 10:
                txtMonth = "0" + str(month)
            else:
                txtMonth = str(month)
            output.write("01" + "/" + txtMonth + "/" + str(year) + ",")
            month += 1
            if month == 13:
                month = 1
                year += 1
        output.write(chr(13))
        nLine = sum(1 for line in open(targetFile, "r", encoding="utf-8"))
        n = 0
        for index, line in enumerate(originalFile):
            mycursor.execute("select year(`date`), month(`date`), round(sum(length(`body`) - length(replace(`body`, '" + str(line).replace("\n", "") + "', ''))) / length('" + str(line).replace("\n", "") + "')) from `main` where year(`date`) <> '1960' group by 1, 2;")
            result = mycursor.fetchall()
            output.write(str(line).replace("\n", "") + ",")
            for result_write in result:
                output.write(str(result_write[2]) + ",")
            output.write(chr(13))
            n += 1
            print("Writing " + str(n) + " of " + str(nLine) + ", " + line, end='\r', flush=True)
        output.close()
        originalFile.close()
__main__()
