import json
import re
from requests_toolbelt import MultipartEncoder

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
        self.instanceWid = None
        self.form = {}

    # 上传图片到阿里云oss
    def uploadPicture(self, picDir):
        url = f'{self.host}wec-counselor-collector-apps/stu/oss/getUploadPolicy'
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
                'file': ('blob', open(picDir, 'rb'), 'image/jpg')
            })
        headers['Content-Type'] = multipart_encoder.content_type
        res = self.session.post(url=policyHost,
                                headers=headers,
                                data=multipart_encoder)
        self.fileName = fileName

    # 获取图片上传位置
    def getPictureUrl(self):
        url = f'{self.host}wec-counselor-collector-apps/stu/collector/previewAttachment'
        params = {'ossKey': self.fileName}
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(params),
                                verify=False)
        photoUrl = res.json().get('datas')
        return photoUrl

    # 查询表单

    def queryForm(self):
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        queryUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'
        params = {
            'pageSize': 20,
            "pageNumber": 1
        }
        # 第一次请求接口获取cookies（MOD_AUTH_CAS）
        self.session.post(queryUrl, headers=headers,
                          data=json.dumps({}), verify=False)
        # 第二次请求接口，真正的拿到具体任务
        res = self.session.post(queryUrl, data=json.dumps(
            params), headers=headers, verify=False)
        res = DT.resJsonEncode(res)
        if res['datas']['totalSize'] < 1:
            raise TaskError('没有查询到信息收集任务')
        LL.log(1, '查询任务返回结果', res['datas'])
        task = res['datas']['rows'][0]
        self.collectWid = task['wid']
        self.taskWid = task['formWid']
        self.instanceWid = task.get('instanceWid', '')
        detailUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
        res = self.session.post(detailUrl, headers=headers, data=json.dumps({'collectorWid': self.collectWid}),
                                verify=False)
        res = DT.resJsonEncode(res)
        try:
            self.schoolTaskWid = res['datas']['collector']['schoolTaskWid']
        except TypeError:
            self.schoolTaskWid = ''
            LL.log(1, '循环普通任务实例wid为空')
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
        task_form = []
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
                if formItem['fieldType'] in ('1', '5', '6', '7'):
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
                # 图片（健康码）上传类型
                elif formItem['fieldType'] == '4':
                    # 如果是传图片的话，那么是将图片的地址（相对/绝对都行）存放于此value中
                    picDir = RT.choicePhoto(userForm['value'])
                    self.uploadPicture(picDir)
                    formItem['value'] = self.getPictureUrl()
                    # 填充其他信息
                    formItem.setdefault('http', {
                        'defaultOptions': {
                            'customConfig': {
                                'pageNumberKey': 'pageNumber',
                                'pageSizeKey': 'pageSize',
                                'pageDataKey': 'pageData',
                                'pageTotalKey': 'pageTotal',
                                'data': 'datas',
                                'codeKey': 'code',
                                'messageKey': 'message'
                            }
                        }
                    })
                    formItem['uploadPolicyUrl'] = '/wec-counselor-collector-apps/stu/oss/getUploadPolicy'
                    formItem['saveAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/saveAttachment'
                    formItem['previewAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/previewAttachment'
                    formItem['downloadMediaUrl'] = '/wec-counselor-collector-apps/stu/collector/downloadMedia'

                else:
                    raise Exception(
                        f'\r\n{userForm}配置项属于未知配置项，请反馈'
                    )
                task_form.append(formItem)
            else:
                pass

        self.form["form"] = task_form
        self.form["formWid"] = self.taskWid
        self.form["address"] = self.userInfo['address']
        self.form["collectWid"] = self.collectWid
        self.form["schoolTaskWid"] = self.schoolTaskWid
        self.form["uaIsCpadaily"] = True
        self.form["latitude"] = self.userInfo['lat']
        self.form["longitude"] = self.userInfo['lon']
        self.form['instanceWid'] = self.instanceWid

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

    # 提交表单
    def submitForm(self):
        self.getSubmitExtension()

        headers = {
            'User-Agent': self.session.headers['User-Agent'],
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': self.cpdailyExtension,
            'Content-Type': 'application/json; charset=utf-8',
            # 请注意这个应该和配置文件中的host保持一致
            'Host': re.findall('//(.*?)/', self.host)[0],
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

        submitUrl = f'{self.host}wec-counselor-collector-apps/stu/collector/submitForm'
        LL.log(1, '提交表单', 'data', self.submitData,
               'headers', headers, 'params', self.submitData)
        data = self.session.post(
            submitUrl, headers=headers, data=json.dumps(self.submitData), verify=False)
        data = DT.resJsonEncode(data)
        return data['message']
