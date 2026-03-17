# 05. 网络编程：从 0 到 socket / 非阻塞 / epoll / 长连接（深挖版）

> 这一章是给**之前几乎没接触过网络编程**的人写的。
>

> 目标不是让你一上来就手搓高性能框架，而是分三步：
>

> 1. 先搞明白网络编程到底在干什么
> 2. 再搞明白 C++ 服务端常见技术栈：socket、非阻塞、epoll、事件循环
> 3. 最后把它整理成能扛住面试追问的回答
>

> 如果你之前只学过 TCP/UDP 协议、HTTP、epoll 名词，但没真正把这些东西串起来，这一章就是那张“总装图”。

---

# 0. 先建立一个总图：网络编程到底在做什么？

很多人第一次学网络编程，会把它理解成：

- 调几个 API
- 发点字符串
- 收点字符串

但这只是表面。

更准确地说：

> **网络编程是在做“两个进程之间，通过操作系统提供的通信接口，在不同主机或同一主机之间交换数据”。**

其中最常见的接口就是：

- `socket`

你可以把 socket 先粗暴理解成：

> **操作系统给你的一种“网络通信文件描述符”**。

它和文件描述符很像：

- 可以创建
- 可以读写
- 可以关闭
- 可以被 `select/poll/epoll` 监听

所以网络编程的很多问题，本质上都不是“网络很玄学”，而是：

- 我怎么建立连接？
- 我怎么发数据？
- 我怎么知道对方发来了数据？
- 我怎么在大量连接里高效处理事件？
- 我怎么处理半包、粘包、断开、超时、心跳？

---

# 1. 先从最基础的问题开始：客户端和服务端分别在干什么？

## 1.1 一个最朴素的理解

### 服务端做什么？
服务端通常做三件事：

1. 在某个 IP + 端口上等待别人连接
2. 有客户端连上来之后，接收请求
3. 处理请求并返回结果

### 客户端做什么？
客户端通常也做三件事：

1. 知道服务端地址
2. 主动发起连接
3. 发请求、收响应

---

## 1.2 最经典的 TCP 通信流程

### 服务端流程
1. `socket()`：创建监听 socket
2. `bind()`：绑定 IP 和端口
3. `listen()`：开始监听
4. `accept()`：接受客户端连接
5. `recv()/read()`：接收数据
6. `send()/write()`：发送数据
7. `close()`：关闭连接

### 客户端流程
1. `socket()`：创建 socket
2. `connect()`：连接服务端
3. `send()/write()`：发请求
4. `recv()/read()`：收响应
5. `close()`：关闭连接

### 一句话总结
> 服务端先把门开好并站在门口等人；客户端主动敲门；建立连接后双方就可以通过 socket 收发数据。

---

# 2. socket 到底是什么？

## 2.1 别把 socket 只当函数名

很多人会说：“socket 不就是创建套接字的函数吗？”

这不算错，但太浅。

更好的理解是：

> socket 既是一类编程接口，也是内核维护的一类通信对象。

从程序员视角看，它常表现为一个整数 fd：

- Linux 下本质上是文件描述符
- 你可以对它 read/write
- 它可以进入 epoll 监听集合

这也是为什么网络编程和文件 IO、事件驱动模型会天然连在一起。

---

## 2.2 常见 socket 类型

### 1）流式 socket：`SOCK_STREAM`
通常对应 TCP。
特点：

- 面向连接
- 可靠传输
- 字节流

### 2）数据报 socket：`SOCK_DGRAM`
通常对应 UDP。
特点：

- 无连接
- 面向报文
- 不保证可靠

### 先记住一句
> 面试里如果没特别说明，网络编程大多数默认在聊 **TCP 服务端编程**。

---

# 3. 一段最小可理解的 TCP 服务端代码

下面这段代码不是生产级代码，但它很适合你第一次建立整体印象。

```cpp
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <iostream>

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) {
        std::cerr << "socket failed\n";
        return 1;
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    if (bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0) {
        std::cerr << "bind failed\n";
        close(listen_fd);
        return 1;
    }

    if (listen(listen_fd, 128) < 0) {
        std::cerr << "listen failed\n";
        close(listen_fd);
        return 1;
    }

    std::cout << "server listening on 8080\n";

    sockaddr_in client_addr{};
    socklen_t client_len = sizeof(client_addr);
    int conn_fd = accept(listen_fd, reinterpret_cast<sockaddr*>(&client_addr), &client_len);
    if (conn_fd < 0) {
        std::cerr << "accept failed\n";
        close(listen_fd);
        return 1;
    }

    char buf[1024] = {0};
    ssize_t n = recv(conn_fd, buf, sizeof(buf) - 1, 0);
    if (n > 0) {
        std::cout << "received: " << buf << "\n";
        const char* resp = "hello from server\n";
        send(conn_fd, resp, std::strlen(resp), 0);
    }

    close(conn_fd);
    close(listen_fd);
    return 0;
}
```

---

## 3.1 这段代码每一步在干嘛？

### `socket(AF_INET, SOCK_STREAM, 0)`
- `AF_INET`：IPv4
- `SOCK_STREAM`：流式 socket，通常就是 TCP
- 返回一个 fd

### `bind(...)`
把这个 socket 绑定到某个地址和端口上。

