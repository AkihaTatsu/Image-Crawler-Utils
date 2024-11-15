<h1 align="center">
Building a Crawler
</h1>

This document includes information about classes and functions useful for building a crawler. It is suggested to finish [tutorials](tutorials.md) before reading this.

Mostly, you only need to construct a Parser, which should return a list of `image_crawler_utils.ImageInfo`. The Downloader class can handle this list for downloading.

**Table of Contents**

- [image\_crawler\_utils](#image_crawler_utils)
  - [CrawlerSettings](#crawlersettings)
  - [ImageInfo](#imageinfo)
  - [Parser and KeywordParser](#parser-and-keywordparser)
  - [Cookies](#cookies)
- [image\_crawler\_utils.keyword](#image_crawler_utilskeyword)
  - [KeywordLogicTree](#keywordlogictree)
- [image\_crawler\_utils.log](#image_crawler_utilslog)
  - [Log](#log)
- [image\_crawler\_utils.user\_agent](#image_crawler_utilsuser_agent)
  - [UserAgent](#useragent)
- [image\_crawler\_utils.utils](#image_crawler_utilsutils)
---

## image_crawler_utils

### CrawlerSettings

Attributes of CrawlerSettings include (\* means information can be referred from [tutorials#Set up CrawlerSettings()](tutorials.md#set-up-crawlersettings)):

### ImageInfo

Please refer to [tutorials#The list of ImageInfo()](tutorials.md#the-list-of-imageurlnameinfo) for detailed information.

### Parser and KeywordParser

### Cookies

Please refer to [tutorials#Cookies() class](tutorials.md#cookies-class) for detailed information.

## image_crawler_utils.keyword

### KeywordLogicTree

## image_crawler_utils.log

### Log

## image_crawler_utils.user_agent

### UserAgent

## image_crawler_utils.utils
