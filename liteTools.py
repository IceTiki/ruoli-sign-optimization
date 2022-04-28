import time
from typing import Sequence
import requests
import yaml
import math
import random
import os
from Crypto.Cipher import AES
from pyDes import des, CBC, PAD_PKCS5
import base64
import hashlib
import urllib.parse
import re
import json
import imghdr
from requests_toolbelt import MultipartEncoder
import datetime

import checkRepositoryVersion


class TaskError(Exception):
    '''目前(配置/时间/签到情况)不宜完成签到任务，出现本异常不进行重试。'''

    def __init__(self, msg="目前(配置/时间/签到情况)不宜完成签到任务", code=301):
        self.msg = str(msg)
        self.code = code

    def __str__(self):
        return self.msg


class TT:
    '''time Tools'''
    startTime = time.time()

    @staticmethod
    def isInTimeList(timeRanges, nowTime: float = startTime):
        '''判断(在列表中)是否有时间限定字符串是否匹配时间
        :params timeRages: 时间限定字符串列表。
            :时间限定字符串是形如"1,2,3 1,2,3 1,2,3 1,2,3 1,2,3"形式的字符串。
            :其各位置代表"周(星期几) 月 日 时 分", 周/月/日皆以1开始。
            :可以以"2-5"形式代表时间范围。比如"3,4-6"就等于"3,4,5,6"
        :params nowTime: 时间戳
        :return bool: 在列表中是否有时间限定字符串匹配时间
        '''
        timeRanges = DT.formatStrList(timeRanges)
        for i in timeRanges:
            if TT.isInTime(i, nowTime):
                return True
            else:
                pass
        else:
            return False

    @staticmethod
    def isInTime(timeRange: str, nowTime: float = startTime):
        '''
        判断时间限定字符串是否匹配时间
        :params timeRage: 时间限定字符串。
            :是形如"1,2,3 1,2,3 1,2,3 1,2,3 1,2,3"形式的字符串。
            :其各位置代表"周(星期几) 月 日 时 分", 周/月/日皆以1开始。
            :可以以"2-5"形式代表时间范围。比如"3,4-6"就等于"3,4,5,6"
        :params nowTime: 时间戳
        :return bool: 时间限定字符串是否匹配时间
        '''
        # 判断类型
        if type(timeRange) != str:
            raise TypeError(
                f"timeRange(时间限定字符串)应该是字符串, 而不是『{type(timeRange)}』")
        # 判断格式
        if not re.match(r"^(?:\d+-?\d*(?:,\d+-?\d*)* ){4}(?:\d+-?\d*(?:,\d+-?\d*)*)$", timeRange):
            raise Exception(f'『{timeRange}』不是正确格式的时间限定字符串')
        # 将时间范围格式化

        def formating(m):
            '''匹配a-e样式的字符串替换为a,b,c,d,e样式'''
            a = int(m.group(1))
            b = int(m.group(2))
            if a > b:
                a, b = b, a
            return ','.join([str(i) for i in range(a, b)]+[str(b)])
        timeRange = re.sub(r"(\d*)-(\d*)", formating, timeRange)
        # 将字符串转为二维整数数组
        timeRange = timeRange.split(' ')
        timeRange = [[int(j) for j in i.split(',')] for i in timeRange]
        # 将当前时间格式化为"周 月 日 时 分"
        nowTime = tuple(time.localtime(nowTime))
        nowTime = (nowTime[6]+1, nowTime[1],
                   nowTime[2], nowTime[3], nowTime[4])
        for a, b in zip(nowTime, timeRange):
            if a not in b:
                return False
            else:
                pass
        else:
            return True


