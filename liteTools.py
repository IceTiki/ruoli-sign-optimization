import time
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


class TaskError(Exception):
    '''目前(配置/时间/签到情况)不宜完成签到任务'''
    pass


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
        if type(dir) == list:
            dir = random.choice(dir)
        if os.path.isfile(dir):
            return dir
        else:
            files = os.listdir(dir)
            if len(files) == 0:
                raise Exception("路径(%s)指向一个空文件夹" % dir)
            return os.path.join(dir, random.choice(files))

    @staticmethod
    def choiceInList(item):
        if type(item) == list:
            return random.choice(item)
        else:
            return item

    @staticmethod
    def choicePhoto(dir):
        '''从指定路径(路径列表)中随机选取一个图片路径'''
        if type(dir) == list:
            dir = random.choice(dir)
        if os.path.isfile(dir):
            return dir
        else:
            files = filter(lambda x: x.endswith('.jpg'), os.listdir(dir))
            files = list(files)
            if len(files) == 0:
                raise Exception("路径(%s)指向一个没有图片(.jpg)的文件夹" % dir)
            return os.path.join(dir, random.choice(files))

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
    '''dict tools'''
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


class LL:
    '''lite log'''
    prefix = "V-T3.4.1"  # 版本标识
    startTime = time.time()
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
