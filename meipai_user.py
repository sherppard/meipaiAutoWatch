# import 这边需要注意的是只有一个rsa这个模块是需要install的，其他的都是内置
import re , urllib.parse , urllib.request , http.cookiejar , base64 , binascii , rsa , json ,  bs4
from bs4 import BeautifulSoup
import time
import configparser

import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

print('=============================')
print('美拍自动关注用户脚本')
print('version: 1.0')
print('From Git.dns team By sherpper')
print('=============================')

# 以下4行代码说简单点就是让你接下来的所有get和post请求都带上已经获取的cookie，因为稍大些的网站的登陆验证全靠cookie
cj = http.cookiejar.LWPCookieJar()
cookie_support = urllib.request.HTTPCookieProcessor(cj)
opener = urllib.request.build_opener(cookie_support , urllib.request.HTTPHandler)
urllib.request.install_opener(opener)

# 封装一个用于get的函数，新浪微博这边get出来的内容编码都是-8，所以把utf-8写死在里边了，真实项目中建议根据内容实际编码来决定
def getData(url) :
    headers_get = {'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)'}
    request = urllib.request.Request(url , data=None , headers=headers_get)
    response = urllib.request.urlopen(request)
    text = response.read().decode('utf-8')
    return text

# 封装一个用于post的函数，验证密码和用户名都是post的，所以这个postData在本demo中专门用于验证用户名和密码
def postData(url , data) :
    # headers需要我们自己来模拟
    headers = {'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)','Referer' : 'http://www.meipai.com/users/followers?uid=1092109'}
    # 这里的urlencode用于把一个请求对象用'&'来接来字符串化，接着就是编码成utf-8
    data = urllib.parse.urlencode(data).encode('utf-8')
    request = urllib.request.Request(url , data , headers)
    response = urllib.request.urlopen(request)
    text = response.read().decode('gbk')
    # print(response.info())
    return text


def login_weibo(nick , pwd) :
    #==========================获取servertime , pcid , pubkey , rsakv===========================
    # 预登陆请求，获取到若干参数
    prelogin_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.15)&_=1400822309846' % nick
    preLogin = getData(prelogin_url)
    # 下面获取的四个值都是接下来要使用的
    servertime = re.findall('"servertime":(.*?),' , preLogin)[0]
    pubkey = re.findall('"pubkey":"(.*?)",' , preLogin)[0]
    rsakv = re.findall('"rsakv":"(.*?)",' , preLogin)[0]
    nonce = re.findall('"nonce":"(.*?)",' , preLogin)[0]
    #===============对用户名和密码加密================
    # 好，你已经来到登陆新浪微博最难的一部分了，如果这部分没有大神出来指点一下，那就真是太难了，我也不想多说什么，反正就是各种加密，最后形成了加密后的su和sp
    su = base64.b64encode(bytes(urllib.request.quote(nick) , encoding = 'utf-8'))
    rsaPublickey = int(pubkey , 16)
    key = rsa.PublicKey(rsaPublickey , 65537)
    # 稍微说一下的是在我网上搜到的文章中，有些文章里并没有对拼接起来的字符串进行bytes，这是python3的新方法好像是。rsa.encrypt需要一个字节参数，这一点和之前不一样。其实上面的base64.b64encode也一样
    message = bytes(str(servertime) + '\t' + str(nonce) + '\n' + str(pwd) , encoding = 'utf-8')
    sp = binascii.b2a_hex(rsa.encrypt(message , key))
    #=======================登录=======================
    
    #param就是激动人心的登陆post参数，这个参数用到了若干个上面第一步获取到的数据，可说的不多
    param = {
    		'entry' : 'weibo' , 
    		'gateway' : 1 , 
    		'from' : '' , 
    		'savestate' : 7 , 
    		'useticket' : 1 , 
    		'pagerefer' : 'http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D' , 
    		'vsnf' : 1 , 
    		'su' : su , 
    		'service' : 'miniblog' , 
    		'servertime' : servertime , 
    		'nonce' : nonce , 
    		'pwencode' : 'rsa2' , 
    		'rsakv' : rsakv , 
    		'sp' : sp , 
    		'sr' : '1680*1050' ,
            'encoding' : 'UTF-8' , 
            'prelt' : 961 , 
            'url' : 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack'
            }
    # 这里就是使用postData的唯一一处，也很简单
    s = postData('http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)' , param)
    #print(s)
    # 好了，当你的代码执行到这里时，已经完成了大部分了，可是有很多爬虫童鞋跟我一样还就栽在了这里，假如你跳过这里直接去执行获取粉丝的这几行代码你就会发现你获取的到还是让你登陆的页面，真郁闷啊，我就栽在这里长达一天啊
    # 好了，我们还是继续。这个urll是登陆之后新浪返回的一段脚本中定义的一个进一步登陆的url，之前还都是获取参数和验证之类的，这一步才是真正的登陆，所以你还需要再一次把这个urll获取到并用get登陆即可
    urll = re.findall("location.replace\(\'(.*?)\'\);" , s)[0]
    #print(urll)
    ticketValue = re.findall('&ticket=(.*?)&',urll)
    getData(urll)

    #===============test============
    # print(su) 
    # print(sp)
	#===============test============  

    #======================获取粉丝====================
    # 如果你没有跳过刚才那个urll来到这里的话，那么恭喜你！你成功了，接下来就是你在新浪微博里畅爬的时候了，获取到任何你想获取到的数据了！
    # 可以尝试着获取你自己的微博主页看看，你就会发现那是一个多大几百kb的文件了
    # text = getData('http://weibo.com/sherpper/home?topnav=1&wvr=6')
    # fp = open('yeah.txt' , 'w' , encoding = 'utf-8')
    # fp.write(text)
    # fp.close()

