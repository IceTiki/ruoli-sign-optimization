import random
import traceback
import os
import sys

from liteTools import FileOut, LL, TT, DT, HSF, ST, RT, ProxyGet, TaskError
from actions.teacherSign import teacherSign
from actions.workLog import workLog
from actions.sleepCheck import sleepCheck
from actions.collection import Collection
from actions.autoSign import AutoSign
from actions.sendMessage import SendMessage
from todayLoginService import TodayLoginService


class SignTask:
    userSessions = {}
    codeHeadCounts = 5
    statusMsg_en = {
        0: 'todo',
        1: 'done',
        2: 'skip',
        3: 'error',
        4: 'notFound'
    }
    status_msg = {
        0: "等待执行",
        1: "出现错误(等待重试)",
        100: "任务已被完成",
        101: "该任务正常执行完成",
        200: "用户设置不执行该任务",
        201: "该任务不在执行时间",
        300: "出错",
        301: "当前情况无法完成该任务",
        400: "没有找到需要执行的任务"
    }

    def __init__(self, userConfig: dict, maxTry: int = 3):
        '''
        :params userConfig: 用户配置
        :params maxTry: 最大尝试次数
        '''
        self.config: dict = userConfig
        self.msg: str = ""
        self.code: int = 0
        self.maxTry: int = int(maxTry)
        self.attempts: int = 0  # 任务触发次数
        self.username = userConfig.get("username", "?username?")

        # 检查任务是否在执行时间
        if TT.isInTimeList(userConfig['taskTimeRange']):
            self.code = 0
        else:
            self.code = 201
            self.msg = '该任务不在执行时间'

    def execute(self):
        '''
        任务执行函数(含异常处理、重试次数等)
        '''
        self.attempts += 1
        # 检查是否已经完成该任务
        if not self.codeHead == 0:
            return
        LL.log(1, '即将在第%d轮尝试中为[%s]签到' % (self.attempts, self.username))

        # 执行签到
        try:
            # 登录
            self._login()
            # 执行签到任务
            self._execute()
        except TaskError as e:
            self.code = e.code
            self.msg = str(e)
        except Exception as e:
            self.code = 1
            self.msg = f"[{e}]\n{traceback.format_exc()}"
            LL.log(3, ST.notionStr(self.msg),
                   self.config['username']+'签到失败'+self.msg)
        finally:
            # 收尾工作
            self._afterExecute()

    def _login(self):
        '''
        登录, 更新self.session和self.host
        '''
        LL.log(1, '准备登录')
        uuid = self.uuid
        userSessions = SignTask.userSessions

        if userSessions.get(uuid):
            LL.log(1, '正在复用登录Session')
            uSession = userSessions[uuid]['session']
            uHost = userSessions[uuid]['host']
        else:
            LL.log(1, '正在尝试进行登录')
            today = TodayLoginService(self.config)
            today.login()
            uSession = today.session
            uHost = today.host

        userSessions[uuid] = {
            'session': uSession, 'host': uHost}
        LL.log(1, '登录完成')
        # 更新数据
        self.session = uSession
        self.host = uHost
        return

    def _execute(self):
        '''任务执行函数'''
        user = self.config
        # 通过type判断当前属于 信息收集、签到、查寝
        # 信息收集
        if user['type'] == 0:
            # 以下代码是信息收集的代码
            LL.log(1, '即将开始信息收集填报')
            collection = Collection(user, self.session, self.host)
            collection.queryForm()
            collection.fillForm()
            msg = collection.submitForm()
        elif user['type'] == 1:
            # 以下代码是签到的代码
            LL.log(1, '即将开始签到')
            sign = AutoSign(user, self.session, self.host)
            sign.getUnSignTask()
            sign.getDetailTask()
            sign.fillForm()
            msg = sign.submitForm()
        elif user['type'] == 2:
            # 以下代码是查寝的代码
            LL.log(1, '即将开始查寝填报')
            check = sleepCheck(user, self.session, self.host)
            check.getUnSignedTasks()
            check.getDetailTask()
            check.fillForm()
            msg = check.submitForm()
        elif user['type'] == 3:
            # 以下代码是工作日志的代码
            raise TaskError('工作日志模块已失效')
            LL.log(1, '即将开始工作日志填报')
            work = workLog(today, user)
            work.checkHasLog()
            work.getFormsByWids()
            work.fillForms()
            msg = work.submitForms()
        elif user['type'] == 4:
            # 以下代码是政工签到的代码
            LL.log(1, '即将开始政工签到填报')
            check = teacherSign(user, self.session, self.host)
            check.getUnSignedTasks()
            check.getDetailTask()
            check.fillForm()
            msg = check.submitForm()
        else:
            raise Exception('任务类型出错，请检查您的user的type')

        self.msg = msg
        return msg

    def _afterExecute(self):
        '''
        执行后收尾工作
        '''
        # 如果执行出错需要重试, 则跳过收尾工作
        if self.codeHead == 0 and self.maxTry != self.attempts:
            return

        # 消息推送
        msg = f"--{self.username}|{self.attempts}\n--{self.msg}"
        LL.log(1, msg)
        sm = self.sendMsg
        sm.send(f"『[{LL.prefix}]用户签到情况\n{msg}』",
                f"用户签到情况|{self.statusMsg_en}")
        LL.log(1, f"『{self.username}』用户推送情况", sm.log_str)

    @property
    def webhook(self):
        return {
            "username": self.username,
            "remarkName": self.config["remarkName"]
        }

    @property
    def sendMsg(self):
        '''
        任务绑定的消息发送类
        :returns SendMessage
        '''
        return SendMessage(self.config.get('sendMessage'))

    @staticmethod
    def cleanSession(uuid=None):
        '''
        清理用户Session, 如果uuid为空, 则清理全部Session; 否则清理对应uuid的Session。
        '''
        if not uuid:
            SignTask.userSessions.clear()
        else:
            SignTask.userSessions.pop(uuid, None)

    @property
    def uuid(self):
        '''
        根据用户名和学校给每个用户分配一个uuid。
        用于一个用户有多个任务时, 登录状态的Sesssion复用。
        '''
        HSF.strHash(self.config.get('schoolName', '') +
                    self.config.get('username', ''), 256)

    @property
    def codeHead(self):
        return int(self.code/100)

    @property
    def msgEn(self):
        return SignTask.statusMsg_en[self.codeHead()]


