import hashlib
import os


class VersionInfo:
    codeVersion = "V-T3.10.0a"
    # 代码文件哈希列表
    codeStandardHashDict = {'todayLoginService.py': '9ea1028525927b881f3c69fd95007e348074b34493c1537b94c8ef007380fac1', 'actions/autoSign.py': '7fd80ef6fbbc102a761e1d67bb459b42f33b151b47f939083d1ef4c9549702ac', 'actions/collection.py': 'd0117675819a45dd4e2254b3648eecb8ea1f058c244526f04bb81ae6ad874f81', 'actions/sleepCheck.py': 'e239ae660aad52de05f0bea7342399e39ab2a8b8e0ea40053330f9b5b860a63e', 'actions/workLog.py': '935afc4ed491cddf47d76e2b75c9ffaf9d91e8d19ec156e97870a367a621e39e', 'actions/sendMessage.py': 'bc33d0714513200c9b073cbd0e23b46fc033255d7d55860e705a847523493646', 'actions/teacherSign.py': '6f7e76556a41be709d639e078c3dee2527c15cc860181d33d030085b60f85f95',
                            'login/Utils.py': 'd5da76b333cf204515a4b6e76903fd7ddd7f7039e7fd135ba0b40475f5aa16f3', 'login/casLogin.py': '4c164cda7592382061bacfcace2168e34bfb7ae4b024a53387a72a6b8ef0f0b4', 'login/iapLogin.py': 'ed2775a15dc628b8c0c01429d7a2f84ee3fef56f0623b4118b51d733081b6b40', 'login/RSALogin.py': '9ec9bb985b95564ab00216df14ab892ce2f262e08a216538f60ca293f1a12c12', 'index.py': '898835f8582604c785a3b63f6b2e9a1d6c97ebf56da233992581d17357806051', 'liteTools.py': 'b4f6d8ec2a917426130161f9327bedf4034039b65751c7169f203632ea757ed5', 'handler.py': 'af8b97a929e68ebb9dfd11d9d32433d40fb891f657f7a6e8d9b46ba245ad9e11', 'userDefined.py': 'e9b1f8e3c8a31fbeed9f67ee8860dfb86b5ae1b156dc514b2062a3dabd2fe893'}


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
