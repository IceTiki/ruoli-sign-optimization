import yaml
import time
import random
from todayLoginService import TodayLoginService
from actions.autoSign import AutoSign
from actions.collection import Collection
from actions.workLog import workLog
from actions.sleepCheck import sleepCheck
from actions.rlMessage import RlMessage


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
            if type(item) == dict:
                string += yaml.dump(item, allow_unicode=True)
            else:
                string += str(item)
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
    config = getYmlConfig()
    for user in config['users']:
        # 对用户配置中的经纬度进行随机偏移
        user['user']['lon'], user['user']['lat'] = locationOffset(
            user['user']['lon'], user['user']['lat'], config['locationOffsetRange'])
        rl = RlMessage(user['user']['email'], config['emailApiUrl'])
        if config['debug']:
            msg = working(user)
        else:
            try:
                msg = working(user)
            except Exception as e:
                msg = str(e)
                print(msg)
                msg = rl.sendMail('error', msg)
        print(msg)
        msg = rl.sendMail('maybe', msg)


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
        sign.getUnSignTask()
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
