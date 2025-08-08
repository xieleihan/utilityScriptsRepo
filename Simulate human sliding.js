/**
 * 生成高斯分布的随机数
 */
function gaussianRandom(mean, stdDev) {
    var u1 = Math.random();
    var u2 = Math.random();
    var z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return z0 * stdDev + mean;
}

/**
 * 非线性缓动（easeInOutCubic）
 */
function easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/**
 * 贝塞尔曲线（四点）插值
 */
function cubicBezier(p0, p1, p2, p3, t) {
    var oneMinusT = 1 - t;
    return oneMinusT * oneMinusT * oneMinusT * p0 +
        3 * oneMinusT * oneMinusT * t * p1 +
        3 * oneMinusT * t * t * p2 +
        t * t * t * p3;
}

/**
 * 生成贝塞尔轨迹采样点（带微抖动）
 */
function generateBezierPath(start, c1, c2, end, pointNum) {
    var path = [];
    for (var i = 0; i <= pointNum; i++) {
        // t采用缓动分布，起止点密集，中间稀疏
        var t = easeInOut(i / pointNum);
        var x = cubicBezier(start[0], c1[0], c2[0], end[0], t);
        var y = cubicBezier(start[1], c1[1], c2[1], end[1], t);

        // 每个点加入微小高斯扰动，模拟手指抖动
        x += gaussianRandom(0, 1.8);
        y += gaussianRandom(0, 1.8);

        path.push([Math.round(x), Math.round(y)]);
    }
    return path;
}

/**
 * 控制点生成，更自然的贝塞尔曲线
 */
function getControlPoints(x1, y1, x2, y2) {
    let dx = x2 - x1;
    let dy = y2 - y1;

    let isVertical = Math.abs(dy) > Math.abs(dx);

    // 主方向扰动弱，非主方向扰动强（制造曲线）
    let offsetX1 = gaussianRandom(0, isVertical ? 60 : 20);
    let offsetY1 = gaussianRandom(0, isVertical ? 20 : 60);
    let offsetX2 = gaussianRandom(0, isVertical ? 60 : 20);
    let offsetY2 = gaussianRandom(0, isVertical ? 20 : 60);

    let cx1 = x1 + dx * 0.3 + offsetX1;
    let cy1 = y1 + dy * 0.3 + offsetY1;
    let cx2 = x1 + dx * 0.7 + offsetX2;
    let cy2 = y1 + dy * 0.7 + offsetY2;

    return [[cx1, cy1], [cx2, cy2]];
}

/**
 * 生成起止点带扰动（避免每次都一样）
 */
function getRandomizedPoints(startX, startY, endX, endY) {
    var dx = Math.abs(endX - startX);
    var dy = Math.abs(endY - startY);

    // Y方向滑动为主，X扰动小
    var isVertical = dy > dx;

    var startOffsetX = isVertical ? 10 : 25;
    var startOffsetY = isVertical ? 20 : 10;
    var endOffsetX = isVertical ? 10 : 25;
    var endOffsetY = isVertical ? 20 : 10;

    return {
        x1: startX + gaussianRandom(0, startOffsetX),
        y1: startY + gaussianRandom(0, startOffsetY),
        x2: endX + gaussianRandom(0, endOffsetX),
        y2: endY + gaussianRandom(0, endOffsetY)
    };
}

/**
 * 生成拟人化的观看延迟
 */
function generateViewingDelay(minMs, maxMs) {
    var mean = 11000;
    var stdDev = 3000;
    var delay = gaussianRandom(mean, stdDev);
    delay = Math.max(minMs, Math.min(maxMs, delay));
    return delay;
}

/**
 * 增加“顿挫”或“微调”动作（可选）
 */
