import argparse

# 初始化参数
class cpdaily_args:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=False, help="配置文件路径（可选）")
    parser.add_argument("--qinglong", required=False, action="store_true", help="此参数代表环境为使用青龙面板，"
                                                                                "加入此参数将不会输出日志到文件，"
                                                                                "日志请从青龙面板的“日志管理”页面查看")
    args = parser.parse_args()

# print(cpdaily_args.args)