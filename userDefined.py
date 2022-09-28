class ExecuteEvent:
    def __init__(self, event, context):
        self.event = event
        self.context = context
        self.code = event["code"]

    def execute(self):
        '''执行事件'''
        if self.code == 300:
            return self.handleCapcha()
        else:
            return "什么都没有干"

    def handleCapcha(self):
        '''验证码识别'''
        raise Exception("图片验证码识别错误: \n验证码问题尚未解决, 请手签(就是用今日校园app自己手动签到的意思)")
        # from liteTools import reqSession, LL
        # sess = reqSession()
        # url = TODOTODOTODOTODO
        # LL.log(1, "即将进行验证码识别")
        # res = sess.post(url, json=self.context["capcode"])
        # res = res.json()
        # LL.log(1, "验证码识别返回值", res)
        # if res["code"] != 200 or res["data"]["unKnownCode"]:
        #     '''识别出错'''
        #     raise TODOTODOTODOTODO
        # return res["data"]["succCode"]

        # import private.handleCap as hc
        # capCode = self.context["capcode"]
        # return hc.getAnswer(capCode)


def index(event, context):
    event = ExecuteEvent(event, context)
    return event.execute()
