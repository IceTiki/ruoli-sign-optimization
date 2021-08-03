import base64
import json
import re
import uuid
from pyDes import PAD_PKCS5, des, CBC
import yaml

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


class Collection:
    # 初始化信息收集类
    def __init__(self, todaLoginService: TodayLoginService, userInfo):
        self.session = todaLoginService.session
        self.host = todaLoginService.host
        self.userInfo = userInfo
        self.task = None
        self.collectWid = None
        self.taskWid = None
        self.schoolTaskWid = None
        self.form = []

    # 查询表单
    def queryForm(self):
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        queryUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'
        params = {
            'pageSize': 6,
            "pageNumber": 1
        }
        res = self.session.post(queryUrl, data=json.dumps(
            params), headers=headers, verify=False).json()
        if len(res['datas']['rows']) < 1:
            raise Exception('查询表单失败，请确认你是信息收集并且当前有收集任务。确定请联系开发者')
        log('查询任务返回结果', res['datas'])
        self.collectWid = res['datas']['rows'][0]['wid']
        self.taskWid = res['datas']['rows'][0]['formWid']
        detailUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
        res = self.session.post(detailUrl, headers=headers, data=json.dumps({'collectorWid': self.collectWid}),
                                verify=False).json()
        self.schoolTaskWid = res['datas']['collector']['schoolTaskWid']
        getFormUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/getFormFields'
        params = {"pageSize": 100, "pageNumber": 1,
                  "formWid": self.taskWid, "collectorWid": self.collectWid}
        res = self.session.post(
            getFormUrl, headers=headers, data=json.dumps(params), verify=False).json()
        log('查询任务详情返回结果', res['datas'])
        self.task = res['datas']['rows']

    # 填写表单
    def fillForm(self):
        # 检查用户配置长度与查询到的表单长度是否匹配
        if len(self.task) != len(self.userInfo['forms']):
            raise Exception('用户只配置了%d个问题，查询到的表单有%d个问题，不匹配！' %
                            (len(self.userInfo['forms']), len(self.task)))
        for formItem, userForm in zip(self.task, self.userInfo['forms']):
            userForm = userForm['form']
            # 根据用户配置决定是否要填此选项
            if userForm['isNeed'] == 1:
                # 判断用户是否需要检查标题
                if self.userInfo['checkTitle'] == 1:
                    # 如果检查到标题不相等
                    if formItem['title'] != userForm['title']:
                        raise Exception(
                            f'\r\n有配置项的标题不正确\r\n您的标题为：{userForm["title"]}\r\n系统的标题为：{formItem["title"]}')
                # 开始填充表单
                # 文本选项直接赋值
                if formItem['fieldType'] == 1 or formItem['fieldType'] == 5:
                    formItem['value'] = userForm['value']
                # 单选框填充
                elif formItem['fieldType'] == 2:
                    formItem['value'] = userForm['value']
                    # 单选需要移除多余的选项
                    for fieldItem in formItem['fieldItems'].copy():
                        if fieldItem['content'] != userForm['value']:
                            formItem['fieldItems'].remove(fieldItem)
                # 多选填充
                elif formItem['fieldType'] == 3:
                    userItems = userForm['value'].split('|')
                    for fieldItem in formItem['fieldItems'].copy():
                        if fieldItem['content'] in userItems:
                            formItem['value'] += fieldItem['content'] + ' '
                        else:
                            formItem['fieldItems'].remove(fieldItem)
                elif formItem['fieldType'] == 4:
                    pass
                self.form.append(formItem)
            else:
                pass

    # 提交表单
    def submitForm(self):
        extension = {
            "model": "OPPO R11 Plus",
            "appVersion": "8.2.14",
            "systemVersion": "9.1.0",
            "userId": self.userInfo['username'],
            "systemName": "android",
            "lon": self.userInfo['lon'],
            "lat": self.userInfo['lat'],
            "deviceId": str(uuid.uuid1())
        }

        headers = {
            'User-Agent': self.session.headers['User-Agent'],
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': self.DESEncrypt(json.dumps(extension)),
            'Content-Type': 'application/json; charset=utf-8',
            # 请注意这个应该和配置文件中的host保持一致
            'Host': re.findall('//(.*?)/', self.host)[0],
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }
        params = {
            "formWid": self.taskWid, "address": self.userInfo['address'], "collectWid": self.collectWid,
            "schoolTaskWid": self.schoolTaskWid, "form": self.form, "uaIsCpadaily": True
        }
        submitUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/submitForm'
        log('提交表单', 'extension', extension, 'headers', headers, 'params', params)
        data = self.session.post(
            submitUrl, headers=headers, data=json.dumps(params), verify=False).json()
        return data['message']

    # DES加密
    def DESEncrypt(self, content):
        key = 'b3L26XNL'
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(content)
        return base64.b64encode(encrypt_str).decode()
