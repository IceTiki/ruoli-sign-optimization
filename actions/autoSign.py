import base64
import json
import re
import uuid
import math
import yaml

from pyDes import des, CBC, PAD_PKCS5
from requests_toolbelt import MultipartEncoder

from todayLoginService import TodayLoginService


def log(*args):
    if args:
        string = '|||log|||\n'
        for item in args:
            if type(item) == dict or type(item) == list:
                string += yaml.dump(item, allow_unicode=True)+'\n'
            else:
                string += str(item)+'\n'
        print(string)


class AutoSign:
    # 初始化签到类
    def __init__(self, todayLoginService: TodayLoginService, userInfo):
        self.session = todayLoginService.session
        self.host = todayLoginService.host
        self.userInfo = userInfo
        self.taskInfo = None
        self.task = None
        self.form = {}
        self.fileName = None

    # 获取未签到的任务

    def getUnSignTask(self):
        # 如果有合适的任务，则返回dict。如果没有需要签到的任务，则返回str。
        log('获取未签到的任务')
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        # 第一次请求接口获取cookies（MOD_AUTH_CAS）
        url = f'{self.host}wec-counselor-sign-apps/stu/sign/getStuSignInfosInOneDay'
        self.session.post(url, headers=headers,
                          data=json.dumps({}), verify=False)
        # 第二次请求接口，真正的拿到具体任务
        res = self.session.post(url, headers=headers,
                                data=json.dumps({}), verify=False).json()
        # 查询是否没有未签到任务
        log('所有未签到任务', res['datas']['unSignedTasks'])
        if len(res['datas']['unSignedTasks']) < 1:
            log('当前暂时没有未签到的任务哦！')
            return '当前暂时没有未签到的任务哦！'
        # 自动获取最后一个未签到任务(如果title==0)
        if self.userInfo['title'] == 0:
            latestTask = res['datas']['unSignedTasks'][0]
            self.taskName = latestTask['taskName']
            log('最后一个未签到的任务', latestTask['taskName'])
            self.taskInfo = {'signInstanceWid': latestTask['signInstanceWid'],
                             'signWid': latestTask['signWid'], 'taskName': latestTask['taskName']}
            return self.taskInfo
        # 获取匹配标题的任务
        for righttask in res['datas']['unSignedTasks']:
            if righttask['taskName'] == self.userInfo['title']:
                self.taskName = righttask['taskName']
                log('匹配标题的任务', righttask['taskName'])
                self.taskInfo = {'signInstanceWid': righttask['signInstanceWid'],
                                 'signWid': righttask['signWid'], 'taskName': righttask['taskName']}
                return self.taskInfo
        log('没有匹配标题的任务')
        return '没有匹配标题的任务'

    # 获取具体的签到任务详情
    def getDetailTask(self):
        log('获取具体的签到任务详情')
        url = f'{self.host}wec-counselor-sign-apps/stu/sign/detailSignInstance'
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        res = self.session.post(url, headers=headers, data=json.dumps(
            self.taskInfo), verify=False).json()
        log('签到任务的详情', res['datas'])
        self.task = res['datas']

    # 上传图片到阿里云oss
    def uploadPicture(self):
        url = f'{self.host}wec-counselor-sign-apps/stu/oss/getUploadPolicy'
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps({'fileType': 1}),
                                verify=False)
        datas = res.json().get('datas')
        fileName = datas.get('fileName')
        policy = datas.get('policy')
        accessKeyId = datas.get('accessid')
        signature = datas.get('signature')
        policyHost = datas.get('host')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'
        }
        multipart_encoder = MultipartEncoder(
            fields={  # 这里根据需要进行参数格式设置
                'key': fileName, 'policy': policy, 'OSSAccessKeyId': accessKeyId, 'success_action_status': '200',
                'signature': signature,
                'file': ('blob', open(self.userInfo['photo'], 'rb'), 'image/jpg')
            })
        headers['Content-Type'] = multipart_encoder.content_type
        res = self.session.post(url=policyHost,
                                headers=headers,
                                data=multipart_encoder)
        self.fileName = fileName

    # 获取图片上传位置
    def getPictureUrl(self):
        url = f'{self.host}wec-counselor-sign-apps/stu/sign/previewAttachment'
        params = {'ossKey': self.fileName}
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(params),
                                verify=False)
        photoUrl = res.json().get('datas')
        return photoUrl

    # 填充表单
    def fillForm(self):
        log('填充表单')
        # 判断签到是否需要照片
        if self.task['isPhoto'] == 1:
            self.uploadPicture()
            self.form['signPhotoUrl'] = self.getPictureUrl()
            # self.form['signPhotoUrl'] = 'https://www.campushoy.com/wp-content/uploads/2019/06/cropped-hoy.png'
        else:
            self.form['signPhotoUrl'] = ''
        self.form['isNeedExtra'] = self.task['isNeedExtra']
        if self.task['isNeedExtra'] == 1:
            extraFields = self.task['extraField']
            userItems = self.userInfo['forms']
            extraFieldItemValues = []
            for i in range(len(extraFields)):
                userItem = userItems[i]['form']
                extraField = extraFields[i]
                if self.userInfo['checkTitle'] == 1:
                    if userItem['title'] != extraField['title']:
                        raise Exception(
                            f'\r\n第{i + 1}个配置出错了\r\n您的标题为：{userItem["title"]}\r\n系统的标题为：{extraField["title"]}')
                extraFieldItems = extraField['extraFieldItems']
                flag = False
                for extraFieldItem in extraFieldItems:
                    if extraFieldItem['isSelected']:
                        data = extraFieldItem['content']
                    # log(extraFieldItem)
                    if extraFieldItem['content'] == userItem['value']:
                        flag = True
                        extraFieldItemValue = {'extraFieldItemValue': userItem['value'],
                                               'extraFieldItemWid': extraFieldItem['wid']}
                        extraFieldItemValues.append(extraFieldItemValue)
                    # 其他 额外的文本
                    if extraFieldItem['isOtherItems'] == 1:
                        flag = True
                        extraFieldItemValue = {'extraFieldItemValue': userItem['value'],
                                               'extraFieldItemWid': extraFieldItem['wid']}
                        extraFieldItemValues.append(extraFieldItemValue)
                if not flag:
                    raise Exception(
                        f'\r\n第{ i + 1 }个配置出错了\r\n表单未找到你设置的值：{userItem["value"]}\r\n，你上次系统选的值为：{ data }')
            self.form['extraFieldItems'] = extraFieldItemValues
        self.form['signInstanceWid'] = self.task['signInstanceWid']
        self.form['longitude'] = self.userInfo['lon']
        self.form['latitude'] = self.userInfo['lat']
        # 检查是否在签到范围内
        self.form['isMalposition'] = 1
        for place in self.task['signPlaceSelected']:
            if self.geodistance(self.form['longitude'], self.form['latitude'], place['longitude'], place['latitude']) < place['radius']:
                self.form['isMalposition'] = 0
                break
        self.form['abnormalReason'] = self.userInfo['abnormalReason']
        self.form['position'] = self.userInfo['address']
        self.form['uaIsCpadaily'] = True
        self.form['signVersion'] = '1.0.0'

    # DES加密
    def DESEncrypt(self, s, key='b3L26XNL'):
        key = key
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(s)
        return base64.b64encode(encrypt_str).decode()

    # 提交签到信息
    def submitForm(self):
        log('提交签到信息')
        extension = {
            "lon": self.userInfo['lon'],
            "model": "OPPO R11 Plus",
            "appVersion": "8.1.14",
            "systemVersion": "4.4.4",
            "userId": self.userInfo['username'],
            "systemName": "android",
            "lat": self.userInfo['lat'],
            "deviceId": str(uuid.uuid1())
        }
        headers = {
            'User-Agent': self.session.headers['User-Agent'],
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': self.DESEncrypt(json.dumps(extension)),
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Encoding': 'gzip',
            'Host': re.findall('//(.*?)/', self.host)[0],
            'Connection': 'Keep-Alive'
        }
        # log(json.dumps(self.form))
        log('即将提交的信息', extension, headers)
        res = self.session.post(f'{self.host}wec-counselor-sign-apps/stu/sign/submitSign', headers=headers,
                                data=json.dumps(self.form), verify=False).json()
        log('提交后返回的信息', res['message'])
        return res['message']

    # 两经纬度算距离
    def geodistance(self, lon1, lat1, lon2, lat2):
        #lon1,lat1,lon2,lat2 = (120.12802999999997,30.28708,115.86572000000001,28.7427)
        # 经纬度转换成弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [float(
            lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2-lon1
        dlat = lat2-lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2*math.asin(math.sqrt(a))*6371393  # 地球平均半径，6371393m
        distance = round(distance/1000, 3)
        return distance