def saveConfig(file,option,index,key):
    configData = configparser.ConfigParser()
    configData.read(file)
    configData.set(option,index,key)
    configData.write(open(file ,'w'))

def readConfig(file,option,index):
    configData = configparser.ConfigParser()
    configData.read(file)
    cf = configData.get(option,index)
    return cf

def readOptionLen(file,option):
    configData = configparser.ConfigParser()
    configData.read(file)
    option = configData.options('account') 
    optionLen = len(option)
    return optionLen

#==================================================后记============================================================
# my change start

# -------------------- 获取明星的json数据  -------------------
try:
    starData = open('starIdDB.txt','r')   # 第一次打开，检查starIdDB.txt是否存在，如果不存在就下载数据并且生成
except FileNotFoundError:
    print('正在初识化数据文件')
    starData = open('starIdDB.txt','w')
    for i in range(1,42):
        urlc = 'http://www.meipai.com/squares/new_timeline?page=' + str(i) + '&count=100&tid=16'   # count=50 获取50条明星记录，一次最多100条，tid=16 表示明星类别的一组记录，明星大概有4千多一点
        data = getData(urlc)
        jsonData = json.loads(data)

        # -------------------- 将明星id数据写入文件 -------------------
        
        for j in range(0,100):
            try:
                starData.write(str(jsonData['medias'][j]['user']['id'])+'\n')
            except IndexError:
                break
        print('已经获取了第 '+str(i)+'页/总共41页')
    starData.close()
    print('初始化完成')

# -------------------- 从starData.txt取出明星id数据放入列表,并且去重复 -------------------

test = re.findall("mode='w'",str(starData))
if test:
    starData = open('starIdDB.txt','r')
    starID=[]
    for line in starData:
        line=line.replace("\n","")
        starID.append(line)
    temp = set(starID)
    starID_list = list(temp)
else:
    starID=[]
    for line in starData:
        line=line.replace("\n","")
        starID.append(line)
    temp = set(starID)
    starID_list = list(temp)

# -------------------- 打开明星粉丝页-------------------

userid = []  # 所有的女生用户id
fail = 0     # 记录关注失败的次数
totalfail = 0 # 记录所有失败的次数
howManyPost = 0 # 记录关注post的次数

# -------------------- 从配置文件读取starID数据  -------------------


