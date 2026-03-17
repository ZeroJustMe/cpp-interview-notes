# 06. 网络编程示例篇：从阻塞到 epoll，一步步敲出来（深挖版）

> 这一章是配合 `05_network_programming_socket_epoll.md` 的**练手篇**。
>

> 目标：
> - 每个示例都能编译运行
> - 从最简单的阻塞模型一直演进到 epoll + 协议解析
> - 每段代码后面都会讲：**这段在做什么、为什么这样做、有什么坑**
>

> 建议你：
> 1. 先看 `05` 那篇理解概念
> 2. 回到这里一段一段敲
> 3. 每敲完一段，再回头对照 `05` 里的解释
>

> 所有代码都是 Linux 下 C++ 风格，编译方式：
> ```bash
> g++ -std=c++17 -o server server.cpp -lpthread
> ```
>

> 测试客户端可以用 `telnet` 或 `nc`：
> ```bash
> nc 127.0.0.1 8080
> ```

---

# 示例 1：最简单的阻塞 TCP Echo Server

## 代码

```cpp
// echo_blocking.cpp
// 最简单的阻塞 echo server：一次只能服务一个客户端
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <iostream>

int main() {
    // 1. 创建监听 socket
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) {
        perror("socket");
        return 1;
    }

    // 允许地址重用，方便重启后立刻绑定
    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 2. 绑定地址
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);  // 监听所有网卡
    addr.sin_port = htons(8080);

    if (bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0) {
        perror("bind");
        close(listen_fd);
        return 1;
    }

    // 3. 开始监听
    if (listen(listen_fd, 128) < 0) {
        perror("listen");
        close(listen_fd);
        return 1;
    }

    std::cout << "blocking echo server listening on :8080\n";

    // 4. 主循环：每次接受一个连接，处理完再接下一个
    while (true) {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);

        // accept 会阻塞，直到有客户端连上来
        int conn_fd = accept(listen_fd,
                             reinterpret_cast<sockaddr*>(&client_addr),
                             &client_len);
        if (conn_fd < 0) {
            perror("accept");
            continue;
        }

        // 打印客户端地址
        char ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, ip, sizeof(ip));
        std::cout << "new connection from " << ip
                  << ":" << ntohs(client_addr.sin_port) << "\n";

        // 5. 循环读写，直到客户端断开
        char buf[1024];
        while (true) {
            ssize_t n = recv(conn_fd, buf, sizeof(buf), 0);
            if (n > 0) {
                // 原样返回
                send(conn_fd, buf, n, 0);
            } else if (n == 0) {
                // 对端正常关闭
                std::cout << "client disconnected\n";
                break;
            } else {
                perror("recv");
                break;
            }
        }

        close(conn_fd);
    }

    close(listen_fd);
    return 0;
}
```

---

## 逐行讲解

### `setsockopt(... SO_REUSEADDR ...)`
这行很重要。如果不加，你 Ctrl+C 停掉 server 后，短时间内再启动会报 `bind: Address already in use`。

原因是上次 `close` 后端口可能还在 `TIME_WAIT` 状态。`SO_REUSEADDR` 允许重新绑定。

### `listen(listen_fd, 128)`
- `128` 是 backlog 参数
- 可以简单理解为"等待被 accept 取走的连接队列容量提示"
- 实际行为受内核限制，不用死记数字

### `accept(...)`
- 阻塞在这里直到有新连接
- 返回的 `conn_fd` 是和这个客户端通信用的新 fd
- `listen_fd` 继续等下一个人

### `recv` 返回值含义
- `> 0`：收到 n 字节
- `== 0`：对端关闭了连接（TCP FIN）
- `< 0`：出错

**`recv == 0` 这个判断很关键，面试经常问。**

### `send(conn_fd, buf, n, 0)`
把收到的数据原样回写。这就是 echo。

---

## 这段代码的致命问题

**一次只能服务一个客户端。**

当第一个客户端连着的时候：

- 第二个客户端虽然能建立 TCP 连接（三次握手由内核完成）
- 但你的代码还在 `recv` 循环里傻等第一个客户端
- 所以第二个客户端的 `accept` 根本没执行

这就是阻塞模型最直接的问题。

---

## 怎么测试？

### 终端 1：启动 server
```bash
g++ -std=c++17 -o echo_blocking echo_blocking.cpp
./echo_blocking
```

