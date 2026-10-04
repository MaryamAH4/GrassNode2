import asyncio
import random
import ssl
import json
import time
import uuid
import os
import websockets
from loguru import logger

async def connect_to_wss(user_id):
    # إنشاء معرف جهاز افتراضي ثابت وسريع للسيرفر
    device_id = str(uuid.uuid4())
    logger.info(f"Starting connection with Device ID: {device_id}")
    
    while True:
        try:
            await asyncio.sleep(random.uniform(1.0, 3.0))
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            uri = "wss://proxy2.wynd.network:4444/"
            
            async with websockets.connect(uri, ssl=ssl_context, extra_headers={
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
                "User-Agent": custom_headers["User-Agent"]
            }) as websocket:
                
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(60)

                send_ping_task = asyncio.create_task(send_ping())
                
                try:
                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(f"Received from server: {message}")
                        
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
                            logger.debug(f"Sending AUTH Response: {auth_response}")
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(f"Sending PONG Response: {pong_response}")
                            await websocket.send(json.dumps(pong_response))
                finally:
                    send_ping_task.cancel()

        except Exception as e:
            logger.error(f"Connection error occurred: {str(e)}")
            await asyncio.sleep(10)  # الانتظار قبل إعادة المحاولة لمنع حظر السيرفر

async def main():
    user_id = os.environ.get("GRASS_USER_ID", "")
    if not user_id:
        logger.error("Error: GRASS_USER_ID environment variable is missing!")
        return
        
    logger.info(f"Successfully loaded User ID: {user_id}")
    await connect_to_wss(user_id)

if __name__ == '__main__':
    asyncio.run(main())
