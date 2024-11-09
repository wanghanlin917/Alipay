from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from urllib.parse import quote_plus
from urllib.parse import urlparse, parse_qs
from base64 import decodebytes, encodebytes
import json


class AliPay(object):
    """
    支付宝支付接口(PC端支付接口)
    """

    def __init__(self, appid, app_notify_url, app_private_key_path, alipay_public_key_path, return_url):
        self.appid = appid
        self.app_notify_url = app_notify_url
        self.app_private_key_path = app_private_key_path
        self.app_private_key = None
        self.return_url = return_url

        with open(self.app_private_key_path) as fp:
            self.app_private_key = RSA.importKey(fp.read())

        self.alipay_public_key_path = alipay_public_key_path
        with open(self.alipay_public_key_path) as fp:
            self.alipay_public_key = RSA.importKey(fp.read())

    def direct_pay(self, subject, out_trade_no, total_amount):
        data = {
            "app_id": self.appid,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps({
                "subject": subject,
                "out_trade_no": out_trade_no,
                "total_amount": total_amount,
                "product_code": "FAST_INSTANT_TRADE_PAY",
            }, separators=(',', ':'))
        }
        if self.return_url:
            data["notify_url"] = self.app_notify_url
            data["return_url"] = self.return_url

        return self.sign_data(data)

    def transfer(self, out_biz_no, trans_amount):
        data = {
            "app_id": self.appid,
            "method": "alipay.fund.trans.uni.transfer",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps({
                "out_biz_no": out_biz_no,
                "trans_amount": trans_amount,
                "product_code": "TRANS_ACCOUNT_NO_PWD",
                "biz_scene": "DIRECT_TRANSFER",
                "order_title": "武沛齐的提现",
                "remark": "备注信息",
                "payee_info": json.dumps({
                    "identity_type": "ALIPAY_LOGON_ID",
                    "identity": "nbjsag5718@sandbox.com",
                    "name": "沙箱环境"
                }, separators=(',', ':'))
            }, separators=(',', ':'))
        }
        if self.return_url:
            data["notify_url"] = self.app_notify_url
            data["return_url"] = self.return_url
        return self.sign_data(data)

    def sign_data(self, data):

        data.pop("sign", None)
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)

        sign = self.sign(unsigned_string.encode("utf-8"))

        # ordered_items = self.ordered_data(data)
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)

        # 获得最终的订单信息字符串
        signed_string = quoted_string + "&sign=" + quote_plus(sign)
        print("signed_string", signed_string)
        return signed_string

    def ordered_data(self, data):
        complex_keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                complex_keys.append(key)

        # 将字典类型的数据dump出来
        for key in complex_keys:
            data[key] = json.dumps(data[key], separators=(',', ':'))

        return sorted([(k, v) for k, v in data.items()])

    def sign(self, unsigned_string):
        # 开始计算签名
        key = self.app_private_key
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(SHA256.new(unsigned_string))
        # base64 编码，转换为unicode表示并移除回车
        sign = encodebytes(signature).decode("utf8").replace("\n", "")
        return sign

    def _verify(self, raw_content, signature):
        # 开始计算签名
        print("signature", signature)
        key = self.alipay_public_key
        signer = PKCS1_v1_5.new(key)
        print("signer", signer)
        digest = SHA256.new()
        digest.update(raw_content.encode("utf8"))
        if signer.verify(digest, decodebytes(signature.encode("utf8"))):
            return True
        return False

    def verify(self, data, signature):
        if "sign_type" in data:
            sign_type = data.pop("sign_type")
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        return self._verify(message, signature)
