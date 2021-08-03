## [基于若离的自动签到](https://github.com/ZimoLoveShuang/auto-submit/tree/ruoli)

[仓库地址](https://github.com/IceTiki/ruoli-sign-optimization)

> 腾讯云函数依赖安装
>
> ```bash
> cd ./src
> pip3 install -r requirements.txt -t ./ -i https://mirrors.aliyun.com/pypi/simple
> ```

## 整体修改

- [x] Qmsg简单推送
- [x] 签到坐标随机偏移
- [x] 签到失败自动重试

## autosign.py修改

- [x] 签到任务Title匹配
- [x] ismalposition参数本地判定
- [x] 修复了提交表单中，单项选择会提交多个选项的bug(提交返回SUCCESS但没签到成功的原因)

## collection.py修改

- [x] 支持非必填项的填写
