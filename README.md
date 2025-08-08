# pythonUtilityScripts
Python实用脚本仓库 --开源版

1. `Modify the engineering batch script of Openwrt's passwall plug-in.py`

   > 这个python文件主要实现了`通过 SMB 协议读取和修改 OpenWrt PassWall 配置`,目的为了解决跨境tk等设备一机一网的工程化,降低运营的重复操作,并且有助于路由端管理
   >
   > **使用方式:**
   >
   > 配置`.env`文件
   >
   > ```text
   > SERVER_IP=192.168.10.1
   > MYUSERNAME=root
   > MYPASSWORD=
   > ```
   >
   > 然后安装包
   >
   > ```bash
   > pip install
   > ```
   >
   > 然后会暴露接口
   >
   > 通过访问`http://127.0.0.1:8000/docs#/`可以看到接口
   >
   > 路由器端需要配置上`samba`和`passwall`
   >
   > **配置samba需要注意:**
   >
   > ```text
   > 开启root用户登录
   > 修改模版
   > #invalidusers = root 注释这一行
   > 
   > 往下面添加一个
   > 共享名 | 目录 | 允许用户
   > smb | / | root
   > 
   > 设置共享用户密码,一开始文件不存在
   > 执行
   > `touch /etc/samba/smbpasswd`
   > smbpasswd -a root
   > 输入密码的步骤我跳过
   > ```
   >
   > 剩下没什么难度

2. `Simulate human sliding.js`

   > 模拟人类滑动算法,避免人机验证导致的tk封号,有效率90%,但是并不能阻止IP原因导致的播放量过低的问题
   >
   > 已经导出了,直接使用
   >
   > ```javascript
   > module.exports = {
   >     randomUpForNextVideo,
   >     randomDownForPreviousVideo
   > }
   > ```
   >
   > 