### `listen(...)`
告诉内核：

- 这是一个监听 socket
- 你可以开始接收连接请求了

### `accept(...)`
从监听 socket 上取出一个“已经建立好的连接”。

要特别注意：

- `listen_fd` 是监听用的
- `conn_fd` 是和具体客户端通信用的

面试里这是个很基础但容易混的点。

### `recv(...)`
从连接里读数据。

### `send(...)`
往连接里写数据。

### `close(...)`
关闭 fd，释放资源。

---

# 4. 为什么服务端要有两个 fd：listen_fd 和 conn_fd？

这是初学者很容易糊掉的点。

## 4.1 listen_fd 是“门口”
它只负责：

- 接受新的连接请求
- 不直接承载具体业务收发

## 4.2 conn_fd 是“客人进门后的专属会话”
一个客户端连接建立后，内核会返回一个新的连接 fd：

- 这个 fd 才用于 `recv/send`
- 一个客户端对应一个连接 fd

### 类比一下
- `listen_fd`：饭店大门
- `conn_fd`：某一桌客人的包厢

你不能拿饭店大门直接给某一桌上菜。

---

# 5. 客户端最小代码示例

```cpp
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <iostream>

int main() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return 1;
    }

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    if (connect(fd, reinterpret_cast<sockaddr*>(&server_addr), sizeof(server_addr)) < 0) {
        std::cerr << "connect failed\n";
        close(fd);
        return 1;
    }

    const char* msg = "hello server\n";
    send(fd, msg, std::strlen(msg), 0);

    char buf[1024] = {0};
    ssize_t n = recv(fd, buf, sizeof(buf) - 1, 0);
    if (n > 0) {
        std::cout << "response: " << buf;
    }

    close(fd);
    return 0;
}
```

---

# 6. 只会写这个最小示例，为什么还远远不够？

因为真实服务端会遇到下面这些问题：

1. 不止一个客户端
2. 客户端不会刚好一次把完整消息发完
3. 连接可能随时断掉
4. 你不能一个连接傻等一个线程
5. 读写可能返回一部分，不是一次完成
6. 你要处理超时、心跳、背压、异常关闭

所以最小示例只是“会打电话”，不是“会做通信系统”。

---

# 7. 阻塞 IO 到底有什么问题？

## 7.1 什么叫阻塞？
如果你调用 `recv()`，但数据还没到，线程会卡住等数据。

这就是阻塞。

## 7.2 阻塞最直观的问题
如果服务端这么写：

```cpp
while (true) {
    int conn_fd = accept(listen_fd, ...);
    recv(conn_fd, buf, ...);  // 卡住
    process();
    send(conn_fd, ...);
}
```

那么：

- 当前客户端没发完，线程就卡住
- 其他客户端即使来了，也处理不到

这在单连接示例里没问题，
但在多连接服务端里会非常差。

---

# 8. 最朴素的多连接办法：一连接一线程

## 8.1 思路
每来一个连接，就开一个线程专门服务它。

```cpp
while (true) {
    int conn_fd = accept(listen_fd, ...);
    std::thread([conn_fd]() {
        char buf[1024];
        while (true) {
            ssize_t n = recv(conn_fd, buf, sizeof(buf), 0);
            if (n <= 0) break;
            send(conn_fd, buf, n, 0);
        }
        close(conn_fd);
    }).detach();
}
```

## 8.2 这种模型为什么早期常见？
因为：

- 写起来简单
- 思维直观
- 每个连接像一段同步逻辑

## 8.3 为什么高并发下不行？
因为线程不是免费的：

- 线程栈占内存
- 线程切换有成本
- 连接很多时线程数爆炸
- 大量连接其实多数时间不活跃，线程在空等

### 面试里的经典一句
> 一连接一线程的问题，不在于“功能不对”，而在于“资源模型太差”。

---

# 9. 非阻塞 socket 是什么？

## 9.1 核心理解
非阻塞不是“数据自动来了你不用管”，而是：

> 这次调用如果做不了，不要把线程挂住，立刻返回给我。

比如对一个非阻塞 socket 调 `recv()`：

- 如果当前没数据
- 不会一直卡住
- 而是返回 `-1`，并设置 `errno = EAGAIN` 或 `EWOULDBLOCK`

---

## 9.2 怎么设置非阻塞？

