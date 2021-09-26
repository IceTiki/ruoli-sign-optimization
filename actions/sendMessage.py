import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import re


# 通知类
class SendMessage:
    def __init__(self, con: dict):
        if type(con)!=dict:
            con=dict()
        self.rl = RlMessage(con.get('rl_email'),
                            con.get('rl_emailApiUrl'))
        self.qmsg = Qmsg(con.get('qmsg_key'), con.get(
            'qmsg_qq'), con.get('qmsg_isGroup'))
        self.smtp = Smtp(con.get('smtp_host'), con.get('smtp_user'),
                         con.get('smtp_key'), con.get('smtp_sender'), con.get('smtp_receivers'))

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
    '''Qmsg发送类'''

    def __init__(self, key: str, qq: str, isGroup: bool = False):
        """
        :param key: qmsg密钥
        :param qq: 接收消息的qq(多个qq以","分隔)
        :param isGroup: 接收者是否为群
        """
        self.key = key
        self.qq = qq
        self.isGroup = isGroup
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        """简单检查配置是否合法"""
        if type(self.key) != str:
            return 0
        elif type(self.qq) != str:
            return 0
        elif not re.match('^[0-9a-f]{32}$', self.key):
            return 0
        elif not re.match('^\d+(,\d+)*$', self.qq):
            return 0
        else:
            return 1

    def send(self, msg):
        """发送消息
        :param msg: 要发送的消息(自动转为字符串类型)"""
        # msg：要发送的信息|消息推送函数
        msg = str(msg)
        # 简单检查配置
        if not self.configIsCorrect:
            print('Qmsg配置错误，信息取消发送')
        else:
            sendtype = 'group/' if self.isGroup else 'send/'
            res = requests.post(url='https://qmsg.zendee.cn/'+sendtype +
                                self.key, data={'msg': msg, 'qq': self.qq})
            return str(res)


class Smtp:
    '''Smtp发送类'''

    def __init__(self, host: str, user: str, key: str, sender: str, receivers: list):
        """
        :param host: SMTP的域名
        :param user: 用户名
        :param key: 用户的密钥
        :param sender: 邮件发送者(邮箱)
        :param receivers: 邮件接收者列表(邮箱)
        """
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

    def sendmail(self, msg, title='no title'):
        """发送邮件
        :param msg: 要发送的消息(自动转为字符串类型)
        :param title: 邮件标题(自动转为字符串类型)"""
        msg = str(msg)
        title = str(title)
        if not self.configIsCorrect:
            print('邮件配置出错')
            return '邮件配置出错'
        else:
            mail = MIMEText(msg, 'plain', 'utf-8')
            mail['Subject'] = Header(title, 'utf-8')

            smtpObj = smtplib.SMTP()
            smtpObj.connect(self.host, 25)
            smtpObj.login(self.user, self.key)
            smtpObj.sendmail(self.sender, self.receivers, mail.as_string())
            print("邮件发送成功")
