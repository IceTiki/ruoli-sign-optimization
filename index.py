# coding=utf-8
# ====================开始导入模块====================
# 导入标准库
import imp
import os
import sys
import codecs
import argparse
import textwrap

# ==========检查python版本==========
if not (sys.version_info[0] == 3 and sys.version_info[1] >= 6):
    raise Exception(
        "!!!!!!!!!!!!!!Python版本错误!!!!!!!!!!!!!!\n请使用python3.6及以上版本，而不是[python %s]" % sys.version)
# ==========环境变量初始化==========
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
# ==========检查第三方模块==========
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
# ==========检查代码完整性==========
try:
    for i in ("todayLoginService", "actions/autoSign", "actions/collection", "actions/sleepCheck", "actions/workLog",
              "actions/sendMessage", "actions/teacherSign", "login/Utils", "login/casLogin", "login/iapLogin",
              "login/RSALogin", "liteTools", "handler", "checkRepositoryVersion"):
        i = os.path.normpath(i)  # 路径适配系统
        imp.find_module(i)
except ImportError as e:
    raise ImportError(f"""!!!!!!!!!!!!!!脚本代码文件缺失!!!!!!!!!!!!!!
请尝试重新下载代码
错误信息: [{e}]""")
# 导入脚本的其他部分(不使用结构时, 格式化代码会将import挪至最上)
if True:
    from handler import MainHandler
    from liteTools import LL
    import checkRepositoryVersion
# 检查代码文件是否被修改
diff = checkRepositoryVersion.checkCodeDifference()
if diff:
    LL.log(1, "以下代码文件相比发布版本有变动: \n" + "\n".join(diff))
else:
    LL.log(1, "一切代码文件保持初始状态")
# ====================完成导入模块====================


# ====================初始化本模块对象====================
def getCommandArgs():
    """
    使用命令传入参数时, 解析传入参数
    :returns args:(dict)字典
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-c", "--configfile",
                        required=False, help="配置文件路径（可选）")
    parser.add_argument("-e", "--environment", required=False, help=textwrap.dedent("""\
针对特殊运行环境使用，目前可选值为：
local：本地环境，如需使用外部配置文件需要加入该参数
qinglong: 此参数代表环境为使用青龙面板，加入此参数将不会输出日志到文件，日志请从青龙面板的“日志管理”页面查看"""))
    args = vars(parser.parse_args())
    return args
# ====================初始化本模块对象====================


# ====================开始执行任务====================
def handler(event, context):
    '''阿里云的入口函数'''
    MainHandler("handler", event, context).execute()


def main_handler(event, context):
    '''腾讯云的入口函数'''
    MainHandler("main_handler", event, context).execute()
    return 'ok'


if __name__ == '__main__':
    '''本地执行入口位置'''
    MainHandler("__main__", {"args": getCommandArgs()}, {}).execute()
