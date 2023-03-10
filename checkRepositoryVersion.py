import hashlib
import os
import re


class VersionInfo:
    # 代码文件哈希列表
    codeStandardHashDict = {
        "todayLoginService.py": "5c93fbdceca792f3cf7ecc621d570de218580aed3150fcc7ef80a483f78e7a02",
        "actions/autoSign.py": "3e9d0b18723e44a1a297009762a57d74c8898efa8657ddbfad0388501179087a",
        "actions/collection.py": "9509cdeb59dba47013d850ca85f16cf2df50d34aa6728b61c4afffb9eae95415",
        "actions/sleepCheck.py": "aeb190b19e18098acaec7334dad52c9e554ecc98e257decbe8e3c260bfcf20b8",
        "actions/workLog.py": "829b721adc4005fc55fc56b37f4c93baf70f0518987d566b04fba3d351c0e01a",
        "actions/sendMessage.py": "37ff6a09f646ccd3171ed0d129eada734759a9f333244ea12e8f86c3d54867c0",
        "actions/teacherSign.py": "c3e760f06c30f09f94550a4c4906796e45dc485be7c55d5018d88532063a3aa1",
        "login/Utils.py": "ad03d5691e31b3948766e988ddbacbfd5e552b074e0e6cf1ba1c56b4904713d1",
        "login/casLogin.py": "0a675a7d2bb6a49bebb709c6046a39bf0c15c90de51ca14fc508184359579cb0",
        "login/iapLogin.py": "ed2775a15dc628b8c0c01429d7a2f84ee3fef56f0623b4118b51d733081b6b40",
        "login/RSALogin.py": "9ec9bb985b95564ab00216df14ab892ce2f262e08a216538f60ca293f1a12c12",
        "index.py": "f86b8097905bd08af54c1ae954bfc0e09acca3197612f5335fa6edafae1fa942",
        "liteTools.py": "6a9c2961a9ac37b0a0d7fde5ca5863a217624370eafb21079e9f7e7c332e2da0",
        "handler.py": "cd01d8123d717d9c9aaca70f6f700f2a9d4cc50fe3a54f213e14934540eb2136",
        "userDefined.py": "42cbd0c82e59be9a6e21d8f7ae1f54f9d504d10a7cf2fd8fdda4789a353d2770",
    }
    codeVersion = "VT-unknown(where did (pyproject.toml) go?)"
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            version = re.findall(r"version ?= ?\"(.*)\"", f.read())[0]
            codeVersion = f"V-T{version}"
    except:
        pass
    # codeVersion = "内测版本(仅供仓库贡献者使用, 禁止外传)"  # 临时加的一句话


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
            raise Exception("类型错误, 初始化失败")

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
                raise Exception("%s计算哈希出错: %s" % (path, e))
        else:
            raise Exception('路径错误, 没有指向文件: "%s"')

    @staticmethod
    def strHash(str_: str, hash_type, charset="utf-8"):
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
    """检查与预设哈希列表不相符的代码文件"""
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
    """检查代码文件哈希是否与预设的哈希一致"""
    difference = checkCodeDifference()
    if len(difference) == 0:
        """未修改"""
        versionNumber = VersionInfo.codeVersion
    elif difference == ["userDefined.py"]:
        """修改用户自定义函数"""
        versionNumber = VersionInfo.codeVersion + "-u"
    else:
        """有其他未知修改"""
        versionNumber = VersionInfo.codeVersion + "-?"

    if printOutput:
        codeHash = {
            i: HSF.fileHash(i, 256) for i in VersionInfo.codeStandardHashDict.keys()
        }
        print("==========VersionNumber==========\n" + str(versionNumber))
        print("==========Difference==========\n" + "\n".join(difference))
        print("==========CodeHash==========\n" + str(codeHash))
        print("=========================")
    return versionNumber


if __name__ == "__main__":
    getCodeVersion(True)
