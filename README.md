# 使用Scrapy框架分布式爬取知乎网站的问答信息，并用Scrapyd+Gerapy实现对分布式爬虫的管理
## 声明：该内容不得用于商业用途，仅做学习交流，如若侵犯了您的利益和权益,请邮箱联系我，我将删除该项目。
作者：EatJelly
邮箱：woyaochijelly@163.com
# 项目的部分模块说明
redis_custom模块是账户池管理模块，主要通过redis数据库实现对知乎登录账号、密码、cookie、cookie对应的起始url进行管理。
xici_proxy模块是西刺代理池管理模块，主要通过redis数据库实现代理池的维护，xila_proxy模块同xici_proxy模块。
fateadm_api模块是菲菲代码平台提供的模块，用于识别英文数字验证码的。
zheye模块是用来识别倒立汉字验证码的，下载地址：https://github.com/996refuse/zheye
# 模块依赖
pip install -r requriements.txt 
除了requriements.txt中的模块，因为使用Scrapyd+Gerapy管理，还需在服务端安装scrapyd，客户端安装scrapyd-client以及gerapy模块。
# 所需环境
服务端需安装redis数据库，并将redis.windows.conf中的bind改为0.0.0.0，安装mongodb数据库，并将mongod.cfg中的bindIp改为0.0.0.0，
安装mysql数据库，给远程登录增加权限，grant all privileges on *.* to "root"@"%" identified by '123456' with options; flush privileges;
若以win系统作为服务端，还需在python解释器的Scripts文件夹中添加scrapyd-deploy.bat文件，内容为
@echo off

"D:\Python37\python.exe" "D:\Python37\Scripts\scrapyd-deploy" %1 %2 %3 %4 %5 %6 %7 %8 %9
# 项目的启动
1. 需将chrome浏览器改为调试端口为9222，在win系统下cd进入chrome.exe所在的目录中运行，chrome.exe --remote-debugging-port=9222命令；
2. 向redis中添加起始的url以及账号信息；
3. 更改scrapy.cfg文件，将url指向scrapyd的服务端ip及端口
4. 在服务端一目录中添加scrapyd.conf文件，文件中内容为：
[scrapyd]
bind_address = 0.0.0.0
http_port   = 6800
5. 在该目录中启动scrapyd；
6. 在客户端使用scrapyd-deploy将scrapy项目上传到scrapyd的服务端；
7. 在一目录中启动gerapy，然后初始化gerapy init，然后进入gerapy目录中输入gerapy migrate生成sqlite数据表，然后用gerapy createsuperuser创建登录账号；
8. 将scrapy项目放到gerapy目录中的projects目录中；
9. 通过ip和端口进入gerapy的页面后台，在主机管理中添加scrapyd服务端，在项目管理中部署scrapy项目；
10. 在主机管理中调用，然后运行即可。