class LL:
    '''lite log'''
    prefix = checkRepositoryVersion.checkCodeVersion()
    startTime = TT.startTime
    log_list = []
    printLevel = 0
    logTypeDisplay = ['debug', 'info', 'warn', 'error', 'critical']

    @staticmethod
    def formatLog(logType: str, args):
        '''返回logItem[时间,类型,内容]'''
        string = ''
        for item in args:
            if type(item) == dict or type(item) == list:
                string += yaml.dump(item, allow_unicode=True)+'\n'
            else:
                string += str(item)+'\n'
        return [time.time()-LL.startTime, logType, string]

    @staticmethod
    def log2FormatStr(logItem):
        logType = LL.logTypeDisplay[logItem[1]]
        return '|||%s|||%s|||%0.3fs|||\n%s' % (LL.prefix, logType, logItem[0], logItem[2])

    @staticmethod
    def log(logType=1, *args):
        '''日志函数
        logType:int = debug:0|info:1|warn:2|error:3|critical:4'''
        if not args:
            return
        logItem = LL.formatLog(logType, args)
        LL.log_list.append(logItem)
        if logType >= LL.printLevel:
            print(LL.log2FormatStr(logItem))

    @staticmethod
    def getLog(level=0):
        '''获取日志函数'''
        string = ''
        for item in LL.log_list:
            if level <= item[1]:
                string += LL.log2FormatStr(item)
        return string

    @staticmethod
    def saveLog(dir, level=0):
        '''保存日志函数'''
        if type(dir) != str:
            return

        log = LL.getLog(level)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        dir = os.path.join(dir, time.strftime(
            "LOG#t=%Y-%m-%d--%H-%M-%S##.txt", time.localtime()))
        with open(dir, 'w', encoding='utf-8') as f:
            f.write(log)


class CpdailyTools:
    '''今日校园相关函数'''
    desKey = 'XCE927=='
    aesKey = b"SASEoK4Pa5d4SssO"
    aesKey_str = "SASEoK4Pa5d4SssO"

    @staticmethod
    def encrypt_CpdailyExtension(text, key=desKey):
        '''CpdailyExtension加密'''
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        d = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)

        text = d.encrypt(text)  # 加密
        text = base64.b64encode(text)  # base64编码
        text = text.decode()  # 解码
        return text

    @staticmethod
    def decrypt_CpdailyExtension(text, key=desKey):
        '''CpdailyExtension加密'''
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        d = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)

        text = base64.b64decode(text)  # Base64解码
        text = d.decrypt(text)  # 解密
        text = text.decode()  # 解码
        return text

    @staticmethod
    def encrypt_BodyString(text, key=aesKey):
        """BodyString加密"""
        iv = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\x01\x02\x03\x04\x05\x06\x07'
        cipher = AES.new(key, AES.MODE_CBC, iv)

        text = CT.pkcs7padding(text)  # 填充
        text = text.encode(CT.charset)  # 编码
        text = cipher.encrypt(text)  # 加密
        text = base64.b64encode(text).decode(CT.charset)  # Base64编码
        return text

    @staticmethod
    def decrypt_BodyString(text, key=aesKey):
        """BodyString解密"""
        iv = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\x01\x02\x03\x04\x05\x06\x07'
        cipher = AES.new(key, AES.MODE_CBC, iv)

        text = base64.b64decode(text)  # Base64解码
        text = cipher.decrypt(text)  # 解密
        text = text.decode(CT.charset)  # 解码
        text = CT.pkcs7unpadding(text)  # 删除填充
        return text

    @staticmethod
    def signAbstract(submitData: dict, key=aesKey_str):
        '''表单中sign项目生成'''
        abstractKey = ["appVersion", "bodyString", "deviceId", "lat",
                       "lon", "model", "systemName", "systemVersion", "userId"]
        abstractSubmitData = {k: submitData[k] for k in abstractKey}
        abstract = urllib.parse.urlencode(abstractSubmitData) + '&' + key
        abstract_md5 = HSF.strHash(abstract, 5)
        return abstract_md5

    @staticmethod
    def baiduGeocoding(address: str):
        '''地址转坐标'''
        # 获取百度地图API的密钥
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        url = 'https://feres.cpdaily.com/bower_components/baidumap/baidujsSdk@2.js'
        res = requests.get(url, headers=headers, verify=False)
        baiduMap_ak = re.findall(r"ak=(\w*)", res.text)[0]
        # 用地址获取相应坐标
        url = f'http://api.map.baidu.com/geocoding/v3'
        params = {
            "output": "json", "address": address, "ak": baiduMap_ak}
        res = requests.get(
            url, headers=headers, params=params, verify=False)
        res = DT.resJsonEncode(res)
        lon = res['result']['location']['lng']
        lat = res['result']['location']['lat']
        return (lon, lat)

    @staticmethod
    def baiduReverseGeocoding(lon: float, lat: float):
        '''地址转坐标'''
        # 获取百度地图API的密钥
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        url = 'https://feres.cpdaily.com/bower_components/baidumap/baidujsSdk@2.js'
        res = requests.get(url, headers=headers, verify=False)
        baiduMap_ak = re.findall(r"ak=(\w*)", res.text)[0]
        # 用地址获取相应坐标
        url = f'http://api.map.baidu.com/reverse_geocoding/v3'
        params = {
            "output": "json", "location": "%f,%f" % (lon, lat), "ak": baiduMap_ak}
        res = requests.get(url, headers=headers, params=params, verify=False)
        res = DT.resJsonEncode(res)
        address = res['result']['formatted_address']
        return address

    @staticmethod
    def uploadPicture(url, session, picBlob, picType):
        '''上传图片到阿里云oss'''
        res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps({'fileType': 1}),
                           verify=False)
        datas = DT.resJsonEncode(res).get('datas')
        fileName = datas.get('fileName')
        policy = datas.get('policy')
        accessKeyId = datas.get('accessid')
        signature = datas.get('signature')
        policyHost = datas.get('host')
        ossKey = f'{fileName}.{picType}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'
        }
        multipart_encoder = MultipartEncoder(
            fields={  # 这里根据需要进行参数格式设置
                'key': ossKey, 'policy': policy, 'AccessKeyId': accessKeyId,
                'signature': signature, 'x-obs-acl': 'public-read',
                'file': ('blob', picBlob, f'image/{picType}')
            })
        headers['Content-Type'] = multipart_encoder.content_type
        res = session.post(url=policyHost,
                           headers=headers,
                           data=multipart_encoder)
        return ossKey

    @staticmethod
    def getPictureUrl(url, session, ossKey):
        '''获取图片上传位置'''
        params = {'ossKey': ossKey}
        res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(params),
                           verify=False)
        photoUrl = res.json().get('datas')
        return photoUrl


