import requests
import json
import pystache
import os
import dateutil.parser
import datetime
import calendar
import webbrowser
import shutil
from shutil import copyfile
import argparse
import sys

class ArticleInformation(object):

    summarizedContent = None

    def __init__(self, title, url, content, author, imageUrl, publishedAt, source):
        if title is None:
            title = 'N/A'
        
        if url is None:
            url = 'N/A'

        if content is None:
            content = 'N/A'

        if author is None:
            author = 'N/A'
        
        if imageUrl is None:
            imageUrl = 'N/A'

        if publishedAt is None:
            publishedAt = 'N/A'
        
        if source is None:
            source = "N/A"

        self.title = title
        self.url = url
        self.content = content
        self.author = author
        self.imageUrl = imageUrl
        self.publishedAt = publishedAt
        self.source = source

    def print(self):
        print("Title: " + self.title)
        print("Url: " + self.url)
        print("Content: " + self.content)
        if self.summarizedContent is not None:
            print("SummarizedContent: " + self.summarizedContent)
        print("Author: " + self.author)
        print("ImageUrl: " + self.imageUrl)
        print("PublishedAt: " + self.publishedAt)
        if self.source is not None:
            print("Source: " + self.source)
        print('\n')

def initKeys():
    # reading from file so as not to publish my API keys
    f = open("api_keys.txt", "r")

    global newsApiKey 
    newsApiKey = f.readline()
    if (newsApiKey.endswith('\n')):
        newsApiKey = newsApiKey[:-1]

    global smmryApiKey
    smmryApiKey = f.readline()
    if(smmryApiKey.endswith('\n')):
        smmryApiKey = smmryApiKey[:-1]

    f.close()

    return

def GetNewsAPIResponseAsJSON(country, apiKey, articleCategory = 'general'):
    # example response:
    #{
    #   "status": "ok",
    #   "totalResults": 20,
    #   "articles": [ … ]
    #}

    newsAPIRequest = requests.get(
        'https://newsapi.org/v2/top-headlines?country=' + country 
        + '&category=' + articleCategory 
        + '&pageSize=20' 
        + '&apiKey=' + apiKey
        )
    newsAPIJson = json.loads(newsAPIRequest.text)
    return newsAPIJson

def GetNewsAPIResponseAsJSONViaSource(source, apiKey):
    # example response:
    #{
    #   "status": "ok",
    #   "totalResults": 20,
    #   "articles": [ … ]
    #}

    newsAPIRequest = requests.get(
        'https://newsapi.org/v2/top-headlines?source=' + source 
        + '&pageSize=20' 
        + '&apiKey=' + apiKey
        )
    newsAPIJson = json.loads(newsAPIRequest.text)
    return newsAPIJson

def SmmryAPIGet(urlToSend, apiKey, numberOfSentences = '7'):
    # example response:
    #{
    #   'sm_api_character_count': '1015',
    #   'sm_api_title': 'Government shutdown: Air Force cancels all athletic events',
    #   'sm_api_content': ' The school announced Saturday that all events would be canceled until there was some resolution. "Due to the government shutdown, all Air Force Academy home and away intercollegiate athletic events have been canceled until further notice. In the event a solution is reached, the Academy will work to reschedule as many missed events as possible." MORE: Government shutdown 2018: What we know now, what happens next. Swimming and diving teams were to be at UNLV.It is all systems go on Saturday for Army and Navy, which operate differently than the Air Force Academy. The Naval Academy Athletic Association, whose objective is to "Promote, influence, and assist in financing the athletic contests of the midshipmen of the United States Naval Academy," is technically separate from the Naval Academy and uses non-appropriated money. The federal government shut down Friday night after the Senate blocked a short-term spending bill. Many government agencies are now in the process of shutting down.',
    #   'sm_api_limitation': 'Waited 0 extra seconds due to API Free mode, 98 requests left to make for today.'
    #}

    url = 'http://api.smmry.com/?SM_API_KEY=' + apiKey + '&SM_LENGTH=' + numberOfSentences + '&SM_URL=' + urlToSend

    smmryRequest = requests.get(url)
    smmryJSON = json.loads(smmryRequest.text)
    return smmryJSON

def GetArticleInformationList():
    newsApiJson = GetNewsAPIResponseAsJSON('us', newsApiKey)
    articleInformationList = []

    for currentArticle in newsApiJson["articles"]:
        newArticleInformation = ArticleInformation(
            currentArticle["title"], 
            currentArticle["url"], 
            currentArticle["description"], 
            currentArticle["author"], 
            currentArticle["urlToImage"], 
            currentArticle["publishedAt"], 
            currentArticle["source"]["name"]
            )
        articleInformationList.append(newArticleInformation)
    return articleInformationList

