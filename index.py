# coding=utf-8
# ====================开始导入模块====================
# 导入标准库
import imp
import os
import sys
import codecs
import traceback
import random

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
if os.name == "posix":
    # 如果是linux系统, 增加TZ环境变量
    os.environ['TZ'] = "Asia/Shanghai"
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
    from liteTools import TaskError, RT, DT, LL, NT, MT, ST, TT, HSF, ProxyGet, SignTaskStatus, UserMsg, GlobalData
    from login.Utils import Utils
    from actions.teacherSign import teacherSign
    from actions.sendMessage import SendMessage
    from actions.workLog import workLog
    from actions.sleepCheck import sleepCheck
    from actions.collection import Collection
    from actions.autoSign import AutoSign
    from todayLoginService import TodayLoginService
# ====================完成导入模块====================


def working(user: dict, userSession, userHost: str):
    '''任务执行入口函数'''
    LL.log(1, '登录完成')
    # 登陆成功，通过type判断当前属于 信息收集、签到、查寝
    # 信息收集
    if user['type'] == 0:
        # 以下代码是信息收集的代码
        LL.log(1, '即将开始信息收集填报')
        collection = Collection(user, userSession, userHost)
        collection.queryForm()
        collection.fillForm()
        msg = collection.submitForm()
        return msg
    elif user['type'] == 1:
        # 以下代码是签到的代码
        LL.log(1, '即将开始签到')
        sign = AutoSign(user, userSession, userHost)
        sign.getUnSignTask()
        sign.getDetailTask()
        sign.fillForm()
        msg = sign.submitForm()
        return msg
    elif user['type'] == 2:
        # 以下代码是查寝的代码
        LL.log(1, '即将开始查寝填报')
        check = sleepCheck(user, userSession, userHost)
        check.getUnSignedTasks()
        check.getDetailTask()
        check.fillForm()
        msg = check.submitForm()
        return msg
    elif user['type'] == 3:
        # 以下代码是工作日志的代码
        raise TaskError('工作日志模块已失效')
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
        check = teacherSign(user, userSession, userHost)
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
    GlobalData.initInMainHead()
    config = GlobalData.config
    maxTry = config['maxTry']

    # 开始签到
    # 自动重试
    users = config['users']
    userSessions = {}
    for tryTimes in range(1, maxTry+1):
        LL.log(1, '正在进行第%d轮尝试' % tryTimes)
        userSessions.clear()
        # 遍历用户
        for user in users:
            # 检查是否完成该任务
            if not user['taskStatus'].codeHead() == 0:
                continue
            LL.log(1, '即将在第%d轮尝试中为[%s]签到' % (tryTimes, user['username']))

            # 用户间随机延迟
            RT.randomSleep(config['delay'])

            # 执行签到
            try:
                # 准备登录
                LL.log(1, '准备登录')
                userId = user['userHashId']
                if userSessions.get(userId):
                    userSession = userSessions[userId]['session']
                    userHost = userSessions[userId]['host']
                else:
                    today = TodayLoginService(user)
                    today.login()
                    userSession = today.session
                    userHost = today.host
                userSessions[userId] = {
                    'session': userSession, 'host': userHost}
                # 开始执行任务
                msg = working(user, userSession, userHost)
            except TaskError as e:
                user['taskStatus'].code = e.code
                msg = str(e)
            except Exception as e:
                user['taskStatus'].code = 1
                msg = f"[{e}]\n{traceback.format_exc()}"
                LL.log(3, ST.notionStr(msg), user['username']+'签到失败'+msg)
                if maxTry != tryTimes:
                    continue
            # 登录状态内存释放: 如果同用户还有没有待执行的任务，则删除session
            for i in users:
                if i['taskStatus'].codeHead() == 0 and i['userHashId'] == userId:
                    break
            else:
                userSessions.pop(userId, None)
            # 消息格式化
            msg = f"--{user['username']}|{tryTimes}\n--{msg}"
            user['taskStatus'].msg = msg
            LL.log(1, msg)
            # 消息推送
            sm = SendMessage(user.get('sendMessage'))
            sm.send(f"『[{LL.prefix}]用户签到情况\n{msg}』",
                    f"用户签到情况|{user['taskStatus'].liteMsgEn()}")
            LL.log(1, f"『{user['username']}』用户推送情况", sm.log_str)

    # 签到情况推送
    umsg = UserMsg(users)
    LL.log(1, umsg.msg_g1)
    sm = SendMessage(config.get('sendMessage'))
    sm.send(msg=umsg.msg_g1+'\n'+LL.getLog(4), title=umsg.title_g1, attachments=[(LL.getLog().encode(encoding='utf-8'),
                                                                                  TT.formatStartTime("LOG#t=%Y-%m-%d--%H-%M-%S##.txt"))])
    LL.log(1, '全局推送情况', sm.log_str)


def handler(event, context):
    '''阿里云的入口函数'''
    GlobalData.entrance = "handler"
    GlobalData.launchData["event"] = event
    GlobalData.launchData["context"] = context
    main()


def main_handler(event, context):
    '''腾讯云的入口函数'''
    GlobalData.entrance = "main_handler"
    GlobalData.launchData["event"] = event
    GlobalData.launchData["context"] = context
    main()
    return 'ok'


if __name__ == '__main__':
    '''本地执行入口位置'''
    try:
        GlobalData.entrance = "__main__"
        main()
    finally:
        LL.saveLog(GlobalData.config.get('logDir'))  # 生成日志文件