```cpp
#include <fcntl.h>

int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

这通常会对：

- 监听 fd
- 已连接 fd

都做非阻塞设置。

---

## 9.3 非阻塞为什么不是异步？
这个特别爱考。

### 非阻塞
- 你来问
- 没准备好就立刻返回
- 你之后还得自己再来问

### 异步
- 你把任务交出去
- 底层自己完成
- 完成后通知你

所以：

> 非阻塞只是“不等”，不代表“整个 IO 过程都由内核替你做完”。

---

# 10. 光有非阻塞为什么还不够？

因为如果你这么写：

```cpp
while (true) {
    ssize_t n = recv(fd, buf, sizeof(buf), 0);
    if (n < 0 && errno == EAGAIN) {
        continue;
    }
}
```

这会变成忙等：

- CPU 白白空转
- 不断轮询
- 很浪费

所以我们真正需要的是：

> **当 socket 真正“有事可做”时，再通知我。**

这就是 IO 多路复用要解决的事。

---

# 11. select / poll / epoll 到底在帮什么忙？

它们的共同目标是：

> 让一个线程可以同时关注多个 fd，谁准备好了就处理谁。

### 也就是说
不是线程傻等某一个连接，
而是线程在等“事件”。

这些事件最常见是：

- 可读
- 可写
- 异常
- 对端关闭

---

# 12. 为什么 epoll 这么重要？

在 Linux 高并发服务端里，最常见的组合就是：

- 非阻塞 socket
- epoll
- 事件循环
- 线程池 / Reactor 架构

原因很简单：

- 连接数很多
- 活跃连接只占一部分
- 不想每次全量扫描所有 fd

所以 epoll 很适合这种：

- “连接很多”
- “真正活跃的少数连接触发事件”

---

# 13. epoll 的核心 API

## 13.1 `epoll_create1`
创建一个 epoll 实例。

```cpp
int epfd = epoll_create1(0);
```

## 13.2 `epoll_ctl`
向 epoll 注册、修改、删除 fd。

```cpp
epoll_event ev{};
ev.events = EPOLLIN;
ev.data.fd = listen_fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);
```

## 13.3 `epoll_wait`
等待就绪事件。

```cpp
epoll_event events[1024];
int n = epoll_wait(epfd, events, 1024, -1);
```

返回后：

- `events[i]` 里就是就绪事件
- 你只处理这些有事的 fd

---

# 14. 一个最小 epoll 服务端框架

```cpp
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <iostream>

int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    listen(listen_fd, 128);
    set_nonblocking(listen_fd);

    int epfd = epoll_create1(0);

    epoll_event ev{};
    ev.events = EPOLLIN;
    ev.data.fd = listen_fd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    epoll_event events[1024];

    while (true) {
        int n = epoll_wait(epfd, events, 1024, -1);
        for (int i = 0; i < n; ++i) {
            int fd = events[i].data.fd;

            if (fd == listen_fd) {
                while (true) {
                    sockaddr_in client_addr{};
                    socklen_t len = sizeof(client_addr);
                    int conn_fd = accept(listen_fd, reinterpret_cast<sockaddr*>(&client_addr), &len);
                    if (conn_fd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        break;
                    }

                    set_nonblocking(conn_fd);
                    epoll_event client_ev{};
                    client_ev.events = EPOLLIN;
                    client_ev.data.fd = conn_fd;
                    epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &client_ev);
                }
            } else {
                char buf[1024];
                while (true) {
                    ssize_t cnt = recv(fd, buf, sizeof(buf), 0);
                    if (cnt > 0) {
                        send(fd, buf, cnt, 0); // echo
                    } else if (cnt == 0) {
                        close(fd);
                        epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                        break;
                    } else {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        close(fd);
                        epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                        break;
                    }
                }
            }
        }
    }
}
```

---

# 15. 这段 epoll 代码的关键理解点

## 15.1 为什么监听 fd 和连接 fd 都要进 epoll？
- 监听 fd：有新连接到来时可读
- 连接 fd：有业务数据到来时可读

## 15.2 为什么 `accept` 要循环？
因为一次监听事件可能不止一个连接到来。
如果是非阻塞模式，通常要一直 `accept` 到：

- 返回 `EAGAIN`

这意味着“目前接收队列已经取空”。

## 15.3 为什么 `recv` 也常要循环？
同理，一次可读事件可能缓冲区里不止一点数据。
通常也要反复读到：

- 返回 `EAGAIN`

尤其在 ET 模式下更重要。

---

# 16. LT 和 ET 到底怎么理解？

## 16.1 LT：水平触发
只要 fd 还处于可读/可写状态，就会持续通知。

优点：

- 不容易漏处理
- 对初学者更友好

缺点：

- 可能有重复通知

## 16.2 ET：边沿触发
只有状态从“不可读”变成“可读”这种变化发生时，才通知一次。

优点：

- 事件通知更精简

缺点：

- 更容易写错
- 你必须一次尽量把数据读干净/写干净

---

## 16.3 初学者应该怎么选？

如果你是刚上手：

> **先用 LT 把整体流程写明白。**

因为 ET 最大的坑是：

- 你以为读了一次就够了
- 其实缓冲区还有数据
- 但后面不一定再提醒你
- 然后你程序就“假死”了

### 面试里比较稳的回答
> LT 更稳、更容易写对；ET 更强调减少重复通知，但要求使用者把非阻塞读写循环处理得更完整。

---

# 17. 为什么 TCP 网络编程一定会讲“粘包 / 拆包 / 半包”？

因为 TCP 是**字节流**。

它不保留你业务层“一条消息”的边界。

比如发送端：
```cpp
send(fd, "hello", 5, 0);
send(fd, "world", 5, 0);
```

接收端可能会收到：

- 一次收到 `helloworld`
- 或先收到 `hel`
- 再收到 `loworld`

所以你不能把一次 `recv()` 当作“一条完整消息”。

---

# 18. 业务层协议怎么设计消息边界？

最常见有三种思路：

## 18.1 固定长度
每条消息固定大小。

优点：

- 简单

缺点：

- 不灵活
- 容易浪费空间

## 18.2 分隔符
比如每条消息以 `\n` 结尾。

优点：

- 文本协议直观

缺点：

- 要考虑消息内容里出现分隔符
- 要考虑转义

## 18.3 长度字段 + 消息体
最常见。

比如协议头里有 4 字节长度字段：

- 先读头
- 得到 body 长度
- 再读满 body

### 这才是工程里最常见的做法
因为它既灵活，又适合二进制协议。

---

# 19. 一个长度字段协议的接收思路示例

假设协议：

- 前 4 字节：消息体长度（网络字节序）
- 后面 N 字节：消息体

伪代码：

```cpp
std::vector<char> inbuf;