class NT:
    '''NetTools'''
    @staticmethod
    def isDisableProxies(proxies: dict):
        '''
        检查代理是否可用
        :return 如果代理正常返回0，代理异常返回1
        '''
        try:
            requests.get(url='https://www.baidu.com/',
                         proxies=proxies, timeout=20)
        except requests.RequestException as e:
            LL.log(4, f'代理[{proxies}]存在问题\n错误: [{e}]')
            return 1
        LL.log(1, f'代理[{proxies}]可用')
        return 0


class MT:
    '''MiscTools'''
    @staticmethod
    def geoDistance(lon1, lat1, lon2, lat2):
        '''两经纬度算距离'''
        # 经纬度转换成弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [float(
            lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2-lon1
        dlat = lat2-lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2*math.asin(math.sqrt(a))*6371393  # 地球平均半径，6371393m
        return distance


class PseudoRandom:
    '''随机数种子临时固定类(用于with语句)'''

    def __init__(self, seed=time.time()):
        self.seed = str(seed)
        random.seed(self.seed, version=2)

    def __enter__(self):
        return self.seed

    def __exit__(self, exc_type, exc_val, exc_tb):
        random.seed(str(time.time()), version=2)


class RT:
    '''randomTools'''
    default_offset = 50
    default_location_round = 6

    @staticmethod
    def locationOffset(lon, lat, offset=default_offset, round_=default_location_round):
        '''经纬度随机偏移(偏移不会累积)
        lon——经度
        lat——纬度
        offset——偏移范围(单位m)
        round_——保留位数
        '''
        lon = float(lon)
        lat = float(lat)
        if offset == 0:
            return (lon, lat)
        # 限定函数(经度-180~180，维度-90~90)

        def limit(n, a, b):
            if n < a:
                n = a
            if n > b:
                n = b
            return n
        # 弧度=弧长/半径，角度=弧长*180°/π，某地经度所对应的圆半径=cos(|维度|)*地球半径
        # ==纬度==
        # 偏移大小
        latOffset = offset/6371393*(180/math.pi)
        # 偏移范围
        lat_a = lat-lat % latOffset
        lat_a = limit(lat_a, -90, 90)
        lat_b = lat+0.99*latOffset-lat % latOffset
        lat_b = limit(lat_b, -90, 90)
        # 随机偏移
        lat = random.uniform(lat_a, lat_b)
        # 保留小数
        lat = round(lat, round_)

        # ==经度==
        # 偏移大小(依赖纬度计算)
        lonOffset = offset / \
            (6371393*math.cos(abs(lat_a/180*math.pi)))*(180/math.pi)
        # 偏移范围
        lon_a = lon-lon % lonOffset
        lon_b = lon+0.99*lonOffset-lon % lonOffset
        lon_a = limit(lon_a, -180, 180)
        lon_b = limit(lon_b, -180, 180)
        # 随机偏移
        lon = random.uniform(lon_a, lon_b)
        # 保留小数
        lon = round(lon, round_)

        return (lon, lat)

    @staticmethod
    def choiceFile(dir):
        '''从指定路径(路径列表)中随机选取一个文件路径'''
        if type(dir) == list or type(dir) == tuple:
            '''如果路径是一个列表/元组，则从中随机选择一项'''
            dir = random.choice(dir)
        if os.path.isfile(dir):
            '''如果路径指向一个文件，则返回这个路径'''
            return dir
        else:
            files = os.listdir(dir)
            '''如果路径指向一个文件夹，则随机返回一个文件夹里的文件'''
            if len(files) == 0:
                raise Exception("路径(%s)指向一个空文件夹" % dir)
            return os.path.join(dir, random.choice(files))

    @staticmethod
    def choiceInList(item):
        '''从列表/元组中随机选取一项'''
        if type(item) in (list, tuple):
            return random.choice(item)
        else:
            return item

    @staticmethod
    def choicePhoto(picList):
        """
        从图片(在线/本地/文件夹)文件夹中选取可用图片(优先选取在线图片)，并返回其对应的二进制文件和图片类型

        :param picList: 图片(在线/本地/文件夹)地址，可用是序列或字符串
        :param dirTimeFormat: 是否对本地地址中的时间元素格式化(使用time.strftime)
        :returns: 返回(picBlob: bytes二进制图片, picType: str图片类型)
        """
        # 格式化picList为list
        picList = DT.formatStrList(picList)
        # 打乱picList顺序
        random.shuffle(picList)

        # 根据图片地址前缀筛选出在线图片列表
        urlList = filter(lambda x: re.match(r'https?:\/\/', x), picList)
        for url in urlList:
            '''遍历url列表, 寻找可用图片'''
            # 下载图片
            LL.log(1, f'正在尝试下载[{url}]')
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.46", }
            try:
                response = requests.get(
                    url=url, headers=headers, timeout=(10, 20))
            except requests.exceptions.ConnectionError:
                LL.log(1, f'在线图片[{url}]下载失败，错误原因:\n{e}\
                    \n可能造成此问题的原因有:\
                    \n1. 图片链接失效(请自行验证链接是否可用)\
                    \n2. 图片请求超时(过几分钟再试一下)\
                    \n如持续遇到此问题，请检查该链接的有效性或移除此链接')
                continue
            picBlob = response.content
            LL.log(1, f'在线图片[{url}]下载成功')
            # 判断图片类型
            picType = imghdr.what(None, picBlob)
            if picType:
                LL.log(1, f'在线图片[{url}]属于{picType}')
                return picBlob, picType
            else:
                LL.log(1, f'在线图片[{url}]不是正常图片')
                continue

        # 根据图片地址前缀筛选出本地路径列表
        dirList = list(set(picList) - set(urlList))
        # 将被路径指向文件加入列表
        fileList = list(filter(lambda x: os.path.isfile(x), dirList))
        # 将被路径指向文件夹中的图片加入列表
        folderList = list(filter(lambda x: os.path.isdir(x), dirList))
        for folder in folderList:
            for root, _, files in os.walk(folder, topdown=False):
                for name in files:
                    fileDir = os.path.join(root, name)
                    fileDir = os.path.abspath(fileDir)
                    fileList.append(fileDir)
        # 打乱文件列表
        random.shuffle(fileList)

        for file in fileList:
            '''遍历路径列表, 寻找可用图片'''
            with open(file, 'rb') as f:
                picBlob = f.read()
            picType = imghdr.what(None, picBlob)
            if picType:
                LL.log(1, f'本地图片[{file}]属于{picType}')
                return picBlob, picType
            else:
                LL.log(1, f'本地图片[{file}]不是正常图片')
                continue

        # 如果没有找到可用图片，开始报错
        LL.log(2, '图片列表中没有可用图片')
        # 报出无效本地路径列表
        invalidPath = list(set(dirList) - set(fileList) - set(folderList))
        if invalidPath:
            LL.log(1, '无效本地路径列表', invalidPath)
        raise Exception('图片列表中没有可用图片')

    @staticmethod
    def randomSleep(timeRange: tuple = (5, 7)):
        '''随机暂停一段时间'''
        if len(timeRange) != 2:
            raise Exception("时间范围应包含开始与结束，列表长度应为2")
        a = timeRange[0]
        b = timeRange[1]
        sleepTime = random.uniform(a, b)
        LL.log(0, '程序正在暂停%.3f秒' % sleepTime)
        time.sleep(sleepTime)

    @staticmethod
    def genDeviceID(seed=time.time()):
        '''根据种子生成uuid'''
        with PseudoRandom(seed):
            def ranHex(x): return ''.join(
                random.choices('0123456789ABCDEF', k=x))  # 指定长度随机Hex字符串生成
            deviceId = "-".join([ranHex(8), ranHex(4), ranHex(4),
                                ranHex(4), ranHex(12)])  # 拼合字符串
        return deviceId


