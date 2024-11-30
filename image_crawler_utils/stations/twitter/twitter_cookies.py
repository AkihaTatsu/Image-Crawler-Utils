import traceback
from typing import Optional

import nodriver
import asyncio

from image_crawler_utils import Cookies
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress
from image_crawler_utils.utils import set_up_nodriver_browser



async def __get_twitter_cookies(
    twitter_account: Optional[str]=None, 
    user_id: Optional[str]=None,
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    log: Log=Log(),
) -> Cookies:
    with CustomProgress(has_spinner=True, transient=True) as progress:
        try:
            log.info(f"Getting cookies by logging in to https://x.com/ ...")
        
            task = progress.add_task(total=4, description='Loading browser components...')
                    
            browser = await set_up_nodriver_browser(
                proxies=proxies,
                headless=False,
                window_width=800,
                window_height=600,
            )
            
            progress.update(task, advance=1, description="Loading login page...")

            tab = await browser.get("https://x.com/i/flow/login", new_tab=True)
            if twitter_account is not None:  
                user_input = await tab.find('input[autocomplete="username"]', timeout=30)
                await user_input.send_keys(twitter_account)
                await asyncio.sleep(0.5)
                await user_input.send_keys('\n')
            
            progress.update(task, advance=1, description="Inputting password...")

            async def find_password_element(_tab: nodriver.Tab):
                try:
                    await _tab.find('input[autocomplete="current-password"]', timeout=1)
                    return True
                except:
                    return False
            
            while not await find_password_element(tab):
                # Input user name (have problems in logging in account)
                if user_id is not None:
                    username_input = await tab.find('input')
                    await username_input.send_keys(user_id)
                    await asyncio.sleep(0.5)
                    await username_input.send_keys('\n')
            
            if password is not None:
                # Input password
                password_input = await tab.find('input[autocomplete="current-password"]')
                await password_input.send_keys(password)
                await asyncio.sleep(0.5)
                login_button = await tab.find('button[data-testid="LoginForm_Login_Button"]')
                await login_button.click()

            progress.update(task, advance=1, description="Trying to login...")

            while True:  # As long as no successful loggin in, continue this loop
                try:
                    await tab.find('button[data-testid="SideNav_AccountSwitcher_Button"]', timeout=1)
                    break
                except:
                    continue
            
            progress.update(task, advance=1, description="Parsing cookies...")

            cookies_nodriver = await browser.cookies.get_all()
            cookies = Cookies.create_by(cookies_nodriver)

            progress.update(task, advance=1, description="[green]Cookies successfully parsed!")

            browser.stop()
        except Exception as e:
            log.error(f"FAILED to parse cookies from Twitter / X.\n{traceback.format_exc()}", output_msg=f"FAILED to parse cookies from Twitter / X because {e}\n{traceback.format_exc()}")
            cookies = None
    return cookies


# Actually used
def get_twitter_cookies(
    twitter_account: Optional[str]=None, 
    user_id: Optional[str]=None,
    password: Optional[str]=None, 
    proxies: Optional[dict]=None, 
    log: Log=Log(),
) -> Optional[Cookies]:
    """
    Manually get cookies by logging in to Twitter / X.
    
    Parameters:
        twitter_account (str, optional): Your Twitter / X mail address. Leave it to input manually.
        user_id (str, optional): Your Twitter / X mail user id (@user_id). Sometimes Twitter / X requires it to confirm your logging in. Leave it to input manually.
        password (str, optional): Your Twitter / X password. Leave it to input manually.
        proxies (dict, optional): The proxies you use. Must be requests type.
        log (crawler_utils.log.Log, optional): Logging config.

    Returns:
        A crawler_utils.cookies.Cookies class.
    """
    
    return nodriver.loop().run_until_complete(
        __get_twitter_cookies(
            twitter_account=twitter_account,
            user_id=user_id,
            password=password,
            proxies=proxies,
            log=log,
        )
    )
