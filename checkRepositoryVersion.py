import hashlib
import os


class VersionInfo:
    codeVersion = "V-T3.8.8b"
    # 代码文件列表
    codeList = ("todayLoginService.py", "actions/autoSign.py", "actions/collection.py", "actions/sleepCheck.py", "actions/workLog.py",
                "actions/sendMessage.py", "actions/teacherSign.py", "login/Utils.py", "login/casLogin.py", "login/iapLogin.py", "login/RSALogin.py", "index.py", 'liteTools.py')
    # 代码文件哈希列表
    codeStandardHashDict = {'todayLoginService.py': '39acd0282ce498b85d33423ac9971b061fa1e5b9b567b33eafa2af7ee0bc6800', 'actions/autoSign.py': 'd4c8d466b73ca17871d2076b73ceb1c019f19066b0fc203e209461b4c8fa4f15', 'actions/collection.py': '1a19677fcd8fa55834b1b7e74ae7adfc6211be3e3dfdff05be20ec028a409f44', 'actions/sleepCheck.py': '658a314bb26f756285086605a98aa219999afe98db1249c5e1c490b147cec52a', 'actions/workLog.py': '935afc4ed491cddf47d76e2b75c9ffaf9d91e8d19ec156e97870a367a621e39e', 'actions/sendMessage.py': '4675b073cbdcc05ef8235f290ab74e02dfe0517e07ac653f23888a8e9b353f71',
                            'actions/teacherSign.py': '6f7e76556a41be709d639e078c3dee2527c15cc860181d33d030085b60f85f95', 'login/Utils.py': 'd5da76b333cf204515a4b6e76903fd7ddd7f7039e7fd135ba0b40475f5aa16f3', 'login/casLogin.py': '4c164cda7592382061bacfcace2168e34bfb7ae4b024a53387a72a6b8ef0f0b4', 'login/iapLogin.py': 'ed2775a15dc628b8c0c01429d7a2f84ee3fef56f0623b4118b51d733081b6b40', 'login/RSALogin.py': '9ec9bb985b95564ab00216df14ab892ce2f262e08a216538f60ca293f1a12c12', 'index.py': 'a9b5d3ad32efabf48a61c9b3386e5a649f82ce0edc04051fdcd89317190b7a27', 'liteTools.py': '39ec8d8893b86c167e94de477f98c4a2d996388401a709db6645eb19b522a4ef'}


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
