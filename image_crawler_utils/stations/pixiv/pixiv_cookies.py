from typing import Optional
import traceback

import nodriver
import asyncio

from image_crawler_utils import Cookies
from image_crawler_utils.log import Log
from image_crawler_utils.utils import custom_tqdm, set_up_nodriver_browser



# Async version of get pixiv cookies
async def __get_pixiv_cookies(
    pixiv_id: Optional[str]=None, 
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    log: Log=Log(),
) -> Optional[Cookies]:
    log.info(f"Getting cookies by logging in to https://www.pixiv.net/ ...")
    with custom_tqdm.trange(
        3,
        desc=f'Loading browser components...',
        leave=False,
    ) as pbar:
        try:
            browser = await set_up_nodriver_browser(
                proxies=proxies,
                headless=False,
                window_width=800,
                window_height=600,
            )
            
            pbar.update()
            pbar.set_description(f"Loading login page...")

            tab = await browser.get("https://accounts.pixiv.net/login?lang=en", new_tab=True)
            user_input = await tab.find('input[placeholder="E-mail address or pixiv ID"]', timeout=30)
            if pixiv_id is not None:
                await user_input.send_keys(pixiv_id)
            password_input = await tab.find('input[placeholder="Password"]')
            if password is not None:
                await password_input.send_keys(password)
            await asyncio.sleep(0.5)
            if pixiv_id is not None and password is not None:
                log_in_button = await tab.find("Log In")
                await log_in_button.click()

            pbar.update()
            pbar.set_description(f"Trying to login...")

            while True:  # As long as no successful loggin in, continue this loop
                try:
                    await tab.find('div[id="root"]', timeout=1)
                    break
                except:
                    continue
            
            pbar.update()
            pbar.set_description(f"Parsing cookies...")

            cookies_nodriver = await browser.cookies.get_all()
            cookies = Cookies.create_by(cookies_nodriver)

            browser.stop()
        except Exception as e:
            log.error(f"FAILED to parse cookies from Pixiv.\n{traceback.format_exc()}", output_msg=f"FAILED to parse cookies from Pixiv because {e}")
            cookies = None
    return cookies


# Actually used
def get_pixiv_cookies(
    pixiv_id: Optional[str]=None, 
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    log: Log=Log(),
) -> Optional[Cookies]:
    """
    Manually get cookies by logging in to Pixiv.
    
    Parameters:
        pixiv_id (str, optional): Your Pixiv ID or mail address. Leave it to input manually.
        password (str, optional): Your Pixiv password. Leave it to input manually.
        proxies (dict, optional): The proxies you use. Must be requests type.
        log (crawler_utils.log.Log, optional): Logging config.

    Returns:
        A crawler_utils.cookies.Cookies class.
    """

    return nodriver.loop().run_until_complete(
        __get_pixiv_cookies(
            pixiv_id=pixiv_id,
            password=password,
            proxies=proxies,
            log=log,
        )
    )