def SummarizeArticleList(articleInformationList):
    for currentArticle in articleInformationList:
        smmryResponse = SmmryAPIGet(currentArticle.url, smmryApiKey)
        summarizedText = smmryResponse["sm_api_content"]

        if len(summarizedText) >= 1860:
            summarizedText = str(summarizedText[:1856] + " ...")

        currentArticle.summarizedContent = summarizedText
    
    return

def ReadInFile(filename):
    file = open(os.getcwd() + filename, "r")
    fileAsString = file.read()
    file.close()
    return fileAsString

def GenerateCardFromArticleInformation(articleInformation):
    cardHTML = ReadInFile("/html/card.html")
    renderer = pystache.Renderer()
    preParsed = pystache.parse(cardHTML)

    content = articleInformation.content
    if articleInformation.summarizedContent is not None:
        content = articleInformation.summarizedContent

    date = dateutil.parser.parse(articleInformation.publishedAt)
    date = date - datetime.timedelta(hours=6)
    day = date.day
    month = calendar.month_name[date.month]
    time = date.strftime("%I:%M %p")
    if (time.startswith("0")):
        time = time[1:]

    image_url = articleInformation.imageUrl + "?width=350&height=275"
    if(image_url.startswith("https")):
        image_url = image_url[8:]
        image_url = "https://rsz.io/" + image_url
    else:
        image_url = image_url[7:]
        image_url = "http://rsz.io/" + image_url

    if (str(requests.get(image_url)) == "<Response [500]>"):
        image_url = "bad.png"

    renderedCardHTML = renderer.render(
        preParsed,
        {'url' : articleInformation.url}, 
        {'title' : articleInformation.title}, 
        {'source' : articleInformation.source}, 
        {'content' : content},
        {'time' : time},
        {'day' : day}, 
        {'month' : str(month + " ")}, 
        {'imageUrl' : image_url}
        )
    return renderedCardHTML

def SaveToFile(path, content):
    file = open(os.getcwd() + path, 'w')
    file.write(content)
    file.close()
    return

def InsertCardIntoHTMLDoc(card, more = False):
    path = "/html/tl-dr.html"
    htmlFile = ReadInFile(path)
    renderer = pystache.Renderer()
    preParsed = pystache.parse(htmlFile)

    renderedHTML = None
    
    if more is True:
        renderedHTML = renderer.render(preParsed, {'card' : card + '\n\n{{{card}}}'})
    else:
        renderedHTML = renderer.render(preParsed, {'card' : card})
    
    SaveToFile('/html/tl-dr.html', renderedHTML)

def initHTML():
    newHTML = "<html>\n<head><title>TL-DR</title>\n<link href=\"styles\style.css\" rel=\"stylesheet\"/>\n<body>\n{{{card}}}\n</body>"
    SaveToFile('/html/tl-dr.html', newHTML)
    return

def OpenInWebBrowser():
    webbrowser.open_new_tab(os.getcwd() + '/html/tl-dr.html')

def GetArticlesAndGenerateHtml():
    articleInformationList = GetArticleInformationList()

    global blnIsLocalRun
    if( not blnIsLocalRun):
        SummarizeArticleList(articleInformationList)

    for articleInformation in articleInformationList:
        card = GenerateCardFromArticleInformation(articleInformation)
        if articleInformation != articleInformationList[len(articleInformationList) - 1]:
            InsertCardIntoHTMLDoc(card, True)
        else:
            InsertCardIntoHTMLDoc(card)
    return

def DeployToServer():
    htmlLocation = os.getcwd() + "/html/tl-dr.html"
    cssLocation = os.getcwd() + "/html/styles/style.css"
    global destPath
    global serverRootPath
    destHtmlLocation = os.path.join(destPath, 'tl-dr.html')
    destCssLocation = destPath + '/styles/style.css'
    
    try:
        if (os.path.isfile(destHtmlLocation)):
            os.remove(destHtmlLocation)
        if (os.path.isfile(destCssLocation)):
            os.remove(destCssLocation)

        shutil.move(htmlLocation, destHtmlLocation)
        copyfile(cssLocation, destCssLocation)
        os.chdir(serverRootPath)
        os.system("firebase deploy")
    except Exception as e:
        print(str(e))
    return

def discernRunType():
    if(len(sys.argv) == 4 and sys.argv[1] == '-d'):
        global destPath
        destPath = sys.argv[2]
        global serverRootPath
        serverRootPath = sys.argv[3]
        return False
    else:
        return True

def main():
    global blnIsLocalRun
    blnIsLocalRun = discernRunType()

    initKeys()
    initHTML()
    GetArticlesAndGenerateHtml()
    if (blnIsLocalRun):
        OpenInWebBrowser()
    else:
        DeployToServer()

    sys.exit()

main()