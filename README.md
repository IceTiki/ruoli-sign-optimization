## [ruoli-sign-optimization](https://github.com/IceTiki/ruoli-sign-optimization)

[基于若离的自动签到](https://github.com/ZimoLoveShuang/auto-submit/tree/ruoli)而写的今日校园自动签到。

## 常见问题

* 如果在日志发现HTTP 418(I'm a teapot.)，意为被怀疑为爬虫脚本。因为腾讯云函数广州节点用的人太多了，试着把函数复制到其他区域。
* 如果在模拟登录后开始抓取任务列表时HTTP 405(请求方式错误)

> Carlton大佬:
>
> ​	发生在cas登录时：
>
> ​	405是因为取辅导猫表单时候 发现没有登录态 302回你学校了
>
> ​	离谱就是，302回你学校cas服务以后他是登录的，又给你302回调回来了，302肯定是get，所以返回405

## 修改摘要

### 整体修改

- [x] Qmsg推送
- [x] 签到坐标随机偏移
- [x] 签到失败自动重试
- [x] SMTP推送
- [x] 事无巨细的日志记录

### autosign.py修改

- [x] 签到任务Title匹配
- [x] ismalposition参数本地判定
- [x] 修复了提交表单中，单项选择会提交多个选项的bug(提交返回SUCCESS但没签到成功的原因)

### collection.py修改

- [x] 支持非必填项的填写，以及不填写必填项

### workLog.py修改

- [x] 修复了关于遍历下标的bug(容易引发index out of range)

## 使用方法

### 第一步

登录腾讯云，进入腾讯云函数https://console.cloud.tencent.com/scf/list

### 第二步

选择一个**非广州的内陆节点**(比如上海、北京、成都)

![image-20210808213157826](README.assets/image-20210808213157826.png)

### 第三步

点击 **新建**

![image-20210808213307298](README.assets/image-20210808213307298.png)

### 第四步

选择自定义创建

选择本地上传文件夹

![image-20210808213511227](README.assets/image-20210808213511227.png)

然后上传文件夹

![image-20210808213748344](README.assets/image-20210808213748344.png)

### 第五步

触发器选择 **自定义创建**

触发周期选择 **自定义触发周期**

Cron表达式填```15 0,8 * * *```(意思是每天0点和8点15分触发)

最后点 **完成**

![image-20210808214224780](README.assets/image-20210808214224780.png)

### 第六步

自动跳转到函数管理，进入函数配置

点击**编辑**

将**执行超时时间**设置为100秒

最后**保存**

![image-20210808214408055](README.assets/image-20210808214408055.png)

![image-20210808214524063](README.assets/image-20210808214524063.png)

![image-20210808214601868](README.assets/image-20210808214601868.png)

### 第七步

进入 **函数代码**

进入**config.yml**

将依照config.yml里的注释，**将自己的配置信息填入config.yml**

![image-20210808214956680](README.assets/image-20210808214956680.png)

### 第八步

点击 **终端-新终端**

在终端中**输入**```pip3 install -r ./src/requirements.txt -t ./src/ -i https://mirrors.aliyun.com/pypi/simple```

**按回车**，然后**等待执行完毕**

执行完毕后，点击**部署**，并**等待部署完毕**

**大 功 告 成**，第二天看看自动签到是否成功吧。(如果没成功，去询问别人为什么失败的时候一定要截图日志最后那一页)

![image-20210808214914963](README.assets/image-20210808214914963.png)

![image-20210808215316573](README.assets/image-20210808215316573.png)

![image-20210808215517157](README.assets/image-20210808215517157.png)