function maybeInsertHesitation(path, probability) {
    probability = (typeof probability !== 'undefined') ? probability : 0.22;
    if (Math.random() > probability || path.length < 7) return path;

    // 在路径前1/3或后1/3插入顿挫点
    var idx = Math.random() < 0.5 ? Math.floor(path.length / 3) : Math.floor(path.length * 2 / 3);
    var pt = path[idx];
    var back = [
        pt[0] - gaussianRandom(2, 4),
        pt[1] - gaussianRandom(3, 7)
    ];
    var forward = [
        pt[0] + gaussianRandom(3, 7),
        pt[1] + gaussianRandom(2, 4)
    ];

    var newPath = [];
    for (var i = 0; i < path.length; i++) {
        newPath.push(path[i]);
        if (i == idx) {
            newPath.push([Math.round(back[0]), Math.round(back[1])]);
            newPath.push([Math.round(forward[0]), Math.round(forward[1])]);
        }
    }
    return newPath;
}

/**
 * 生成指定范围内的随机整数
 */
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * 拟人化滑动主函数
 */
function humanizedSwipe(startX, startY, endX, endY, minDuration, maxDuration) {
    var duration = randomInt(minDuration, maxDuration);
    duration = Math.round(gaussianRandom(duration, 70));
    duration = Math.max(minDuration, Math.min(maxDuration, duration));

    // 控制点
    var cps = getControlPoints(startX, startY, endX, endY);
    // 贝塞尔轨迹采样点数（随机波动，避免每次都一样）
    var pointNum = randomInt(15, 25);
    var path = generateBezierPath(
        [startX, startY], cps[0], cps[1], [endX, endY], pointNum
    );

    // 概率性插入“顿挫”微动作
    path = maybeInsertHesitation(path);

    console.log(JSON.stringify(path));

    // 轨迹去重（偶尔采样点坐标一致）
    var filtered = [];
    var last = null;
    for (var i = 0; i < path.length; i++) {
        var pt = path[i];
        if (!last || last[0] != pt[0] || last[1] != pt[1]) {
            filtered.push(pt);
            last = pt;
        }
    }
    path = filtered;

    // 使用gesture滑动
    // gesture(dur, [x1, y1], [x2, y2], ...)
    var gestureArgs = [duration];
    for (var i = 0; i < path.length; i++) {
        gestureArgs.push(path[i]);
    }

    gesture.apply(null, gestureArgs);

    // 调试输出
    console.log("拟人滑动 from (" + startX + "," + startY + ") to (" + endX + "," + endY + ") in " + duration + "ms, points=" + path.length);
}

/**
 * 上滑看下一个视频
 */
function swipeUpForNextVideo() {
    var w = device.width;
    var h = device.height;
    var startX = w / randomInt(1.5, 5);
    var startY = h * 0.7;
    var endX = startX + gaussianRandom(0, 25); // 结束点X偏移小
    var endY = h * 0.3;

    var pts = getRandomizedPoints(startX, startY, endX, endY);

    // 先press一下起点，模拟手指按下
    // press(pts.x1, pts.y1, randomInt(50, 110));
    sleep(randomInt(50, 100));

    // 拟人滑动
    humanizedSwipe(pts.x1, pts.y1, pts.x2, pts.y2, 230, 420);

}

function swipeDownForPreviousVideo() {
    var w = device.width;
    var h = device.height;
    var startX = w / (Math.random() * 4) + 1;
    var startY = h * 0.3;
    var endX = startX + gaussianRandom(0, 25); // 结束点X偏移小
    var endY = h * 0.7;

    var pts = getRandomizedPoints(startX, startY, endX, endY);

    // 先press一下起点，模拟手指按下
    // press(pts.x1, pts.y1, randomInt(50, 110));
    sleep(randomInt(50, 100));

    // 拟人滑动
    humanizedSwipe(pts.x1, pts.y1, pts.x2, pts.y2, 230, 420);
}

// 随机滑动 70% swipeUpForNextVideo 30% swipeDownForPreviousVideo
function randomUpForNextVideo() {
    if (Math.random() < 0.9) {
        swipeUpForNextVideo();
    } else {
        swipeDownForPreviousVideo();
    }
}

function randomDownForPreviousVideo() {
    if (Math.random() < 0.9) {
        swipeDownForPreviousVideo();
    } else {
        swipeUpForNextVideo();
    }
}

/**
 * 导出函数
 */
module.exports = {
    randomUpForNextVideo,
    randomDownForPreviousVideo
}