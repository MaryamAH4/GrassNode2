# -*- coding: utf-8 -*-
# @Author   :Solana0x
# @File     :main.py
# @Software :PyCharm
import asyncio
import random
import ssl
import json
import time
import uuid
import os
from loguru import logger
from websockets_proxy import Proxy, proxy_connect

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0))  # Reduced frequency
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy2.wynd.network:4444/"     # wss://proxy2.wynd.network:4650/
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, extra_headers={
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
                "User-Agent": custom_headers["User-Agent"]
            }) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(110)  # Increased interval to reduce bandwidth usage

                send_ping_task = asyncio.create_task(send_ping())
                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(message)
                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "4.26.2",
                                    "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                                }
                            }
                            logger.debug(auth_response)
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(pong_response)
                            await websocket.send(json.dumps(pong_response))
                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"Error with proxy {socks5_proxy}: {str(e)}")
            await asyncio.sleep(5)  # انتظام قبل إعادة المحاولة لعدم حظر السيرفر
            continue

async def main():
    user_id = os.environ.get("GRASS_USER_ID", "")
    active_proxies = ["socks5://127.0.0.1:1080"]

    # تم تصحيح بناء القاموس هنا وحذف النقطتين التي سببت الخطأ القديم
    tasks = {asyncio.create_task(connect_to_wss(proxy, user_id)): proxy for proxy in active_proxies}

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            failed_proxy = tasks[task]
            logger.info(f"إعادة الاتصال للبروكسي: {failed_proxy}")
            tasks.pop(task)  # حذف المهمة المنتهية
            
            # إنشاء مهمة جديدة بديلة للحفاظ على استمرارية العمل بدون انهيار
            new_task = asyncio.create_task(connect_to_wss(failed_proxy, user_id))
            tasks[new_task] = failed_proxy
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
