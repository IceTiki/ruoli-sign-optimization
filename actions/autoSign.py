import base64
import json
import re
import uuid
import math
import yaml

from requests_toolbelt import MultipartEncoder

from todayLoginService import TodayLoginService
from liteTools import *


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
        LL.log(1, '获取未签到的任务')
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        # 第一次请求接口获取cookies（MOD_AUTH_CAS）
        url = f'{self.host}wec-counselor-sign-apps/stu/sign/getStuSignInfosInOneDay'
        self.session.post(url, headers=headers,
                          data=json.dumps({}), verify=False)
        # 第二次请求接口，真正的拿到具体任务
        res = self.session.post(url, headers=headers,
                                data=json.dumps({}), verify=False)
        res = DT.resJsonEncode(res)

        signLevel = self.userInfo.get('signLevel', 1)
        if signLevel >= 0:
            taskList = res['datas']['unSignedTasks']  # 未签到任务
        if signLevel >= 1:
            taskList += res['datas']['leaveTasks']  # 不需签到任务
        if signLevel == 2:
            taskList += res['datas']['signedTasks']  # 已签到任务
        # 查询是否没有未签到任务
        LL.log(1, '获取到的签到任务列表', taskList)
        if len(taskList) < 1:
            LL.log(1, '签到任务列表为空')
            raise TaskError('签到任务列表为空')
        # 自动获取最后一个未签到任务(如果title==0)
        if self.userInfo['title'] == 0:
            latestTask = taskList[0]
            self.taskName = latestTask['taskName']
            LL.log(1, '最后一个未签到的任务', latestTask['taskName'])
            self.taskInfo = {'signInstanceWid': latestTask['signInstanceWid'],
                             'signWid': latestTask['signWid'], 'taskName': latestTask['taskName']}
        # 获取匹配标题的任务
        for righttask in taskList:
            if righttask['taskName'] == self.userInfo['title']:
                self.taskName = righttask['taskName']
                LL.log(1, '匹配标题的任务', righttask['taskName'])
                self.taskInfo = {'signInstanceWid': righttask['signInstanceWid'],
                                 'signWid': righttask['signWid'], 'taskName': righttask['taskName']}
                return self.taskInfo
        LL.log(1, '没有匹配标题的任务')
        raise TaskError('没有匹配标题的任务')

    # 获取具体的签到任务详情
    def getDetailTask(self):
        LL.log(1, '获取具体的签到任务详情')
        url = f'{self.host}wec-counselor-sign-apps/stu/sign/detailSignInstance'
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        res = self.session.post(url, headers=headers, data=json.dumps(
            self.taskInfo), verify=False)
        res = DT.resJsonEncode(res)
        LL.log(1, '签到任务的详情', res['datas'])
        self.task = res['datas']

    # 上传图片到阿里云oss
    def uploadPicture(self):
        url = f'{self.host}wec-counselor-sign-apps/stu/oss/getUploadPolicy'
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps({'fileType': 1}),
                                verify=False)
        datas = DT.resJsonEncode(res).get('datas')
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
                'file': ('blob', open(RT.choicePhoto(self.userInfo['photo']), 'rb'), 'image/jpg')
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

        photoUrl = DT.resJsonEncode(res).get('datas')
        return photoUrl

    # 填充表单
    def fillForm(self):
        LL.log(1, '填充表单')
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
                    # LL.log(1,extraFieldItem)
                    if extraFieldItem['content'] == userItem['value']:
                        flag = True
                        extraFieldItemValue = {'extraFieldItemValue': userItem['value'],
                                               'extraFieldItemWid': extraFieldItem['wid']}
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
            if MT.geoDistance(self.form['longitude'], self.form['latitude'], place['longitude'], place['latitude']) < place['radius']:
                self.form['isMalposition'] = 0
                break
        self.form['abnormalReason'] = self.userInfo['abnormalReason']
        self.form['position'] = self.userInfo['address']
        self.form['uaIsCpadaily'] = True
        self.form['signVersion'] = '1.0.0'

    def getSubmitExtension(self):
        '''生成各种额外参数'''
        extension = {
            "lon": self.userInfo['lon'],
            "lat": self.userInfo['lat'],
            "model": "OPPO R11 Plus",
            "appVersion": "9.0.12",
            "systemVersion": "4.4.4",
            "userId": self.userInfo['username'],
            "systemName": "android",
            "deviceId": self.userInfo['deviceId']
        }

        self.cpdailyExtension = CT.encrypt_CpdailyExtension(
            json.dumps(extension))

        self.bodyString = CT.encrypt_BodyString(json.dumps(self.form))

        self.submitData = {
            "lon": self.userInfo['lon'],
            "version": "first_v2",
            "calVersion": "firstv",
            "deviceId": self.userInfo['deviceId'],
            "userId": self.userInfo['username'],
            "systemName": "android",
            "bodyString": self.bodyString,
            "lat": self.userInfo['lat'],
            "systemVersion": "4.4.4",
            "appVersion": "9.0.12",
            "model": "OPPO R11 Plus",
        }

        sign = ''.join("%s=%s&" % (i, self.submitData[i]) for i in [
                       "appVersion", "bodyString", "deviceId", "lat", "lon", "model", "systemName", "systemVersion", "userId"]) + "ytUQ7l2ZZu8mLvJZ"
        sign = HSF.strHash(sign, 5)
        self.submitData['sign'] = sign

    # 提交签到信息
    def submitForm(self):
        LL.log(1, '提交签到信息')
        self.getSubmitExtension()

        headers = {
            'User-Agent': self.session.headers['User-Agent'],
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': self.cpdailyExtension,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Encoding': 'gzip',
            'Host': re.findall('//(.*?)/', self.host)[0],
            'Connection': 'Keep-Alive'
        }

        LL.log(1, '即将提交的信息', headers, self.submitData)
        res = self.session.post(f'{self.host}wec-counselor-sign-apps/stu/sign/submitSign', headers=headers,
                                data=json.dumps(self.submitData), verify=False)
        res = DT.resJsonEncode(res)
        LL.log(1, '提交后返回的信息', res['message'])
        return '[%s]%s' % (res['message'], self.taskInfo['taskName'])
