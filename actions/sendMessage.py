import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
import re
from urllib import parse
import json


# 通知类
class SendMessage:
    def __init__(self, con: dict):
        if type(con) != dict:
            con = dict()
        self.qmsg = Qmsg(con.get('qmsg_key'), con.get(
            'qmsg_qq'), con.get('qmsg_isGroup'))
        self.smtp = Smtp(con.get('smtp_host'), con.get('smtp_user'),
                         con.get('smtp_key'), con.get('smtp_sender'),
                         con.get('smtp_senderName'), con.get('smtp_receivers'))
        self.rl = RlMessage(con.get('rl_email'),
                            con.get('rl_emailApiUrl'))
        self.iceCream = IceCream(con.get('iceCream_token'))
        self.pp = Pushplus(con.get('pushplus_parameters'))
        self.sc = Serverchan(con.get('severchan_sendkey'))
        self.gotify = Gotify(con.get('gotify_url'), con.get('gotify_apptoken'))
        self.log_str = '推送情况\n'

    def send(self, msg='no msg', title='no title', attachments=()):
        try:
            self.log_str += '\nQMSG酱|' + self.qmsg.send(f"{title}\n{msg}")
        except Exception as e:
            self.log_str += '\nQMSG酱|出错|%s' % e
        try:
            self.log_str += '\nSMTP|' + \
                            self.smtp.sendmail(msg, title, attachments)
        except Exception as e:
            self.log_str += '\nSMTP|出错|%s' % e
        try:
            self.log_str += '\n若离邮箱API|' + self.rl.sendMail(msg, title)
        except Exception as e:
            self.log_str += '\n若离邮箱API|出错|%s' % e
        try:
            self.log_str += '\nIceCream|' + \
                            self.iceCream.send(f"{title}\n{msg}")
        except Exception as e:
            self.log_str += '\nIceCream|出错|%s' % e
        try:
            self.log_str += '\nPushplus|' + self.pp.sendPushplus(msg, title)
        except Exception as e:
            self.log_str += '\nPushplus|出错|%s' % e
        try:
            self.log_str += '\nServerchan|' + self.sc.sendServerchan(msg, title)
        except Exception as e:
            self.log_str += '\nServerchan|出错|%s' % e
        try:
            self.log_str += '\nGotify|' + self.gotify.sendWithGotify(msg, title)
        except Exception as e:
            self.log_str += '\nGotify|出错|%s' % e


class RlMessage:
    '''若离消息通知类'''

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
            if not item:
                return 0
            if "*" in item:
                return 0
        return 1

    # 发送邮件消息
    def sendMail(self, msg, title):
        # 若离邮件api， 将会存储消息到数据库，并保存1周以供查看，请勿乱用，谢谢合作
        if self.configIsCorrect:
            params = {
                'recipient': self.mail,
                'title': title,
                'content': msg
            }
            res = requests.post(url=self.apiUrl, params=json.dumps(params))
            res = res.json()
            return res['message']
        else:
            return '无效配置'


class Pushplus:
    '''Pushplus推送类'''

    def __init__(self, parameters: str):
        """
        :params parameters: "xxx"形式的令牌 或者 "token=xxx&topic=xxx&yyy=xxx"形式参数列表
        """
        self.parameters = parameters
        self.api = "https://www.pushplus.plus/send"
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查邮箱地址或API地址是否合法
        if not type(self.parameters) == str:
            return 0
        if not self.parameters:
            return 0
        return 1

    def sendPushplus(self, msg, title):
        title = str(title)

        msgs = []
        for seg in str(msg).split("\n"):
            if seg:
                if seg.startswith(">>"):
                    seg = f"> {seg[2:]}\n"
                msgs.append(seg)
        msg = '\n'.join(msgs)

        if self.configIsCorrect:
            # 解析参数
            if "=" in self.parameters:  # 如果是url形式的参数
                params = parse.parse_qs(
                    parse.urlparse(self.parameters).path)  # 解析参数
                params = {k: params.copy()[k][0]
                          for k in params.copy()}  # 解析参数
                params.update({'title': title, 'content': msg})
            else:  # 如果参数是token本身
                params = {
                    'token': self.parameters,
                    'title': title,
                    'content': msg,
                }
            # 准备发送
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
            }
            res = requests.post(
                self.api, headers=headers, params=params)
            if res.status_code == 200:
                return "发送成功"
            else:
                return "发送失败"
        else:
            return '无效配置'


class Serverchan:
    '''ServerChan推送类'''

    def __init__(self, sendkey: str):
        """
        :params sendkey: serverchan的SendKey,例如: SCT77****************S
        """
        try:
            self.sendkey = sendkey if sendkey.startswith("SCT") else None
        except Exception:
            self.sendkey = None

    def sendServerchan(self, msg, title):
        if self.sendkey is None:
            return '无效配置'

        msgs = []
        for seg in str(msg).split("\n"):
            if seg:
                if seg.startswith(">>"):
                    seg = f"> {seg[2:]}\n"
                msgs.append(seg)

        params = {
            'title': str(title),
            'desp': '\n'.join(msgs)
        }
        # 准备发送
        res = requests.post(
            f"https://sctapi.ftqq.com/{self.sendkey}.send", params=params)
        return "发送成功" if res.status_code == 200 else "发送失败"


