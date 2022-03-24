一个练手的小小demo。
修改自ESP32SDK自带的例程，从flash加载并且传输图像。其余的工作是用在视频、图像分段处理上，做的并不详细。
* 使用EverydayOneCat老师在B站投稿的[《EveOneCat「 烟花+猫+烟花 」No.0145》](https://www.bilibili.com/video/BV1sk4y1y7go)作为测试

1. 使用[ffmpeg](https://github.com/FFmpeg/FFmpeg)将b站上下载的视频进行抽帧，使用jupyter脚本转换为base64格式（有点垃）手动存到cat.h中，构成字符串数组。
2. tcp_client.c将储存在cat.h数组作为传输的数据加载，使用socket API 将字符串发送出去。
3. socket_host_recieve.py是电脑运行的上位机程序，主要功能是创建socket，并接收发来的数据，拆包组包。将base64字符串再转换成recievepic.jpg保存到本地。

下载后，先运行socket_host_recieve.py，再复位ESP32，就可以看到动图效果了。