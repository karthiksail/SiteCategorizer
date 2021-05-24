import random
import json
import requests 
import hashlib
import os
import time
import datetime
import pickle
from urllib.parse import urlparse



class SiteReview(object): 
    def __init__(self) : 
        self.CookiesFileName = "Bluecoat.cookies"
        self.FirstReqHeader =  {
                                    "Host": "sitereview.bluecoat.com",
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                                    "Accept-Language": "en-US,en;q=0.5",
                                    "Accept-Encoding": "gzip, deflate, br",
                                    "Connection": "keep-alive",
                                    "Upgrade-Insecure-Requests": "1"
                                }
        self.RestReqHeader = {
                                    "Host": "sitereview.bluecoat.com",
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
                                    "Accept": "application/json, text/plain, */*",
                                    "Accept-Language": "en_US",
                                    "Accept-Encoding": "gzip, deflate, br",
                                    "Content-Type": "application/json; charset=utf-8",
                                    "Content-Length": "0",
                                    "Origin": "https://sitereview.bluecoat.com",
                                    "Connection": "keep-alive",
                                    "Referer": "https://sitereview.bluecoat.com/",      
                                }
        self.BlueCoatBaseUrl = "https://sitereview.bluecoat.com/"
        self.NeedCaptachaUrl = "https://sitereview.bluecoat.com/resource/captcha-request"
        self.SiteCatLookupUrl = "https://sitereview.bluecoat.com/resource/lookup"
        self.LocalCache = self.LoadCache()
        self.AutoSaveCacheCounter = 0
        self.AutoSaveCacheForEvery = 1
        self.LastRequestTime = time.time()
        self.CoolingTime = 8.0

    def GetBaseUrl(self, url):
        parsed_uri = urlparse(url)
        if parsed_uri.scheme == '':
            parsed_uri.scheme == "http"
        if parsed_uri.netloc == '':
            if not parsed_uri.path == '':
                parsed_uri = parsed_uri.path
        return '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    def SaveCache(self):
        PreviousCache = {}
        if os.path.exists("LocalCache") :
            with open('LocalCache', 'rb') as handle:
                PreviousCache=   pickle.load(handle)
        PreviousCache.update(self.LocalCache)
        with open("LocalCache", 'wb') as handle:
            pickle.dump(PreviousCache, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def LoadCache(self):
        emptyDict = dict()
        if os.path.exists("LocalCache") :
            with open('LocalCache', 'rb') as handle:
                return  pickle.load(handle)
        else :
            return emptyDict

    def GetNetLoc(self, url):
        parsed_uri = urlparse(url)
        return '{uri.netloc}'.format(uri=parsed_uri)

    def encrypt_string(self,hash_string):
        sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
        return sha_signature

    def BlueCoatReqPost(self,url, headers,payload,allow_redirects):
        r = requests.post(url,headers=headers,data=payload,allow_redirects=allow_redirects)
        return r
    def BlueCoatReqGet(self):
        r = requests.get(self.BlueCoatBaseUrl, headers = self.FirstReqHeader)
        return r

        
    def BlueCoatGetSiteCategory(self,url) :
        Key = self.GetNetLoc(url)
        
        if Key in self.LocalCache :
            return "OK" ,Key, self.LocalCache[Key]
        else :
            SearchUrl = self.GetBaseUrl(url)
            timeDif = time.time() - self.LastRequestTime 
            if timeDif < self.CoolingTime:
                time.sleep(self.CoolingTime - timeDif)
            headers = self.RestReqHeader
            payload = json.dumps({"url": SearchUrl, "captcha":"", "key" : self.encrypt_string(headers["X-XSRF-TOKEN"] +  headers["X-XSRF-TOKEN"].split("-")[random.randrange(0, len(headers["X-XSRF-TOKEN"].split("-")), 1 )] )})
            headers["Content-Length"] = str(len(payload))
            resp =  self.BlueCoatReqPost(self.SiteCatLookupUrl,headers,payload,True)
            self.LastRequestTime = time.time()
            if resp.status_code == 200:
                content =  resp.content.decode('utf-8', 'ignore')
                if not content.startswith("<!DOCTYPE html>"):
                    JsonValue =json.loads(content)  
                    if "curTrackingId" in JsonValue :
                        self.LocalCache[Key] = JsonValue
                        if self.AutoSaveCacheCounter % self.AutoSaveCacheForEvery == 0 :
                            # print("Saving Cache")
                            self.SaveCache()
                        self.AutoSaveCacheCounter = self.AutoSaveCacheCounter + 1
                        return "OK" ,SearchUrl, JsonValue
                    elif "errorMessage" in JsonValue:
                        return "CATCHED" + str(resp.status_code) ,SearchUrl, resp.content
                else :
                    return "CATCHED"  + str(resp.status_code) ,SearchUrl, resp.content
            else : 
                return "NA Status Code:" + str(resp.status_code),SearchUrl, resp.content

        
    def BlueCoatNeedCaptacha(self,allow_redirects) :
        headers = self.RestReqHeader
        payload = '''{"check":"captcha"}'''
        headers["Content-Length"] = str(len(payload))
        resp = self.BlueCoatReqPost(self.NeedCaptachaUrl,headers,payload,allow_redirects)
        if resp.status_code == 200:
            if resp.content == b'{"required":false}':
                return "OK", None
            else :
                return "NOTOK", {"content" : resp.content}
        elif resp.status_code == 302:
            if "Set-Cookie" in resp.headers:
                if "XSRF-TOKEN=" in resp.headers["Set-Cookie"]:
                    return "SETXSRF" , {"X-XSRF-TOKEN" : resp.headers["Set-Cookie"].split(";")[0] }
                else :
                    return "XSRFNOTFOUND" , {"Set-Cookie" : resp.headers["Set-Cookie"]}
            else:
                return "NOCOOKIES" , {"headers" : resp.headers }
        else :
            return "FAILED", {"resp" : resp}

    def InitTheBlueCoat(self):
        InitRes = self.BlueCoatReqGet()
        if InitRes.status_code == 200 :
            if "Set-Cookie" in InitRes.headers:
                if "JSESSIONID=" in InitRes.headers["Set-Cookie"]:
                    f = open(self.CookiesFileName, "w")
                    f.write(InitRes.headers["Set-Cookie"])
                    f.close()
                    self.RestReqHeader["Cookie"] = InitRes.headers["Set-Cookie"].split(";")[0]
                    Status , CheckCaptachaRes = self.BlueCoatNeedCaptacha(False)
                    if Status == "SETXSRF":
                        f = open(self.CookiesFileName, "a+")
                        f.write("\n")
                        f.write(CheckCaptachaRes["X-XSRF-TOKEN"])
                        f.close()
                        self.RestReqHeader["Cookie"] = self.RestReqHeader["Cookie"] + " ; " + CheckCaptachaRes["X-XSRF-TOKEN"]
                        self.RestReqHeader["X-XSRF-TOKEN"] = CheckCaptachaRes["X-XSRF-TOKEN"].split("=")[1]
                        return "OK"
                    elif Status == "OK" :
                        return "OK"
                    else :
                        return Status, CheckCaptachaRes
                else :
                    return "Problem in loadintg Site : JSEESIONID not Found"
            else :
                return "Problem in loading site : Cookies not got"
        else :
            return "Problem in loading site Status Code : " + str(InitRes.status_code), InitRes

    def LoadBlueCoat(self):
        if os.path.exists(self.CookiesFileName):
            f = open(self.CookiesFileName, "r")
            Lines = f.readlines() 
            f.close()
            for line in Lines :
                if "JSESSIONID=" in line :
                    self.RestReqHeader["Cookies"] = line.split(";")[0]
                elif "XSRF-TOKEN="  in line :
                    self.RestReqHeader["X-XSRF-TOKEN"] = line.split(";")[0].split("=")[1]
                    self.RestReqHeader["Cookies"] = self.RestReqHeader["Cookies"] + " ; " +line.split(";")[0]
                else :
                    self.InitTheBlueCoat()
                    return "Initlaized since no JSESSIONID or  Xref"
            return "Loaded From Cookies"
        else:  
            self.InitTheBlueCoat()
            return "Initlaized"

    def CloseBlueSuite(self):
        self.SaveCache()