class DT:
    '''dict/list tools'''
    @staticmethod
    def loadYml(ymlDir='config.yml'):
        with open(ymlDir, 'r', encoding="utf-8") as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    @staticmethod
    def writeYml(item, ymlDir='config.yml'):
        with open(ymlDir, 'w', encoding='utf-8') as f:
            yaml.dump(item, f, allow_unicode=True)

    @staticmethod
    def resJsonEncode(res):
        '''响应内容的json解析函数(换而言之，就是res.json()的小优化版本)'''
        try:
            return res.json()
        except Exception as e:
            raise Exception(
                f'响应内容以json格式解析失败({e})，响应内容:\n\n{res.text}')

    @staticmethod
    def formatStrList(item):
        '''字符串序列或字符串 格式化为 字符串列表。
        :feature: 超级字符串会被格式化为字符串
        :feature: 空值会被格式化为 空列表'''
        if isinstance(item, str):
            strList = [item]
        elif isinstance(item, dict):
            strList = [item]
        elif type(item) == SuperString:
            strList = [item]
        elif isinstance(item, Sequence):
            strList = list(item)
        elif not item:
            strList = []
        else:
            raise TypeError('请传入序列/字符串')
        # 格式化超级字符串
        for i, v in enumerate(strList):
            if isinstance(v, str) or isinstance(v, dict) or v == SuperString:
                strList[i] = str(SuperString(v))
        return strList