class MainHandler:
    msgOut: FileOut = sys.stdout

    def __init__(self, entranceType: str, event: dict = {}, context: dict = {}):
        '''
        初始化
        :params entranceType: 执行方式, 主要区分云函数与本地执行(因为云函数一般无法写入文件)
        '''
        self.entrance: str = entranceType
        self.event: dict = event
        self.context: dict = context

        self.config: dict = self.loadConfig()
        self.msgOut = self._setMsgOut()
        self._maxTry = self.config['maxTry']
        self.taskList = [SignTask(u, self._maxTry)
                         for u in self.config['users']]

    def execute(self):
        '''
        执行签到任务
        '''
        LL.log(1, "==========脚本开始执行==========")
        # 开始签到
        # 自动重试
        maxTry = self._maxTry
        for tryTimes in range(1, maxTry+1):
            LL.log(1, '正在进行第%d轮尝试' % tryTimes)
            SignTask.cleanSession()
            # 遍历用户
            for task in self.taskList:
                # 用户间随机延迟
                RT.randomSleep(self.config['delay'])
                # 执行
                task.execute()
                # 清理无用session
                self.cleanSession(task.uuid)
        # 签到情况推送
        LL.log(1, self.msg_g1)
        sm = SendMessage(self.config.get('sendMessage'))
        sm.send(msg=self.msg_g1+'\n'+LL.getLog(4), title=self.title_g1, attachments=[(self.msgOut.log.encode(encoding='utf-8'),
                                                                                      TT.formatStartTime("LOG#t=%Y-%m-%d--%H-%M-%S##.txt"))])
        LL.log(1, '全局推送情况', sm.log_str)

    def cleanSession(self, uuid: str):
        '''
        登录状态内存释放: 如果同用户还有没有待执行的任务, 则删除session
        '''
        for i in self.taskList:
            if i.code == 0 and i.uuid == uuid:
                break
        else:
            SignTask.cleanSession(uuid)

    def _setMsgOut(self):
        '''
        设置日志输出
        :returns msgOut: FileOut
        '''
        logDir = self.config.get('logDir')
        if type(logDir) == str and self.entrance == "__main__":
            try:
                logDir = os.path.join(logDir, TT.formatStartTime(
                    "LOG#t=%Y-%m-%d--%H-%M-%S##.txt"))
                msgOut = FileOut(logDir)
            except Exception() as e:
                LL.log(2, f"日志文件输出启用失败, 错误信息: [{e}]")
                msgOut = FileOut(None)
        else:
            msgOut = FileOut(None)
        msgOut.start()
        return msgOut

    def loadConfig(self):
        '''
        配置文件载入
        :returns config: dict
        '''
        try:
            config = DT.loadYml('config.yml')
        except Exception as e:
            errmsg = f"""读取配置文件出错
请尝试检查配置文件(建议下载VSCode并安装yaml插件进行检查)
错误信息: {e}"""
            LL.log(4, ST.notionStr(errmsg))
            raise e
        # 全局配置初始化
        defaultConfig = {
            'delay': (5, 10),
            'locationOffsetRange': 50,
            "shuffleTask": False
        }
        defaultConfig.update(config)
        config.update(defaultConfig)

        # 用户配置初始化
        if config['shuffleTask']:
            LL.log(1, "随机打乱任务列表")
            random.shuffle(config['users'])
        for user in config['users']:
            LL.log(1, f"正在初始化{user['username']}的配置")
            user: dict
            # 初始化静态配置项目
            defaultConfig = {
                'remarkName': '默认备注名',
                'model': 'OPPO R11 Plus',
                'appVersion': '9.0.14',
                'systemVersion': '4.4.4',
                'systemName': 'android',
                "signVersion": "first_v3",
                "calVersion": "firstv",
                'taskTimeRange': "1-7 1-12 1-31 0-23 0-59",
                'getHistorySign': False,
                'title': 0,
                'signLevel': 1,
                'abnormalReason': "回家",
                'qrUuid': None
            }
            defaultConfig.update(user)
            user.update(defaultConfig)

            # 用户设备ID
            user['deviceId'] = user.get(
                'deviceId', RT.genDeviceID(user.get('schoolName', '')+user.get('username', '')))

            # 用户代理
            user.setdefault('proxy')
            user['proxy'] = ProxyGet(user['proxy'])

            # 坐标随机偏移
            user['global_locationOffsetRange'] = config['locationOffsetRange']
            if 'lon' in user and 'lat' in user:
                user['lon'], user['lat'] = RT.locationOffset(
                    user['lon'], user['lat'], config['locationOffsetRange'])
        return config

    @property
    def title_g1(self):
        """
        全局标题1
        示例: 『全局签到情况(114/514)[V-T1.0.0]』
        """
        codeCount = self.codeCount
        # generalSituations —— "done/(total-skip)"
        generalSituations = f'{codeCount[1]}/{sum(codeCount)-codeCount[2]}'
        return f"『全局签到情况({generalSituations})[{LL.prefix}]』"

    @property
    def time_g1(self):
        """
        时间统计1
        示例: Running at 2022-01-01 00:00:00, using 1145.14s
        """
        return f'Running at {TT.formatStartTime()}, using {TT.executionSeconds()}s'

    @property
    def count_g1(self):
        """
        签到情况统计1
        示例: 10: 1todo, 8done, 1skip, 0error, 0notFound
        """
        codeCount = self.codeCount
        cl = SignTask.statusMsg_en
        return f'{sum(codeCount)}: ' + ", ".join([f"{codeCount[i]}{cl[i]}" for i in range(SignTask.codeHeadCounts)])

    @property
    def msg_g1(self):
        """
        全局签到情况1
        示例: 
        『全局签到情况(1/2)[V-T1.0.0]』
        [小李]
        --1145141919|1
        --初始化类失败，请键入完整的参数（用户名，密码，学校名称）
        [小王]
        --1145141919|1
        --[SUCCESS]须弥教令院每日打卡
        Running at 2022-01-01 00:00:00, using 1145.14s
        2: 0todo, 1done, 0skip, 1error, 0notFound
        """
        msg = ""
        msg += self.title_g1
        for task in self.taskList:
            # 忽略跳过的任务
            if task.codeHead != 2:
                msg += ("\n" + f"[{task.config['remarkName']}]")
                msg += ("\n" + task.msg)
        msg += ("\n" + self.time_g1)
        msg += ("\n" + self.count_g1)
        return msg

    @property
    def codeCount(self):
        """状态码统计"""
        codeList = [i.codeHead for i in self.taskList]
        codeCount = [0]*SignTask.codeHeadCounts
        for i in codeList:
            codeCount[i] += 1
        return codeCount
