import base64
import json
import re
import uuid
from pyDes import PAD_PKCS5, des, CBC
import yaml

from todayLoginService import TodayLoginService
from liteTools import *


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
            'pageSize': 20,
            "pageNumber": 1
        }
        res = self.session.post(queryUrl, data=json.dumps(
            params), headers=headers, verify=False)
        res = DT.resJsonEncode(res)
        if res['datas']['totalSize'] < 1:
            raise TaskError('没有查询到信息收集任务')
        LL.log(1, '查询任务返回结果', res['datas'])
        self.collectWid = res['datas']['rows'][0]['wid']
        self.taskWid = res['datas']['rows'][0]['formWid']
        detailUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
        res = self.session.post(detailUrl, headers=headers, data=json.dumps({'collectorWid': self.collectWid}),
                                verify=False)
        res = DT.resJsonEncode(res)
        self.schoolTaskWid = res['datas']['collector']['schoolTaskWid']
        getFormUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/getFormFields'
        params = {"pageSize": 100, "pageNumber": 1,
                  "formWid": self.taskWid, "collectorWid": self.collectWid}
        res = self.session.post(
            getFormUrl, headers=headers, data=json.dumps(params), verify=False)
        res = DT.resJsonEncode(res)
        LL.log(1, '查询任务详情返回结果', res['datas'])
        self.task = res['datas']['rows']

    # 填写表单
    def fillForm(self):
        # 检查用户配置长度与查询到的表单长度是否匹配
        if len(self.task) != len(self.userInfo['forms']):
            raise Exception('用户只配置了%d个问题，查询到的表单有%d个问题，不匹配！' % (
                len(self.userInfo['forms']), len(self.task)))
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
                # 填充多出来的参数（新版增加了三个参数，暂时不知道作用）
                formItem['show'] = True
                formItem['formType'] = '0'  # 盲猜是任务类型、待确认
                formItem['sortNum'] = str(formItem['sort'])  # 盲猜是sort排序
                # 开始填充表单
                # 文本选项直接赋值
                if formItem['fieldType'] == '1' or formItem['fieldType'] == '5' or formItem['fieldType'] == '7':
                    formItem['value'] = userForm['value']
                # 单选框填充
                elif formItem['fieldType'] == '2':
                    # 定义单选框的wid
                    itemWid = ''
                    # 单选需要移除多余的选项
                    for fieldItem in formItem['fieldItems'].copy():
                        if fieldItem['content'] != userForm['value']:
                            formItem['fieldItems'].remove(fieldItem)
                        else:
                            itemWid = fieldItem['itemWid']
                    if itemWid == '':
                        raise Exception(
                            f'\r\n{userForm}配置项的选项不正确，该选项为单选，且未找到您配置的值'
                        )
                    formItem['value'] = itemWid
                # 多选填充
                elif formItem['fieldType'] == '3':
                    # 定义单选框的wid
                    itemWidArr = []
                    userItems = userForm['value'].split('|')
                    for fieldItem in formItem['fieldItems'].copy():
                        if fieldItem['content'] in userItems:
                            formItem['value'] += fieldItem['content'] + ' '
                            itemWidArr.append(fieldItem['itemWid'])
                        else:
                            formItem['fieldItems'].remove(fieldItem)
                    # 若多选一个都未选中
                    if len(itemWidArr) == 0:
                        raise Exception(
                            f'\r\n{userForm}配置项的选项不正确，该选项为多选，且未找到您配置的值'
                        )
                    formItem['value'] = ','.join(itemWidArr)
                else:
                    raise Exception(
                        f'\r\n{userForm}配置项属于未知配置项，请反馈'
                    )
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
            "schoolTaskWid": self.schoolTaskWid, "form": self.form, "uaIsCpadaily": True,
            "latitude": self.userInfo['lat'], 'longitude': self.userInfo['lon']
        }
        submitUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/submitForm'
        LL.log(1, '提交表单', 'extension', extension,
               'headers', headers, 'params', params)
        data = self.session.post(
            submitUrl, headers=headers, data=json.dumps(params), verify=False)
        data = DT.resJsonEncode(data)
        return data['message']

    # DES加密
    def DESEncrypt(self, content):
        key = 'b3L26XNL'
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(content)
        return base64.b64encode(encrypt_str).decode()