class CT:
    '''CryptoTools'''
    charset = 'utf-8'

    @staticmethod
    def pkcs7padding(text: str):
        """明文使用PKCS7填充"""
        remainder = 16 - len(text.encode(CT.charset)) % 16
        return str(text + chr(remainder) * remainder)

    @staticmethod
    def pkcs7unpadding(text: str):
        """去掉填充字符"""
        return text[:-ord(text[-1])]


class HSF:
    """Hashing String And File"""
    @staticmethod
    def geneHashObj(hash_type):
        if hash_type == 1:
            return hashlib.sha1()
        elif hash_type == 224:
            return hashlib.sha224()
        elif hash_type == 256:
            return hashlib.sha256()
        elif hash_type == 384:
            return hashlib.sha384()
        elif hash_type == 512:
            return hashlib.sha512()
        elif hash_type == 5:
            return hashlib.md5()
        elif hash_type == 3.224:
            return hashlib.sha3_224()
        elif hash_type == 3.256:
            return hashlib.sha3_256()
        elif hash_type == 3.384:
            return hashlib.sha3_384()
        elif hash_type == 3.512:
            return hashlib.sha3_512()
        else:
            raise Exception('类型错误, 初始化失败')

    @staticmethod
    def fileHash(path, hash_type):
        """计算文件哈希
        :param path: 文件路径
        :param hash_type: 哈希算法类型
            1       sha-1
            224     sha-224
            256      sha-256
            384     sha-384
            512     sha-512
            5       md5
            3.256   sha3-256
            3.384   sha3-384
            3.512   sha3-512
        """
        hashObj = HSF.geneHashObj(hash_type)
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    for byte_block in iter(lambda: f.read(1048576), b""):
                        hashObj.update(byte_block)
                    return hashObj.hexdigest()
            except Exception as e:
                raise Exception('%s计算哈希出错: %s' % (path, e))
        else:
            raise Exception('路径错误, 没有指向文件: "%s"')

    @staticmethod
    def strHash(str_: str, hash_type, charset='utf-8'):
        """计算字符串哈希
        :param str_: 字符串
        :param hash_type: 哈希算法类型
        :param charset: 字符编码类型
            1       sha-1
            224     sha-224
            256      sha-256
            384     sha-384
            512     sha-512
            5       md5
            3.256   sha3-256
            3.384   sha3-384
            3.512   sha3-512
        """
        hashObj = HSF.geneHashObj(hash_type)
        bstr = str_.encode(charset)
        hashObj.update(bstr)
        return hashObj.hexdigest()


