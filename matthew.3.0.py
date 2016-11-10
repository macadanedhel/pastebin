#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
# encoding=utf8
import ConfigParser
import Queue
import argparse
import datetime
import inspect
import json
import logging
import os
import random
import re
import socket
import sys
import threading
import urllib2
import unicodedata

from bs4 import BeautifulSoup

#---------------------------------------------------
reload(sys)
sys.setdefaultencoding('utf8')

defaultConfig="config.ini"
Config = ConfigParser.ConfigParser()
Config.read(defaultConfig)
#logging.basicConfig(filename=Config.get('LOG','FileLog'),level=Config.get('LOG','Level'),format=Config.get('LOG','Format'),datefmt=Config.get('LOG','DateFMT'))
logging.basicConfig(filename=(Config.get('LOG', 'Path')+Config.get('LOG', 'FileLog')), level=Config.get('LOG', 'Level'),
                    format='%(asctime)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

parser = argparse.ArgumentParser(
    description='Process some file.',
    epilog='comments > /dev/null'
)
parser.add_argument('--fileAgent', "-f", type=str, help='a filename with browser agents')
parser.add_argument('--GetAgents', "-a",  action='store_true', help='Get data about browser agents')
parser.add_argument('--ChangeAgent', "-z",  action='store_true', help='Change browser agent')
parser.add_argument('--GetProxy', "-x",  action='store_true', help='Get info about US proxies')
parser.add_argument('--CheckResults', "-r",  action='store_true', help='Check downloaded data')
parser.add_argument('--CheckResultsDeeper', "-d",  action='store_true', help='Check downloaded data deeper U_U')
parser.add_argument('--ScoreFile', "-c", type=str, help='score a downloaded file')
parser.add_argument('--CheckProxy', "-m", action='store_true', help='Find a proxy')
parser.add_argument('--ListProxies', "-n", action='store_true', help='List proxies')
parser.add_argument('--AddProxies', "-b", action='store_true', help='Add a proxy from data')
parser.add_argument('--FileScoringADD', "-s",  action='store_true', help='scoring a file')
parser.add_argument('--UpdateDIR', "-i",  action='store_true', help='update with all backed up files ')
parser.add_argument('--minimumScore', "-e",  type=int, help='Minimum score in file ')
parser.add_argument('--Verbose', "-v", action='store_true', help='Verbose')
parser.add_argument('--Week', "-7", action='store_true', help='A week')
parser.add_argument('--Month', "-30", action='store_true', help='A month')
parser.add_argument('--Year', "-365", action='store_true', help='A year')
parser.add_argument('--User', "-u", type=str, help='A user')



args = parser.parse_args()


#---------------------------------------------------
browserAgent={'User-Agent': 'None',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
                    'Accept-Encoding': 'none',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Connection': 'keep-alive'}
resultsFile=Config.get('LOG', 'Path')+Config.get('LOG', 'JsonResult')
proxy=""
global exitFlag
VERBOSE = False
exitFlag = 0
queueLock = threading.Lock()
#---------------------------------------------------
#---------------------------------------------------
def whoami():
    return inspect.stack()[1][3]
#---------------------------------------------------
def AgentSwitcher ():
    agentsFile=Config.get('CONST','FileAgents')
    Agents={}
    cont=0
    print "Reading config data :"+agentsFile
    logging.info("Getting data from :"+agentsFile)
    if agentsFile and os.path.exists(agentsFile):
        with open(agentsFile,"r") as all_agents:
                for line in all_agents:
                    Agents[cont]=line
                    cont+=1
    random_numer=random.randrange(len(Agents)+1)
    return Agents[random_numer].rstrip('\n')
#---------------------------------------------------
def getAgents(url):
    myself = whoami()
    prefix=""
    print ("[{0:10}] Getting agent browser from [{1}]").format(myself, url)
    logging.info(("[{0:10}]:Getting agent browser from [{1}]").format(myself, url))
    Agents=[]
    try:
        html = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        print "Fail:[{}] !!!".format(e)
        logging.WARNING(("[{0:10}]:FAIL !!! [{1}]").format(myself, e))
        return None
    try:
        bsObj = BeautifulSoup(html.read(),"lxml")
        letters = bsObj.find_all("a")
    except urllib2.HTTPError as e:
        print "Fail:[{}] !!!".format(e)
        logging.WARNING(("[{0:10}]:FAIL !!! [{1}]").format(myself, e))
        return None
    print ("[{0:10}] Getting agent browser from [{1}]").format(myself, url)
    logging.info(("[{0:10}]:Getting agent browser from [{1}]").format(myself, url))
    for element in letters:
        try:
            if ( not re.search ('Home|Api|Contact|API|Links',element.string)  and element.string != 'List of User Agent Strings' \
                 and element.string != 'WDG Web Design Group' and element.string != 'WDG_Validator/1.6.2' \
                 and element.string != 'UserAgentString.com' and  element.string != 'Wordconstructor - Random Word Generator' \
                 and element.string != '707 Directory - SEO friendly directory' and re.search('\/',element.string)):
                #print element.string
                Agents.append(element.string)
        except: None
    print ("[{0:10}] Agents OK").format(myself)
    logging.info(("[{0:10}]:Agents OK").format(myself))
    return Agents
#---------------------------------------------------
def workerThreadPage (threadID, element, site, prefix, data, workOut):
    myself=whoami()
    myself+="-threadID-"+str(threadID)
    pagename=element.a["href"].lstrip('/')
    print ("[{0:10}] Verifing {1}").format(myself, pagename)
    logging.info("[{0:10}]:Verifing {1}".format(myself, pagename))
    scoring=0
    link=[]
    if Flag:
        if not( existsName(data ,site, pagename)):
            logging.info(("[{0:10}]:Not exists").format(myself))
            scoring = getPage(threadID, pagename,
                              "http://"+prefix+element.a["href"],
                              Config.get('DATA','Path')+pagename,
                              browserAgent,
                              proxy)
            link.append(
                {'page': pagename, 'url': prefix + element.a["href"], 'message': element.text, 'scoring': scoring,
                 'datetime': str(dt)})
        else:
            logging.warning("[{0:10}]:Exists:[{1}]".format(myself, pagename))
            scoring=0
    else:
        logging.info(("[{0:10}]:Flag False {1}").format(myself, pagename))
        scoring = getPage(threadID, pagename,
                          "http://" + prefix + element.a["href"],
                          Config.get('DATA', 'Path') + pagename,
                          browserAgent,
                          proxy)
        link.append({'page': pagename, 'url': prefix + element.a["href"], 'message': element.text, 'scoring': scoring,
             'datetime': str(dt)})
    minimumScore = Config.get('DATA', 'MinimumScore')

    logging.info(("[{0:10}]:Links OK").format(myself))

    workOut.put(link)
#---------------------------------------------------
def forkLink (site, prefix, urlpages, flag, data):
    myself = whoami()
    threads = list()
    logging.info(("[{0:10}]:Starting Threads data for {1}").format(myself, site))
    queueLock = threading.Lock()
    workQueue = Queue.Queue(len(urlpages))
    workOut = Queue.Queue(2000)
    threads = []
    threadID = 1
    for i in range(len(urlpages)):
        logging.info(("[{0:10}]:Thread data for {1}").format(myself, i))
        thread = threading.Thread(target=workerThreadPage, args=(threadID, urlpages[i], site, prefix, data, workOut))
        thread.daemon
        thread.start()
        threads.append(thread)
        threadID += 1

    logging.info(("[{0:10}]:All threads started").format(myself))

    for link in urlpages:
        workQueue.put(link)
    logging.info("[{0:10}]:current data loaded".format(myself))


    for t in threads:
        t.join()

    logging.info(("[{0:10}]:Exiting Main Thread").format(myself))
    cont=0
    link=[]
    while not workOut.empty():
        linkE = workOut.get()
        for i in linkE :
            if flag:
                data[site]['URLS'].append(i)
            else:
                link.append(i)
    if not flag:
        data = json.dumps({site:{'URLS':link}})
    return data
#---------------------------------------------------
def getLinks(site,url,browserAgent,dt,Flag,proxy):
    myself=whoami()
    print ("[{0:10}] opennig mode:[{1}]").format(myself,site)
    logging.info(("[{0:10}]:opennig mode:[{1}]").format(myself,site))
    if site == 'PASTEBIN':
        prefix=Config.get('PASTEBIN','prefix')
    else:
        prefix=""
    link=[]

    if Flag:
        with open(resultsFile) as data_file:
            data = json.load(data_file)
        data_file.close()
    else:
        data = json.dumps({site:{'URLS':[]}})
    try:
        if len(proxy)>0:
            print ("[{0:10}] Try to get data from http://{2} with {1}").format(myself, proxy,
                                                                               Config.get('URL', 'GenericURL'))
            proxy_handler = urllib2.ProxyHandler(proxy)
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)

        print ("[{0:10}] Getting base data from {1}").format(myself,url)
        logging.info(("[{0:10}]:Getting base data from {1}").format(myself,url))
        req = urllib2.Request(url, headers=browserAgent)
        html = urllib2.urlopen(req).read()
    except urllib2.HTTPError as e:
        print ("[{0:10}] Fail:[{1}]".format(myself,e))
        logging.warning("[{0:10}]:Fail:[{1}]".format(myself,e))
        return None
    try:
        bsObj = BeautifulSoup(html, "lxml")
        letters = bsObj.find_all("td")
    except urllib2.HTTPError as e:
        print "[{0:10}] Fail:[{1}]".format(myself,e)
        logging.warning("[{0:10}]:Fail:[{1}]".format(myself,e))
        return None
    cont=0
    urlpages=[]
    for element in letters:
        try:
            if not re.search('\/u\/',element.a["href"]):
                urlpages.append(element)
        except: None
    print ("[{0:10}] {1} links managed").format(myself,len(urlpages))
    link = forkLink( site, prefix, urlpages, Flag, data)
    logging.info(("[{0:10}]:Links OK").format(myself))
    return json.dumps(link)
#---------------------------------------------------
def getPage (threadID, name, url, fileRaw, browserAgent, proxy):
    myself = whoami()
    myself += "-threadID-" + str(threadID)
    print ("[{0:10}] [open] data from :{1}").format(myself,url)
    logging.info("[{0:10}]:[open] data from :{1}".format(myself,url))
    minimumScore = Config.get('DATA', 'MinimumScore')
    logging.info("[{0:10}]:\tMinimum score needed :{1}".format( myself, minimumScore))
    timeout = float(Config.get('CONST', 'TimeOUT'))
    socket.setdefaulttimeout(timeout)
    req = urllib2.Request(url, headers=browserAgent)
    html = urllib2.urlopen(req).read()
    bsObj = BeautifulSoup(html,"lxml")
    scoring=0
    checks={}
    fd= open (fileRaw,'w')

    for line in str(bsObj).splitlines():
        fd.write(line+"\n")
        if VERBOSE:
            print line
        else:
            print "#",
        line.replace(" ", "")
        line.replace("`", "")
        line.replace("(\r){0,1}\n", "")
        keywords=Config.items('CODEWORDS')
        for kw in keywords:
            print ".",
            try:
                if re.search(kw[1],line.upper()):
                    print ("[{}]").format(kw[1])
                    sys.stdout.flush()
                    try :
                        checks[kw[0]]+=1
                    except:
                        checks.update({kw[0]:1})
                    scoring = scoring +int(kw[0])
            except: None
    print ("\nFinal Score: {}").format(scoring)
    sys.stdout.flush()
    logging.info("[{0:10}]:\t[score]{1}:{2}".format(myself,name,scoring))
    fd.close()
    logging.info("[{0:10}]:[close] {1} ".format(myself,url))
    if int(scoring) <= int(minimumScore):
        logging.warning("[{0:10}]:scoring lower [{1}] than minimumScore {2}".format(myself, scoring, minimumScore))
        os.remove(fileRaw)
        logging.warning("[{0:10}]:[{1}] deleted.".format(myself,name))
    print ("[{0:10}] page OK").format(myself)
    logging.info(("[{0:10}]:page OK").format(myself))
    return {'value': scoring, 'checks': checks}
#---------------------------------------------------
def scoringFILE (name, path):
    myself = whoami()
    scoring = 0
    checks = {}
    logging.info(("[{0:10}]: checking {1}").format(myself, path))
    with open(path) as data_file:
        for line in data_file:
            line.replace(" ", "")
            line.replace("`", "")
            line.replace("(\r){0,1}\n", "")
            if VERBOSE :
                print line
            else :
                print "#",
            keywords = Config.items('CODEWORDS')
            for kw in keywords:
                try:
                    if re.search(kw[1],
                                 line.upper()):
                        print ("[{}]").format(kw[0]),
                        try:
                            checks[kw[0]] += 1
                        except:
                            checks.update({kw[0]: 1})
                        scoring = scoring + int(kw[0])
                except:
                    None
        print ("\nFinal Score: {}").format(scoring)
        logging.info(("[{0:10}]: checking {1} finished").format(myself, path))
        return {'value': scoring, 'checks': checks}
#---------------------------------------------------
def existsName(data, site, page):
    val=False
    for element in data[site]['URLS']:
        if element['page'] == page:
            val = True
            break
    return val
#---------------------------------------------------
def visualizationResults (file, flag, Value):
    list=[]
    with open(file) as data_file:
        data = json.load(data_file)
    data_file.close()
    list = Config.items('SITES')
    print ("[{0:10s}]\t{1:26}\t<{2:8}>\t{3:24}\t({4:5s})\t{5}").format("SITE","Date Time","name","URL","score","DESCRIPTION")
    for idsite, site in list:
        sitename=re.sub('\'','', site)
        for element in data[sitename]['URLS']:

            if (element['scoring']['value']) > Value:
                print "[{0:10s}]\t{1:26}\t<{2:8}>\t{3}\t({4:5d})\t{5}".format(site, element['datetime'], element['page'], element['url'], element['scoring']['value'], element['message'])
            if flag:
                if len(element['scoring']['checks'])> 0:
                    print "\t\t\t\t{0:5}\t{1:10}\t{2}".format("CheckID","Num","Check")
                    for id in element['scoring']['checks']:
                        print ("\t\t\t\t{0:5}\t{1:10}\t{2}".format(id,element['scoring']['checks'][id],Config.get('CODEWORDS',id)))
#---------------------------------------------------
def GetProxyList (url):
    myself = whoami()
    aux=Config.get('CONST','MaxLoop')
    while True:
        browserAgent = GetHeaders()
        req = urllib2.Request(url, headers=browserAgent)
        print ("[{0:10}] Try to get data with {1}").format(myself, browserAgent)
        html = urllib2.urlopen(req).read()
        bsObj = BeautifulSoup(html, "lxml")
        letters = bsObj.find_all("td")
        aux=-1
        if len(letters) > 0 or aux<=0:
            break

    print ("[{0:10}] Getting data from {1}").format(myself, url)
    logging.info("[{0:10}]:Getting data from {1}".format(myself, url))
    cont = 0
    Flag = True
    proxies=[]
    for td in letters:
        if cont == 0:
            ip = td.text
            cont+=1
        elif cont == 1:
            port = td.text
            cont+=1
        elif cont == 2:
            code = td.text
            cont+=1
        elif cont == 3:
            country = td.text
            cont+=1
        elif cont == 4:
            anonymity = td.text
            cont+=1
        elif cont == 5:
            google = td.text
            cont+=1
        elif cont == 6:
            https = td.text
            cont+=1
        elif cont == 7:
            lcheck = td.text
            cont=0
            print ("{0:15} {1:5} {2:2} {3:10} {4:10} {5:3} {6:3} {7:20}").format(
                ip,port,code,country,anonymity,google,https,lcheck)
            Flag = False
            proxies.append({'ip':ip,'port':port,'code':code,'country':country,'anonymity':anonymity,'google':google,'https':https,'lcheck':lcheck})
    if not Flag:
        fd = open(Config.get('CONST','FileProxies'), "w")
        jproxy = json.dumps({'Proxies': {'data': proxies, 'datetime':str(dt)}})
        fd.write(jproxy)
        fd.close
        logging.info("[{0:10}]:file {1} created".format(myself, Config.get('CONST','FileProxies')))
    else:
        print "This site {} doesn't like this {}\ntry again !!!!".format(url, browserAgent)
# ---------------------------------------------------
def GetHeaders():
    agent = AgentSwitcher()
    random_numer = random.randrange(4)
    if random_numer >= 2:
        acceptencoding = 'none'
    else:
        acceptencoding = 'gzip, deflate'
    Headers = {'User-Agent': agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
                    'Accept-Encoding': acceptencoding,
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Connection': 'keep-alive'}
    return Headers
#------------------------------------------------
def CheckProxy():
    myself = whoami()
    if not os.path.exists(Config.get('CONST','FileProxies')):
        print ("[{0:10}] File doesn't exist [{1}]").format(myself, Config.get('CONST','FileProxies'))
        logging.warning(("[{0:10}]:File doesn't exist [{1}]").format(myself, Config.get('CONST','FileProxies')))
        GetProxyList(Config.get('URL', 'proxiesSite'))
    else:
        print ("[{0:10}] Reading data from [{1}]").format(myself, Config.get('CONST','FileProxies'))
        logging.info(("[{0:10}]:Reading data from [{1}]").format(myself, Config.get('CONST','FileProxies')))
        with open(Config.get('CONST','FileProxies')) as data_file:
            data = json.load(data_file)
        data_file.close()
        browserAgent = GetHeaders()
        for proxy in data['Proxies']['data']:
            timeout = float(Config.get('CONST', 'TimeOUT'))
            socket.setdefaulttimeout(timeout)
            req = urllib2.Request("http://"+Config.get('URL','GenericURL'), headers=browserAgent)
            proxy={"http": "http://"+proxy['ip']+":"+proxy['port']}
            print ("[{0:10}] Try to get data from http://{2} with {1}").format(myself, proxy, Config.get('URL','GenericURL'))
            logging.info("[{0:10}] Try to get data from http://{2} with {1}".format(myself, proxy, Config.get('URL','GenericURL')))
            proxy_handler = urllib2.ProxyHandler(proxy)
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)
            try:
                print ("[{0:10}] testing  [{1}]").format(myself, Config.get('URL','GenericURL'))
                logging.info(("[{0:10}]:testing  [{1}]").format(myself, Config.get('URL','GenericURL')))
                html = urllib2.urlopen(req).read()
                if len(html) > 10:
                    print ("[{0:10}] Test OK !!!").format(myself)
                    logging.info(("[{0:10}]:Test OK !!!").format(myself))
                    break
            except:
                print ("[{0:10}] TIMEOUT !!!").format(myself)
                logging.warning(("[{0:10}]:TIMEOUT !!!").format(myself))
                print "time out"
    print ("[{0:10}] proxy OK").format(myself)
    logging.info(("[{0:10}]:proxy OK").format(myself))
    return proxy
#---------------------------------------------------
def listProxies():
    if not os.path.exists(Config.get('CONST','FileProxies')):
        print "There isn't proxy file ({})or not is accesible, try with --GetProxy".format(Config.get('CONST','FileProxies'))
    else:
        with open(Config.get('CONST','FileProxies')) as data_file:
            data = json.load(data_file)
        data_file.close()
        print "Data from date: {}".format(data['Proxies']['datetime'])
        print ("{0:15} {1:5} {2:5} {3:20} {4:20} {5:7} {6:5} {7:20}").format(
        "ip", "port", "code", "country", "anonymity", "google", "https", "lcheck")
        for proxy in data['Proxies']['data']:
            print ("{0:15} {1:5} {2:5} {3:20} {4:20} {5:7} {6:5} {7:20}").format(
                proxy['ip'],proxy['port'],proxy['code'],proxy['country'],proxy['anonymity'],proxy['google'],proxy['https'],proxy['lcheck'])
#---------------------------------------------------
def updateDIR():
    myself = whoami()
    with open(resultsFile) as data_file:
        data = json.load(data_file)
    data_file.close()
    #list = Config.items('SITES')
    site = 'PASTEBIN'
    logging.info(("[{0:10}]: Results loaded").format(myself))
    print "[{0:10}]: Results loaded".format(myself)
    #print ("[{0:10s}]\t{1:26}\t<{2:8}>\t{3:24}\t({4:5s})\t{5}").format("SITE", "Date Time", "name", "URL", "score",
    #                                                                   "DESCRIPTION")
    aux=[]
    conjunto = []
    cont=0;
    for element in data[site]['URLS']:
        cont+=1;
        print "checking {}".format(element['page'])
        print (Config.get('DATA', 'Path')+element['page'])
        print element
        if os.path.exists(Config.get('DATA', 'Path')+element['page']):
            print "in conjunto {}".format(element['page'])
            aux.append(element)
            conjunto.append(element['page'])
        else:
            print "{} doesn't exits in {}".format(element['page'], Config.get('DATA', 'Path'))
            logging.warning("{} doesn't exits in {}".format(element['page'], Config.get('DATA', 'Path')))
            #data[site]['URLS'].remove(element)ç
            # ni remove ni pop ni del funcionan correctamente, meto un auxiliar
    dtaux = str(dt)
    print "[{0:10}]: Checking {1}".format(myself,Config.get('DATA', 'Path'))
    for filename in os.listdir(Config.get('DATA', 'Path')):
        if not filename in conjunto and not filename.startswith('.'):
            print "[{0:10}]: {1} Not exist in results file".format(myself,filename)
            scoring = scoringFILE(filename, Config.get('DATA', 'Path')+filename)
            print "+"
            aux.append(
                {"page": filename, "url": "pastebin.com/raw/" + filename, "message": "_backup",
                 "scoring": scoring,
                 "datetime": dtaux})
    data[site]['URLS']=aux
    return json.dumps(data)

#---------------------------------------------------
#---------------------------------------------------
logging.info("[BEGIN]")
dt=datetime.datetime.now()

if not os.path.exists(Config.get('LOG', 'Path')) :
    print ('Dir {} not found, created').format(Config.get('LOG', 'Path'))
    logging.warning('Dir {} not found, created').format(Config.get('LOG', 'Path'))
    os.makedirs(Config.get('LOG', 'Path'))

if not os.path.exists(Config.get('DATA', 'Path')) :
    print ('Dir {} not found, created').format(Config.get('DATA', 'Path'))
    logging.warning('Dir {} not found, created').format(Config.get('DATA', 'Path'))
    os.makedirs(Config.get('DATA', 'Path'))

if args.fileAgent:
    agentsFile = args.fileAgent
else:
    agentsFile = Config.get('CONST', 'FileAgents')


if args.Verbose:
    VERBOSE = True


if args.ChangeAgent:
    browserAgent = GetHeaders()

if args.AddProxies:
    proxy=CheckProxy()

if args.GetProxy:
    GetProxyList(Config.get('URL', 'proxiesSite'))
elif not os.path.exists(agentsFile) or args.GetAgents:
    print ('Agent file {} not found, getting data from {} or updating Agents file').format(agentsFile, Config.get('URL', 'userAgents'))
    logging.warning(("Agent file {} not found, getting data from {} or updating Agents file").format(agentsFile,Config.get('URL','userAgents')))
    Agents = getAgents(Config.get('URL', 'userAgents'))
    fd= open (agentsFile,'w')
    for agent in Agents:
        fd.write(agent+'\n')
        print "#",

    fd.close()
elif args.GetProxy:
    GetProxyList (Config.get('URL','proxiesSite'))
elif args.CheckProxy:
    proxy=CheckProxy()
    print proxy
elif args.ListProxies:
    listProxies()
elif args.CheckResults or args.CheckResultsDeeper:
    flag=False
    Value=0
    if args.CheckResultsDeeper: flag=True
    if args.minimumScore: Value=args.minimumScore
    visualizationResults(resultsFile, flag, Value)
elif args.ScoreFile:
    print args.ScoreFile
    if os.path.exists(args.ScoreFile):
        data= re.search('(\w+[-\w*]*)$',args.ScoreFile)
        name=data.group(1)
        site='PASTEBIN'
        scoring = scoringFILE(name, args.ScoreFile )
        dtaux = str(dt)
        print json.dumps({"page":name, "url": "pastebin.com/raw/"+name, "message": "_backup", "scoring":scoring, "datetime":dtaux  })
        if args.FileScoringADD:
            with open(resultsFile) as data_file:
                data = json.load(data_file)
            data_file.close()
            data[site]['URLS'].append(json.dumps({"page":name, "url": "pastebin.com/raw/"+name, "message": "_backup", "scoring":scoring, "datetime":dtaux  }))
    else:
        print "{} doesn't exist o your haven't rights".format(args.ScoreFile)
elif args.UpdateDIR:
    pages=updateDIR()
    fd = open(resultsFile, "w")
    fd.write(pages)
    fd.close
else:
    print ("Browser Agent:[{}]").format(browserAgent)
    Flag = False
    if os.path.exists(resultsFile) : Flag = True
    logging.info(("Browser Agent:{}").format(browserAgent))

    url=Config.get('PASTEBIN','pastebinTrend')

    if args.Week:
        url += Config.get('PASTEBIN','pastebinWeek')
    elif args.Month:
        url += Config.get('PASTEBIN', 'pastebinMonth')
    elif args.Year:
        url += Config.get('PASTEBIN', 'pastebinYear')
    elif args.User:
        url = Config.get('PASTEBIN', 'pastebinBase') + Config.get('PASTEBIN', 'pastebinUser') + "/" + args.User
        print "NO VA DE MOMENTO"
        exit(0)
    if VERBOSE:
        print "URL:{}".format(url)
    pages = getLinks('PASTEBIN',url ,browserAgent,dt,Flag,proxy)
    fd = open(resultsFile, "w")
    fd.write(pages)
    fd.close
dt=datetime.datetime.now()-dt
logging.info("Time Elapsed {}".format(dt))
logging.info("[END]")
