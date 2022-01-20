import json
import re
from requests_toolbelt import MultipartEncoder

from todayLoginService import TodayLoginService
from liteTools import *


class teacherSign:
    # 初始化政工签到类
    def __init__(self, todaLoginService: TodayLoginService, userInfo):
        self.session = todaLoginService.session
        self.host = todaLoginService.host
        self.userInfo = userInfo
        self.taskInfo = None
        self.form = {}
    # 获取未签到任务

    def getUnSignedTasks(self):
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        # 第一次请求接口获取cookies（MOD_AUTH_CAS）
        url = f'{self.host}wec-counselor-teacher-sign-apps/teacher/sign/getTeacherSignInfosInOneDay'
        self.session.post(url, headers=headers,
                          data=json.dumps({}), verify=False)
        # 第二次请求接口，真正的拿到具体任务
        res = self.session.post(url, headers=headers,
                                data=json.dumps({}), verify=False)
        res = DT.resJsonEncode(res)
        if len(res['datas']['unSignedTasks']) < 1:
            raise TaskError('当前暂时没有未签到的任务哦！')
        LL.log(1, '未签到的查寝', res['datas'])
        # 获取最后的一个任务
        latestTask = res['datas']['unSignedTasks'][0]
        self.taskInfo = {
            'signInstanceWid': latestTask['signInstanceWid'],
            'signWid': latestTask['signWid']
        }

    # 获取具体的签到任务详情
    def getDetailTask(self):
        url = f'{self.host}wec-counselor-teacher-sign-apps/teacher/sign/detailSignInstance'
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        res = self.session.post(url, headers=headers, data=json.dumps(
            self.taskInfo), verify=False)
        res = DT.resJsonEncode(res)
        LL.log(1, '具体查寝任务', res['datas'])
        self.task = res['datas']

    # 上传图片到阿里云oss
    def uploadPicture(self):
        url = f'{self.host}wec-counselor-teacher-sign-apps/teacher/oss/getUploadPolicy'
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
        url = f'{self.host}wec-counselor-teacher-sign-apps/teacher/sign/previewAttachment'
        params = {'ossKey': self.fileName}
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(params),
                                verify=False)
        photoUrl = res.json().get('datas')
        return photoUrl

    # 填充表单

    def fillForm(self):
        # 判断签到是否需要照片
        if self.task['isPhoto'] == 1:
            self.uploadPicture()
            self.form['signPhotoUrl'] = self.getPictureUrl()
        else:
            self.form['signPhotoUrl'] = ''
        self.form['signInstanceWid'] = self.taskInfo['signInstanceWid']
        self.form['longitude'] = self.userInfo['lon']
        self.form['latitude'] = self.userInfo['lat']
        self.form['isMalposition'] = self.task['isMalposition']
        self.form['abnormalReason'] = self.userInfo['abnormalReason']
        self.form['position'] = self.userInfo['address']
        self.form['qrUuid'] = ''
        self.form['uaIsCpadaily'] = True

    def getSubmitExtension(self):
        '''生成各种额外参数'''
        extension = {
            "lon": self.userInfo['lon'],
            "lat": self.userInfo['lat'],
            "model": self.userInfo['model'],
            "appVersion": self.userInfo['appVersion'],
            "systemVersion": self.userInfo['systemVersion'],
            "userId": self.userInfo['username'],
            "systemName": self.userInfo['systemName'],
            "deviceId": self.userInfo['deviceId']
        }

        self.cpdailyExtension = CpdailyTools.encrypt_CpdailyExtension(
            json.dumps(extension))

        self.bodyString = CpdailyTools.encrypt_BodyString(
            json.dumps(self.form))

        self.submitData = {
            "lon": self.userInfo['lon'],
            "version": self.userInfo['signVersion'],
            "calVersion": self.userInfo['calVersion'],
            "deviceId": self.userInfo['deviceId'],
            "userId": self.userInfo['username'],
            "systemName": self.userInfo['systemName'],
            "bodyString": self.bodyString,
            "lat": self.userInfo['lat'],
            "systemVersion": self.userInfo['systemVersion'],
            "appVersion": self.userInfo['appVersion'],
            "model": self.userInfo['model'],
        }

        self.submitData['sign'] = CpdailyTools.signAbstract(self.submitData)

    # 提交签到信息
    def submitForm(self):
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
        LL.log(1, '提交查寝数据', 'data', self.submitData, 'header', headers)
        res = self.session.post(f'{self.host}wec-counselor-teacher-sign-apps/teacher/sign/submitSign', headers=headers,
                                data=json.dumps(self.submitData), verify=False)
        res = DT.resJsonEncode(res)
        return res['message']