void onReadable(int fd) {
    char tmp[4096];
    while (true) {
        ssize_t n = recv(fd, tmp, sizeof(tmp), 0);
        if (n > 0) {
            inbuf.insert(inbuf.end(), tmp, tmp + n);
        } else if (n == 0) {
            // 对端关闭
            close(fd);
            return;
        } else {
            if (errno == EAGAIN) break;
            close(fd);
            return;
        }
    }

    while (true) {
        if (inbuf.size() < 4) break;

        uint32_t len = 0;
        std::memcpy(&len, inbuf.data(), 4);
        len = ntohl(len);

        if (inbuf.size() < 4 + len) break;

        std::string msg(inbuf.begin() + 4, inbuf.begin() + 4 + len);
        handleMessage(msg);
        inbuf.erase(inbuf.begin(), inbuf.begin() + 4 + len);
    }
}
```

---

## 19.1 这里面体现了什么核心思想？

### 1）一次 `recv` 不等于一条消息
先把收到的字节放进输入缓冲区。

### 2）协议解析和 socket 读写是两层事
- socket 层只负责搬字节
- 协议层负责从字节里切消息

### 3）要允许“半包”存在
如果头到了，body 没到齐，先缓存，等下次可读再继续。

### 4）要允许“一次读出多条包”
不能只解析一条就结束，要循环解析直到缓冲区不足以构成完整消息。

### 面试高分句
> 网络编程里要把“收字节”和“解消息”分开看，输入缓冲区就是两者之间的桥梁。

---

# 20. send 也不是永远一次发完，这点很多人会漏

## 20.1 常见误区
很多人默认：
```cpp
send(fd, buf, len, 0);
```
就一定把 `len` 个字节全发出去了。

其实不一定。

尤其：

- 非阻塞 socket
- 发送缓冲区满
- 大包发送

都可能只发出一部分。

---

## 20.2 发送部分成功怎么办？
你要记录“还没发完的部分”，下次 socket 可写时继续发。

伪代码：

```cpp
struct Conn {
    std::string outbuf;
};

void sendMessage(int fd, Conn& conn, const std::string& msg) {
    conn.outbuf += msg;
    tryFlush(fd, conn);
}

