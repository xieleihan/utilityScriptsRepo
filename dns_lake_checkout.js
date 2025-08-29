// 引入是私密的js,需要自己封装
const { drag_normal_up } = require("./swipe_utils");
const log_util = require("../../logs/log_util")

function dnsLakeCheckout() {
    try {
        launch("mark.via")
        sleep(2000)
        if (id("mark.via:id/ed").findOne(3000)) {
            // 如果存在同意按钮，点击同意按钮
            let agreeBtn = id("mark.via:id/ed").findOne(3000);
            let agreeBtnBounds = agreeBtn.bounds();
            if (agreeBtn != null && agreeBtnBounds != null) {
                // log_util.info('同意按钮存在，点击同意按钮');
                click(agreeBtnBounds)
                sleep(3000);
            }
            // log_util.info('点击同意按钮');
        }
        let inputBox = text("Homepage").findOne(3000);
        let url = 'https://ipleak.net/'
        if (inputBox != null) {
            let inputBoxBounds = inputBox.bounds();
            if (inputBoxBounds != null) {
                click(inputBoxBounds);
                sleep(2000);
                setText(url);
                sleep(2000);

            }

        }
        let goBtn = desc("Search").findOne(3000);
        if (goBtn != null) {
            let goBtnBounds = goBtn.bounds();
            if (goBtnBounds != null) {
                click(goBtnBounds);
                sleep(10000);
            }

        }



        // 保证一定加载出来网页
        sleep(5000);
        let content = text("Your IP addresses").findOne(3000).parent();
        // 获取到当前的公网IP对应的国家
        let titleText = content.child(2).child(0).child(2).text();
        // 等发起请求
        sleep(240000);
        drag_normal_up()
        drag_normal_up()
        // console.log("开始检测DNS泄漏")
        log_util.info("开始检测DNS泄漏")
        // console.log(textContains("DNS Address").findOne(3000))
        let dnsContent = textContains("DNS Address").findOne(3000).parent();
        let dnsRequestLayout = dnsContent.child(7).child(0);

        let leak = false
        for (let i = 0; i < dnsRequestLayout.childCount(); i++) {

            let dnsText = dnsRequestLayout.child(i).child(2).text();
            // 如果包含'China'或者'Hong Kong',说明泄漏了
            if (dnsText.indexOf('China') != -1 || dnsText.indexOf('Hong Kong') != -1) {
                // console.log('检测到DNS泄漏')
                leak = true
            } else {
                console.log(dnsText)
            }
        }

        if (leak) {
            log_util.warn("检测到DNS泄漏")
        } else {
            log_util.info("未检测到DNS泄漏")
        }
    } catch (e) {
        log_util.error("dns泄漏检测出错", e);
    }
}

module.exports = {
    dnsLakeCheckout
}