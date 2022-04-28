# coding=utf-8
# ====================开始导入模块====================
# 导入标准库
import imp
import os
import sys
import codecs
import traceback
import re

# 检查python版本
if not (sys.version_info[0] == 3 and sys.version_info[1] >= 6):
    raise Exception(
        "!!!!!!!!!!!!!!Python版本错误!!!!!!!!!!!!!!\n请使用python3.6及以上版本，而不是[python %s]" % sys.version)
# 环境变量初始化
try:
    print("==========脚本开始初始化==========")
except UnicodeEncodeError:
    # 设置默认输出编码为utf-8, 但是会影响腾讯云函数日志输出。
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    print("==========脚本开始初始化(utf-8输出)==========")
absScriptDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(absScriptDir)  # 将工作路径设置为脚本位置
os.environ['TZ'] = "Asia/Shanghai"  # 将时区设为UTC+8
sys.path.append(absScriptDir)  # 将脚本路径加入模块搜索路径

# 检查第三方模块
try:
    for i in ("requests", "requests_toolbelt", "urllib3", "bs4", "Crypto", "pyDes", "yaml", "lxml", "rsa"):
        imp.find_module(i)
except ImportError as e:  # 腾讯云函数在初始化过程中print运作不正常，所以将信息丢入异常中
    raise ImportError(f"""!!!!!!!!!!!!!!缺少第三方模块(依赖)!!!!!!!!!!!!!!
请使用pip3命令安装或者手动将依赖拖入文件夹
错误信息: [{e}]""")
# 检查Crypto是否对应系统版本
try:
    from Crypto.Cipher import AES
except OSError as e:
    raise OSError(f"""!!!!!!!!!!!!!!Crypto模块版本错误!!!!!!!!!!!!!!
请不要将linux系统(比如云函数)和windows系统的依赖混用
错误信息: [{e}]""")

# 检查代码完整性
try:
    for i in ("todayLoginService", "actions/autoSign", "actions/collection", "actions/sleepCheck", "actions/workLog", "actions/sendMessage", "actions/teacherSign", "login/Utils", "login/casLogin", "login/iapLogin", "login/RSALogin", "liteTools"):
        i = os.path.normpath(i)  # 路径适配系统
        imp.find_module(i)
except ImportError as e:
    raise ImportError(f"""!!!!!!!!!!!!!!脚本代码文件缺失!!!!!!!!!!!!!!
请尝试重新下载代码
错误信息: [{e}]""")
# 导入脚本的其他部分(不使用结构时, 格式化代码会将import挪至最上)
if True:
    from liteTools import TaskError, RT, DT, LL, NT, MT, ST, TT
    from login.Utils import Utils
    from actions.teacherSign import teacherSign
    from actions.sendMessage import SendMessage
    from actions.workLog import workLog
    from actions.sleepCheck import sleepCheck
    from actions.collection import Collection
    from actions.autoSign import AutoSign
    from todayLoginService import TodayLoginService
# ====================完成导入模块====================


class SignTaskStatus:
    '''用于标记用户完成情况
    :code的含义
    0: 等待执行
    1: 出现错误(等待重试)
    100: 任务已被完成
    101: 该任务正常执行完成
    200: 用户设置不执行该任务
    201: 该任务不在执行时间
    300: 出错
    301: 当前情况无法完成该任务
    400: 没有找到需要执行的任务
    '''

    def __init__(self, code, msg=''):
        self.code = code
        self.msg = msg

    def codeHead(self):
        return int(self.code/100)
    
    def liteMsgEn(self):
        ch = self.codeHead()
        if ch == 0:
            return 'todo'
        elif ch == 1:
            return 'done'
        elif ch == 2:
            return 'skip'
        elif ch == 3:
            return 'error'
        elif ch == 4:
            return 'notFound'


def loadConfig():
    '''配置文件载入函数'''
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
        'locationOffsetRange': 50
    }
    defaultConfig.update(config)
    config.update(defaultConfig)

    # 用户配置初始化
    for user in config['users']:
        LL.log(1, f"正在初始化{user['username']}的配置")
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

        # 签到状态初始化
        if TT.isInTimeList(user['taskTimeRange']):
            user['taskStatus'] = SignTaskStatus(0)
        else:
            user['taskStatus'] = SignTaskStatus(201, '该任务不在执行时间')

        # 用户设备ID
        user['deviceId'] = user.get(
            'deviceId', RT.genDeviceID(user.get('schoolName', '')+user.get('username', '')))

        # 用户代理
        user.setdefault('proxy')
        if not user['proxy']:  # 如果用户代理设置为空，则不设置代理。
            user['proxy'] = {}
        elif type(user['proxy']) == str:
            if re.match(r"https?:\/\/", user['proxy']):
                userProxy = user['proxy']
                user['proxy'] = {
                    'http': userProxy,
                    'https': userProxy
                }
            else:
                raise Exception("代理应以http://或https://为开头")
        elif type(user['proxy']) == dict:
            pass
        else:
            raise TypeError(f"不支持[{type(user['proxy'])}]类型的用户代理输入")
        # 检查代理可用性
        if user['proxy'] and NT.isDisableProxies(user['proxy']):
            user['proxy'] = {}
            LL.log(2, '用户代理已取消使用')

        # 坐标随机偏移
        user['global_locationOffsetRange'] = config['locationOffsetRange']
        if 'lon' in user and 'lat' in user:
            user['lon'], user['lat'] = RT.locationOffset(
                user['lon'], user['lat'], config['locationOffsetRange'])
    return config