void tryFlush(int fd, Conn& conn) {
    while (!conn.outbuf.empty()) {
        ssize_t n = send(fd, conn.outbuf.data(), conn.outbuf.size(), 0);
        if (n > 0) {
            conn.outbuf.erase(0, n);
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                // 等待下次 EPOLLOUT
                break;
            }
            close(fd);
            break;
        }
    }
}
```

---

# 21. 什么是背压（backpressure）？为什么很重要？

背压就是：

> 下游来不及收，你不能还无限往里塞。

在网络编程里典型表现为：

- 对方处理慢
- 内核发送缓冲区满
- 你的应用层待发送队列越来越长

如果你不控制：

- 内存暴涨
- 延迟越来越大
- 最后整个服务被拖死

### 常见处理方式
- 每连接设置发送缓冲上限
- 超限后断开连接或丢弃低优先级消息
- 做限流
- 拒绝继续接收上游数据

### 面试一句话
> 高并发网络服务不只是“能收能发”，还要有能力在对方慢的时候控制自己别被拖死。

---

# 22. 长连接到底带来了什么好处和什么问题？

## 22.1 好处
- 减少频繁建连/断连开销
- 降低 RTT 成本
- 更适合高频请求
- 支持实时双向通信

## 22.2 问题
- 连接长期占用 fd
- 需要心跳和空闲连接清理
- 需要处理半开连接
- 负载均衡更复杂
- 连接上下文占内存

### 所以面试里不要只说长连接好
更稳的说法是：

> 长连接用空间和连接管理复杂度，换取时延和握手成本上的收益。

---

# 23. 心跳机制为什么存在？

因为长连接场景下，连接可能“表面还在，实际上已经不可靠”。

比如：

- NAT 超时
- 中间设备断开
- 对端程序异常退出
- 网络半开

如果只靠“等下一次业务请求时再发现”，可能太晚。

所以常见做法是：

- 定期发 ping / heartbeat
- 超过若干周期收不到 pong / 响应，就认为连接失效
- 主动清理连接

---

# 24. 超时管理一般怎么做？

网络服务端常见几类超时：

- 建连超时
- 读超时
- 写超时
- 空闲超时
- 心跳超时

### 常见实现思路
- 每个连接记录最后活跃时间
- 定时扫描超时连接
- 或时间轮 / 最小堆管理超时任务

### 面试里别答太死
不一定非得实现时间轮，重点是你要知道：

> 长连接服务必须有超时清理机制，否则连接资源会慢慢被僵尸连接吃掉。

---

# 25. 网络编程为什么总爱和 Reactor 一起讲？

因为 Reactor 非常适合描述这种模式：

1. 事件来了（可读/可写/新连接）
2. 事件分发器发现谁有事
3. 调对应 handler 去处理

### 对应到 epoll 模型
- epoll：事件通知器
- event loop：事件循环
- handler：读回调、写回调、连接回调

所以很多 C++ 网络库本质上就是：

- 非阻塞 socket
- epoll
- Reactor
- 回调/事件驱动

---

# 26. 一个比较现实的 C++ 网络服务结构长什么样？

一个常见结构是：

## 26.1 主线程 / IO 线程负责
- accept 新连接
- epoll_wait 拿事件
- 收发数据
- 协议编解码

## 26.2 业务线程池负责
- 比较重的业务逻辑
- 数据库访问
- 缓存访问
- RPC 调用

### 为什么这样分工？
因为 IO 线程应该尽量轻：

- 快收
- 快发
- 快分发
- 不要被重逻辑卡住

### 一句话总结
> epoll 线程负责“把事件接住”，线程池负责“把活干完”。

---

# 27. 为什么高并发服务端常用“epoll + 线程池”，而不是“一连接一线程”？

这是高频面试题。

## 标准回答
因为大量连接场景下，连接数和活跃度通常不匹配。多数连接很多时候是空闲的，如果为每个连接都绑定一个线程，会造成大量线程资源浪费和上下文切换开销。`epoll + 线程池` 可以让少量线程管理大量连接，并把真正耗时的业务处理交给工作线程执行。

## 更像面试现场的展开
- 网络连接很多，但真正活跃的连接通常只占一部分
- IO 等待不是 CPU 计算，不值得一连接绑一个线程去傻等
- epoll 可以让一个线程管理很多连接的就绪事件
- 业务线程池处理真正的计算和阻塞型任务
- 这样资源利用率和可扩展性更好

---

# 28. accept、recv、send、close 这几个点各有什么常见坑？

## 28.1 accept 的坑
- 一次事件不止一个新连接
- 非阻塞时要循环 accept 到 `EAGAIN`
- 文件描述符耗尽时要有保护意识

## 28.2 recv 的坑
- 返回 >0 不代表完整消息
- 返回 0 表示对端关闭连接
- 返回 -1 需要看 `errno`
- 非阻塞下 `EAGAIN` 不算错误

## 28.3 send 的坑
- 不保证一次全发完
- 非阻塞下可能 `EAGAIN`
- 需要发送缓冲区与继续发送逻辑

## 28.4 close 的坑
- 关闭后要从 epoll 中移除/清理状态
- 避免 fd 重用导致逻辑串台
- 注意连接上下文释放时机

---

# 29. Unix Domain Socket 和 TCP Socket 怎么选？

这个也很像网络编程/IPC 交叉题。

## TCP Socket
适合：

- 跨机器通信
- 通用网络模型

## Unix Domain Socket
适合：

- 同机进程通信
- 保留 socket 编程模型
- 不需要完整网络协议栈那套跨机能力

### 面试稳妥回答
> 同机服务间通信如果希望保留 socket 编程接口，同时减少跨机协议栈开销，Unix Domain Socket 往往是很好的选择；跨机则通常选 TCP。

---

# 30. 网络字节序为什么会被问？

因为不同机器 CPU 可能字节序不同。

网络协议通常统一使用**大端序**作为网络字节序。

所以常见转换函数：

- `htons`：host to network short
- `htonl`：host to network long
- `ntohs`
- `ntohl`

### 为什么面试会问这个？
因为这代表你是否知道：

> 网络传输不只是“传数字”，还要保证跨机器解释一致。

---

# 31. socket 编程里还常见哪些基础名词？

## backlog
`listen(fd, backlog)` 里的 backlog 通常可粗略理解为“连接排队容量相关参数”。

面试里不必抠内核细节到极致，但要知道：

- 它和服务端连接接纳能力有关
- 太小可能在高峰时丢连接/拒连接更明显

## SO_REUSEADDR
常见用于让服务端重启后更容易重新绑定端口。

## keepalive
内核级保活机制，用于探测长时间无数据交互的连接是否还活着。

### 注意
应用层心跳和 TCP keepalive 不是一回事：

- keepalive 更底层、周期通常较长
- 应用层心跳更灵活、能携带业务语义

---

# 32. 一个更贴近面试的“聊天室服务器”思考题

如果让你设计一个简化聊天室服务端，至少要考虑：

1. 多客户端并发接入
2. 长连接
3. 收到一条消息后广播给其他人
4. 用户突然断线
5. 某个客户端很慢，广播时不能把全局拖死
6. 消息边界怎么切
7. 心跳怎么做
8. 在线用户表怎么维护

### 这题想考什么？
其实不只是考 socket API，更多是在考：

- 连接管理
- 协议设计
- 广播策略
- 慢连接治理
- 线程模型

这也是为什么网络编程最终会走向系统设计题。

---

# 33. 一个从 0 上手的学习路线

如果你之前完全没做过网络编程，我建议按这个顺序来：

## 第 1 步：先会写最小 TCP client/server
目标：

- 理解 `socket/bind/listen/accept/connect/send/recv/close`
- 能在本机跑通

## 第 2 步：理解 TCP 字节流
目标：

- 明白为什么会粘包拆包
- 自己实现一个“长度字段 + body”的协议解析器

## 第 3 步：理解阻塞与非阻塞
目标：

- 知道 `EAGAIN` 是什么
- 知道一次收发不一定完成

## 第 4 步：理解 epoll 模型
目标：

- 能说清 `epoll_create / epoll_ctl / epoll_wait`
- 能写一个 echo server

## 第 5 步：理解事件驱动架构
目标：

- 知道 Reactor 是什么
- 知道 IO 线程和业务线程怎么分工

## 第 6 步：补长连接工程问题
目标：

- 心跳
- 超时
- 慢连接
- 背压
- 连接清理

## 第 7 步：整理成面试答案
目标：

- 能从“最小流程”讲到“高并发服务设计”

---

# 34. Boost.Asio / Asio：C++ 网络库里绕不开的名字

## 34.1 Asio 是什么？

Asio 是 C++ 里最主流的跨平台异步 IO 库之一。

- **Boost.Asio**：Boost 库的一部分，历史最久、用户最多
- **独立版 Asio**：不依赖 Boost 也能用（`asio` standalone）
- Asio 的核心设计者 Christopher Kohlhoff 同时也是 C++ 标准网络提案的主要推动者

### 一句话定位
> Asio 把底层的 socket、epoll（Linux）/ kqueue（macOS）/ IOCP（Windows）封装成统一的异步编程模型，让你不用直接和系统调用打交道。

---

## 34.2 Asio 和裸 epoll 是什么关系？

你可以这么理解：

| 层级 | 你自己写 | 用 Asio |
|------|---------|---------|
| socket 创建 | `socket()` | `tcp::socket` |
| 非阻塞设置 | `fcntl(O_NONBLOCK)` | Asio 内部自动处理 |
| 事件注册 | `epoll_ctl` | `async_read` / `async_write` |
| 事件循环 | `while(epoll_wait(...))` | `io_context::run()` |
| 回调分发 | 自己 `switch(fd)` | Asio 自动调你的回调/handler |

### 也就是说
Asio 帮你把前面 20 多节讲的那些"裸 epoll + 非阻塞 + 事件循环 + 缓冲区管理"封装好了。

但底层机制是一样的：

- Linux 下 Asio 内部就是 epoll
- macOS 下是 kqueue
- Windows 下是 IOCP

### 面试里该说的
> Asio 不是一种新的 IO 模型，而是对操作系统异步 IO 机制的跨平台封装。理解了 epoll + Reactor 之后再看 Asio，会发现它只是把你自己会写的那套事件驱动包装成了更易用的接口。

---

## 34.3 Asio 的核心概念

### 1）`io_context`（旧版叫 `io_service`）
事件循环的核心。相当于你自己写的那个 `while(epoll_wait(...))` 循环。

```cpp
asio::io_context io;
// ... 注册各种异步操作 ...
io.run();  // 开始事件循环，阻塞在这里
```

### 2）`tcp::acceptor`
相当于 `listen_fd`。

```cpp
asio::ip::tcp::acceptor acceptor(io, {asio::ip::tcp::v4(), 8080});
```

### 3）`tcp::socket`
相当于 `conn_fd`。

```cpp
asio::ip::tcp::socket sock(io);
acceptor.async_accept(sock, [](const auto& ec) {
    // 新连接回调
});
```

### 4）`async_read` / `async_write`
相当于你用 epoll 注册 `EPOLLIN/EPOLLOUT` 再在回调里 `recv/send`。

```cpp
asio::async_read(sock, asio::buffer(buf, len),
    [](const auto& ec, std::size_t bytes) {
        // 读完成回调
    });