### 终端 2：用 nc 连接
```bash
nc 127.0.0.1 8080
hello
```
你输入 `hello`，会收到 `hello`。

### 终端 3：再开一个 nc
```bash
nc 127.0.0.1 8080
```
这个连接建立了（TCP 层面），但你输入的内容不会有回应——因为 server 还在处理第一个连接。

等你断开终端 2，终端 3 的内容才会开始被处理。

---

# 示例 2：多线程 Echo Server

## 代码

```cpp
// echo_multithread.cpp
// 每个连接一个线程，能同时服务多个客户端
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <iostream>
#include <thread>

void handleClient(int conn_fd, sockaddr_in client_addr) {
    char ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &client_addr.sin_addr, ip, sizeof(ip));
    std::cout << "[thread " << std::this_thread::get_id()
              << "] serving " << ip << ":" << ntohs(client_addr.sin_port) << "\n";

    char buf[1024];
    while (true) {
        ssize_t n = recv(conn_fd, buf, sizeof(buf), 0);
        if (n > 0) {
            send(conn_fd, buf, n, 0);
        } else if (n == 0) {
            std::cout << "[thread " << std::this_thread::get_id()
                      << "] client disconnected\n";
            break;
        } else {
            perror("recv");
            break;
        }
    }

    close(conn_fd);
}

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    listen(listen_fd, 128);

    std::cout << "multithread echo server listening on :8080\n";

    while (true) {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);
        int conn_fd = accept(listen_fd,
                             reinterpret_cast<sockaddr*>(&client_addr),
                             &client_len);
        if (conn_fd < 0) {
            perror("accept");
            continue;
        }

        // 每个连接开一个新线程
        std::thread(handleClient, conn_fd, client_addr).detach();
    }

    close(listen_fd);
    return 0;
}
```

---

## 和示例 1 的区别

### 核心改动：一行
```cpp
std::thread(handleClient, conn_fd, client_addr).detach();
```

`accept` 返回后，不再由主线程直接处理这个连接，而是丢给新线程。

这样主线程可以立刻回到 `accept` 等下一个连接。

---

## 这个模型为什么也有问题？

### 问题 1：线程数不可控
100 个连接 = 100 个线程。
10000 个连接 = 10000 个线程。

线程不是免费的：

- 每个线程默认栈 8MB（Linux）
- 10000 个线程光栈就 80GB
- 实际不会真占那么多物理内存，但虚拟地址空间和调度成本是真的

### 问题 2：大量线程切换浪费
很多连接其实大部分时间是空闲的。
它们的线程就在那干等 `recv`，什么也不做，但切换和调度开销白白浪费。

### 问题 3：线程创建/销毁开销
`std::thread(...).detach()` 每次都创建新线程。
频繁创建销毁开销也不小。

---

## 面试里怎么说？

> 多线程模型在连接数不大时可以工作，但高并发场景下线程资源消耗和上下文切换成本会成为主要瓶颈。所以需要更轻量的事件驱动模型。

---

# 示例 3：epoll Echo Server（LT 模式）

## 代码

```cpp
// echo_epoll_lt.cpp
// 非阻塞 + epoll LT 模式的 echo server
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <iostream>

void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    listen(listen_fd, 128);
    setNonBlocking(listen_fd);

    // 创建 epoll 实例
    int epfd = epoll_create1(0);

    // 把监听 fd 加入 epoll
    epoll_event ev{};
    ev.events = EPOLLIN;  // LT 模式：只要可读就通知
    ev.data.fd = listen_fd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    constexpr int MAX_EVENTS = 1024;
    epoll_event events[MAX_EVENTS];

    std::cout << "epoll LT echo server listening on :8080\n";

    while (true) {
        // 等待事件，-1 表示无限等待
        int nready = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (int i = 0; i < nready; ++i) {
            int fd = events[i].data.fd;

            // ---- 情况 1：监听 fd 可读 → 有新连接 ----
            if (fd == listen_fd) {
                // LT 模式下可以只 accept 一次
                // 但循环 accept 更稳妥（一次可能有多个连接到来）
                while (true) {
                    sockaddr_in client_addr{};
                    socklen_t len = sizeof(client_addr);
                    int conn_fd = accept(listen_fd,
                                         reinterpret_cast<sockaddr*>(&client_addr),
                                         &len);
                    if (conn_fd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) {
                            break;  // 当前没有更多新连接了
                        }
                        perror("accept");
                        break;
                    }

                    setNonBlocking(conn_fd);

                    epoll_event client_ev{};
                    client_ev.events = EPOLLIN;
                    client_ev.data.fd = conn_fd;
                    epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &client_ev);

                    char ip[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &client_addr.sin_addr, ip, sizeof(ip));
                    std::cout << "new connection: " << ip
                              << ":" << ntohs(client_addr.sin_port)
                              << " fd=" << conn_fd << "\n";
                }
            }
            // ---- 情况 2：连接 fd 可读 → 有数据 ----
            else {
                char buf[4096];
                ssize_t n = recv(fd, buf, sizeof(buf), 0);
                if (n > 0) {
                    // echo 回去
                    send(fd, buf, n, 0);
                } else if (n == 0) {
                    // 对端关闭
                    std::cout << "fd=" << fd << " disconnected\n";
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                    close(fd);
                } else {
                    if (errno != EAGAIN && errno != EWOULDBLOCK) {
                        perror("recv");
                        epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                        close(fd);
                    }
                    // EAGAIN 在 LT 模式下：没事，下次还会通知
                }
            }
        }
    }

    close(listen_fd);
    close(epfd);
    return 0;
}
```

