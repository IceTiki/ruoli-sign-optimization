def index(event, context):
    event = ExecuteEvent(event, context)
    return event.execute()


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
        import os
        mode = 1 if os.path.isdir("_userdefined_capt") else 0
        capCode = self.context["capcode"]

        # ===============在线识别===============
        if mode == 0:
            from liteTools import reqSession, LL, DT, HSF, ST
            # 检测解谜是否完成
            apple = DT.loadYml("config.yml").get("apple", "")
            if not apple:
                raise Exception("""图片验证码识别错误: 
无法进行处理图形验证码, 请手签(就是用今日校园app自己手动签到的意思)
错误信息: 
config.yml: where's my apple? """)
            else:
                # [对想逃课的人说的话: sha256是不可逆的(何况还加了盐)]
                hashApple = HSF.strHash(apple+'salt_apple_is_nice', 256)
                LL.log(
                    1, f"苹果哈希「{hashApple}」")
                rightAppleHash = ("350fb0c1f9255ddd0a3a6cbfdb88a1f112d1d55618d3ed8864954186a7b0eb83",  # 新苹果
                                  "cfeeeeb1d8f935a8ea7e4c0ab56b101dbdf9e8ce8cd3853a293a37e68b573ae6")  # 旧苹果
                if hashApple not in rightAppleHash:
                    LL.log(2, ST.notionStr("""疑似错误的苹果:
请确定, 当你找到apple时, 看到了「恭喜你找到了apple」这句话"""))
            # 开始验证码识别
            LL.log(1, "即将进行验证码识别")
            res = reqSession().post(apple, json=capCode)
            res = res.json()
            LL.log(1, "验证码识别返回值", res)
            # 处理返回结果
            if res["code"] not in (200, 400):
                '''识别出错'''
                raise Exception(f"使用验证码识别API识别出错『{res}』")
            return res["data"]["succCode"]
        # ===============本地识别===============
        elif mode == 1:
            from _userdefined_capt import captchaHandler
            return captchaHandler(capCode)["right"]
        # ===============报错===============
        else:
            '''报错'''
            raise Exception(
                "图片验证码识别错误: \n验证码问题未解决, 请手签(就是用今日校园app自己手动签到的意思)\n错误信息")