```

### 5）`strand`
用于在多线程 `io_context` 下保证某些回调不被并发执行，相当于轻量级串行化。

---

## 34.4 一个最小 Asio echo server 示例

```cpp
// echo_asio.cpp
// 编译：g++ -std=c++17 -o echo_asio echo_asio.cpp -lpthread
// 如果用 Boost.Asio：加 -lboost_system
// 如果用独立 Asio：加 -DASIO_STANDALONE
#include <asio.hpp>
#include <iostream>
#include <memory>

using asio::ip::tcp;

class Session : public std::enable_shared_from_this<Session> {
public:
    explicit Session(tcp::socket sock) : socket_(std::move(sock)) {}

    void start() { doRead(); }

private:
    void doRead() {
        auto self = shared_from_this();
        socket_.async_read_some(asio::buffer(buf_, sizeof(buf_)),
            [this, self](const asio::error_code& ec, std::size_t n) {
                if (!ec && n > 0) {
                    doWrite(n);
                }
                // ec 或 n==0 时 Session 自动析构（shared_ptr 引用归零）
            });
    }

    void doWrite(std::size_t len) {
        auto self = shared_from_this();
        asio::async_write(socket_, asio::buffer(buf_, len),
            [this, self](const asio::error_code& ec, std::size_t) {
                if (!ec) {
                    doRead();  // 写完继续读
                }
            });
    }

    tcp::socket socket_;
    char buf_[4096];
};