---

## 和多线程版比，变了什么？

### 不再一连接一线程
整个程序只有**一个线程**在处理所有连接。

### 靠 epoll 发现"谁有事做"
- `epoll_wait` 会阻塞
- 但不是等某一个 fd
- 而是等"任意一个 fd 有事"

### 只处理有事件的 fd
而不是像 select 那样扫描全部。

---

## LT 模式下的几个要点

### 1）为什么 `recv` 这里我只读了一次？
因为 LT 模式下，如果缓冲区里还有数据没读完，下一次 `epoll_wait` 还会告诉你这个 fd 可读。

所以 LT 模式对于初学者更安全：

- 你每次不一定要把数据全读完
- 下次还会通知你

### 2）但 `accept` 那里我还是循环了
因为多个连接可能几乎同时到来，一次事件里 `accept` 一次可能不够。
循环 accept 到 `EAGAIN` 更稳妥。

### 3）关闭连接时别忘记从 epoll 删除
```cpp
epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
close(fd);
```
顺序：先删再关。否则有些场景下可能出问题。

---

# 示例 4：epoll Echo Server（ET 模式）

## 代码

```cpp
// echo_epoll_et.cpp
// 非阻塞 + epoll ET 模式的 echo server
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <iostream>

void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    listen(listen_fd, 128);
    setNonBlocking(listen_fd);

    int epfd = epoll_create1(0);

    epoll_event ev{};
    ev.events = EPOLLIN | EPOLLET;  // ← 关键：加了 EPOLLET
    ev.data.fd = listen_fd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    constexpr int MAX_EVENTS = 1024;
    epoll_event events[MAX_EVENTS];

    std::cout << "epoll ET echo server listening on :8080\n";

    while (true) {
        int nready = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (int i = 0; i < nready; ++i) {
            int fd = events[i].data.fd;

            if (fd == listen_fd) {
                // ET 模式：必须循环 accept 到 EAGAIN
                while (true) {
                    sockaddr_in client_addr{};
                    socklen_t len = sizeof(client_addr);
                    int conn_fd = accept(listen_fd,
                                         reinterpret_cast<sockaddr*>(&client_addr),
                                         &len);
                    if (conn_fd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        perror("accept");
                        break;
                    }

                    setNonBlocking(conn_fd);

                    epoll_event client_ev{};
                    client_ev.events = EPOLLIN | EPOLLET;  // 连接 fd 也用 ET
                    client_ev.data.fd = conn_fd;
                    epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &client_ev);

                    char ip[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &client_addr.sin_addr, ip, sizeof(ip));
                    std::cout << "new connection: " << ip
                              << ":" << ntohs(client_addr.sin_port)
                              << " fd=" << conn_fd << "\n";
                }
            } else {
                // ET 模式：必须循环 recv 到 EAGAIN
                char buf[4096];
                while (true) {
                    ssize_t n = recv(fd, buf, sizeof(buf), 0);
                    if (n > 0) {
                        // echo
                        // 注意：send 这里也可能只发出一部分
                        // 简化版先忽略，后面示例会处理
                        send(fd, buf, n, 0);
                    } else if (n == 0) {
                        std::cout << "fd=" << fd << " disconnected\n";
                        epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                        close(fd);
                        break;
                    } else {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) {
                            // 读完了，正常退出循环
                            break;
                        }
                        // 其他错误
                        perror("recv");
                        epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
                        close(fd);
                        break;
                    }
                }
            }
        }
    }

    close(listen_fd);
    close(epfd);
    return 0;
}
```

