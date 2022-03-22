#!/usr/bin/python3
import datetime
import json
import logging
import os
import pathlib
import pdb
import random
import time

import pycountry
import requests
from bs4 import BeautifulSoup
import configparser
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from seleniumrequests import Firefox

dir_path = str(pathlib.Path(__file__).parent.resolve())

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.FileHandler(dir_path + "/messages_proxy_helper.log")
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

config = configparser.ConfigParser()
config.read(dir_path+'/get_proxy_config.ini')

proxy_dir = dir_path + "/dir_proxies"

if not os.path.exists(proxy_dir):
    os.makedirs(proxy_dir)

HEADERS_LIST = [
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; x64; fr; rv:1.9.2.13) Gecko/20101203 Firebird/3.6.13',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
    'Mozilla/5.0 (Windows NT 5.2; RW; rv:7.0a1) Gecko/20091211 SeaMonkey/9.23a1pre',
    'Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
]
headers = {'User-Agent': random.choice(HEADERS_LIST)}

countries = {}
for country in pycountry.countries:
    countries[country.name] = country.alpha_2


def get_ip_cc(ip):
    """
    Get CountryCode (CC) for IP
    :param ip: string IPv4 Address
    :return: CC two letter string - CountryCode
    """
    request_url = 'https://geolocation-db.com/jsonp/' + ip
    response = requests.get(request_url)
    result = response.content.decode()
    # Clean the returned string so it just contains the dictionary data for the IP address
    result = result.split("(")[1].strip(")")
    # Convert this data into a dictionary
    result = json.loads(result)
    time.sleep(1)

    cc = result["country_code"]

    return cc


