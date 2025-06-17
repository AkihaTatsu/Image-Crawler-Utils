import traceback
from typing import Optional

import nodriver
import asyncio

from image_crawler_utils import Cookies
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress
from image_crawler_utils.utils import set_up_nodriver_browser

from .utils import twitter_progress_bar_loading


async def __get_twitter_cookies(
    twitter_account: Optional[str]=None, 
    user_id: Optional[str]=None,
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    timeout: float=60.0, 
    headless: bool=False, 
    waiting_seconds: float=60.0, 
    log: Log=Log(),
) -> Cookies:
    if headless:
        log.warning(f"You are using headless mode to get cookies, this might result in failure as verifications like CAPTCHA are not manually passed!")
    
    with CustomProgress(has_spinner=True, transient=True) as progress:
        try:
            log.info(f"Getting cookies by logging in to https://x.com/ ...")
        
            task = progress.add_task(total=4, description='Loading browser components...')
                    
            browser = await set_up_nodriver_browser(
                proxies=proxies,
                headless=headless,
                window_width=800,
                window_height=600,
            )
            
            progress.update(task, advance=1, description="Loading login page...")

            tab = await browser.get("https://x.com/i/flow/login")
            await tab
            await twitter_progress_bar_loading(tab)

            user_input = await tab.select('input[autocomplete="username"]', timeout=timeout)
            if user_input is None:
                raise ModuleNotFoundError("Failed to find account input")
            if twitter_account is not None:
                await user_input.send_keys(twitter_account)
                await asyncio.sleep(0.5)
                await user_input.send_keys('\n')
            
            progress.update(task, advance=1, description="Inputting password...")

            async def find_password_element(_tab: nodriver.Tab):
                try:
                    result = await _tab.select('input[autocomplete="current-password"]', timeout=1)
                    if result is not None:
                        return True
                except:
                    return False
            
            await twitter_progress_bar_loading(tab)
            while not await find_password_element(tab):
                # Input user name (have problems in logging in account)
                username_input = await tab.select('input', timeout=timeout)
                if username_input is None:
                    raise ModuleNotFoundError("Failed to find user name input")
                if user_id is not None:
                    await username_input.send_keys(user_id)
                    await asyncio.sleep(0.5)
                    await username_input.send_keys('\n')
            
            await twitter_progress_bar_loading(tab)
            password_input = await tab.select('input[autocomplete="current-password"]', timeout=timeout)
            if password_input is None:
                raise ModuleNotFoundError("Failed to find password input")
            if password is not None:
                # Input password
                await password_input.send_keys(password)
                await asyncio.sleep(0.5)
                login_button = await tab.select('button[data-testid="LoginForm_Login_Button"]', timeout=timeout)
                await login_button.click()

            progress.update(task, advance=1, description="Trying to login...")

            if not headless:
                while True:  # As long as no successful loggin in, continue this loop
                    try:
                        result = await tab.select('button[data-testid="SideNav_AccountSwitcher_Button"]', timeout=1)
                        if result is not None:
                            break
                    except:
                        continue
            else:  # In headless mode, waiting_seconds is used.
                try:
                    result = await tab.select('button[data-testid="SideNav_AccountSwitcher_Button"]', timeout=waiting_seconds)
                    if result is None:
                        raise ModuleNotFoundError('Element button[data-testid="SideNav_AccountSwitcher_Button"] not found')
                except Exception as e:
                    log.error(f"Failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'}.\n{traceback.format_exc()}",
                                 output_msg=f"Failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'} because {e}")
                    raise TimeoutError(f"failed to log in within {waiting_seconds} {'seconds' if waiting_seconds > 1 else 'second'}.")
            
            progress.update(task, advance=1, description="Parsing cookies...")

            cookies_nodriver = await browser.cookies.get_all()
            cookies = Cookies(cookies_nodriver)

            progress.update(task, advance=1, description="[green]Cookies successfully parsed!")

            browser.stop()
        except Exception as e:
            log.error(f"FAILED to parse cookies from Twitter / X.\n{traceback.format_exc()}", output_msg=f"FAILED to parse cookies from Twitter / X because {e}.")
            cookies = None
    return cookies


# Actually used
def get_twitter_cookies(
    twitter_account: Optional[str]=None, 
    user_id: Optional[str]=None,
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    timeout: float=30.0,
    headless: bool=False, 
    waiting_seconds: float=60.0, 
    log: Log=Log(),
) -> Optional[Cookies]:
    """
    Manually get cookies by logging in to Twitter / X.
    
    Args:
        twitter_account (str, None): Your Twitter / X mail address. Leave it to input manually.
        user_id (str, None): Your Twitter / X mail user id (@user_id). Sometimes Twitter / X requires it to confirm your logging in. Leave it to input manually.
        password (str, None): Your Twitter / X password. Leave it to input manually.
        proxies (dict, None): The proxies used in nodriver browser.

            + The pattern should be in a :py:mod:`requests`-acceptable form like:

                + HTTP type: ``{'http': '127.0.0.1:7890'}``
                + HTTPS type: ``{'https': '127.0.0.1:7890'}``, or ``{'https': '127.0.0.1:7890', 'http': '127.0.0.1:7890'}``
                + SOCKS type: ``{'https': 'socks5://127.0.0.1:7890'}``

        timeout (float, None): Timeout (seconds) for waiting elements. Default is 30.
        headless (bool, None): Use headless mode. Default is False.
        waiting_seconds (float, None): In headless mode, if the next step cannot be loaded in waiting_seconds, then an error will be raised. Default is 60.
        log (image_crawler_utils.log.Log, None): Logging config.

    Returns:
        A image_crawler_utils.Cookies class.
    """
    
    return nodriver.loop().run_until_complete(
        __get_twitter_cookies(
            twitter_account=twitter_account,
            user_id=user_id,
            password=password,
            proxies=proxies,
            timeout=timeout,
            headless=headless,
            waiting_seconds=waiting_seconds,
            log=log,
        )
    )
