import random
import re


import requests
from urllib3.exceptions import InsecureRequestWarning
from login.Utils import Utils
from login.casLogin import casLogin
from login.iapLogin import iapLogin
from login.RSALogin import RSALogin
from liteTools import *

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TodayLoginService:
    # 初始化本地登录类
    def __init__(self, userInfo):
        if None == userInfo['username'] or '' == userInfo['username'] or None == userInfo['password'] or '' == userInfo[
            'password'] or None == userInfo['schoolName'] or '' == userInfo['schoolName']:
            raise TaskError('初始化类失败，请键入完整的参数（用户名，密码，学校名称）')
        self.username = userInfo['username']
        self.password = userInfo['password']
        self.schoolName = userInfo['schoolName']
        self.session = requests.session()
        headers = {'User-Agent': random.choice(Utils.getUserAgents())}
        # 关闭多余的连接
        self.session.keep_alive = False
        # 增加重试次数
        self.session.adapters.DEFAULT_RETRIES = 5
        self.session.headers = headers
        # 如果设置了用户的代理，那么该用户将走代理的方式进行访问
        self.session.proxies = userInfo['proxy']
        # 添加hooks进行拦截判断该请求是否被418拦截
        self.session.hooks['response'].append(Utils.checkStatus)
        self.login_url = ''
        self.host = ''
        self.login_host = ''
        self.loginEntity = None

    # 通过学校名称借助api获取学校的登陆url
    def getLoginUrlBySchoolName(self):
        schools = self.session.get('https://mobile.campushoy.com/v6/config/guest/tenant/list', verify=False, hooks=dict(response=[Utils.checkStatus])).json()[
            'data']
        flag = True
        for item in schools:
            if item['name'] == self.schoolName:
                if item['joinType'] == 'NONE':
                    raise TaskError(self.schoolName + '未加入今日校园，请检查...')
                flag = False
                params = {
                    'ids': item['id']
                }
                data = self.session.get('https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params,
                                        verify=False, hooks=dict(response=[Utils.checkStatus])).json()['data'][0]
                joinType = data['joinType']
                idsUrl = data['idsUrl']
                ampUrl = data['ampUrl']
                if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                    self.host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl)[0]
                    status_code = 0
                    while status_code != 200:
                        newAmpUrl = self.session.get(ampUrl, allow_redirects=False, verify=False)
                        status_code = newAmpUrl.status_code
                        if 'Location' in newAmpUrl.headers:
                            ampUrl = newAmpUrl.headers['Location']
                    self.login_url = ampUrl
                    self.login_host = re.findall('\w{4,5}\:\/\/.*?\/', self.login_url)[0]
                ampUrl2 = data['ampUrl2']
                if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                    self.host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl2)[0]
                    ampUrl2 = self.session.get(ampUrl2, verify=False).url
                    self.login_url = ampUrl2
                    self.login_host = re.findall(r'\w{4,5}\:\/\/.*?\/', self.login_url)[0]
                break

    # 通过登陆url判断采用哪种登陆方式
    def checkLogin(self):
        if self.login_url.find('/iap') != -1:
            self.loginEntity = iapLogin(self.username, self.password, self.login_url, self.login_host, self.session)
        elif self.login_url.find('kmu.edu.cn') != -1 or self.login_url.find('hytc.edu.cn') != -1:
            self.loginEntity = RSALogin(self.username, self.password, self.login_url, self.login_host, self.session)
        else:
            self.loginEntity = casLogin(self.username, self.password, self.login_url, self.login_host, self.session)
        # 统一登录流程
        self.session.cookies = self.loginEntity.login()

    # 本地化登陆
    def login(self):
        # 获取学校登陆地址
        self.getLoginUrlBySchoolName()
        self.checkLogin()
