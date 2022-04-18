import hashlib
import os


class VersionInfo:
    codeVersion = "V-T3.8.2+1"
    # 代码文件列表
    codeList = ("todayLoginService.py", "actions/autoSign.py", "actions/collection.py", "actions/sleepCheck.py", "actions/workLog.py",
                "actions/sendMessage.py", "actions/teacherSign.py", "login/Utils.py", "login/casLogin.py", "login/iapLogin.py", "login/RSALogin.py", "index.py", 'liteTools.py')
    # 代码文件哈希列表
    codeStandardHashDict = {'todayLoginService.py': '3d584dc22f7823fab64ada0c7eb890c2e051d80813ec1411ecb6026dc9b8706d', 'actions/autoSign.py': '35c7cc28e43f1bb2a3a49de32d6e32a1a7a0693ca081859a7f848e6b84b5450e', 'actions/collection.py': 'a23a5ab86aaa5d55cb1d68f8f6a5014b814fd5a3f62bb0851aaac283c8232b30', 'actions/sleepCheck.py': 'cb47de63125442459ac18242fe71484f4cc03f2de76580b639132a3f27ff6aaf', 'actions/workLog.py': '935afc4ed491cddf47d76e2b75c9ffaf9d91e8d19ec156e97870a367a621e39e', 'actions/sendMessage.py': '142f01115363f3ffde183d2ca728a1337c3d95372e8a11ad00668faf5dd03e01',
                            'actions/teacherSign.py': 'e2ac1a7f162b86e3d4bac7bfcbe9be9668ea03e2dac597e6a1fb73d9aca24ab8', 'login/Utils.py': 'd5da76b333cf204515a4b6e76903fd7ddd7f7039e7fd135ba0b40475f5aa16f3', 'login/casLogin.py': '4c164cda7592382061bacfcace2168e34bfb7ae4b024a53387a72a6b8ef0f0b4', 'login/iapLogin.py': 'ed2775a15dc628b8c0c01429d7a2f84ee3fef56f0623b4118b51d733081b6b40', 'login/RSALogin.py': '9ec9bb985b95564ab00216df14ab892ce2f262e08a216538f60ca293f1a12c12', 'index.py': '85528d5058d5f13f301ed886033c449eafa2a03e545152c481d36f956c8b7533', 'liteTools.py': '720cb8de4a24f76cc2e007e1905ab32eefc9190433d3e0114faa3c1c08007a1f'}


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


def checkCodeVersion(outputCodeHash=False):
    '''检查代码文件哈希是否与预设的哈希一致'''
    codeHash = {}
    # 计算代码文件哈希
    for i in VersionInfo.codeList:
        codeHash[i] = HSF.fileHash(i, 256)
    if codeHash == VersionInfo.codeStandardHashDict:
        VersionNumber = VersionInfo.codeVersion
    else:
        VersionNumber = VersionInfo.codeVersion+'-?'
    if outputCodeHash:
        print(VersionNumber)
        print(codeHash)
    return VersionNumber


if __name__ == '__main__':
    checkCodeVersion(True)