for j in range(0,len(starID_list)):
    currentStarId = int(readConfig('config','record','currentStarId'))
    if j < currentStarId :
        continue
    if j >= currentStarId :
        saveConfig('config','record','currentStarId',str(j))


        for i in range(1,85):
            currentPage = int(readConfig('config','record','currentPage'))
            if i < currentPage :
                continue
            if i >= currentPage :
                saveConfig('config','record','currentPage',str(i))

                urld = 'http://www.meipai.com/users/followers?uid=' + starID_list[j] + '&p=' + str(i)  # 明星的id号 ：txt['medias'][0]['user']['id']
                pageFans = getData(urld)

                # -------------------- 在当前粉丝页获取所有女生的用户id  -------------------

                soup = BeautifulSoup(pageFans)
                alluser = soup.find_all("a", attrs={"class": "black"})

                female = []  # 提取当前粉丝页中所有女生的a标签
                for ii in range(0,len(alluser)):
                    x = str(alluser[ii])
                    if 'icon-female' in x: 
                        female.append(alluser[ii])

                # ------ 提取当前页的所有女生用户id ------
                for iii in range(0,len(female)):
                    xx = str(female[iii])
                    match = re.findall('user\/(.*?)"',xx)
                    userid.append(match[0])

                female = []  # 清空，测试情况下的，有可能不需要

                # print (userid)

                # ------ 做判断:  美拍每次只可以关注29个用户 -----

                if len(userid) >= 29:
                    
                    print('本次有'+str(len(userid))+'用户待关注,下面开始关注')  # 用户使用时,这段注释掉

                    #------------------------------- 登录新浪微博 --------------------
                    
                    userIndex = str(readConfig('config','record','whichUser'))
                    ac = readConfig('config','account','sinaweibo' + userIndex)
                    username = re.findall('(.*),',ac)
                    password = re.findall(',(.*)',ac) 
                    login_weibo(username[0],password[0])  # 因为username跟password都是返回一个列表，所以要加索引
                    howManyUser = readOptionLen('config','account')
                    if int(userIndex) < howManyUser :
                        saveConfig('config','record','whichUser', str(int(userIndex)+1) )
                    if int(userIndex) == howManyUser :
                        saveConfig('config','record','whichUser', '1' )

                    #------------------------------- 进入美拍认证页面 --------------------
                    urla = 'http://www.meipai.com/connect/weibo?referer=http%3A%2F%2Fwww.meipai.com%2Fuser%2F1030256350'
                    text = getData(urla)

                    # text = getData('http://www.meipai.com/users/followers?uid=1025713094&p=3')
                    # fp = open('dbug.txt' , 'w' , encoding = 'utf-8')
                    # fp.write(text)
                    # fp.close()
                    

                    # ----------------- 关注他人 --------------------
                    urlfans = 'http://www.meipai.com/users/friendships_create'

                    for iiii in range( 0 , len(userid) ):
                        test = postData( urlfans , {'id':userid[iiii]} )
                        time.sleep(3)
                        if 'true' in test:
                            print('账号'+userIndex+': '+username[0]+'  关注成功-'+str(iiii+1))
                        # 如果提示“10115 操作繁忙”，fail值加1，直到第五次就休息, "20506 已经关注过TA","1001 未登录
                        elif '10115' in test:
                            print('账号'+userIndex+': '+username[0]+'  关注失败-'+str(iiii+1))
                            fail += 1
                            totalfail +=1

                            if totalfail == 30:   # 如果总失败次数等于30就退出程序
                                print('已经关注 ' + str(howManyPost) + ' 个用户, 但是现在关注的失败次数超过30次,请等一下再试试!')
                                exit()

                            if fail == 3:
                                print("关注失败了3次,进入下一个账号! ")
                                time.sleep(5)  # 这段实际上可以不需要的,它的存在没什么意义
                                fail = 0
                                break
                        else:
                            print('账号'+userIndex+': '+username[0]+ test + '--' +str(iiii+1))

                        howManyPost += 1
                        if howManyPost % 60 == 0:   # 每60次休息60s
                            print("已经关注了 60 次 , 让我们休息60s后再继续!")
                            time.sleep(60)

                    userid = []   # 清空userid

            if i == 84:
                saveConfig('config','record','currentPage','1')

    if j == len(starID_list):
        saveConfig('config','record','currentStarId','0')










