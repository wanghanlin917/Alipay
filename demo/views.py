import requests
from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.shortcuts import redirect
from django.http import JsonResponse
import uuid
import hashlib
from utils.alipay import AliPay
from django.conf import settings
from urllib.parse import parse_qs


def index(request):
    return render(request, 'index.html')


def pay(request):
    def md5(string):
        """ MD5加密 """
        hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
        hash_object.update(string.encode('utf-8'))
        return hash_object.hexdigest()

    def uid(string):
        data = "{}-{}".format(str(uuid.uuid4()), string)
        return md5(data)

    ali_pay = AliPay(
        appid=settings.ALI_APPID,  # "2016102400754054"
        app_notify_url=settings.ALI_NOTIFY_URL,  # 通知URL：POST
        return_url=settings.ALI_RETURN_URL,  # 支付完成之后，跳转到这个地址: GET
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    query_params = ali_pay.direct_pay(
        subject="trace rpayment",  # 商品简单描述
        out_trade_no=uid('qwe'),  # 商户订单号
        total_amount=100
    )

    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)  # 跳转到支付宝，出现扫码支付


def pay_notify(request):
    """ 支付成功之后触发的URL """
    # app_private_key_path=settings.ALI_PRI_KEY_PATH,
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,
        return_url=settings.ALI_RETURN_URL,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    if request.method == 'GET':
        # 只做跳转，判断是否支付成功了，不做订单的状态更新。
        # 支付吧会讲订单号返回：获取订单ID，然后根据订单ID做状态更新 + 认证。
        # 支付宝公钥对支付给我返回的数据request.GET 进行检查，通过则表示这是支付宝返还的接口。
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = ali_pay.verify(params, sign)
        if status:
            return HttpResponse('支付完成')
        return HttpResponse('支付失败')
    else:
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            out_trade_no = post_dict['out_trade_no']
            print("支付成功", out_trade_no)
            return HttpResponse('success')

        return HttpResponse('error')


def withdraw(request):
    def md5(string):
        """ MD5加密 """
        hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
        hash_object.update(string.encode('utf-8'))
        return hash_object.hexdigest()

    def uid(string):
        data = "{}-{}".format(str(uuid.uuid4()), string)
        return md5(data)

    ali_pay = AliPay(
        appid=settings.ALI_APPID,  # "2016102400754054"
        app_notify_url=settings.ALI_NOTIFY_URL,  # 通知URL：POST
        return_url=settings.ALI_RETURN_URL,  # 支付完成之后，跳转到这个地址: GET
        app_private_key_path=settings.ALI_APP_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = ali_pay.transfer(
        out_biz_no=uid('qwe'),  # 订单号
        trans_amount=1
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)

    res = requests.get(pay_url)
    data_dict = res.json()
    # {"alipay_fund_trans_uni_transfer_response":{"code":"10000","msg":"Success","order_id":"20221204110070000006260000848244","out_biz_no":"a3d634f4f15f1a289df250f588ccf4a9","pay_fund_order_id":"20221204110070001506260000849678","status":"SUCCESS"},"sign":"nNxCEnShXYwfaW+IIbu2gJhZ0Tfb0DcNaB5XUd1SU0MsDgeaFwQJlq8/0V7rrNi256AFzG/Fc4eTOuXKuByKDI2ozHZFmCfOwf7W/3N/76nW8MbesOlcweProFAZo8O1wchMeuicfs7+8tlPBjWvHkcmCMhPRpobckhWSzyR7GLG84/3zd+n4n1sA+16LwBIuzZYMl9CNrbgIOHWk3rqlGRRGQ+mJSsoWYbwtzMLkfk04QSUFGjwr61PXkr9hAvPZf6jdjglN6RC4n0iZD65qP8YE4RkcC1ecwW3KPTikztXsD0ZC0lIZAJ1e3odSicXj3/T2FcWgaFaZvq7KUESiw=="}
    return JsonResponse(data_dict)