class Qmsg:
    '''Qmsg发送类'''

    def __init__(self, key: str, qq: str, isGroup: bool = False):
        """
        :params key: qmsg密钥
        :params qq: 接收消息的qq(多个qq以","分隔)
        :params isGroup: 接收者是否为群
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
        :params msg: 要发送的消息(自动转为字符串类型)"""
        # msg处理
        msg = str(msg)
        # 替换数字(避开qmsg的屏蔽规则)
        for i, k in zip(list('0123456789'), list('𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗')):
            msg = msg.replace(i, k)
        # 简单检查配置
        if not self.configIsCorrect:
            return ('无效配置')
        else:
            # 开始推送
            sendtype = 'group/' if self.isGroup else 'send/'
            res = requests.post(url='https://qmsg.zendee.cn/' + sendtype +
                                    self.key, data={'msg': msg, 'qq': self.qq})
            return str(res)


class Smtp:
    '''Smtp发送类'''

    def __init__(self, host: str, user: str, key: str, sender: str, senderName: str, receivers: list):
        """
        :params host: SMTP域名
        :params user: 用户账户
        :params key: 用户密钥
        :params sender: 邮件发送者(邮箱)
        :params senderName: 发送者名称(可以随便填)
        :params receivers: 邮件接收者列表(邮箱)
        """
        self.host = host
        self.user = user
        self.key = key
        self.sender = sender
        self.senderName = senderName
        self.receivers = receivers
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        # 简单检查邮箱地址或API地址是否合法
        if type(self.receivers) != list:
            return 0
        for item in [self.host, self.user, self.key, self.sender] + self.receivers:
            if not type(item) == str:
                return 0
            if len(item) == 0:
                return 0
            if "*" in item:
                return 0
        return 1

    def sendmail(self, msg, title='no title', attachments=()):
        """发送邮件
        :params msg: 要发送的消息(自动转为字符串类型)
        :params title: 邮件标题(自动转为字符串类型)
        :params attachment: 附件元组，形式为((blob二进制文件,fileName文件名),(blob,fileName),...)"""
        msg = str(msg)
        msg = msg.replace("\n", "<br>")
        title = str(title)
        if not self.configIsCorrect:
            return '无效配置'
        else:
            mail = MIMEMultipart()
            # 添加正文
            mail.attach(MIMEText(msg, 'html', 'utf-8'))
            # 添加标题
            mail['Subject'] = Header(title, 'utf-8')
            # 添加发送者
            mail['From'] = formataddr((self.senderName, self.sender), "utf-8")
            # 添加附件
            for attInfo in attachments:
                att = MIMEText(attInfo[0], 'base64', 'utf-8')
                att["Content-Type"] = 'application/octet-stream'
                att["Content-Disposition"] = f'attachment; filename="{attInfo[1]}"'
                mail.attach(att)
            # 发送邮件
            smtpObj = smtplib.SMTP_SSL(self.host, 465)
            smtpObj.login(self.user, self.key)
            smtpObj.sendmail(self.sender, self.receivers, mail.as_string())
            return ("邮件发送成功")


class IceCream:
    """IceCream发送类"""

    def __init__(self, token: str):
        """
        :params key: IceCream密钥
        """
        self.token = token
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        """简单检查配置是否合法"""
        if type(self.token) != str:
            return 0
        elif not re.match('^[0-9A-F]{32}$', self.token):
            return 0
        else:
            return 1

    def send(self, msg):
        """发送消息
        :params msg: 要发送的消息(自动转为字符串类型)
        """
        # msg处理
        msg = str(msg)
        # 简单检查配置
        if not self.configIsCorrect:
            return ('无效配置')
        else:
            # 开始推送
            res = requests.post(
                url=f'https://ice.ruoli.cc/api/send/{self.token}', data={'msg': msg})
            return str(res.json()['msg'])


class Gotify:
    '''Gotify推送类'''

    # Gotify 是一款可以自行搭建的自主推送服务

    def __init__(self, api_url: str, token: str):
        """
        :params api_url: Gotify 的 API 地址
        :params token： 从 Gotify 创建的 token
        """
        self.gotify_url = api_url
        self.gotify_apptoken = token  # Gotify 分为 app token 和 client token，请勿混淆
        self.configIsCorrect = self.isCorrectConfig()

    def isCorrectConfig(self):
        """简单检查配置是否合法"""
        if type(self.gotify_url) != str:
            return 0
        elif type(self.gotify_apptoken) != str:
            return 0
        else:
            return 1

    def sendWithGotify(self, msg, title):
        if self.gotify_apptoken is None:
            return '无效配置'

        # 简单检查配置
        if not self.configIsCorrect:
            return '无效配置'

        msgs = []
        for seg in str(msg).split("\n"):
            if seg:
                if seg.startswith(">>"):
                    seg = f"> {seg[2:]}\n"
                msgs.append(seg)

        params = {
            "extras": {
                "client::display": {
                    "contentType": "text/markdown"
                }
            },
            "title": str(title),
            "message": '\n'.join(msgs),
            "priority": 2
        }
        # 准备发送
        res = requests.post(
            f"{self.gotify_url}/message?token={self.gotify_apptoken}", json=params)
        return "发送成功" if res.status_code == 200 else "发送失败"
