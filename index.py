# ====================开始导入模块====================
# 导入标准库
import imp
import os
import sys
import codecs
import traceback


# 环境变量初始化
try:
    print("==========脚本开始初始化==========")
except UnicodeEncodeError:
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())  # 设置默认输出编码为utf-8, WARNING!!!但是会影响腾讯云函数日志输出。
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 将工作路径设置为脚本位置
os.environ['TZ'] = "Asia/Shanghai"  # 将时区设为UTC+8

# 检查第三方模块
try:
    for i in ("requests", "requests_toolbelt", "urllib3", "bs4", "Crypto", "pyDes", "yaml", "lxml", "rsa"):
        imp.find_module(i)
except ImportError as e:
    # =======WARNING!!!start=======
    # 在腾讯云函数中将e嵌入字符串中，或者print(e)会导致“except结构中的print()输出”在日志中丢失。但是在Exception中使用格式化，再print出Excetion是正常的。
    # 同时，似乎不能直接raise ImportError，要raise其他类型的异常“except结构中的print()输出”才会正常。
    # 同时似乎还要对e创建一些引用，特性太复杂了
    # 最后放弃了print()出错误信息
    # e2 = e
    # c2 = "asdads%sasda"%e
    # e3 =Exception(c2)
    # print(e3)
    # print("ccc")
    # raise e2
    # =======WARNING!!!end=======
    raise ImportError(f"""!!!!!!!!!!!!!!缺少第三方模块(依赖)!!!!!!!!!!!!!!
请使用pip命令安装或者手动将依赖拖入文件夹
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
    from liteTools import TaskError, RT, DT, LL
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
    '''配置文件载入'''
    try:
        config = DT.loadYml('config.yml')
    except Exception as e:
        print(f"""!!!!!!!!!!!!!!读取配置文件出错!!!!!!!!!!!!!!
请尝试检查配置文件(建议下载VSCode并安装yaml插件进行检查)
错误信息: {e}""")
        raise e
    # 全局配置初始化
    config['delay'] = tuple(config.get("delay", [5, 10]))

    # 用户配置初始化
    for user in config['users']:
        LL.log(1, f"正在初始化{user['username']}的配置")
        # 初始化静态配置项目
        defaultConfig = {
            'remarkName': '默认备注名',
            'state': None,
            'model': 'OPPO R11 Plus',
            'appVersion': '9.0.14',
            'systemVersion': '4.4.4',
            'systemName': 'android',
            "signVersion": "first_v3",
            "calVersion": "firstv",
            'getHistorySign': False
        }
        defaultConfig.update(user)
        user.update(defaultConfig)

        # 用户设备ID
        user['deviceId'] = user.get(
            'deviceId', RT.genDeviceID(user.get('schoolName', '')+user.get('username', '')))

        # 用户代理
        user['proxy'] = user.get('proxy')
        requestsProxies = dict()
        if not user['proxy']:  # 如果用户代理设置为空，则不设置代理。
            requestsProxies = dict()
        elif type(user['proxy']) == str:
            if "http://" in user['proxy'][0:7]:
                requestsProxies['http'] = user['proxy']
            elif "https://" == user['proxy'][0:8]:
                requestsProxies['https'] = user['proxy']
            else:
                raise Exception("代理应以http://或https://为开头")
        elif type(user['proxy']) == dict:
            requestsProxies = user['proxy']
        user['proxy'] = requestsProxies

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
            # 检查是否已经在上一轮尝试中签到
            if type(user['state']) == str:
                continue
            LL.log(1, '即将在第%d轮尝试中为[%s]签到' % (tryTimes, user['username']))

            # 用户间随机延迟
            RT.randomSleep(config['delay'])

            try:
                msg = working(user)
            except TaskError as e:
                msg = str(e)
            except Exception as e:
                msg = str(e)
                LL.log(3, traceback.format_exc(), user['username']+'签到失败'+msg)
                if maxTry != tryTimes:
                    continue

            # 消息格式化
            msg = '--%s|%d\n--%s' % (user['username'], tryTimes, msg)
            user['state'] = msg
            LL.log(1, msg)
            # 消息推送
            sm = SendMessage(user.get('sendMessage'))
            sm.send(msg, '今日校园自动签到')
            LL.log(1, sm.log_str)

    # 签到情况推送
    msg = '==签到情况==\n'
    for i in config['users']:
        msg += '[%s]\n%s\n' % (i['remarkName'], i['state'])
    LL.log(1, msg)
    sm = SendMessage(config.get('sendMessage'))
    sm.send(msg+'\n'+LL.getLog(4), '自动健康打卡')
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
