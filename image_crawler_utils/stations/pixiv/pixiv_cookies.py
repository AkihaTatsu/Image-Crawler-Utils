from typing import Optional
import traceback

import nodriver
import asyncio

from image_crawler_utils import Cookies
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress
from image_crawler_utils.utils import set_up_nodriver_browser



# Async version of get pixiv cookies
async def __get_pixiv_cookies(
    pixiv_id: Optional[str]=None, 
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    headless: bool=False, 
    waiting_seconds: float=60.0, 
    log: Log=Log(),
) -> Optional[Cookies]:
    if headless:
        log.warning(f"You are using headless mode to get cookies, this might result in failure as verifications like CAPTCHA are not manually passed!")

    log.info(f"Getting cookies by logging in to https://www.pixiv.net/ ...")
    
    with CustomProgress(has_spinner=True, transient=True) as progress:
        task = progress.add_task(total=3, description='Loading browser components...')
                    
        try:
            browser = await set_up_nodriver_browser(
                proxies=proxies,
                headless=headless,
                window_width=800,
                window_height=600,
            )
            
            progress.update(task, advance=1, description="Loading login page...")

            tab = await browser.get("https://accounts.pixiv.net/login?lang=en")
            user_input = await tab.select('input[placeholder="E-mail address or pixiv ID"]', timeout=30)
            if pixiv_id is not None:
                await user_input.send_keys(pixiv_id)
            password_input = await tab.select('input[placeholder="Password"]')
            if password is not None:
                await password_input.send_keys(password)
            await asyncio.sleep(0.5)
            if pixiv_id is not None and password is not None:
                log_in_button = await tab.find("Log In")
                await log_in_button.click()
            
            progress.update(task, advance=1, description="Trying to login...")

            if not headless:
                while True:  # As long as no successful loggin in, continue this loop
                    try:
                        await tab.select('div[id="__next"]', timeout=1)  # New version
                        break
                    except:
                        try:
                            await tab.select('div[id="root"]', timeout=1)  # Old version
                        except:
                            continue
            else:  # In headless mode, waiting_seconds is used.
                try:
                    await tab.select('div[id="__next"]', timeout=waiting_seconds)  # New version
                except Exception as e:
                    log.error(f"Failed to log in to the new main page within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'}. Switching to the old version.\n{traceback.format_exc()}",
                                output_msg=f"Failed to log in to the new main page within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'} because {e}. Switching to the old version.".replace('..', '.'))
                    try:
                        await tab.select('div[id="root"]', timeout=waiting_seconds)  # Old version
                    except Exception as e:
                        log.error(f"Failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'}.\n{traceback.format_exc()}",
                                    output_msg=f"Failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'} because {e}")
                        raise TimeoutError(f"failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'}.")

            progress.update(task, advance=1, description="Parsing cookies...")

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
    headless: bool=False, 
    waiting_seconds: float=60.0, 
    log: Log=Log(),
) -> Optional[Cookies]:
    """
    Manually get cookies by logging in to Pixiv.
    
    Parameters:
        pixiv_id (str, optional): Your Pixiv ID or mail address. Leave it to input manually.
        password (str, optional): Your Pixiv password. Leave it to input manually.
        proxies (dict, optional): The proxies you use. Must be requests type.
        headless (bool, optional): Use headless mode. Default is False.
        waiting_seconds (float, optional): In headless mode, if the next step cannot be loaded in waiting_seconds, then an error will be raised. Default is 60.
        log (crawler_utils.log.Log, optional): Logging config.

    Returns:
        A crawler_utils.cookies.Cookies class.
    """

    return nodriver.loop().run_until_complete(
        __get_pixiv_cookies(
            pixiv_id=pixiv_id,
            password=password,
            proxies=proxies,
            headless=headless,
            waiting_seconds=waiting_seconds,
            log=log,
        )
    )
