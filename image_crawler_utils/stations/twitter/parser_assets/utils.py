from typing import Optional

import nodriver



async def twitter_progress_bar_loading(
    tab: nodriver.Tab,
) -> Optional[str]:
    """
    As long as there is an progress bar (rotating circle) in loading Twitter / X page, this function will not exit.

    Args:
        tab (nodriver.Tab): Nodriver tab with loaded searching result page.
    """
    
    while True:
        try:
            progressbar_elem = await tab.select('div[role="progressbar"]', timeout=1)
            if progressbar_elem is None:
                break
        except:
            break


async def twitter_error_check(
    tab: nodriver.Tab, 
) -> Optional[str]:
    """
    Check if there is an error in loading Twitter / X page.

    Args:
        tab (nodriver.Tab): Nodriver tab with loaded searching result page.

    Returns:
        Return True if found error element, or return False.
    """

    try:
        main_structure = await tab.select('div[data-testid="primaryColumn"]')
        error_element = await main_structure.query_selector('button[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-2yi16 r-1qi8awa r-3pj75a r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
        return True if error_element is not None else False    
    except:
        return False
    

async def twitter_empty_check(
    tab: nodriver.Tab,
) -> Optional[str]:
    """
    Check if the result is empty.

    Args:
        tab (nodriver.Tab): Nodriver tab with loaded searching result page.
        tab_url (str): URL of the tab.
        log (image_crawler_utils.log.Log, None): Logging config.

    Returns:
        Return True if found empty element, or return False.
    """

    try:
        await tab
        empty_elem = await tab.select('div[data-testid="empty_state_header_text"]')
        return True if empty_elem is not None else False    
    except:
        return False
    