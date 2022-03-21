import json
import re
import os
from requests_toolbelt import MultipartEncoder

from todayLoginService import TodayLoginService
from liteTools import LL, DT, RT, MT, TaskError, CpdailyTools


class Collection:
    # 初始化信息收集类
    def __init__(self, todaLoginService: TodayLoginService, userInfo):
        self.session = todaLoginService.session
        self.host = todaLoginService.host
        self.userInfo = userInfo
        self.task = None
        self.wid = None
        self.formWid = None
        self.schoolTaskWid = None
        self.instanceWid = None
        self.form = {}
        self.historyTaskData = {}

    # 保存图片
    def savePicture(self, picSize, picNumber, ossKey):
        url = f'{self.host}wec-counselor-collector-apps/stu/collector/saveAttachment'
        attachName = '图片-' + str(picNumber).rjust(2, '0')
        params = {'attachmentSize': picSize,
                  'ossKey': ossKey, "attachName": attachName}
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(params),
                                verify=False)

    # 查询表单
    def queryForm(self):
        headers = self.session.headers
        headers['Content-Type'] = 'application/json'
        url = f'{self.host}wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'
        # 第一次请求接口获取cookies（MOD_AUTH_CAS）
        self.session.post(url, headers=headers,
                          data=json.dumps({}), verify=False)
        # 获取首页信息, 获取页数
        pageSize = 20
        pageReq = {"pageNumber": 1, "pageSize": pageSize}
        pageNumber = 0
        totalSize = 1
        # 按页遍历
        while pageNumber*pageSize <= totalSize:
            pageNumber += 1
            pageReq["pageNumber"] = pageNumber
            # 获取**任务列表**数据
            res = self.session.post(url, headers=headers,
                                    data=json.dumps(pageReq), verify=False)
            res = DT.resJsonEncode(res)
            LL.log(1, f"获取到的第{pageNumber}页任务列表", res)
            # 在**首页**获取历史信息收集**总数**
            if pageNumber == 1:
                # 历史信息收集总数
                totalSize = res['datas']['totalSize']
                # 如果没有获取到历史任务则报错
                if totalSize == 0:
                    LL.log(2, "没有获取到信息收集任务")
                    raise TaskError("没有获取到信息收集任务")
            # 按页中任务遍历
            for task in res['datas']['rows']:
                if self.userInfo.get('title'):
                    # 如果任务需要匹配标题
                    if not re.search(self.userInfo['title'], task["subject"]):
                        # 跳过标题不匹配的任务
                        continue
                    if self.userInfo.get('signLevel') == 1 and task['isHandled'] == 1:
                        # 如果仅填报"未填报的任务"且相应任务已被填报，则报错
                        LL.log(2, f"收集任务({task['subject']})已经被填报")
                        raise TaskError(f"收集任务({task['subject']})已经被填报")
                else:
                    # 如果不需要匹配标题，则获取第一个任务
                    if self.userInfo.get('signLevel') == 1 and task['isHandled'] == 1:
                        # 仅填报"未填报的任务"时如果任务已被填报，则跳过该任务
                        continue
                # 提取任务的基本信息
                self.wid = task['wid']
                self.formWid = task['formWid']
                self.instanceWid = task.get('instanceWid', '')
                self.taskName = task['subject']
                # 获取任务详情
                url = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
                params = {"collectorWid": self.wid,
                          "instanceWid": self.instanceWid}
                res = self.session.post(
                    url, headers=headers, data=json.dumps(params), verify=False)
                res = DT.resJsonEncode(res)
                try:
                    self.schoolTaskWid = res['datas']['collector']['schoolTaskWid']
                except TypeError:
                    self.schoolTaskWid = ''
                    LL.log(1, '循环普通任务实例wid为空')
                # 获取任务表单
                url = f'{self.host}wec-counselor-collector-apps/stu/collector/getFormFields'
                params = {"pageSize": 9999, "pageNumber": 1,
                          "formWid": self.formWid, "collectorWid": self.wid}
                res = self.session.post(
                    url, headers=headers, data=json.dumps(params), verify=False)
                res = DT.resJsonEncode(res)
                LL.log(1, '查询任务详情返回结果', res['datas'])
                self.task = res['datas']['rows']
                return
        LL.log(1, "没有获取到合适的信息收集任务")
        raise TaskError("没有获取到合适的信息收集任务")

    # 获取历史签到任务详情
    def getHistoryTaskInfo(self):
        '''获取历史签到任务详情'''
        headers = self.session.headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        # 获取首页信息, 获取页数
        pageSize = 20
        url = f'{self.host}wec-counselor-collector-apps/stu/collector/queryCollectorHistoryList'
        pageReq = {"pageNumber": 1, "pageSize": pageSize}
        pageNumber = 0
        totalSize = 1
        # 按页遍历
        while pageNumber*pageSize <= totalSize:
            pageNumber += 1
            pageReq["pageNumber"] = pageNumber
            # 获取**任务列表**数据
            res = self.session.post(url, headers=headers,
                                    data=json.dumps(pageReq), verify=False)
            res = DT.resJsonEncode(res)
            LL.log(1, f"获取到第{pageNumber}页历史信息收集数据", res)
            # 在**首页**获取历史信息收集**总数**
            if pageNumber == 1:
                # 历史信息收集总数
                totalSize = res['datas']['totalSize']
                # 如果没有获取到历史任务则报错
                if totalSize < 0:
                    LL.log(2, "没有获取到历史任务")
                    raise TaskError("没有获取到历史任务")
            # 按页中任务遍历
            for task in res['datas']['rows']:
                if task['isHandled'] == 1 and task['formWid'] == self.formWid:
                    # 找到和当前任务匹配的历史已处理任务，开始获取表单
                    historyInstanceWid = task['instanceWid']
                    historyWid = task['wid']
                    # 模拟请求
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/getUnSeenQuestion'
                    self.session.post(url, headers=headers, data=json.dumps(
                        {"wid": self.wid, "instanceWid": self.instanceWid}), verify=False)
                    # 模拟请求:获取历史信息收集信息
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/detailCollector'
                    self.session.post(url, headers=headers, data=json.dumps(
                        {"collectorWid": self.wid, "instanceWid": self.instanceWid}), verify=False)
                    # 获取表单
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/getFormFields'
                    formReq = {"pageNumber": 1, "pageSize": 9999, "formWid": self.formWid,
                               "collectorWid": historyWid, "instanceWid": historyInstanceWid}
                    res = self.session.post(url, headers=headers, data=json.dumps(formReq),
                                            verify=False)
                    res = DT.resJsonEncode(res)
                    # 模拟请求
                    url = f'{self.host}wec-counselor-collector-apps/stu/collector/queryNotice'
                    self.session.post(url, headers=headers,
                                      data=json.dumps({}), verify=False)
                    # 处理表单
                    form = res['datas']['rows']
                    # 逐个处理表单内问题
                    for item in form:
                        # 填充额外参数
                        item['show'] = True
                        item['formType'] = '0'  # 盲猜是任务类型、待确认
                        item['sortNum'] = str(item['sort'])  # 盲猜是sort排序
                        if item['fieldType'] == '2':
                            '''如果是单选题，需要删掉多余选项'''
                            item['fieldItems'] = list(
                                filter(lambda x: x['isSelected'], item['fieldItems']))
                            if item['fieldItems']:
                                '''如果已选有选项，则将itemWid填入value中'''
                                item['value'] = item['fieldItems'][0]['itemWid']
                        elif item['fieldType'] == '3':
                            '''如果是多选题，也需要删掉多余选项'''
                            item['fieldItems'] = list(
                                filter(lambda x: x['isSelected'], item['fieldItems']))
                            if item['fieldItems']:
                                '''如果已选有选项，则将itemWid填入value中'''
                                item['value'] = ','.join(
                                    [i['itemWid'] for i in item['fieldItems']])
                        elif item['fieldType'] == '4':
                            '''如果是图片上传类型'''
                            # 填充其他信息
                            item.setdefault('http', {
                                'defaultOptions': {
                                    'customConfig': {
                                        'pageNumberKey': 'pageNumber',
                                        'pageSizeKey': 'pageSize',
                                        'pageDataKey': 'rows',
                                        'pageTotalKey': 'totalSize',
                                        'dataKey': 'datas',
                                        'codeKey': 'code',
                                        'messageKey': 'message'
                                    }
                                }
                            })
                            item['uploadPolicyUrl'] = '/wec-counselor-collector-apps/stu/obs/getUploadPolicy'
                            item['saveAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/saveAttachment'
                            item['previewAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/previewAttachment'
                            item['downloadMediaUrl'] = '/wec-counselor-collector-apps/stu/collector/downloadMedia'
                    self.historyTaskData['form'] = form
                    return self.historyTaskData
        # 如果没有获取到历史信息收集则报错
        LL.log(2, "没有找到匹配的历史任务")
        raise TaskError("没有找到匹配的历史任务")

    # 填写表单

    def fillForm(self):
        LL.log(1, '填充表单')
        if self.userInfo['getHistorySign']:
            hti = self.getHistoryTaskInfo()
            self.form['form'] = hti['form']
            self.form["formWid"] = self.formWid
            self.form["address"] = self.userInfo['address']
            self.form["collectWid"] = self.wid
            self.form["schoolTaskWid"] = self.schoolTaskWid
            self.form["uaIsCpadaily"] = True
            self.form["latitude"] = self.userInfo['lat']
            self.form["longitude"] = self.userInfo['lon']
            self.form['instanceWid'] = self.instanceWid
        else:
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
                        userItems = userForm['value']
                        # 多选也需要移除多余的选项
                        for fieldItem in formItem['fieldItems'].copy():
                            if fieldItem['content'] in userItems:
                                # formItem['value'] += fieldItem['content'] + ' ' # 这句不知道有什么用
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
                        dirList = userForm['value']
                        # 序列/字符串转列表
                        dirList = DT.formatStrList(dirList)
                        # 检查列表长度
                        dirListLen = len(dirList)
                        if dirListLen > 10 or dirListLen == 0:
                            raise TaskError(f'配置中填写的图片路径({dirListLen})过多')
                        # 将列表中的每一项都加入到value中
                        imgUrlList = []
                        for i, pic in enumerate(dirList, 1):
                            picBlob, picType = RT.choicePhoto(
                                pic, dirTimeFormat=True)
                            # 上传图片
                            url_getUploadPolicy = f'{self.host}wec-counselor-collector-apps/stu/obs/getUploadPolicy'
                            ossKey = CpdailyTools.uploadPicture(
                                url_getUploadPolicy, self.session, picBlob, picType)
                            # 获取图片url
                            url_previewAttachment = f'{self.host}wec-counselor-collector-apps/stu/collector/previewAttachment'
                            imgUrl = CpdailyTools.getPictureUrl(
                                url_previewAttachment, self.session, ossKey)
                            # 加入到value中
                            imgUrlList.append(imgUrl)
                            # 保存图片
                            self.savePicture(len(picBlob), i, ossKey)
                        formItem['value'] = ",".join(imgUrlList)
                        # 填充其他信息
                        formItem.setdefault('http', {
                            'defaultOptions': {
                                'customConfig': {
                                    'pageNumberKey': 'pageNumber',
                                    'pageSizeKey': 'pageSize',
                                    'pageDataKey': 'rows',
                                    'pageTotalKey': 'totalSize',
                                    'dataKey': 'datas',
                                    'codeKey': 'code',
                                    'messageKey': 'message'
                                }
                            }
                        })
                        formItem['uploadPolicyUrl'] = '/wec-counselor-collector-apps/stu/obs/getUploadPolicy'
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
            self.form["formWid"] = self.formWid
            self.form["address"] = self.userInfo['address']
            self.form["collectWid"] = self.wid
            self.form["schoolTaskWid"] = self.schoolTaskWid
            self.form["uaIsCpadaily"] = True
            self.form["latitude"] = self.userInfo['lat']
            self.form["longitude"] = self.userInfo['lon']
            self.form['instanceWid'] = self.instanceWid

    def getSubmitExtension(self):
        '''生成各种额外参数'''
        extension = {
            "lon": self.form['longitude'],
            "lat": self.form['latitude'],
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
            "lon": self.form['longitude'],
            "version": self.userInfo['signVersion'],
            "calVersion": self.userInfo['calVersion'],
            "deviceId": self.userInfo['deviceId'],
            "userId": self.userInfo['username'],
            "systemName": self.userInfo['systemName'],
            "bodyString": self.bodyString,
            "lat": self.form['latitude'],
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
        return '[%s]%s' % (data['message'], self.taskName)
