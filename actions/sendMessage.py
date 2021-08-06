import requests



# 通知类
class SendMessage:
    def __init__(self, sendMessageConfig):
        self.rl = RlMessage(sendMessageConfig['email'],
                       sendMessageConfig['emailApiUrl'])
        self.qmsg = Qmsg(
            {'key': sendMessageConfig['key'], 'qq': sendMessageConfig['qq'], 'isGroup': sendMessageConfig['isGroup']})
    def send(self, msg='default_msg', title='default_title'):
        try:
            self.qmsg.send(msg)
        except Exception as e:
            print('|||log|||\nqmsg酱推送失败|%s'%e)
        try:
            self.rl.sendMail(title, msg)
        except Exception as e:
            print('|||log|||\n若离消息推送失败|%s'%e)


# 若离消息通知类
class RlMessage:
    # 初始化类
    def __init__(self, mail, apiUrl):
        self.mail = mail
        self.apiUrl = apiUrl
        self.configIsCorrect=self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查邮箱地址或API地址是否合法
        for item in [self.mail, self.apiUrl]:
            if not type(item) == str:
                return 0
            if len(item) == 0:
                return 0
            if "*" in item:
                return 0
        return 1

    # 发送邮件消息
    def sendMail(self, title, msg):
        # 若离邮件api， 将会存储消息到数据库，并保存1周以供查看，请勿乱用，谢谢合作
        if self.configIsCorrect:
            params = {
                'to': self.mail,
                'title': title,
                'content': msg
            }
            res = requests.post(url=self.apiUrl, params=params).json()
            return res['msg']
        else:
            print('邮箱或邮件api填写无效，已取消发送邮件！')
            return '邮箱或邮件api填写无效，已取消发送邮件！'



# Qmsg酱通知类
class Qmsg:
    def __init__(self, config):
        # config={'key':'*****','qq':'*****','isgroup':0}
        self.config = config
        self.configIsCorrect=self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查key和qq是否合法
        for item in [self.config['key'], self.config['qq']]:
            if not type(item) == str:
                return 0
            if len(item) == 0:
                return 0
            if "*" in item:
                return 0
        return 1

    def send(self, msg):
        # msg：要发送的信息|消息推送函数
        msg = str(msg)
        # 简单检查配置
        if self.configIsCorrect:
            sendtype = 'group/' if self.config['isGroup'] else 'send/'
            res = requests.post(url='https://qmsg.zendee.cn/'+sendtype +
                                self.config['key'], data={'msg': msg, 'qq': self.config['qq']})
            return str(res)
            #    code = res.json()['code']
            #    print(code)
        else:
            print('Qmsg配置出错')
            return 'Qmsg配置出错'