---

## 和 LT 版的关键差异

### 差异 1：注册事件时加了 `EPOLLET`
```cpp
ev.events = EPOLLIN | EPOLLET;
```

### 差异 2：recv 必须循环到 EAGAIN
在 ET 模式下，一次可读通知只来一次。
如果你只读了一部分就退出：

- 剩下的数据还在缓冲区
- 但 epoll 不会再通知你
- 你的程序就"假死"了

所以 ET 模式下的铁律：

> **读到 `EAGAIN`，写到 `EAGAIN`。**

### 差异 3：accept 也必须循环
同理，一次通知可能有多个新连接，不循环就可能漏。

---

## 一个经典 ET 模式 bug

假设你这么写：
```cpp
// 错误写法！
ssize_t n = recv(fd, buf, sizeof(buf), 0);
if (n > 0) {
    send(fd, buf, n, 0);
}
```

只读了一次。

如果客户端发了 8000 字节，但你 buf 只有 4096：

- 第一次读了 4096
- 还剩 4096 在缓冲区
- ET 模式下不会再通知
- 客户端永远收不到后半段的 echo

**所以 ET 模式下一定要循环读写。**

---

# 示例 5：带长度头的协议解析器

前面几个 echo server 都是"收到什么转发什么"，不关心消息边界。
但真实服务端一定要关心"一条消息从哪到哪"。

## 协议定义

```
+-------------------+---------------------+
|  4 字节长度头     |   N 字节消息体       |
|  (网络字节序)     |   (任意内容)         |
+-------------------+---------------------+
```

- 先读 4 字节，得到 N
- 再读 N 字节，得到完整消息

---

## 代码：每连接一个 Buffer 的协议解析

