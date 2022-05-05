import json
import re
from requests_toolbelt import MultipartEncoder

from todayLoginService import TodayLoginService
from liteTools import LL, DT, RT, MT, ST, SuperString, TaskError, CpdailyTools


class teacherSign:
    # 初始化政工签到类
    def __init__(self, userInfo, userSession, userHost):
        self.session = userSession
        self.host = userHost
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
            raise TaskError('当前暂时没有未签到的任务哦！', 400)
        LL.log(1, '未签到的政工签到', res['datas'])
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
        LL.log(1, '具体政工签到任务', res['datas'])
        self.task = res['datas']
        return self.task

    # 填充表单

    def fillForm(self):
        # 判断签到是否需要照片
        if self.task['isPhoto'] == 1:
            pic = self.userInfo['photo']
            picBlob, picType = RT.choicePhoto(pic)
            # 上传图片
            url_getUploadPolicy = f'{self.host}wec-counselor-teacher-sign-apps/teacher/obs/getUploadPolicy'
            ossKey = CpdailyTools.uploadPicture(
                url_getUploadPolicy, self.session, picBlob, picType)
            # 获取图片url
            url_previewAttachment = f'{self.host}wec-counselor-teacher-sign-apps/teacher/sign/previewAttachment'
            imgUrl = CpdailyTools.getPictureUrl(
                url_previewAttachment, self.session, ossKey)
            self.form['signPhotoUrl'] = imgUrl
        else:
            self.form['signPhotoUrl'] = ''
        self.form['signInstanceWid'] = self.taskInfo['signInstanceWid']
        self.form['longitude'] = self.userInfo['lon']
        self.form['latitude'] = self.userInfo['lat']
        self.form['isMalposition'] = self.task['isMalposition']
        self.form['abnormalReason'] = str(
            SuperString(self.userInfo['abnormalReason']))
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
        # 检查签到情况
        if self.getDetailTask()['signTime']:
            self.userInfo['taskStatus'].code = 101
        else:
            raise TaskError(f'提交表单返回『{res}』且任务状态仍是未签到', 300)
        return res['message']
