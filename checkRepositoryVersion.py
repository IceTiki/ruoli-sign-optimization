import hashlib
import os


class _VersionInfo:
    # 代码文件哈希列表
    codeStandardHashDict = {'todayLoginService.py': '84948a1a3fd1a0b69d780a7c1feb508075fafa55a3f1a30ad09cbab11caf5a71', 'actions/autoSign.py': '423bed733db6bc6f119b7ffef7fe313f002fed2fd2172c3e4eabe6601b94f975', 'actions/collection.py': '2177a14a75026fa454ab1a328e922901c2588dde2f7f803dc2955d3009eec09c', 'actions/sleepCheck.py': '59b5e28894a3ad3fcc160e3198d0b63cd9a1842f59b6df3ebec22d6d5bac12d8', 'actions/workLog.py': '935afc4ed491cddf47d76e2b75c9ffaf9d91e8d19ec156e97870a367a621e39e', 'actions/sendMessage.py': 'bc33d0714513200c9b073cbd0e23b46fc033255d7d55860e705a847523493646', 'actions/teacherSign.py': 'b40f756c049d537290ba864c9909fe92a3918ff1584e2d4d47cbd5236b3705d1',
                            'login/Utils.py': 'd5da76b333cf204515a4b6e76903fd7ddd7f7039e7fd135ba0b40475f5aa16f3', 'login/casLogin.py': '4c164cda7592382061bacfcace2168e34bfb7ae4b024a53387a72a6b8ef0f0b4', 'login/iapLogin.py': 'ed2775a15dc628b8c0c01429d7a2f84ee3fef56f0623b4118b51d733081b6b40', 'login/RSALogin.py': '9ec9bb985b95564ab00216df14ab892ce2f262e08a216538f60ca293f1a12c12', 'index.py': '54ee7bddb32de87684a7f3d70ef316c7c2171e0a5e322fdfbdfc20327da63747', 'liteTools.py': 'b4f6d8ec2a917426130161f9327bedf4034039b65751c7169f203632ea757ed5', 'handler.py': '920ad81176235b432f1a0d53146d4b1cea726925a74622fd6e5ed98a64075ab9', 'userDefined.py': 'e9b1f8e3c8a31fbeed9f67ee8860dfb86b5ae1b156dc514b2062a3dabd2fe893'}
    def __init__(self):
        with open("pyproject.toml",'r',encoding='utf-8') as f:
            for item_ in f:
                if "version" in item_:
                    _,version = item_.split(" = ")
                    version = version.replace('"',"").replace("\n","")
                    self.codeVersion = f"V-T{version}c"
                    break
VersionInfo = _VersionInfo()


class HSF:
    """Hashing String And File"""
    @staticmethod
    def geneHashObj(hash_type):
        if hash_type == 1:
            return hashlib.sha1()
        elif hash_type == 224:
            return hashlib.sha224()
        elif hash_type == 256:
            return hashlib.sha256()
        elif hash_type == 384:
            return hashlib.sha384()
        elif hash_type == 512:
            return hashlib.sha512()
        elif hash_type == 5:
            return hashlib.md5()
        elif hash_type == 3.224:
            return hashlib.sha3_224()
        elif hash_type == 3.256:
            return hashlib.sha3_256()
        elif hash_type == 3.384:
            return hashlib.sha3_384()
        elif hash_type == 3.512:
            return hashlib.sha3_512()
        else:
            raise Exception('类型错误, 初始化失败')

    @staticmethod
    def fileHash(path, hash_type):
        """计算文件哈希
        :param path: 文件路径
        :param hash_type: 哈希算法类型
            1       sha-1
            224     sha-224
            256      sha-256
            384     sha-384
            512     sha-512
            5       md5
            3.256   sha3-256
            3.384   sha3-384
            3.512   sha3-512
        """
        hashObj = HSF.geneHashObj(hash_type)
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    for byte_block in iter(lambda: f.read(1048576), b""):
                        hashObj.update(byte_block)
                    return hashObj.hexdigest()
            except Exception as e:
                raise Exception('%s计算哈希出错: %s' % (path, e))
        else:
            raise Exception('路径错误, 没有指向文件: "%s"')

    @staticmethod
    def strHash(str_: str, hash_type, charset='utf-8'):
        """计算字符串哈希
        :param str_: 字符串
        :param hash_type: 哈希算法类型
        :param charset: 字符编码类型
            1       sha-1
            224     sha-224
            256      sha-256
            384     sha-384
            512     sha-512
            5       md5
            3.256   sha3-256
            3.384   sha3-384
            3.512   sha3-512
        """
        hashObj = HSF.geneHashObj(hash_type)
        bstr = str_.encode(charset)
        hashObj.update(bstr)
        return hashObj.hexdigest()


def checkCodeDifference():
    '''检查与预设哈希列表不相符的代码文件'''
    difference = []
    for k, v in VersionInfo.codeStandardHashDict.items():
        try:
            sha = HSF.fileHash(k, 256)
        except Exception as e:
            sha = e
        if sha != v:
            difference.append(k)
    return difference


def getCodeVersion(printOutput=False):
    '''检查代码文件哈希是否与预设的哈希一致'''
    difference = checkCodeDifference()
    if len(difference) == 0:
        '''未修改'''
        versionNumber = VersionInfo.codeVersion
    elif difference == ["userDefined.py"]:
        '''修改用户自定义函数'''
        versionNumber = VersionInfo.codeVersion+'-u'
    else:
        '''有其他未知修改'''
        versionNumber = VersionInfo.codeVersion+'-?'

    if printOutput:
        codeHash = {i: HSF.fileHash(i, 256)
                    for i in VersionInfo.codeStandardHashDict.keys()}
        print("==========VersionNumber==========\n" + str(versionNumber))
        print("==========Difference==========\n" + "\n".join(difference))
        print("==========CodeHash==========\n" + str(codeHash))
        print("=========================")
    return versionNumber


if __name__ == '__main__':
    getCodeVersion(True)
