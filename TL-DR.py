import requests
import json
import pystache
import os
import dateutil.parser
import calendar
import webbrowser

class ArticleInformation(object):

    # member variables
    # title, url, content, author, imageUrl, publishedAt

    summarizedContent = None

    def __init__(self, title, url, content, author, imageUrl, publishedAt):
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
        
        self.title = title
        self.url = url
        self.content = content
        self.author = author
        self.imageUrl = imageUrl
        self.publishedAt = publishedAt

    def print(self):
        print("Title: " + self.title)
        print("Url: " + self.url)
        print("Content: " + self.content)
        if self.summarizedContent is not None:
            print("SummarizedContent: " + self.summarizedContent)
        print("Author: " + self.author)
        print("ImageUrl: " + self.imageUrl)
        print("PublishedAt: " + self.publishedAt)
        print('\n')

def initKeys():
    # reading from file so as not to publish my API keys
    f = open("api_keys.txt", "r")

    global newsApiKey 
    newsApiKey = f.readline()
    # was getting extraneous endline
    newsApiKey = newsApiKey[:-1]

    global smmryApiKey
    smmryApiKey = f.readline()
    f.close()

    return

def NewsAPIGetAsJSON(country, apiKey, articleCategory = ''):
    # example response:
    #{
    #   "status": "ok",
    #   "totalResults": 20,
    #   "articles": [ … ]
    #}

    if articleCategory == '':
        articleCategory = 'general'
    
    # pageSize of 10 is a limitation of the SMMRY API see here: http://smmry.com/api
    newsAPIRequest = requests.get('https://newsapi.org/v2/top-headlines?country=' + country + '&category=' + articleCategory + '&pageSize=10' + '&apiKey=' + apiKey)
    newsAPIJson = json.loads(newsAPIRequest.text)
    # print(newsAPIJson["articles"][0]["description"])
    return newsAPIJson

def NewsAPIGetAsJSONviaSource(source, apiKey):
    # example response:
    #{
    #   "status": "ok",
    #   "totalResults": 20,
    #   "articles": [ … ]
    #}

    # pageSize of 10 is a limitation of the SMMRY API see here: http://smmry.com/api
    newsAPIRequest = requests.get('https://newsapi.org/v2/top-headlines?source=' + source + '&pageSize=10' + '&apiKey=' + apiKey)
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
    newsApiJson = NewsAPIGetAsJSON('us', newsApiKey)
    articleInformationList = []

    for currentArticle in newsApiJson["articles"]:
        newArticleInformation = ArticleInformation(currentArticle["title"], currentArticle["url"], currentArticle["description"], currentArticle["author"], currentArticle["urlToImage"], currentArticle["publishedAt"])
        articleInformationList.append(newArticleInformation)

    return articleInformationList

def SummarizeArticleList(articleInformationList):

    for currentArticle in articleInformationList:
        smmryResponse = SmmryAPIGet(currentArticle.url, smmryApiKey)
        currentArticle.summarizedContent = smmryResponse["sm_api_content"]
    
    return

def ReadInFile(filename):
    f = open(os.getcwd() + filename, "r")
    fileAsString = f.read()
    f.close()
    return fileAsString

def GenerateCardFromArticleInformation(articleInformation):
    cardHTML = ReadInFile("/html/card.html")
    renderer = pystache.Renderer()
    preParsed = pystache.parse(cardHTML)

    content = articleInformation.content
    if articleInformation.summarizedContent is not None:
        content = articleInformation.summarizedContent

    date = dateutil.parser.parse(articleInformation.publishedAt)
    day = date.day
    month = calendar.month_name[date.month]

    renderedCardHTML = renderer.render(preParsed,{'url' : articleInformation.url}, {'title' : articleInformation.title}, {'author' : articleInformation.author}, {'content' : content}, {'day' : day}, {'month' : month}, {'imageUrl' : articleInformation.imageUrl})
    return renderedCardHTML

def SaveToFile(path, content):
    f = open(os.getcwd() + path, 'w')
    f.write(content)
    f.close()
    return

def InsertCardIntoHTMLDoc(card, more = False):
    path = "/html/main.html"
    htmlFile = ReadInFile(path)
    renderer = pystache.Renderer()
    preParsed = pystache.parse(htmlFile)

    renderedHTML = None
    if more is True:
        renderedHTML = renderer.render(preParsed, {'card' : card + '\n\n{{{card}}}'})
    else:
        renderedHTML = renderer.render(preParsed, {'card' : card})
    
    SaveToFile('/html/main.html', renderedHTML)

def initHTML():
    newHTML = "<html>\n<head><title>TL-DR</title>\n<link href=\"style.css\" rel=\"stylesheet\"/>\n<body>\n{{{card}}}\n</body>"
    SaveToFile('/html/main.html', newHTML)
    return

def OpenInWebBrowser():
    webbrowser.open_new_tab(os.getcwd() + '/html/main.html')

def main():
    initKeys()
    initHTML()
    articleInformationList = GetArticleInformationList()

    #smmryResponse = SmmryAPIGet(articleInformationList[0].url, smmryApiKey)
    articleInformationList[0].summarizedContent = "A group of gunmen have launched an attack on the Intercontinental Hotel in Kabul, authorities said Saturday. Interior ministry spokesman Nasrat Rahimi told CBS News that they believe four gunmen attacked the hotel. Rahimi did not provide details on casualties but said foreign and Afghan guests were inside the hotel during the attack. The attackers entered the hotel through its garden and then through the kitchen, Danish said, adding that the hotel's security was recently handed over to a private security company, but did not provide its name. \"We are aware of reports that extremist groups may be planning an attack against hotels in Kabul,\" the warning read. The Intercontinental Hotel is typically used for conferences and gatherings. In 2011, an attack at the hotel left 21 people dead, including nine attackers. A guest hiding in his hotel room told AFP he could hear the gunfire."

    articleInformationList[0].print()
    card = GenerateCardFromArticleInformation(articleInformationList[0])
    InsertCardIntoHTMLDoc(card, True)
    InsertCardIntoHTMLDoc(card)


    OpenInWebBrowser()
    return

main()