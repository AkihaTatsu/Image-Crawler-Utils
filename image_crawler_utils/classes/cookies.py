from __future__ import annotations
import dataclasses
from collections import Counter
from typing import Optional, Union

import copy
import json
import os, traceback
from rich import markup

import nodriver

from image_crawler_utils.log import Log
from image_crawler_utils.utils import check_dir



@dataclasses.dataclass
class Cookies:
    """
    Convert format of cookies between selenium, requests and string.
    Use .create_by() to input cookies.
    Use .cookies_nodriver / .cookies_selenium / .cookies_dict / .cookies_string to get the cookies of suitable format.
    """

    cookies_nodriver: Optional[list[nodriver.cdp.network.Cookie]] = None
    cookies_selenium: Optional[list[dict]] = dataclasses.field(default_factory=lambda: [])
    cookies_dict: Optional[dict] = dataclasses.field(default_factory=lambda: {})
    cookies_string: Optional[str] = ''
    

    def __add__(self, other: Cookies):
        """
        Concatenate two cookies.
        If two Cookies have same values, the latter will be omitted.
        """

        cookies_list = self.cookies_selenium.copy()
        for cookie in other.cookies_selenium:
            if cookie['name'] not in self.cookies_dict.keys():
                cookies_list.append(cookie.copy())
        return Cookies.create_by(cookies_list)
    

    def __most_domain(self, cookies: list):
        if isinstance(cookies[0], dict):
            domain_list = [cookie["domain"] for cookie in cookies 
                           if "domain" in cookie.keys()]
        elif isinstance(cookies[0], object):
            domain_list = [cookie.domain for cookie in cookies 
                           if hasattr(cookie, "domain")]
        domain_list = [domain for domain in domain_list if len(domain) > 0]
        return Counter(domain_list).most_common(1)[0][0]
    
    
    def __selenium_cookies_to_nodriver(self):
        attribute_dict = {
            "name": "",
            "value": "",
            "domain": "",
            "path": "/",
            "size": 0,
            "httpOnly": False,
            "secure": True,
            "session": False,
            "priority": "Medium",
            "sameParty": False,
            "sourceScheme": "Secure",
            "sourcePort": 443,
        }
        if self.cookies_selenium is not None:
            self.cookies_nodriver = []
            for cookie in self.cookies_selenium:
                insert_cookies = cookie.copy()
                for key, item in attribute_dict.items():
                    if key not in insert_cookies.keys():
                        if key == "size":
                            insert_cookies[key] = len(insert_cookies["name"]) + len(insert_cookies["value"])
                        else:
                            insert_cookies[key] = item
                self.cookies_nodriver.append(nodriver.cdp.network.Cookie.from_json(insert_cookies))
        else:
            raise ValueError("cookies_selenium cannot be None.")
        

    @classmethod
    def load_from_json(cls, json_file: str, encoding: str='UTF-8', log: Log=Log()) -> Cookies:
        """
        Load the Cookies from a json file.
        ONLY WORKS IF the info can be JSON serialized.

        Parameters:
            json_file (str): Name / path of json file.
            encoding (str): Encoding of JSON file.
            log (crawler_utils.log.Log, optional): Logging config.

        Returns:
            The Cookies, or None if failed.
        """
        
        try:
            with open(json_file, "r", encoding=encoding) as f:
                new_cls = cls.create_by(json.load(f))            

            log.info(f'Cookies has been loaded from [repr.filename]{markup.escape(os.path.abspath(json_file))}[reset]', extra={"markup": True})
            return new_cls
            
        except Exception as e:
            log.error(f'Failed to load Cookies from [repr.filename]{markup.escape(os.path.abspath(json_file))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None
        

    def save_to_json(self, json_file: str, encoding: str='UTF-8', log: Log=Log()) -> Optional[tuple[str, str]]:
        """
        Save the Cookies into a json file.

        Parameters:
            json_file (str): Name / path of json file. (Suffix is optional.)
            encoding (str): Encoding of JSON file.
            log (crawler_utils.log.Log, optional): Logging config.
            
        Returns:
            (Saved file name, Absolute path of the saved file), or None if failed.
        """

        path, filename = os.path.split(json_file)
        check_dir(path, log)
        f_name = os.path.join(path, f"{filename}.json")
        f_name = f_name.replace(".json.json", ".json")  # If .json is already contained in json_file, skip it
        try:
            with open(f_name, "w", encoding=encoding) as f:
                json.dump(self.cookies_selenium, f, indent=4, ensure_ascii=False)
                log.info(f'Cookies has been saved at [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset]', extra={"markup": True})
                return f_name, os.path.abspath(f_name)
        except Exception as e:
            log.error(f'Failed to save Cookies at [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None
        

    @classmethod
    def create_by(cls, cookies: Optional[Union[list, dict, str]]) -> Cookies:
        """
        Input the cookies. The other types will be automatically converted.

        Parameters:
            cookies (list, dict, str, None): Cookies generated as string, dict (requests), list (selenium or nodriver).

        Returns:
            New Cookies class with input cookies.
        """
        if cookies is None:
            return cls()
        elif isinstance(cookies, str):
            return cls.create_by_string(cookies)
        elif isinstance(cookies, dict):
            if len(cookies) == 0:
                raise ValueError("Empty cookies is not accepted.")
            else:
                return cls.create_by_dict(cookies)
        elif isinstance(cookies, list):
            if len(cookies) == 0:
                raise ValueError("Empty cookies is not accepted.")
            else:
                if isinstance(cookies[0], dict):
                    return cls.create_by_selenium(cookies)
                elif isinstance(cookies[0], object):
                    return cls.create_by_nodriver(cookies)
        raise ValueError("Cookies type not identifiable.")

    
    @classmethod
    def create_by_nodriver(cls, cookies_nodriver: list[nodriver.cdp.network.Cookie]) -> Cookies:
        """
        Input nodriver-type cookies. The other types will be automatically converted.

        Parameters:
            cookies_nodriver (list[nodriver.cdp.network.Cookie]): nodriver-generated cookies.

        Returns:
            New Cookies class with input cookies.
        """

        result_cls = cls()
        result_cls.cookies_nodriver = cookies_nodriver
        result_cls.cookies_selenium = [cookie.to_json() for cookie in result_cls.cookies_nodriver]
        result_cls.cookies_dict = {cookie.name: cookie.value 
                                 for cookie in result_cls.cookies_nodriver}
        result_cls.cookies_string = '; '.join([f'{cookie.name}={cookie.value}' 
                                 for cookie in result_cls.cookies_nodriver])
        return result_cls


    @classmethod
    def create_by_selenium(cls, cookies_selenium: list[dict]) -> Cookies:
        """
        Input selenium-type cookies. The other types will be automatically converted.

        Parameters:
            cookies_selenium (list[dict]): Selenium-generated cookies.

        Returns:
            New Cookies class with input cookies.
        """

        result_cls = cls()
        result_cls.cookies_selenium = cookies_selenium
        result_cls.cookies_dict = {cookie['name']: cookie['value'] 
                                 for cookie in result_cls.cookies_selenium}
        result_cls.cookies_string = '; '.join([f'{cookie["name"]}={cookie["value"]}' 
                                 for cookie in result_cls.cookies_selenium])
        result_cls.__selenium_cookies_to_nodriver()
        return result_cls


    @classmethod
    def create_by_dict(cls, cookies_dict: dict) -> Cookies:
        """
        Input requests-type cookies. The other types will be automatically converted.

        Parameters:
            cookies_dict (dict): Requests-generated cookies.

        Returns:
            New Cookies class with input cookies.
        """

        result_cls = cls()
        result_cls.cookies_dict = cookies_dict
        result_cls.cookies_selenium = [{"name": key, "value": value}
                                 for key, value in result_cls.cookies_dict.items()]
        result_cls.cookies_string = '; '.join([f'{key}={value}' 
                                 for key, value in result_cls.cookies_dict.items()])
        result_cls.__selenium_cookies_to_nodriver()
        return result_cls
        

    @classmethod
    def create_by_string(cls, cookies_string: str) -> Cookies:
        """
        Input string-type cookies. The other types will be automatically converted.

        Parameters:
            cookies_string (str): Cookies in string.

        Returns:
            New Cookies class with input cookies.
        """

        result_cls = cls()
        result_cls.cookies_string = cookies_string.strip()
        if cookies_string[-1] == ';':
            result_cls.cookies_string = result_cls.cookies_string[:-1]
        result_cls.cookies_selenium = []
        result_cls.cookies_dict = {}
        for item in cookies_string.replace('\n', '').split(';'):
            if "=" not in item:
                continue
            name = item.split("=")[0].strip()
            value = item.split("=")[1].strip()
            result_cls.cookies_selenium.append({"name": name, "value": value})
            result_cls.cookies_dict[name] = value
        result_cls.__selenium_cookies_to_nodriver()
        return result_cls
        

    def update_selenium_cookies(self, old_selenium_cookies: list[dict]):
        """
        Update selenium cookies;
        For every cookie in the input cookies with the same name as the ones in the Cookies class, replace the values with the latter ones.
        Also add cookies in Cookies class which not exists in input cookies.

        Parameters:
            old_selenium_cookies (list[dict]): Cookies from selenium.

        Returns:
            New selenium cookies (a list[dict]).
        """

        new_selenium_cookies = copy.deepcopy(old_selenium_cookies)
        for cookie in self.cookies_selenium:
            for new_cookie in new_selenium_cookies:
                if new_cookie['name'] == cookie['name']:
                    new_cookie['value'] = cookie['value']
            if cookie['name'] not in [new_cookie['name'] for new_cookie in new_selenium_cookies]:
                new_selenium_cookies.append(cookie)
        # Set those without domain to the most frequent domain in cookies provided
        most_domain = self.__most_domain(new_selenium_cookies)
        for i in range(len(new_selenium_cookies)):
            if len(new_selenium_cookies[i]["domain"]) == 0:
                new_selenium_cookies[i]["domain"] = most_domain
        return new_selenium_cookies
    

    def update_nodriver_cookies(self, old_nodriver_cookies: list[nodriver.cdp.network.Cookie]):
        """
        Update nodriver cookies;
        For every cookie in the input cookies with the same name as the ones in the Cookies class, replace the values with the latter ones.
        Also add cookies in Cookies class which not exists in input cookies.

        Parameters:
            old_nodriver_cookies (list[nodriver.cdp.network.Cookie]): Cookies from nodriver.

        Returns:
            New nodriver cookies (a list[nodriver.cdp.network.Cookie]).
        """

        new_nodriver_cookies = copy.deepcopy(old_nodriver_cookies)
        for cookie in self.cookies_nodriver:
            for new_cookie in new_nodriver_cookies:
                if new_cookie.name == cookie.name:
                    new_cookie.value = cookie.value
                    new_cookie.size = len(new_cookie.name) + len(new_cookie.value)
            if cookie.name not in [new_cookie.name for new_cookie in new_nodriver_cookies]:
                new_nodriver_cookies.append(cookie)
        # Set those without domain to the most frequent domain in cookies provided
        most_domain = self.__most_domain(new_nodriver_cookies)
        for i in range(len(new_nodriver_cookies)):
            if len(new_nodriver_cookies[i].domain) == 0:
                new_nodriver_cookies[i].domain = most_domain
        return new_nodriver_cookies
        
    
    def is_none(self) -> bool:
        """
        Check whether Cookies is None.

        Returns:
            A bool, telling whethers Cookies is None.
        """
        return (self.cookies_nodriver is None
                and len(self.cookies_selenium) == 0 
                and len(self.cookies_dict) == 0 
                and len(self.cookies_string) == 0)


##### nodriver currently has bugs when setting cookies, so I will set it manually


async def update_nodriver_browser_cookies(
    browser: nodriver.Browser,
    cookies: Cookies,
):
    """
    This function will update nodriver browser cookies with Cookies provided.
    As nodriver includes a browser.cookies.set_all() but it has a critical bug that stay unfixed for a long time, I'll do it myself!

    Parameters:
        browser (nodriver.Browser): The browser created by nodriver.
        cookies (image_crawler_utils.Cookies): The cookies containing account information.
    """

    # Replace cookies
    nodriver_cookies = await browser.cookies.get_all()
    new_nodriver_cookies = cookies.update_nodriver_cookies(nodriver_cookies)

    connection = None
    for tab in browser.tabs:
        if tab.closed:
            continue
        connection = tab
        break
    else:
        connection = browser.connection

    await connection.send(nodriver.cdp.storage.set_cookies(new_nodriver_cookies))
