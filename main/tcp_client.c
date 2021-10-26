/* BSD Socket API Example

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "protocol_examples_common.h"
#include "addr_from_stdin.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "cat.h"


/*
 This code demonstrates how to use the SPI master half duplex mode to read/write a AT32C46D EEPROM (8-bit mode).
*/

#if defined(CONFIG_EXAMPLE_IPV4)    //我们采用IPV4连接对这个例程进行测试，这边的还挺有意思的，只有IPV4有值
#define HOST_IP_ADDR CONFIG_EXAMPLE_IPV4_ADDR
#elif defined(CONFIG_EXAMPLE_IPV6)
#define HOST_IP_ADDR CONFIG_EXAMPLE_IPV6_ADDR
#else
#define HOST_IP_ADDR ""
#endif

#define PORT CONFIG_EXAMPLE_PORT

static const char *TAG = "example";
int flage = 555;

char msgp[60000] ;

static void tcp_client_task(void *pvParameters)//这边是对tcp——client——task做一个
{
    char rx_buffer[8];
    char host_ip[] = HOST_IP_ADDR;
    int addr_family = 0;
    int ip_protocol = 0;

    while (1) {
#if defined(CONFIG_EXAMPLE_IPV4)    //接下来是对IPV4协议的socket进行初始化参数输入
        struct sockaddr_in dest_addr;//下面对这个结构体做一些操作
        dest_addr.sin_addr.s_addr = inet_addr(host_ip);
        dest_addr.sin_family = AF_INET; //af 为地址族（Address Family），也就是 IP 地址类型，常用的有 AF_INET 和 AF_INET6
        dest_addr.sin_port = htons(PORT);
        addr_family = AF_INET; //af 为地址族（Address Family），也就是 IP 地址类型，常用的有 AF_INET 和 AF_INET6
        ip_protocol = IPPROTO_IP;//IP协议
#elif defined(CONFIG_EXAMPLE_IPV6)
        struct sockaddr_in6 dest_addr = { 0 };
        inet6_aton(host_ip, &dest_addr.sin6_addr);
        dest_addr.sin6_family = AF_INET6;
        dest_addr.sin6_port = htons(PORT);
        dest_addr.sin6_scope_id = esp_netif_get_netif_impl_index(EXAMPLE_INTERFACE);
        addr_family = AF_INET6;
        ip_protocol = IPPROTO_IPV6;
#elif defined(CONFIG_EXAMPLE_SOCKET_IP_INPUT_STDIN)
        struct sockaddr_storage dest_addr = { 0 };
        ESP_ERROR_CHECK(get_addr_from_stdin(PORT, SOCK_STREAM, &ip_protocol, &addr_family, &dest_addr));
#endif
        int sock =  socket(addr_family, SOCK_STREAM, ip_protocol);//这里是创建socket
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
            break;
        }
        ESP_LOGI(TAG, "Socket created, connecting to %s:%d", host_ip, PORT);

        int err = connect(sock, (struct sockaddr *)&dest_addr, sizeof(struct sockaddr_in6));//连接socket
        if (err != 0) {
            ESP_LOGE(TAG, "Socket unable to connect: errno %d", errno);
            break;
        }
        ESP_LOGI(TAG, "Successfully connected");

        while (1) { //这个while里面的全部都是发送函数
            // int err = send(sock, payload, strlen(payload), 0);
            // if (err < 0) {
            //     ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
            //     break;
            // }

            int len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            // Error occurred during receiving
            if (len < 0) {
                ESP_LOGE(TAG, "recv failed: errno %d", errno);
                break;
            }
            // Data received
            else {
                
                rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string
                ESP_LOGI(TAG, "Received %d bytes from %s:", len, host_ip);
                ESP_LOGI(TAG, "%s", rx_buffer);
                char *ret;
                
                ret = strstr(rx_buffer,"Picture");
                if(ret!=NULL){
                    // if (err < 0) {
                    //     ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
                    //     break;
                    // }
                    ESP_LOGI(TAG, "Start Picture Transimit Test");
                    memset(rx_buffer, 0, sizeof(rx_buffer));
                    // char rd[20];
                    while(1){
                        for(int i=0;i<65;i++)
                        {   
                                int32_t xlen = strlen(cat[i]);
                                
                                // %04
                                sprintf(msgp,"%010dgoo%s",xlen,cat[i]);
                                ESP_LOGI(TAG, "PIC LENTH = %d NUM= %d",xlen,i);
                                // err = send(sock, (char)xlen, 4, 0);
                                err = send(sock, msgp, 13+xlen, 0);
                                if (err < 0) {
                                    ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
                                    break;
                                }
                            memset(rx_buffer, 0, sizeof(rx_buffer));
                        }
                    }
                    
                }
            }

            // vTaskDelay(2000 / portTICK_PERIOD_MS);//这个还是挺有意思的，这个Task只是把任务挂起了，到时间在恢复。而不是那种Delay
        }

        if (sock != -1) {
            ESP_LOGE(TAG, "Shutting down socket and restarting...");
            shutdown(sock, 0);
            close(sock);
        }
    }
    vTaskDelete(NULL);//掉出发送while就结束任务
    esp_restart();
}


void app_main(void)
{
    
    ESP_ERROR_CHECK(nvs_flash_init());
    spi_flash_init();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    //上面全部是初始化，话说啥事event loop？
    
    /* This helper function configures Wi-Fi or Ethernet, as selected in menuconfig.
     * Read "Establishing Wi-Fi or Ethernet Connection" section in
     * examples/protocols/README.md for more information about this function.
     */
    ESP_ERROR_CHECK(example_connect());

    xTaskCreate(tcp_client_task, "tcp_client", 4096, NULL, 5, NULL);
}
