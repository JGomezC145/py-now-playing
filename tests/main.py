import sys
sys.path.append('.')
sys.path.append('..')
import py_now_playing
import asyncio
from pypresence import Presence
from pypresence.exceptions import InvalidID
import time
import multiprocessing
import logging
import traceback

# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)

def start_rpc(client_id, now_playing_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    rpc = Presence(client_id)

    def connect_rpc():
        while True:
            try:
                logger.info("try to connect")
                rpc.connect()
                logger.info("Connected to Discord RPC")
                break
            except Exception as e:
                logger.error(f"Failed to connect to Discord RPC: {e}")
                time.sleep(15)

    # Call connect_rpc directly
    connect_rpc()

    while True:
        try:
            now_playing_list = now_playing_queue.get()
            logger.info(now_playing_list)
            if now_playing_list:
                rpc.update(
                    details=now_playing_list['title'] or "Unknown Song", 
                    state='by ' + now_playing_list['artist'] if now_playing_list['artist'] is not None else 'by Unknown Artist',
                    large_image='https://pro2-bar-s3-cdn-cf4.myportfolio.com/42020405547ae2dc93d34e8df7965fc4/5d5b55e2-c1b4-46cb-a027-6a21bee9de3f_rw_1920.gif?h=85babbd0e5d4aa7c618295a359c1811f',  # Replace with your image key
                    large_text='Amazon Music',
                )
            else:
                logger.info("No music playing")
                rpc.clear()
        except:
            connect_rpc()

        time.sleep(5)


async def main():
    np = py_now_playing.NowPlaying()
    await np.initalize_mediamanger()

    client_id = '1187213553673965619'  # Replace with your client ID
    manager = multiprocessing.Manager()
    now_playing_queue = manager.Queue()

    # Start the Discord RPC in a separate process
    rpc_process = multiprocessing.Process(target=start_rpc, args=(client_id, now_playing_queue))
    rpc_process.start()

    try:
        while True:
            now_playing = await np.get_active_app_user_model_ids()
            now_playing = [app for app in now_playing if app['Name'] == 'Amazon Music.exe']

            if not now_playing:
                now_playing_queue.put(None)
                await asyncio.sleep(5)
                continue

            now_playing_appid = now_playing[0]['AppID']
            data = await np.get_now_playing(now_playing_appid)
            now_playing_queue.put(data)
            logger.info("main" + str(data))
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Interrupted by user, stopping processes...")
        rpc_process.terminate()  # Terminate the rpc_process
        # Kill the event loop
        asyncio.get_event_loop().stop()
    except OSError as e:
        logger.error(e)
        now_playing_queue.put(None)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        traceback.print_exc(e)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user, caught in if, exiting...")
        sys.exit(0)