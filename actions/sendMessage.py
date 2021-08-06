import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header


# 通知类
class SendMessage:
    def __init__(self, con):
        self.rl = RlMessage(con['rl_email'],
                            con['rl_emailApiUrl'])
        self.qmsg = Qmsg(con['qmsg_key'], con['qmsg_qq'], con['qmsg_isGroup'])
        self.smtp = Smtp(con['smtp_host'], con['smtp_user'],
                         con['smtp_key'], con['smtp_sender'], con['smtp_receivers'])

    def send(self, msg='default_msg', title='default_title'):
        try:
            self.qmsg.send(msg)
        except Exception as e:
            print('\nqmsg酱推送失败|%s' % e)
        try:
            self.rl.sendMail(msg, title)
        except Exception as e:
            print('\n若离消息推送失败|%s' % e)
        try:
            self.smtp.sendmail(msg, title)
        except Exception as e:
            print('\nSMTP推送失败|%s' % e)


# 若离消息通知类
class RlMessage:
    # 初始化类
    def __init__(self, mail, apiUrl):
        self.mail = mail
        self.apiUrl = apiUrl
        self.configIsCorrect = self.isCorrectConfig()

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
    def sendMail(self, msg, title):
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
    def __init__(self, key, qq, isGroup):
        # config={'key':'*****','qq':'*****','isgroup':0}
        self.key = key
        self.qq = qq
        self.isGroup = isGroup
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查key和qq是否合法
        for item in [self.key, self.qq]:
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
            sendtype = 'group/' if self.isGroup else 'send/'
            res = requests.post(url='https://qmsg.zendee.cn/'+sendtype +
                                self.key, data={'msg': msg, 'qq': self.qq})
            return str(res)
            #    code = res.json()['code']
            #    print(code)
        else:
            print('Qmsg配置出错')
            return 'Qmsg配置出错'


class Smtp:
    def __init__(self, host, user, key, sender, receivers):
        self.host = host
        self.user = user
        self.key = key
        self.sender = sender
        self.receivers = receivers
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查邮箱地址或API地址是否合法
        if type(self.receivers) != list:
            return 0
        for item in [self.host, self.user, self.key, self.sender]+self.receivers:
            if not type(item) == str:
                return 0
            if len(item) == 0:
                return 0
            if "*" in item:
                return 0
        return 1

    def sendmail(self, msg, title):
        if self.configIsCorrect:
            mail = MIMEText(msg, 'plain', 'utf-8')
            mail['Subject'] = Header(title, 'utf-8')

            smtpObj = smtplib.SMTP()
            smtpObj.connect(self.host, 25)
            smtpObj.login(self.user, self.key)
            smtpObj.sendmail(self.sender, self.receivers, mail.as_string())
            print("邮件发送成功")
        else:
            print('邮件配置出错')
            return '邮件配置出错'