class Server {
public:
    Server(asio::io_context& io, uint16_t port)
        : acceptor_(io, {tcp::v4(), port}) {
        doAccept();
    }

private:
    void doAccept() {
        acceptor_.async_accept(
            [this](const asio::error_code& ec, tcp::socket sock) {
                if (!ec) {
                    std::make_shared<Session>(std::move(sock))->start();
                }
                doAccept();  // 继续等下一个连接
            });
    }

    tcp::acceptor acceptor_;
};

int main() {
    asio::io_context io;
    Server server(io, 8080);
    std::cout << "asio echo server listening on :8080\n";
    io.run();
    return 0;
}
```

---

## 34.5 这段代码和裸 epoll 版的对比

| 你在裸 epoll 版里做的事 | Asio 里谁帮你做了 |
|------------------------|------------------|
| `socket() + bind() + listen()` | `tcp::acceptor` 构造函数 |
| `setNonBlocking()` | Asio 内部自动设置 |
| `epoll_create + epoll_ctl` | Asio 内部自动管理 |
| `while(epoll_wait(...))` | `io_context::run()` |
| `accept()` 循环 | `async_accept` + 回调 |
| `recv()` 循环 + EAGAIN 处理 | `async_read_some` + 回调 |
| `send()` + 发送缓冲区 + EPOLLOUT | `async_write` + 回调 |
| 连接上下文管理（`unordered_map`） | `shared_ptr<Session>` 生命周期 |

### 核心感受
> 用 Asio 写网络服务，代码量大概是裸 epoll 的 1/3 到 1/5，而且自动跨平台。

---

## 34.6 Asio 的异步模型：Proactor 还是 Reactor？

这是面试偶尔会问的进阶点。

### Asio 的设计更接近 Proactor
- 你发起一个异步操作（比如 `async_read`）
- 底层帮你完成 IO
- 完成后回调你

### 但在 Linux 上
Linux 内核并没有真正的 Proactor 式异步 IO（`io_uring` 之前）。

所以 Asio 在 Linux 上的实现是：

- 底层用 epoll（Reactor 风格）
- 但在 API 层封装成 Proactor 风格

### 面试稳妥回答
> Asio 的编程接口是 Proactor 风格：你发起异步操作，完成后收到回调。但在 Linux 下它的底层实现仍然是基于 epoll 的 Reactor 模型，只是在库层面做了 Proactor 的包装。

---

## 34.7 Asio 里的 `shared_ptr` 生命周期管理

这是 Asio 代码里最常见的模式，也是初学者最容易搞不懂的点。

### 为什么 Session 要继承 `enable_shared_from_this`？

因为异步回调是"发起操作后过一段时间才调用"的。

如果你不持有 Session 的引用：

- 回调还没来
- Session 对象已经析构了
- 回调触发时访问已释放内存 → 崩溃

所以常见做法：

1. Session 继承 `enable_shared_from_this`
2. 每次发起异步操作时，capture `shared_from_this()`
3. 只要还有未完成的异步操作，Session 就不会被析构

### 这就是为什么你会看到这种写法
```cpp
auto self = shared_from_this();
socket_.async_read_some(..., [this, self](...) { ... });
```

`self` 保证了"只要这个回调还没执行，Session 就活着"。

### 面试里怎么说
> Asio 的异步回调模型下，连接对象的生命周期通常用 `shared_ptr` 管理：只要还有未完成的异步操作持有引用，连接对象就不会被析构。这比手动管理 fd 和连接上下文更安全，但要注意避免循环引用。

---

## 34.8 Asio 的多线程模型

### 单线程
最简单：一个线程调 `io.run()`。
所有回调都在这个线程里串行执行。

### 多线程
多个线程同时调 `io.run()`：
```cpp
std::vector<std::thread> threads;
for (int i = 0; i < 4; ++i) {
    threads.emplace_back([&io]() { io.run(); });
}
```

这时回调可能在不同线程并发执行。
如果同一个连接的读写回调被并发调用，就需要同步。

### `strand`：Asio 的串行化工具
```cpp
asio::strand<asio::io_context::executor_type> strand(io.get_executor());
asio::async_read(sock, buf, asio::bind_executor(strand, handler));
```

`strand` 保证绑定到它的回调不会并发执行，即使多线程环境下也是串行的。

### 面试一句话
> Asio 多线程模型下，`strand` 用于保证同一个连接的回调不被并发调用，避免加锁。

---

## 34.9 Asio 和其他 C++ 网络库的关系

| 库 | 特点 | 和 Asio 的关系 |
|---|------|---------------|
| **Boost.Asio** | 最主流、最成熟 | Asio 的 Boost 版本 |
| **独立 Asio** | 不依赖 Boost | 同一个作者，API 几乎一样 |
| **muduo** | 陈硕写的教学级网络库 | Reactor 风格，裸 epoll，风格和 Asio 不同 |
| **libevent / libev** | C 语言事件库 | 更底层，不如 Asio 面向对象 |
| **gRPC C++** | Google 的 RPC 框架 | 底层用了类似 Asio 的异步思路 |
| **C++ 标准网络提案** | 未来可能进标准 | 基于 Asio 的设计 |

### 面试里如果被问"你了解哪些 C++ 网络库"
可以说：

> 我了解 Boost.Asio，它是 C++ 里最主流的异步 IO 库，底层在 Linux 上基于 epoll，API 是 Proactor 风格。另外也知道 muduo 是国内比较流行的教学级 Reactor 网络库。

---

## 34.10 面试里 Asio 相关的典型问题

### 问：Asio 的 io_context 是什么？
> 它是 Asio 的事件循环核心，相当于自己写 epoll 时的 `while(epoll_wait(...))` 主循环。调用 `io.run()` 后，它会不断从内部事件队列中取出就绪事件并执行对应回调。

### 问：Asio 是 Reactor 还是 Proactor？
> API 层面是 Proactor：你发起异步操作，完成后收到回调。但在 Linux 下底层实现基于 epoll，本质上是 Reactor + 库层 Proactor 包装。

### 问：为什么 Session 要用 shared_ptr？
> 因为异步回调可能在未来某个时刻才执行，必须保证回调触发时 Session 对象仍然存活。用 `shared_ptr` + `shared_from_this()` 可以让未完成的异步操作持有 Session 引用，防止提前析构。

### 问：多线程下怎么保证安全？
> 用 `strand`。它保证绑定到同一个 `strand` 的回调串行执行，即使 `io_context` 在多个线程上运行。

### 问：你觉得用 Asio 和自己写 epoll 各有什么好处？
> 自己写 epoll 对底层机制理解更深，适合学习和极致性能调优；Asio 开发效率更高、跨平台、生命周期管理更安全，适合工程项目。两者不矛盾，理解了底层再用 Asio 会更清楚它在帮你做什么。

---

# 35. 一组很典型的面试追问链

1. socket 编程的基本流程是什么？
2. 服务端为什么要有 listen fd 和 conn fd？
3. 阻塞 socket 有什么问题？
4. 一连接一线程为什么不适合高并发？
5. 非阻塞 socket 是什么？为什么非阻塞不等于异步？
6. epoll 在解决什么问题？
7. LT 和 ET 区别？为什么 ET 容易写错？
8. 为什么 `recv` 一次不等于一条完整消息？
9. 粘包拆包怎么处理？
10. 为什么 `send` 也可能只发一部分？
11. 什么是背压？慢连接怎么处理？
12. 长连接为什么需要心跳和超时清理？
13. 为什么高并发服务端常用 epoll + 线程池？
14. Unix Domain Socket 和 TCP Socket 怎么选？

如果你能把这 14 个问题接住，网络编程这一块就已经比很多校招候选人强很多了。

---

# 36. 一份更像面试现场的总结回答

> 网络编程本质上是在用操作系统提供的 socket 接口，让两个进程通过网络或本机通信。对 TCP 服务端来说，基本流程是 socket、bind、listen、accept、recv、send、close。真正的难点不在于把最小 demo 写出来，而在于多连接场景下如何高效、稳定地管理连接和数据流。阻塞模型虽然简单，但在大量连接下资源利用率很差，所以工程上通常会用非阻塞 socket 配合 epoll 做事件驱动。再往上，还要处理 TCP 字节流带来的粘包拆包、发送不完整、长连接心跳、超时清理、慢连接和背压等问题。高并发 C++ 网络服务常见的整体方案，就是 epoll + Reactor + 线程池：IO 线程负责接住事件和收发数据，业务线程负责执行重逻辑。这套回答链既能覆盖从 0 上手，也能接住面试里的深入追问。

---

# 37. 复习建议：你应该至少掌握到什么程度？

如果你目标是“能接受面试拷打”，至少做到：

## 入门必须会
- socket 编程基本流程
- 服务端 listen fd / conn fd 区别
- 阻塞 / 非阻塞区别
- `recv == 0` 的含义
- `EAGAIN` 是什么

## 进阶必须会
- epoll 的核心作用
- LT / ET 区别
- 粘包拆包原因与处理
- 输入缓冲区 / 输出缓冲区思路
- 长连接为什么要心跳和超时

## 面试加分会更强
- 背压和慢连接治理
- Reactor 思想
- epoll + 线程池分工
- Unix Domain Socket vs TCP Socket
- keepalive 和应用层心跳区别
- Asio 的 io_context / Proactor 包装 / shared_ptr 生命周期
- Asio 和裸 epoll 的关系

---

# 38. 你现在可以怎么练？

给你一个最实用的练习顺序：

1. 自己手打一遍最小 TCP server/client
2. 把 server 改成 echo server
3. 给协议加上“4 字节长度头 + body”
4. 把阻塞版改成非阻塞 + epoll 版
5. 给每个连接加输入缓冲区和输出缓冲区
6. 再补心跳、超时和慢连接处理思路

如果你真把这 6 步做过一遍，哪怕项目经验不多，面试里这一块也会明显更稳。

---

# 39. 和现有章节怎么串起来？

这一章建议和下面几篇一起看：

- `03_computer_network/01_tcp_udp_http.md`
  - 看 TCP 字节流、粘包拆包、三次握手、长连接基础
- `03_computer_network/02_http_details.md`
  - 看长连接、WebSocket、HTTP 层语义
- `02_operating_system/02_io_multiplexing.md`
  - 看 epoll、Reactor、零拷贝
- `05_design_patterns_architecture/01_patterns_architecture.md`
  - 看高并发系统线程模型和架构分层

这样你就能把：

- 协议
- 系统调用
- IO 模型
- 工程架构

四条线真正串起来。