```cpp
// echo_protocol.cpp
// 带长度头协议的 epoll echo server
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>

void setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

// 每个连接的状态
struct Connection {
    std::vector<char> inbuf;   // 输入缓冲区
    std::string outbuf;        // 输出缓冲区（待发送）
};

// 全局连接表
std::unordered_map<int, Connection> conns;

// 构造一条带长度头的消息
std::string packMessage(const std::string& body) {
    uint32_t len = htonl(static_cast<uint32_t>(body.size()));
    std::string pkt(reinterpret_cast<const char*>(&len), 4);
    pkt += body;
    return pkt;
}

// 尝试从输入缓冲区里解析完整消息
void processInbuf(int fd) {
    auto& conn = conns[fd];

    while (true) {
        // 头部还没到齐
        if (conn.inbuf.size() < 4) break;

        // 读长度
        uint32_t body_len = 0;
        std::memcpy(&body_len, conn.inbuf.data(), 4);
        body_len = ntohl(body_len);

        // 防御：消息体不能超过合理范围（防大包攻击）
        if (body_len > 10 * 1024 * 1024) {
            std::cerr << "fd=" << fd << " message too large: " << body_len << "\n";
            // 关闭连接
            conns.erase(fd);
            epoll_ctl(3, EPOLL_CTL_DEL, fd, nullptr); // epfd 硬编码仅为简化
            close(fd);
            return;
        }

        // body 还没到齐
        if (conn.inbuf.size() < 4 + body_len) break;

        // 提取完整消息
        std::string msg(conn.inbuf.begin() + 4,
                        conn.inbuf.begin() + 4 + body_len);

        // 从缓冲区移除已解析部分
        conn.inbuf.erase(conn.inbuf.begin(),
                         conn.inbuf.begin() + 4 + body_len);

        // 业务处理：echo
        std::cout << "fd=" << fd << " msg(" << msg.size() << "): " << msg << "\n";

        // 把回复打包放进输出缓冲区
        conn.outbuf += packMessage("echo: " + msg);
    }
}

// 尝试把输出缓冲区的数据发出去
void tryFlush(int fd, int epfd) {
    auto it = conns.find(fd);
    if (it == conns.end()) return;
    auto& conn = it->second;

    while (!conn.outbuf.empty()) {
        ssize_t n = send(fd, conn.outbuf.data(), conn.outbuf.size(), 0);
        if (n > 0) {
            conn.outbuf.erase(0, n);
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                // 发送缓冲区满了，注册 EPOLLOUT 等下次可写
                epoll_event ev{};
                ev.events = EPOLLIN | EPOLLOUT | EPOLLET;
                ev.data.fd = fd;
                epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);
                return;
            }
            // 其他错误
            perror("send");
            conns.erase(fd);
            epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
            close(fd);
            return;
        }
    }

    // 全部发完，取消 EPOLLOUT 关注
    epoll_event ev{};
    ev.events = EPOLLIN | EPOLLET;
    ev.data.fd = fd;
    epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);
}

void closeConn(int fd, int epfd) {
    conns.erase(fd);
    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);
    close(fd);
    std::cout << "fd=" << fd << " closed\n";
}

int main() {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(8080);

    bind(listen_fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    listen(listen_fd, 128);
    setNonBlocking(listen_fd);

    int epfd = epoll_create1(0);

    epoll_event ev{};
    ev.events = EPOLLIN | EPOLLET;
    ev.data.fd = listen_fd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    constexpr int MAX_EVENTS = 1024;
    epoll_event events[MAX_EVENTS];

    std::cout << "protocol echo server listening on :8080\n";

    while (true) {
        int nready = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (int i = 0; i < nready; ++i) {
            int fd = events[i].data.fd;
            uint32_t ev_flags = events[i].events;

            // ---- 新连接 ----
            if (fd == listen_fd) {
                while (true) {
                    sockaddr_in client_addr{};
                    socklen_t len = sizeof(client_addr);
                    int conn_fd = accept(listen_fd,
                                         reinterpret_cast<sockaddr*>(&client_addr),
                                         &len);
                    if (conn_fd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        perror("accept");
                        break;
                    }

                    setNonBlocking(conn_fd);
                    conns[conn_fd] = Connection{};

                    epoll_event client_ev{};
                    client_ev.events = EPOLLIN | EPOLLET;
                    client_ev.data.fd = conn_fd;
                    epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &client_ev);

                    std::cout << "new connection fd=" << conn_fd << "\n";
                }
                continue;
            }

            // ---- 连接异常 ----
            if (ev_flags & (EPOLLERR | EPOLLHUP)) {
                closeConn(fd, epfd);
                continue;
            }

            // ---- 可读 ----
            if (ev_flags & EPOLLIN) {
                auto it = conns.find(fd);
                if (it == conns.end()) continue;

                char buf[4096];
                bool closed = false;
                while (true) {
                    ssize_t n = recv(fd, buf, sizeof(buf), 0);
                    if (n > 0) {
                        it->second.inbuf.insert(it->second.inbuf.end(),
                                                buf, buf + n);
                    } else if (n == 0) {
                        closeConn(fd, epfd);
                        closed = true;
                        break;
                    } else {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        closeConn(fd, epfd);
                        closed = true;
                        break;
                    }
                }

                if (!closed) {
                    processInbuf(fd);
                    tryFlush(fd, epfd);
                }
            }

            // ---- 可写 ----
            if (ev_flags & EPOLLOUT) {
                tryFlush(fd, epfd);
            }
        }
    }

    close(listen_fd);
    close(epfd);
    return 0;
}
```

---

## 这段代码体现了哪些核心思想？

### 1）每连接一个输入缓冲区
`recv` 只负责把字节搬进 `inbuf`，不管消息边界。

### 2）协议解析和 IO 分离
`processInbuf` 从缓冲区里按"4 字节头 + body"切消息。
它不关心 socket 层的事。

### 3）处理半包
如果头到了但 body 还没到齐，直接 `break` 等下次数据来。

### 4）处理粘包
一次 `recv` 可能收了好几条消息，所以 `processInbuf` 里是 `while` 循环。

### 5）输出缓冲区 + EPOLLOUT
`send` 不一定一次发完。发不完就先存着，注册 `EPOLLOUT`，等内核告诉你"可以继续写了"再接着发。

### 6）大包防御
```cpp
if (body_len > 10 * 1024 * 1024) { ... }
```
如果客户端声称要发 10GB 的消息，你不能真的去分配那么大内存。

---

## 如何用自己写的客户端测试？