def parse_siteA():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []
    url = config["DEFAULT"]["siteA"]
    try:
        req = requests.get(url, timeout=5, headers=headers)

        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, 'html.parser')
        else:
            logger.info("{} - {}".format(req.status_code, req.reason))
            raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))

        soup = BeautifulSoup(req.text, 'html.parser')

        table = soup.find("table", {'class': "table table-striped table-bordered"}).tbody.children

        datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        foldername = datetime.datetime.now().strftime("%Y%m%d")
        year = datetime.datetime.now().strftime("%Y")
        path = proxy_dir + "/" + year + "/" + foldername
        # path =  proxy_dir
        os.makedirs(path, exist_ok=True)

        with open("{}/ListA_{}.txt".format(path, str(int(time.time()))), "w") as g:
            for tr in table:
                tds = tr.findAll("td")
                ip = tds[0].text
                port = tds[1].text
                cc = tds[2].text

                cc2 = "--" if len(cc) == 2 else get_ip_cc(ip)

                cc0 = cc if cc != "--" else cc2

                ssl_proxies.append("{}:{}".format(ip, port))

                line = ",".join([ip, port, cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteA from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_siteB():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []
    url = config["DEFAULT"]["siteB"]
    try:
        req = requests.get(url, timeout=5, headers=headers)

        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, 'html.parser')
        else:
            raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))

        soup = BeautifulSoup(req.text, 'html.parser')

        tables = soup.find(id="page")
        if tables is None:
            raise Exception("No table found on page siteB")

        table = tables.find_all("table")[2].find_all("tr")[2:]

        foldername = datetime.datetime.now().strftime("%Y%m%d")
        year = datetime.datetime.now().strftime("%Y")
        path = proxy_dir + "/" + year + "/" + foldername
        # path =  proxy_dir
        os.makedirs(path, exist_ok=True)
        with open("{}/ListB_{}.txt".format(path, str(int(time.time()))), "w") as g:
            for tr in table:
                tds = tr.findAll("td")

                ip = tds[1].text
                port = tds[2].text
                cc = tds[4].text

                cc = countries[cc] if cc in countries.keys() else cc

                cc2 = "--" if len(cc) == 2 else get_ip_cc(ip)

                cc0 = cc if len(cc) == 2 else cc2

                ssl_proxies.append("{}:{}".format(ip, port))
                line = ",".join([ip, port, cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteB from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_siteC():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []
    url = config["DEFAULT"]["siteC"]
    try:
        req = requests.get(url, timeout=5, headers=headers)

        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, 'html.parser')
        else:
            logger.info("{} - {}".format(req.status_code, req.reason))
            raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))

        soup = BeautifulSoup(req.text, 'html.parser')
        table = soup.find(id="tbl_proxy_list").tbody.findAll("tr")

        foldername = datetime.datetime.now().strftime("%Y%m%d")
        year = datetime.datetime.now().strftime("%Y")
        path = proxy_dir + "/" + year + "/" + foldername
        # path =  proxy_dir
        os.makedirs(path, exist_ok=True)

        with open("{}/ListC_{}.txt".format(path, str(int(time.time()))), "w") as g:
            counter = 0
            for tr in table:
                if tr.find("div", {"class": "ad728x90"}):
                    continue
                tds = tr.findAll("td")

                # ip1 = tds[0].find("abbr").text[24:].replace(");","").split("+")[0].replace(".substr(8)","")[:-2]
                # ip2 = tds[0].find("abbr").text[24:].replace(");","").split("+")[1][2:-2]
                # ip = tds[0].find("abbr").text[17:].split("\'")[0]
                ip = str(tds[0].find("abbr").find("script"))[24:].split("\'")[0]
                port = tds[1].text.strip()
                # port = tds[2].text

                cc = tds[5].text.strip().replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")

                cc = countries[cc] if cc in countries.keys() else cc

                cc2 = "--" if len(cc) == 2 else get_ip_cc(ip)

                cc0 = cc if len(cc) == 2 else cc2

                ssl_proxies.append("{}:{}".format(ip, port))
                line = ",".join([ip, port, cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteC from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_siteD():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []
    url = config["DEFAULT"]["siteD"]
    try:
        req = requests.get(url, timeout=5, headers=headers)

        if req.status_code == requests.codes.ok:
            all_data = json.loads(req.text)

        else:
            logger.info("{} - {}".format(req.status_code, req.reason))
            raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))

        foldername = datetime.datetime.now().strftime("%Y%m%d")
        year = datetime.datetime.now().strftime("%Y")
        path = proxy_dir + "/" + year + "/" + foldername
        # path =  proxy_dir
        os.makedirs(path, exist_ok=True)
        with open("{}/ListD_{}.txt".format(path, str(int(time.time()))), "w") as g:
            for pag in all_data:
                ip = pag["ip"]
                port = pag["port"]
                cc = pag["country_code"]
                cc = countries[cc] if cc in countries.keys() else cc

                cc2 = "--" if cc != "--" else get_ip_cc(ip)

                cc0 = cc if len(cc) == 2 else cc2
                cc0 = cc2 if cc0 == "--" else cc

                ssl_proxies.append("{}:{}".format(ip, port))
                line = ",".join([ip, str(port), cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies

    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteD from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_siteE():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []
    url = config["DEFAULT"]["siteE"]
    try:
        req = requests.get(url, timeout=5, headers=headers)
        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, 'html.parser')
        else:
            logger.info("{} - {}".format(req.status_code, req.reason))
            raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))

        soup = BeautifulSoup(req.text, 'html.parser')
        table = soup.find("div", {"class": "table-responsive fpl-list"}).tbody.findAll("tr")
        foldername = datetime.datetime.now().strftime("%Y%m%d")
        year = datetime.datetime.now().strftime("%Y")
        path = proxy_dir + "/" + year + "/" + foldername
        # path =  proxy_dir

        os.makedirs(path, exist_ok=True)

        with open("{}/ListE_{}.txt".format(path, str(int(time.time()))), "w") as g:
            counter = 0
            for tr in table:
                tds = tr.findAll("td")

                ip = str(tds[0])[4:-5]
                port = str(tds[1])[4:-5]
                cc = str(tds[2])[4:-5]

                cc = countries[cc] if cc in countries.keys() else cc

                cc2 = "--" if len(cc) == 2 else get_ip_cc(ip)

                cc0 = cc if len(cc) == 2 else cc2
                cc0 = cc2 if cc0 == "--" else cc

                ssl_proxies.append("{}:{}".format(ip, port))

                line = ",".join([ip, port, cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteE from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_siteF():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []

    foldername = datetime.datetime.now().strftime("%Y%m%d")
    year = datetime.datetime.now().strftime("%Y")
    path = proxy_dir + "/" + year + "/" + foldername
    # path =  proxy_dir

    os.makedirs(path, exist_ok=True)

    try:
        with open("{}/ListF_{}.txt".format(path, str(int(time.time()))), "w") as g:
            # list_f=[1,64,128]
            list_f = [1]

            for i in range(0, len(list_f)):
                # url = "https://hidemy.name/en/proxy-list/?type=s&anon=4&start=1#list"
                url = config["DEFAULT"]["siteF"] + str(list_f[i]) + "#list"
                req = requests.get(url, timeout=5, headers=headers)
                u = req.text
                u = u.encode('unicode-escape').decode('utf-8')
                if req.status_code == requests.codes.ok:
                    soup = BeautifulSoup(u, 'html.parser')
                else:
                    logger.info("{} - {}".format(req.status_code, req.reason))
                    raise requests.exceptions.RequestException("{} - {}".format(req.status_code, req.reason))
                soup = BeautifulSoup(u, 'html.parser')
                table = soup.find("div", {"class": "table_block"}).tbody.findAll("tr")
                # counter = 0
                for tr in table:
                    tds = tr.findAll("td")
                    ip = str(tds[0])[4:-5]
                    port = str(tds[1])[4:-5]
                    if tds[2].find("span", {"class": "country"}):
                        cc = str(tds[2].find("span", {"class": "country"}))[22:-7]
                    else:
                        cc = ""

                    cc = countries[cc] if cc in countries.keys() else cc

                    cc2 = "--" if len(cc) == 2 else get_ip_cc(ip)

                    cc0 = cc if len(cc) == 2 else cc2
                    cc0 = cc2 if cc0 == "--" else cc

                    ssl_proxies.append("{}:{}".format(ip, port))
                    line = ",".join([ip, port, cc0, cc, cc2])
                    g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteF from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def parse_api_siteG():
    """
    Crawls proxies site, write to csv file of format IP,PORT,CC and return array of sockets
    :return: array of sockets of type IP:PORT
    """
    ssl_proxies = []

    foldername = datetime.datetime.now().strftime("%Y%m%d")
    year = datetime.datetime.now().strftime("%Y")
    path = proxy_dir + "/" + year + "/" + foldername
    # path =  proxy_dir

    os.makedirs(path, exist_ok=True)

    try:
        # with open("{}/api_proxyscrape.txt".format(path),"w") as g:
        with open("{}/ListG_{}.txt".format(path, str(int(time.time()))), "w") as g:
            url = config["DEFAULT"]["siteG"]
            req = requests.get(url, timeout=5, headers=headers)
            u = req.text
            # u=u.encode('unicode-escape').decode('utf-8')

            for tr in u.splitlines():
                # print(tr)
                # tr=tr.replace(":",",")
                x = tr.split(":")
                ip = x[0]
                port = x[1]
                cc = "--"

                cc2 = get_ip_cc(ip)

                cc0 = cc if len(cc) == 2 else cc2
                cc0 = cc2 if cc0 == "--" else cc

                ssl_proxies.append("{}:{}".format(ip, port))

                line = ",".join([ip, port, cc0, cc, cc2])
                g.write(line + "\n")

        return ssl_proxies
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.warning("Err getting siteG from {}, ".format(url, str(e)))
        return []

    except Exception as e:
        logger.error(str(e))
        return []


def get_all_proxies():
    global all_list
    aa = parse_siteA()
    # print(aa)

    bb = parse_siteB()
    # print(bb)

    cc = parse_siteC()
    # print(cc)

    dd = parse_siteD()
    # print(dd)

    ee = parse_siteE()
    # print(ee)

    ff = parse_siteF()
    # print(ff)

    gg = parse_api_siteG()
    # print(gg)

    # with open(os.path.join(proxy_dir, 'proxy.txt'),"w") as g:
    #    g.write("\n".join(aa+bb+cc+dd+ee++ff+gg).replace(":",","))

logger.debug("Start")
get_all_proxies()
logger.debug("END")
