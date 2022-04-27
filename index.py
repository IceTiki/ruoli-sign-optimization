# coding=utf-8
# ====================开始导入模块====================
# 导入标准库
import imp
import os
import sys
import codecs
import traceback
import re
import datetime
import pytz
import time

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
    from liteTools import TaskError, RT, DT, LL, NT, MT, ST
    from login.Utils import Utils
    from actions.teacherSign import teacherSign
    from actions.sendMessage import SendMessage
    from actions.workLog import workLog
    from actions.sleepCheck import sleepCheck
    from actions.collection import Collection
    from actions.autoSign import AutoSign
    from todayLoginService import TodayLoginService
# ====================完成导入模块====================


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
        'locationOffsetRange': 50,
        'API_trigger': None
    }
    defaultConfig.update(config)
    config.update(defaultConfig)

    # 用户配置初始化
    for user in config['users']:
        LL.log(1, f"正在初始化{user['username']}的配置")
        # 初始化静态配置项目
        defaultConfig = {
            'remarkName': '默认备注名',
            'sendMessage': None,
            'PlanSignWeek': '0,1,2,3,4,5,6',
            'PlanSignHour': '',
            'PlanSignMinute': '0',
            'if_sign_in': True,
            'state': None,
            'model': 'OPPO R11 Plus',
            'appVersion': '9.0.14',
            'systemVersion': '4.4.4',
            'systemName': 'android',
            "signVersion": "first_v3",
            "calVersion": "firstv",
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
        for user in config['users']:
            # 判断是否属于应该签到的时间
            # 当前是星期几
            Current_Time_Week = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai')).strftime('%w')
            # 获取当前时间（单位：小时）
            Current_Time_Hour = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai')).strftime('%H')
            # 获取当前时间（单位：分钟）
            Current_Time_Minute = datetime.datetime.now().timetuple().tm_min
            # 如果当前时间不在计划时间内，则跳过签到
            if Current_Time_Week not in user['PlanSignWeek']:
                user['if_sign_in'] = False
            elif Current_Time_Hour not in user['PlanSignHour']:
                user['if_sign_in'] = False
            else:
                user['if_sign_in'] = False
                for minute in user['PlanSignMinute']:
                    if (abs(Current_Time_Minute - int(minute)) < 15):
                        user['if_sign_in'] = True
                        break
            if user['if_sign_in'] == False:
                continue
            # 检查是否已经在上一轮尝试中签到
            if type(user['state']) == str:
                continue
            LL.log(1, '即将在第%d轮尝试中为[%s]签到' % (tryTimes, user['username']))

            # 用户间随机延迟
            RT.randomSleep(config['delay'])

            # 执行签到
            try:
                msg = working(user)
            except TaskError as e:
                msg = str(e)
            except Exception as e:
                msg = f"[{e}]\n{traceback.format_exc()}"
                LL.log(3, ST.notionStr(msg), user['username']+'签到失败'+msg)
                if maxTry != tryTimes:
                    continue

            # 消息格式化
            signtime = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            msg = '[%s]\n--%s|%d\n--%s\n签到时间：%s' % (user['remarkName'], user['username'], tryTimes, msg, signtime)
            user['state'] = '%s\n' % (msg)
            if user['sendMessage'] is not None:
                user['state'] += '<font color="green">该用户接收推送消息</font>'
            else:
                user['state'] += '<font color="red">该用户拒绝推送消息</font>'
            LL.log(1, msg)
            # 消息推送
            sm = SendMessage(user.get('sendMessage'))
            sm.send(f"---[{LL.prefix}]签到情况---\n{msg}", '用户签到情况')
            LL.log(1, sm.log_str)

    # 签到情况推送
    msg = f'---[{LL.prefix}]签到情况---\n'
    sign_sum = 0
    success_sum = 0
    # 统计参与登录的和签到成功的账号数量
    for i in config['users']:
        if i['if_sign_in'] is True:
            sign_sum += 1
            if 'SUCCESS' in i['state']:
                success_sum += 1
    if sign_sum == 0:
        msg += '当前时段无账号签到'
    else:
        msg += '本次共有 <b>%d</b> 个账号签到，其中有 <b>%d</b> 个签到成功：\n\n' % (sign_sum,success_sum)
        for i in config['users']:
            if i['if_sign_in'] is True:
                msg += '%s\n\n' % (i['state'])
        if config['API_trigger'] is not None:
            msg += '<a href="%s">手动触发任务</a>' % (config['API_trigger'])
    LL.log(1, msg)
    sm = SendMessage(config.get('sendMessage'))
    msgTitle = '全局签到情况 (%s / %s)' % (success_sum , sign_sum)
    sm.send(msg+'\n'+LL.getLog(4), msgTitle)
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
