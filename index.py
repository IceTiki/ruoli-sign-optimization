import yaml
import time
import random
import math
from todayLoginService import TodayLoginService
from actions.autoSign import AutoSign
from actions.collection import Collection
from actions.workLog import workLog
from actions.sleepCheck import sleepCheck
import actions.sendMessage as sendMessage


def getYmlConfig(yaml_file='config.yml'):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


def log(*args):
    ExecutingTime = time.time()-startExecutingTime
    if args:
        string = '|||log|||%0.3fs|||\n' % ExecutingTime
        for item in args:
            if type(item) == dict or type(item) == list:
                string += yaml.dump(item, allow_unicode=True)+'\n'
            else:
                string += str(item)+'\n'
        print(string)


# 经纬度随机偏移
def locationOffset(self, lon, lat, offset=50):
    '''
    lon——经度
    lat——纬度
    offset——偏移范围(单位m)
    '''
    # 弧度=弧长/半径，角度=弧长*180°/π，某地经度所对应的圆半径=cos(|维度|)*地球半径
    lonOffset = offset/(6371393*math.cos(abs(lat)))*(180/math.pi)
    latOffset = offset/6371393*(180/math.pi)
    # 生成随机偏移
    randomLonOffset = random.uniform(lonOffset, -lonOffset)
    randomLatOffset = random.uniform(latOffset, -latOffset)
    # 将偏移应用到原有坐标上
    # 南北极/对向子午线附近的坐标可能会超出范围(经度-180~180，维度-90~90)，对此进行了调整
    offset_lon = ((lon+randomLonOffset)+180) % 360-180
    offset_lat = (((lat+randomLatOffset)+90) % 180-90) * \
        (-1)**(int(((lat+randomLatOffset)+90)/180))
    return (offset_lon, offset_lat)


def main():
    global startExecutingTime
    startExecutingTime = time.time()
    workingStatus = {} # 储存各用户自动签到情况
    workingStatus.clear
    config = getYmlConfig()
    for user in config['users']:
        username = user['user']['username']
        # 用户签到状态初始(status)为-1，代表还未尝试签到，签到成功后会被working函数的返回信息覆盖。如果已尝试签到，则跳过该用户。
        # 尝试签到次数(times)初始为1，每次重试+1
        if username not in workingStatus:# 第一次尝试签到，初始化状态信息
            workingStatus[username] = {'status':-1,'times':1}
        else:
            if not workingStatus[username]['status'] == -1:# 如果status已经被working函数返回的msg覆盖，则跳过
                continue
            workingStatus[username]['times'] += 1
            if workingStatus[username]['times'] > config['maxRetryTimes']:# 如果times超过最大重试次数，则跳过
                continue
        log('正在处理%s|||第%d次尝试'%(username,workingStatus[username]['times']))
        # 对用户配置中的经纬度进行随机偏移
        if workingStatus[username]['times'] == 1:
            user['user']['lon'], user['user']['lat'] = locationOffset(
                user['user']['lon'], user['user']['lat'], config['locationOffsetRange'])
        # 实例化消息推送
        sm = sendMessage.SendMessage(user['user']['sendMessage'])
        # 开始自动信息收集/签到/查寝
        try:
            msg = working(user)
            log(msg)
            workingStatus[username]['status'] = msg
            sm.send(msg, '[maybe]今日校园通知')
        except Exception as e:
            config['users'].append(user)# 加入到user列表中重试
            msg = str(e)
            log(msg)
            sm.send(msg, '[error]今日校园通知')
    log(workingStatus)
    # 函数整体执行情况推送
    sws=sendMessage.SendMessage(config['sendWorkingStatus'])
    sws.send(yaml.dump(workingStatus, allow_unicode=True), '[status]今日校园通知')


def working(user):
    today = TodayLoginService(user['user'])
    today.login()
    # 登陆成功，通过type判断当前属于 信息收集、签到、查寝
    # 信息收集
    if user['user']['type'] == 0:
        # 以下代码是信息收集的代码
        collection = Collection(today, user['user'])
        collection.queryForm()
        collection.fillForm()
        msg = collection.submitForm()
        return msg
    elif user['user']['type'] == 1:
        # 以下代码是签到的代码
        sign = AutoSign(today, user['user'])
        msg = sign.getUnSignTask()
        if type(msg)==str:
            return msg
        sign.getDetailTask()
        sign.fillForm()
        msg = sign.submitForm()
        return msg
    elif user['user']['type'] == 2:
        # 以下代码是查寝的代码
        check = sleepCheck(today, user['user'])
        check.getUnSignedTasks()
        check.getDetailTask()
        check.fillForm()
        msg = check.submitForm()
        return msg
    elif user['user']['type'] == 3:
        # 以下代码是工作日志的代码
        work = workLog(today, user['user'])
        work.checkHasLog()
        work.getFormsByWids()
        work.fillForms()
        msg = work.submitForms()
        return msg
# 阿里云的入口函数


def handler(event, context):
    main()


# 腾讯云的入口函数
def main_handler(event, context):
    main()
    return 'ok'


if __name__ == '__main__':
    main()