class ST:
    '''StringTools'''
    @staticmethod
    def timeFormating(string: str):
        '''字符串根据time.strftime()的规则，按照当前时间进行格式化'''
        return time.strftime(string, time.localtime())

    @staticmethod
    def randomFormating(string: str):
        r'''对字符串中的<rd>和</rd>之间(由\a分隔的字符串)随机选取一项加入到字符串中'''
        return re.sub(r"<rd>.*?</rd>", lambda x: random.choice(x.group()[4:-5].split('\a')), string)

    @staticmethod
    def avoidRegular(string: str):
        '''对字符串中的正则特殊符号前加上"\\", 并且在头尾加上"^"和"$"'''
        return '^' + re.sub(r"\.|\^|\$|\*|\+|\?|\{|\}|\[|\]|\(|\)|\||\\", lambda x: '\\'+x.group(), string) + "$"

    @staticmethod
    def notionStr(s: str):
        '''让输入的句子非常非常显眼'''
        return ('↓'*50 + '看这里' + '↓'*50 + '\n')*5 + s + ('\n' + '↑'*50 + '看这里' + '↑'*50)*5


class SuperString:
    '''超级字符串是带有flag的字符串。
    通过flag, 可以增加字符串功能(比如自动时间格式化/随机化), 定义匹配规则(正则/全等)'''

    def __init__(self, strLike):
        '''初始化超级字符串
        :param strLike: str|dict|SuperString
            : 字典要求{"str+": "字符串", "flag":"flag1|flag2"}形式'''
        # 参数初始化
        self.str = ''
        self.flags = []
        self.fStr = ''
        self.reFlag = False
        # 根据类型处理传入的项目
        if isinstance(strLike, str):
            self.str = str(strLike)
        elif isinstance(strLike, dict):
            if not ('str+' in strLike and 'flag' in strLike):
                raise TypeError('不支持缺少键"str+"或"flag"的字典转超级字符串')
            self.str = strLike['str+']
            self.flags = strLike['flag'].split('|')
        elif isinstance(strLike, SuperString):
            self.str = SuperString.str
            self.flags = SuperString.flags
        elif isinstance(strLike, (int, float, datetime.date, datetime.datetime)):
            self.str = str(strLike)
        else:
            raise TypeError(f'不支持[{type(strLike)}]转超级字符串')
        # 生成格式化字符串
        self.formating()
        # 判断self.match函数是否启用正则
        if 're' in self.flags:
            self.reFlag = True

    def formating(self):
        '''根据flags, 格式化字符串'''
        string = self.str
        for flag in self.flags:
            if flag == 'tf':
                string = ST.timeFormating(string)
            elif flag == 'rd':
                string = ST.randomFormating(string)
        self.fStr = string
        return self

    def match(self, str_):
        '''判断输入的字符串是否与超级字符串匹配'''
        if self.reFlag:
            return re.search(self.fStr, str_)
        else:
            return self.fStr == str_

    def __str__(self):
        return self.fStr
