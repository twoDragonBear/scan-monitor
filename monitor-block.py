import os
import json
import time
import datetime

import requests
from loguru import logger

from FuncData import FuncData
from perpar_data import (oxdata, apikey_BSC, apikey_ETH, apikey_FTM, apikey_ARBITRUM, apikey_OPTIMISM,
                         accessKeyId, apikey_AVAX, apikey_MATIC, phone_number)

funcdata = FuncData()

class Exercises:
    '''基于各大scan的api开发的监控地址预警系统'''

    def __init__(self):
        self.BASE_URL_BSC = "https://api.bscscan.com/api"
        self.BASE_URL_ETH = "https://api.etherscan.com/api"
        self.BASE_URL_FTM = "https://api.ftmscan.com/api"
        self.BASE_URL_MATIC = "https://api.polygonscan.com/api"
        self.BASE_URL_AVAX = "https://api.snowtrace.io/api"
        self.BASE_URL_ARBITRUM = "https://api.arbiscan.io/api"
        self.BASE_URL_OPTIMISM = "https://api-optimistic.etherscan.io/api"
        self.apikey_FTM = apikey_FTM
        self.apikey_MATIC = apikey_MATIC
        self.wei = 1000000000000000000
        self.apikey_BSC = apikey_BSC
        self.apikey_ETH = apikey_ETH
        self.apikey_AVAX = apikey_AVAX
        self.apikey_ARBITRUM = apikey_ARBITRUM
        self.apikey_OPTIMISM = apikey_OPTIMISM
        self.eth_dingding_token = ""  # 可不填

    def call(self, phone):
        url = "https://uni.apistd.com/?action=sms.voice.verification.send&accessKeyId={}".format(
            accessKeyId)

        payload = json.dumps({"to": phone, "code": "5201"})
        headers = {'Content-Type': 'application/json'}

        response = requests.request("POST", url, headers=headers, data=payload)

        logger.info("打电话!!")
        logger.info(response.text)

    def stampTransformTime(self, timestamp):
        '''10位时间戳转为时间'''
        time_local = time.localtime(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_local)

    def _get_txlist_api(self, offset, address, type_api):
        '''封装scan中 txlist接口
            @param int offset：当前地址最近几条信息
            @param address ：监控的地址
            @param type_api: 关于链的类型。传入对应链的api_key。例如 apikey_BSC
        '''
        params = {
            'module': 'account',
            'action': 'txlist',
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": offset,
            "sort": 'desc',
            'address': address,
            'apikey': type_api
        }
        url = ""
        if type_api == self.apikey_BSC:
            url = self.BASE_URL_BSC
        elif type_api == self.apikey_ETH:
            url = self.BASE_URL_ETH
        elif type_api == self.apikey_FTM:
            url = self.BASE_URL_FTM
        elif type_api == self.apikey_MATIC:
            url = self.BASE_URL_MATIC
        elif type_api == self.apikey_AVAX:
            url = self.BASE_URL_AVAX
        elif type_api == self.apikey_ARBITRUM:
            url = self.BASE_URL_ARBITRUM
        elif type_api == self.apikey_OPTIMISM:
            url = self.BASE_URL_OPTIMISM
        try:
            headers = {}
            res = requests.get(url, params,headers=headers,timeout=20)
            return res.json()
        except Exception as e:
            logger.info(e)
            if str(e).find("443") != -1:  # 网络错误不用报错
                return 443

    # ---- API接口封装  ------
    def get_recent_tx(
        self,
        address,
        start,
        apikey_list,
        rotate_count=0,
    ):
        '''获取最新交易信息'''
        for item in apikey_list:
            try:
                res = self._get_txlist_api(3, address, item)
                if not res:
                    continue
                if res == 443 and rotate_count < 10:  # 网络问题并且20次都访问都是443则报错停止运行
                    rotate_count += 1
                    time.sleep(2)
                    self.get_recent_tx(address, True, rotate_count)

                elif 'status' in res and res['status'] == '1' and len(
                        res['result']) > 1:
                    first_mes = res['result'][0]
                    # second_mes = res['result'][1]
                    logger.info('正常监控中...block number:{}'.format(
                        first_mes['blockNumber']))

                    if first_mes['blockNumber'] not in funcdata.get_block_list(
                            item) and start:
                        logger.info('有新交易了...block number:{}'.format(
                            first_mes['blockNumber']))
                        # 范围时间
                        d_time = datetime.datetime.strptime(
                            str(datetime.datetime.now().date()) + '00:00', '%Y-%m-%d%H:%M')
                        d_time1 = datetime.datetime.strptime(
                            str(datetime.datetime.now().date()) + '23:59', '%Y-%m-%d%H:%M')
                        n_time = datetime.datetime.now()
                        logger.info('准备打电话')
                        if n_time > d_time and n_time < d_time1:
                            logger.info('打电话')
                            for phone in phone_number:
                                self.call(phone)
                            time.sleep(120)
                        funcdata.modify_block_list(
                            str(first_mes['blockNumber']), item)

                    if first_mes['blockNumber'] not in funcdata.get_block_list(
                            item) and not start:
                        logger.info('该交易为初始化...block number:{}'.format(
                            first_mes['blockNumber']))
                        funcdata.modify_block_list(
                            str(first_mes['blockNumber']), item)

            except Exception as e:
                logger.exception(e)


def init_logger():
    log_dir = os.path.dirname(os.path.realpath(__file__))
    logger.info(log_dir)
    logger.add("%s/log/%s" % (log_dir, 'monitor.log'),
               rotation='16MB',
               encoding='utf-8',
               enqueue=True,
               retention='10 days')
    logger.info("Logging initialized.")


if __name__ == "__main__":
    init_logger()
    logger.info('start')
    ins = Exercises()
    start = False
    while (True):
        try:
            for key,value in oxdata.items():
                ins.get_recent_tx(key, start, value)
            start = True
        except Exception as e:
            logger.exception(e)