def working(user):
    '''任务执行入口函数'''
    LL.log(1, '准备登录')
    today = TodayLoginService(user)
    today.login()
    LL.log(1, '登录完成')
    # 登陆成功，通过type判断当前属于 信息收集、签到、查寝
    # 信息收集
    if user['type'] == 0:
        # 以下代码是信息收集的代码
        LL.log(1, '即将开始信息收集填报')
        collection = Collection(today, user)
        collection.queryForm()
        collection.fillForm()
        msg = collection.submitForm()
        return msg
    elif user['type'] == 1:
        # 以下代码是签到的代码
        LL.log(1, '即将开始签到')
        sign = AutoSign(today, user)
        sign.getUnSignTask()
        sign.getDetailTask()
        sign.fillForm()
        msg = sign.submitForm()
        return msg
    elif user['type'] == 2:
        # 以下代码是查寝的代码
        LL.log(1, '即将开始查寝填报')
        check = sleepCheck(today, user)
        check.getUnSignedTasks()
        check.getDetailTask()
        check.fillForm()
        msg = check.submitForm()
        return msg
    elif user['type'] == 3:
        # 以下代码是工作日志的代码
        LL.log(1, '即将开始工作日志填报')
        work = workLog(today, user)
        work.checkHasLog()
        work.getFormsByWids()
        work.fillForms()
        msg = work.submitForms()
        return msg
    elif user['type'] == 4:
        # 以下代码是政工签到的代码
        LL.log(1, '即将开始政工签到填报')
        check = teacherSign(today, user)
        check.getUnSignedTasks()
        check.getDetailTask()
        check.fillForm()
        msg = check.submitForm()
        return msg
    else:
        raise Exception('任务类型出错，请检查您的user的type')


def main():
    '''主函数'''
    print("==========脚本开始执行==========")

    # 加载配置
    config = loadConfig()
    maxTry = config['maxTry']

    # 开始签到
    # 自动重试
    for tryTimes in range(1, maxTry+1):
        LL.log(1, '正在进行第%d轮尝试' % tryTimes)
        # 遍历用户
        users = config['users']
        for user in users:
            # 检查是否完成该任务
            if not user['taskStatus'].codeHead() == 0:
                continue
            LL.log(1, '即将在第%d轮尝试中为[%s]签到' % (tryTimes, user['username']))

            # 用户间随机延迟
            RT.randomSleep(config['delay'])

            # 执行签到
            try:
                msg = working(user)
            except TaskError as e:
                user['taskStatus'].code = e.code
                msg = str(e)
            except Exception as e:
                user['taskStatus'].code = 1
                msg = f"[{e}]\n{traceback.format_exc()}"
                LL.log(3, ST.notionStr(msg), user['username']+'签到失败'+msg)
                if maxTry != tryTimes:
                    continue

            # 消息格式化
            msg = f"--{user['username']}|{tryTimes}\n--{msg}"
            user['taskStatus'].msg = msg
            LL.log(1, msg)
            # 消息推送
            sm = SendMessage(user.get('sendMessage'))
            sm.send(f"『[{LL.prefix}]用户签到情况\n{msg}』", f"用户签到情况|{user['taskStatus'].liteMsgEn()}")
            LL.log(1, sm.log_str)

    # 签到情况推送
    msg = f'『[{LL.prefix}]全局签到情况』\n'
    for user in users:
        msg += '[%s]\n%s\n' % (user['remarkName'], user['taskStatus'].msg)
    LL.log(1, msg)
    codeList = [i['taskStatus'].codeHead() for i in users]
    codeCount = [0]*5
    for i in codeList:
        codeCount[i] += 1
    sm = SendMessage(config.get('sendMessage'))
    sm.send(msg+'\n'+LL.getLog(4),
            f'全局签到情况|do:{len(codeList)-codeCount[2]}done:{codeCount[1]}notFound:{codeCount[4]}')
    LL.log(1, sm.log_str)


def handler(event, context):
    '''阿里云的入口函数'''
    main()


def main_handler(event, context):
    '''腾讯云的入口函数'''
    main()
    return 'ok'


if __name__ == '__main__':
    '''本地执行入口位置'''
    try:
        main()
    finally:
        LL.saveLog(DT.loadYml('config.yml').get('logDir'))  # 生成日志文件
