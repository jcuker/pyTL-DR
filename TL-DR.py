import requests
import json
import pystache
import os
import dateutil.parser
import datetime
import calendar
import webbrowser
import shutil
import argparse
import sys
from shutil import copyfile
from unidecode import unidecode

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
        + '&pageSize=25' 
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
        + '&pageSize=25' 
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

        if('sm_api_content' in smmryResponse):
            summarizedText = smmryResponse["sm_api_content"]
            if len(summarizedText) >= 1360:
                summarizedText = str(summarizedText[:1356] + " ...")

        else:
            summarizedText = None

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
        image_url = "data:image/png;base64,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"

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
    
    renderedHTML = unidecode(renderedHTML)

    SaveToFile('/html/tl-dr.html', renderedHTML)

def initHTML():
    htmlLocation = '/html/template.html'
    htmlTemplate = ReadInFile(htmlLocation)
    SaveToFile('/html/tl-dr.html', htmlTemplate)
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
    jsLocation = os.getcwd() + "/html/script.js"

    global destPath
    global serverRootPath
    destHtmlLocation = os.path.join(destPath, 'tl-dr.html')
    destCssLocation = destPath + '/styles/style.css'
    destJsLocation = os.path.join(destPath, 'script.js')

    try:
        if (os.path.isfile(destHtmlLocation)):
            os.remove(destHtmlLocation)
        if (os.path.isfile(destCssLocation)):
            os.remove(destCssLocation)
        if(os.path.isfile(destJsLocation)):
            os.remove(destJsLocation)

        shutil.move(htmlLocation, destHtmlLocation)
        copyfile(cssLocation, destCssLocation)
        copyfile(jsLocation, destJsLocation)
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