```cpp
// test_client.cpp
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <iostream>
#include <string>

void sendMessage(int fd, const std::string& msg) {
    uint32_t len = htonl(static_cast<uint32_t>(msg.size()));
    send(fd, &len, 4, 0);
    send(fd, msg.data(), msg.size(), 0);
}

std::string recvMessage(int fd) {
    uint32_t len = 0;
    // 简化版：假设能一次读完头（生产代码不能这么假设）
    recv(fd, &len, 4, MSG_WAITALL);
    len = ntohl(len);

    std::string body(len, '\0');
    recv(fd, body.data(), len, MSG_WAITALL);
    return body;
}

int main() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);

    connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));

    sendMessage(fd, "hello server");
    std::cout << "response: " << recvMessage(fd) << "\n";

    sendMessage(fd, "this is a test");
    std::cout << "response: " << recvMessage(fd) << "\n";

    sendMessage(fd, "goodbye");
    std::cout << "response: " << recvMessage(fd) << "\n";

    close(fd);
    return 0;
}
```

---

# 示例 6：简化版心跳与超时清理

在长连接服务端里，你必须清理"不再活跃"的连接。不然 fd 和内存会慢慢被僵尸连接吃掉。

## 思路
- 每个连接记录最后一次活跃时间
- 定期扫描所有连接
- 超过阈值未活跃就关掉

---

## 代码片段（加到示例 5 的 Connection 结构上）

```cpp
#include <chrono>

struct Connection {
    std::vector<char> inbuf;
    std::string outbuf;
    std::chrono::steady_clock::time_point last_active;
};

// 每次 accept 新连接时：
conns[conn_fd] = Connection{{}, {}, std::chrono::steady_clock::now()};

// 每次 recv 到数据时更新：
it->second.last_active = std::chrono::steady_clock::now();
```

---

## 定时扫描（主循环中加超时检查）

```cpp
// 在 epoll_wait 之后加一个扫描
auto now = std::chrono::steady_clock::now();
std::vector<int> to_close;
for (auto& [fd, conn] : conns) {
    auto idle = std::chrono::duration_cast<std::chrono::seconds>(
        now - conn.last_active).count();
    if (idle > 60) {  // 60 秒无活动就清理
        to_close.push_back(fd);
    }
}
for (int fd : to_close) {
    std::cout << "fd=" << fd << " idle timeout, closing\n";
    closeConn(fd, epfd);
}
```

---

## 更优的方式：用 `epoll_wait` 超时配合

把 `epoll_wait(epfd, events, MAX_EVENTS, -1)` 改成：
```cpp
int nready = epoll_wait(epfd, events, MAX_EVENTS, 5000); // 5秒超时
```

这样：

- 有事件就立刻返回处理
- 5 秒没事件也返回一次
- 此时你就可以做超时扫描

---

## 面试里怎么回答心跳和超时？

> 长连接服务端必须有超时清理机制。常见做法是记录每个连接的最后活跃时间，定期扫描超时连接并主动关闭。更成熟的方案会用时间轮或最小堆来降低扫描开销。心跳通常是应用层周期性发送的探活消息，和 TCP keepalive 是不同层级的机制。

---

# 示例 7：慢连接和发送队列限制

## 问题：如果某个客户端一直不 recv，会怎样？

你的 `send` 会先进内核发送缓冲区。
内核缓冲区满了以后，非阻塞 `send` 返回 `EAGAIN`。
你的应用层 `outbuf` 就会越积越多。

如果不加限制：

- 每个慢连接的 `outbuf` 可能无限增长
- 最后整个服务被 OOM 杀掉

---

## 解决：给每连接发送缓冲区设上限

```cpp
constexpr size_t MAX_OUTBUF = 1024 * 1024;  // 1MB

void tryFlush(int fd, int epfd) {
    auto it = conns.find(fd);
    if (it == conns.end()) return;
    auto& conn = it->second;

    // 检查发送缓冲区是否超限
    if (conn.outbuf.size() > MAX_OUTBUF) {
        std::cerr << "fd=" << fd << " outbuf overflow, closing\n";
        closeConn(fd, epfd);
        return;
    }

    while (!conn.outbuf.empty()) {
        ssize_t n = send(fd, conn.outbuf.data(), conn.outbuf.size(), 0);
        if (n > 0) {
            conn.outbuf.erase(0, n);
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                epoll_event ev{};
                ev.events = EPOLLIN | EPOLLOUT | EPOLLET;
                ev.data.fd = fd;
                epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);
                return;
            }
            closeConn(fd, epfd);
            return;
        }
    }

    epoll_event ev{};
    ev.events = EPOLLIN | EPOLLET;
    ev.data.fd = fd;
    epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);
}
```

---

## 面试一句话
> 背压控制的核心是：当下游收不动时，上游要有能力限制自己的发送队列，而不是无限堆积。

---

# 示例 8：常见错误集锦

## 错误 1：忘记设置非阻塞

```cpp
int conn_fd = accept(listen_fd, ...);
// 忘记 setNonBlocking(conn_fd) ←
epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &ev);
```

后果：

- ET 模式下 `recv` 可能阻塞
- 卡住整个事件循环
- 其他所有连接都不动了

---

## 错误 2：ET 模式下只读一次

```cpp
// 错误！
ssize_t n = recv(fd, buf, sizeof(buf), 0);
if (n > 0) {
    send(fd, buf, n, 0);
}
```

后果：

- 缓冲区没读完
- 后续不再通知
- 客户端以为服务端死了

---

## 错误 3：close 之后 fd 被复用

```cpp
close(fd);
// ... 后续又有新连接 accept 返回了同一个 fd 数字 ...
// 此时如果 conns[fd] 还残留旧数据，就会逻辑串台
```

所以关闭连接时要：

1. 从 epoll 删除
2. 从 conns 表删除
3. 然后 close

---

## 错误 4：send 返回值不检查

```cpp
send(fd, buf, len, 0);
// 假设一定全发完了 ←
```

后果：

- 非阻塞下可能只发了一部分
- 剩余的数据丢了
- 客户端收到截断消息

---

## 错误 5：不检查 recv == 0

```cpp
ssize_t n = recv(fd, buf, sizeof(buf), 0);
if (n > 0) {
    // 处理
}
// 缺少 n == 0 的判断 ←
```

后果：

- 对端关闭后你不知道
- 继续往这个 fd 写会得到 SIGPIPE
- 默认行为是进程直接终止

防御：

- 检查 `n == 0` 并关闭
- 或者 `signal(SIGPIPE, SIG_IGN)` 忽略 SIGPIPE

---

# 整体演进路线总结

```
示例 1：阻塞 echo server
  ↓ 问题：一次只能服务一个客户端
示例 2：多线程 echo server
  ↓ 问题：线程资源不可控，大量空闲连接浪费
示例 3：epoll LT echo server
  ↓ 优化：一个线程管理所有连接
示例 4：epoll ET echo server
  ↓ 优化：减少重复通知，但要循环读写
示例 5：带协议解析的 epoll server
  ↓ 真实服务端必须有消息边界、输入缓冲区、输出缓冲区
示例 6：心跳和超时清理
  ↓ 长连接必须有连接生命周期管理
示例 7：慢连接和背压
  ↓ 不能让慢客户端拖死整个服务
示例 8：常见错误集锦
  ↓ 知道哪些坑最容易踩
```

这条线从"能跑"一直走到"能在面试里讲明白为什么这样设计"。

---

# 面试里这些示例怎么用？

你不需要在面试里手写完整代码。

但你需要能说清楚：

1. "我理解 TCP 服务端的基本流程是 socket / bind / listen / accept / recv / send / close。"
2. "我知道阻塞模型的局限性在于一个线程只能等一个连接。"
3. "我知道多线程模型的瓶颈在于线程资源消耗。"
4. "我理解 epoll 的核心价值是让一个线程高效管理大量连接。"
5. "我知道 ET 和 LT 的区别，ET 要循环读写到 EAGAIN。"
6. "我知道 TCP 是字节流，需要应用层协议设计消息边界。"
7. "我知道长连接需要心跳和超时清理。"
8. "我知道要做背压控制，防止慢连接把服务拖死。"

如果你能把这 8 句话展开，每句话后面能接住 1-2 轮追问，网络编程这一块在校招里已经非常够了。

---

# 和仓库其他章节的关系

| 本章内容 | 关联章节 |
|---------|---------|
| socket 基础、TCP 字节流 | `03/01_tcp_udp_http.md` |
| 非阻塞、epoll、Reactor | `02/02_io_multiplexing.md` |
| 长连接、心跳 | `03/02_http_details.md` |
| 高并发架构、线程模型 | `05/01_patterns_architecture.md` |
| 协议设计概念 | `05/05_network_programming_socket_epoll.md` |

建议先看 `05` 概念篇，再回这里敲代码，最后对照上面这些章节串着复习。