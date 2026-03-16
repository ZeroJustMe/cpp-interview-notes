# 02. 项目出发的八股文题

> 大厂面试官通常不会凭空考八股，而是顺着项目往深处追问底层原理。  
> 以下题目全部从简历项目的技术关键词出发，分为 **C++ 核心**、**操作系统**、**计算机网络**、**数据库** 四大板块。  
> 每题包含：起手问 → 简答思路 → 追问方向 → 📎 repo 内链接。  
> 最后一节 **项目结合扩展** 专门讲"如何把八股知识点应用到自己的项目上"。

---

# 一、C++ 核心

## Q1. 无锁队列与内存序（← SPSC 队列矩阵）

**起手问：** 你项目里用了 SPSC 无锁队列，讲讲无锁编程的核心原理。

> **简答思路：** 无锁编程的核心是用原子操作（CAS / load-store + memory order）替代锁来保证并发安全。SPSC 场景只需 acquire/release 语义：生产者 `store(release)` 写入数据后更新写指针，消费者 `load(acquire)` 读写指针后读取数据，保证"数据写入 happens-before 数据被消费"。  
> 📎 [并发编程 · 原子操作与内存序](../cpp_interview_notes/01_cpp_language/04_cpp_concurrency.md)

**追问方向：**

1. `std::atomic` 的六种内存序（`relaxed` / `acquire` / `release` / `acq_rel` / `seq_cst` / `consume`）分别是什么语义？你的 SPSC 队列用了哪几种？为什么？
2. x86 的 TSO（Total Store Order）模型下，`acquire/release` 和 `seq_cst` 的实际开销差异有多大？
3. 什么是 false sharing？怎么避免？你的队列里有做 cache line padding 吗？
4. CAS（compare-and-swap）操作在 ABA 问题中的表现？你的场景需要处理 ABA 吗？
5. 无锁 vs. 有锁在什么负载下性能会反转？你怎么判断一个场景适不适合无锁？

---

## Q2. 线程模型与上下文切换（← 多核并行算子 / Subtask 模型）

**起手问：** 你的并行算子基于运行时 Subtask 模型，线程是怎么管理的？

> **简答思路：** 每个 Subtask 是一个逻辑执行单元，由线程池中的工作线程调度执行。线程数通常设为 CPU 核数（CPU 密集型场景），通过 `sched_setaffinity` 绑核减少跨 NUMA 访问和上下文切换。上下文切换的开销主要来自寄存器保存/恢复、TLB flush 和 cache 污染。  
> 📎 [进程 · 线程 · 内存](../cpp_interview_notes/02_operating_system/01_process_thread_memory.md)

**追问方向：**

1. 用户态线程（协程）和内核态线程的区别？你的 Subtask 模型更接近哪一种？
2. 上下文切换的开销主要包括哪些（寄存器保存/恢复、TLB flush、cache 污染）？
3. Linux 调度器 CFS 的原理？`nice` 值和 `sched_setaffinity` 你用过吗？
4. 线程池的常见实现方式？如何确定线程数——CPU 密集型 vs. I/O 密集型的不同策略？
5. 线程 vs. 进程的选择依据？仿真器里各模块选进程还是线程、为什么？

---

## Q3. 智能指针与对象生命周期（← PyBind11 封装 / C++ 组件设计）

**起手问：** 你在 PyBind11 封装中怎么处理 C++ 和 Python 的对象生命周期？

> **简答思路：** PyBind11 默认用 `unique_ptr` 持有 C++ 对象，但跨语言共享时需要用 `shared_ptr` holder——Python 侧持有一个 `shared_ptr`，C++ 侧也可以持有 `shared_ptr`，引用计数归零时才析构。循环引用通过 `weak_ptr` 或 Python 侧的弱引用打破。  
> 📎 [值类别 · 移动语义 · 智能指针](../cpp_interview_notes/01_cpp_language/02_value_categories_move_smartptr.md)

**追问方向：**

1. `unique_ptr`、`shared_ptr`、`weak_ptr` 的区别？引用计数的线程安全怎么保证？
2. `shared_ptr` 的控制块（control block）内存布局是什么样的？`make_shared` 和直接 `shared_ptr(new T)` 有什么区别？
3. 循环引用怎么检测和解决？你在项目中遇到过吗？
4. `shared_ptr` 的自定义删除器（deleter）和分配器（allocator）怎么用？
5. Python 的 GC（引用计数 + 分代回收）和 C++ 的 RAII 有什么互操作问题？

---

## Q4. 模板与编译期多态（← 工厂模式 / 插件化体系 / BaseMethod 接口）

**起手问：** 你的插件体系用了虚函数多态，为什么不用模板（编译期多态）？

> **简答思路：** 插件化需要运行时根据配置决定使用哪种 Join 策略，这只能用虚函数（运行期多态）。模板在编译期实例化，无法做到运行时切换。但在性能热点路径（如距离计算），可以用 CRTP 或模板特化做编译期分派避免虚调用开销。  
> 📎 [模板元编程](../cpp_interview_notes/01_cpp_language/08_templates_metaprogramming.md) · [STL · 模板 · 编译链接](../cpp_interview_notes/01_cpp_language/03_stl_template_compile.md)

**追问方向：**

1. 虚函数的实现原理（vtable / vptr）？虚调用的开销有多大？
2. CRTP 是什么？怎么用它实现编译期多态？和虚函数的性能差异？
3. `std::variant` + `std::visit` 作为运行期多态的替代方案，你了解吗？
4. 模板导致编译膨胀怎么处理？`extern template` 怎么用？

---

## Q5. 内存管理与分配器（← 高性能流计算 / 无锁队列）

**起手问：** 你的流处理引擎在内存管理上有什么特殊考虑？

> **简答思路：** 流式场景下数据持续流入流出，频繁 malloc/free 会导致碎片化和性能抖动。SPSC 队列用预分配的环形缓冲区避免运行时分配；窗口内的向量数据使用内存池（arena allocator）批量分配，窗口过期时整块回收，避免逐对象 free。  
> 📎 [内存管理与 Allocator](../cpp_interview_notes/01_cpp_language/07_memory_management_allocator.md)

**追问方向：**

1. `malloc` 的底层实现（ptmalloc / jemalloc / tcmalloc）？它们在多线程场景下的区别？
2. 内存池（memory pool / arena）的设计思路？你的项目里具体怎么实现的？
3. placement new 是什么？在内存池中怎么用？
4. 内存碎片的类型（内部碎片 vs 外部碎片）？你的场景容易出现哪种？
5. RAII 和智能指针怎么和自定义分配器配合？

---

## Q6. STL 容器选型（← 各项目中的数据结构选择）

**起手问：** 你项目中频繁用到的 STL 容器有哪些？选型的依据是什么？

> **简答思路：** 索引分区路由用 `unordered_map`（O(1) 查找），有序合并用 `map`/`priority_queue`，窗口数据用 `deque`（两端高效插入删除），算子配置用 `vector`（连续内存、cache 友好）。选型核心考虑：访问模式（随机/顺序）、插入删除频率、cache 亲和性。  
> 📎 [STL 容器深入](../cpp_interview_notes/01_cpp_language/05_stl_containers_deep_dive.md)

**追问方向：**

1. `vector` 的扩容策略？`reserve` 和 `resize` 的区别？移动语义对扩容的影响？
2. `unordered_map` 的哈希冲突解决方式？负载因子和 rehash 的时机？
3. `map`（红黑树）vs. `unordered_map`（哈希表）的性能对比？什么时候选 `map`？
4. `deque` 的内存布局？为什么它能两端 O(1) 插入？
5. 容器的迭代器失效规则？你踩过什么坑？

---

# 二、操作系统

## Q7. I/O 多路复用（← 仿真器通信 / 流式数据接入）

**起手问：** 你的仿真器和中间件之间大量使用 socket 通信，讲讲 I/O 多路复用。

> **简答思路：** select/poll/epoll 都是让一个线程同时监听多个 fd 的就绪事件。epoll 使用红黑树管理 fd 和就绪列表，只返回就绪的 fd（O(就绪数) 而非 O(总fd数)），适合大量连接但活跃连接少的场景。仿真器模块间通信如果走 socket，epoll 是首选。  
> 📎 [IO 多路复用](../cpp_interview_notes/02_operating_system/02_io_multiplexing.md)

**追问方向：**

1. select / poll / epoll 的区别？各自的 fd 上限和性能特征？
2. epoll 的 LT（水平触发）和 ET（边缘触发）的区别？ET 模式下为什么必须用非阻塞 I/O？
3. Reactor 和 Proactor 模式的区别？你的项目更接近哪种？
4. `epoll_wait` 返回后具体怎么处理？工作线程模型怎么组织？

---

## Q8. 虚拟内存与页表（← GPU 内存管理 / 大规模向量数据）

**起手问：** 你处理的向量数据规模很大，讲讲虚拟内存的原理。

> **简答思路：** 虚拟内存通过页表将进程的虚拟地址映射到物理页框，MMU 硬件负责翻译。TLB 缓存频繁访问的页表项以加速。大规模向量数据时要注意：数据可能超出物理内存，触发 page fault 走磁盘换页，会导致延迟尖刺——所以要用 mmap + mlock 或 huge pages 减少 TLB miss。  
> 📎 [进程 · 线程 · 内存](../cpp_interview_notes/02_operating_system/01_process_thread_memory.md)

**追问方向：**

1. 页表的结构？多级页表为什么比单级页表省内存？
2. TLB 的作用和命中率对性能的影响？Huge Pages 为什么能提升性能？
3. `mmap` 的原理和使用场景？和 `read/write` 系统调用的区别？
4. Copy-on-Write 的原理？fork 之后的内存是怎么共享的？
5. NUMA 架构下的内存访问不对称怎么影响你的并行程序？

---

## Q9. 文件系统与 I/O（← 仿真日志 / 索引持久化）

**起手问：** 你的仿真器会产生大量日志，讲讲 Linux 的文件 I/O 模型。

> **简答思路：** Linux 文件 I/O 有缓冲 I/O（经过 Page Cache）和直接 I/O（O_DIRECT 绕过 Page Cache）两种。仿真日志适合缓冲 I/O（写入 Page Cache 后由内核异步刷盘），而索引持久化如果要保证持久性则需要 `fsync` 或直接 I/O。零拷贝技术（sendfile / splice）可以减少日志传输的内存拷贝。  
> 📎 [文件系统与信号](../cpp_interview_notes/02_operating_system/03_linux_filesystem_signals.md) · [IO 多路复用 · 零拷贝](../cpp_interview_notes/02_operating_system/02_io_multiplexing.md)

**追问方向：**

1. Page Cache 的作用？`sync` / `fsync` / `fdatasync` 的区别？
2. 直接 I/O（O_DIRECT）的使用场景？数据库为什么经常用？
3. inode 的结构？一个文件的数据块是怎么组织的？
4. 日志系统的设计：同步写 vs. 异步写、日志轮转、压缩？

---

# 三、计算机网络

## Q10. TCP 三次握手与四次挥手（← 多节点 Stream Join / 分布式通信）

**起手问：** 如果你的 Vector Stream Join 引擎扩展到多节点，节点间通信用 TCP，讲讲 TCP 连接的建立和释放。

> **简答思路：** 三次握手（SYN → SYN-ACK → ACK）建立连接，确保双方的序列号同步。四次挥手（FIN → ACK → FIN → ACK）释放连接，因为 TCP 是全双工，每个方向需要独立关闭。TIME_WAIT 状态持续 2MSL，确保对端收到最后的 ACK。在多节点流计算场景下，大量短连接会导致 TIME_WAIT 堆积，应该使用长连接 + 连接池。  
> 📎 [TCP · UDP · HTTP](../cpp_interview_notes/03_computer_network/01_tcp_udp_http.md)

**追问方向：**

1. 为什么是三次握手而不是两次？
2. TIME_WAIT 状态的作用？大量 TIME_WAIT 怎么处理？`SO_REUSEADDR` / `SO_REUSEPORT` 的区别？
3. TCP 的 Nagle 算法和延迟 ACK 对你的流计算低延迟需求有什么影响？怎么关闭？
4. TCP keepalive 和应用层心跳的区别？你的多节点系统怎么检测节点故障？

---

## Q11. TCP 拥塞控制（← 多节点数据传输 / 高吞吐场景）

**起手问：** 多节点 Stream Join 的节点间数据量很大，讲讲 TCP 的拥塞控制。

> **简答思路：** TCP 拥塞控制核心有四个阶段：慢启动（cwnd 指数增长）→ 拥塞避免（cwnd 线性增长）→ 快重传（3 个 dupACK 立即重传）→ 快恢复（cwnd 减半而非回到 1）。在高带宽数据中心网络中，传统 Cubic 可能收敛太慢，DCTCP / BBR 等算法更适合。流计算场景要关注尾延迟——丢包触发的重传会导致流水线 stall。  
> 📎 [重传与拥塞控制](../cpp_interview_notes/03_computer_network/02_http_details.md)

**追问方向：**

1. 慢启动、拥塞避免、快重传、快恢复四个阶段的 cwnd 变化？
2. Cubic 和 BBR 的区别？数据中心网络适合哪种？
3. 丢包对你的流计算场景有什么影响？如何做应用层的补偿（如缓冲、重排序）？
4. TCP 和 UDP 在你的多节点场景下怎么选型？什么时候考虑 RDMA？

---

## Q12. RPC 框架与序列化（← Pipeline 服务化 / Protobuf 地图重构）

**起手问：** 你的 Pipeline 用了 gRPC，讲讲 RPC 的原理和 Protobuf 的编码。

> **简答思路：** RPC 屏蔽网络细节让远程调用看起来像本地调用，核心组件是服务注册、序列化、传输、反序列化。gRPC 使用 HTTP/2 作为传输层（支持多路复用和头部压缩），Protobuf 作为序列化层（Varint 编码压缩整数，ZigZag 编码处理负数）。与 RESTful HTTP + JSON 相比，gRPC + Protobuf 在带宽和延迟上都有优势。  
> 📎 [RPC · 消息队列 · DNS · CDN](../cpp_interview_notes/03_computer_network/03_rpc_message_queue_dns_cdn.md)

**追问方向：**

1. Protobuf 的 Varint 编码怎么工作？ZigZag 编码解决了什么问题？
2. Protobuf vs. FlatBuffers vs. Cap'n Proto 的区别？
3. gRPC 的四种调用模式（Unary / Server-streaming / Client-streaming / Bidirectional）各适合什么场景？
4. Protobuf 的 schema 演进规则？字段编号为什么不能复用？
5. HTTP/2 的多路复用和 HTTP/1.1 的 pipeline 有什么本质区别？

---

## Q13. 网络分区与一致性（← 多节点 Stream Join 的容错）

**起手问：** 如果你的 Stream Join 引擎扩展到多节点，网络分区怎么处理？

> **简答思路：** 根据 CAP 定理，网络分区（P）不可避免时，必须在一致性（C）和可用性（A）之间取舍。流计算场景通常选 AP——允许短暂的结果不精确（近似召回），保证服务不中断。分区恢复后通过窗口重放或增量同步修复数据。具体可用 Raft/Paxos 做元数据的强一致，数据流本身走 eventual consistency。  
> 📎 [分布式 · 负载均衡 · 高可用 · CAP 与 BASE](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

**追问方向：**

1. CAP 定理的含义？你的系统在 CAP 中怎么选择？
2. 脑裂问题怎么发生？怎么防护？
3. 分布式一致性协议（Raft / Paxos）的基本原理？在你的场景下用在什么地方？
4. 最终一致性的实现方式有哪些？你的窗口重放属于哪种？

---

## Q14. 长连接管理与连接池（← 多节点通信 / 中间件通信）

**起手问：** 多节点 Stream Join 的节点间通信怎么管理连接？

> **简答思路：** 节点间使用长连接池：启动时预建连接，运行时从池中取连接发送数据帧，发送完归还而非关闭。连接池大小按"每对节点一条数据通道"设计，用心跳检测死连接并自动重连。相比短连接，长连接避免了频繁握手的延迟和 TIME_WAIT 累积。  
> 📎 [长连接与 keep-alive](../cpp_interview_notes/03_computer_network/02_http_details.md) · [TCP · UDP · HTTP](../cpp_interview_notes/03_computer_network/01_tcp_udp_http.md)

**追问方向：**

1. 连接池的基本设计？最大连接数、空闲超时、健康检查怎么配？
2. 多路复用（HTTP/2 / QUIC）和连接池的区别？哪个更适合你的场景？
3. 连接断开时正在传输的数据怎么处理？需要应用层重传吗？
4. 如果节点数量很多（上百个），全连接拓扑的连接数太大怎么办？

---

# 四、数据库

## Q15. Join 算法（← Vector Stream Join 本质就是 Join）

**起手问：** 你做的 Vector Stream Join 和数据库里的 Join 有什么关系？

> **简答思路：** 本质上都是"从两个数据集中找到满足条件的匹配对"。区别在于数据库 Join 的条件是等值或范围谓词，而向量 Join 的条件是"距离小于阈值"。经典 Join 算法（Nested Loop / Hash Join / Sort-Merge Join）的思想可以借鉴：我的空间分区路由类似 Hash Join 的分桶，全局索引+局部索引的合并类似 Sort-Merge 的思路。  
> 📎 [SQL 基础](../cpp_interview_notes/04_database_cache/00_sql_fundamentals.md) · [事务 · 锁 · 索引](../cpp_interview_notes/04_database_cache/02_mysql_transactions_indexes.md)

**追问方向：**

1. Nested Loop Join / Hash Join / Sort-Merge Join 的原理和复杂度？
2. 数据库优化器怎么选择 Join 算法？你的向量 Join 有没有类似的代价估算？
3. Grace Hash Join 用于内存放不下的情况，你处理大规模向量数据时有没有类似的分块策略？
4. Semi Join 和 Anti Join 了解吗？

---

## Q16. 索引原理（← ANNS 索引 / 数据库 B+ 树索引对比）

**起手问：** 你同时用过向量索引和传统数据库索引，对比一下它们的异同。

> **简答思路：** B+ 树索引适合精确匹配和范围查询（有序键），向量索引（HNSW / IVF）适合近似相似度查询（高维空间距离）。B+ 树的查找是确定性的 O(log N)，向量索引是概率性的（召回率 < 100%）。二者都面临动态更新的挑战——B+ 树有页分裂，HNSW 有图结构维护。  
> 📎 [MySQL B+ 树原理](../cpp_interview_notes/04_database_cache/01_mysql_redis.md) · [索引设计与 EXPLAIN](../cpp_interview_notes/04_database_cache/02_mysql_transactions_indexes.md)

**追问方向：**

1. B+ 树为什么比 B 树更适合数据库？叶子节点的链表有什么作用？
2. 聚簇索引和非聚簇索引的区别？回表是什么？
3. 联合索引的最左前缀原则？在你的向量索引场景有没有类似的概念？
4. 索引的维护代价（插入/删除/更新）？B+ 树 vs. HNSW 哪个维护代价更高？

---

## Q17. 事务与隔离级别（← 多节点 Join 的一致性 / 仿真一致性）

**起手问：** 你在仿真一致性和向量 Join 中都提到了"一致性"，讲讲数据库的事务隔离级别。

> **简答思路：** 四种隔离级别：读未提交（脏读）、读已提交（不可重复读）、可重复读（幻读，MySQL 默认）、串行化（完全隔离但性能最差）。MySQL 的 MVCC 通过 undo log + ReadView 实现可重复读，不用加锁就能并发读。这和我项目中的并发索引类似——读操作看到一致性快照（只读全局索引），写操作在局部索引上进行，类似 MVCC 的思想。  
> 📎 [事务与隔离级别](../cpp_interview_notes/04_database_cache/02_mysql_transactions_indexes.md) · [MVCC 与一致性](../cpp_interview_notes/04_database_cache/01_mysql_redis.md)

**追问方向：**

1. MVCC 的实现原理？undo log 和 ReadView 怎么配合？
2. 四种隔离级别分别会出现什么异常（脏读/不可重复读/幻读）？
3. 间隙锁是什么？解决什么问题？
4. 你的双层索引结构和 MVCC 有什么相似之处？

---

## Q18. 缓存架构（← 向量索引的多级缓存 / Redis 相关）

**起手问：** 你的向量索引有多级存储，讲讲缓存的设计原则。

> **简答思路：** 缓存的核心是"热数据放快存储、冷数据放慢存储"。向量索引中，热分区（最近窗口）的索引放内存（甚至 GPU 显存），冷分区索引降级到 SSD。这和 Redis 做缓存的思路一致——Cache Aside 模式：先查缓存，miss 再查数据库，回填缓存。要注意缓存穿透（不存在的 key）、缓存击穿（热 key 过期）和缓存雪崩（大面积过期）。  
> 📎 [MySQL & Redis · 缓存架构模式](../cpp_interview_notes/04_database_cache/01_mysql_redis.md) · [Redis 高可用](../cpp_interview_notes/04_database_cache/03_redis_high_availability.md)

**追问方向：**

1. Cache Aside / Read Through / Write Through / Write Behind 四种缓存模式的区别？
2. 缓存穿透、缓存击穿、缓存雪崩的区别？各自怎么防护？
3. Redis 的内存淘汰策略有哪些？LRU / LFU 的区别？
4. 你的窗口过期驱逐策略和 Redis 的 key 过期策略有什么相似之处？

---

## Q19. LSM-tree 与写优化（← 流式索引更新 / KV 存储）

**起手问：** 流式场景下索引频繁更新，了解 LSM-tree 吗？

> **简答思路：** LSM-tree 将随机写转化为顺序写：数据先写 WAL + MemTable，MemTable 满后 flush 成 SSTable，后台 compaction 合并 SSTable。这种"写入时只追加，后台合并"的思想和我的双层索引很像——新数据先写线程局部索引（类似 MemTable），再定期合并到全局索引（类似 compaction）。  
> 📎 [NoSQL 与 KV 存储 · LSM-tree](../cpp_interview_notes/04_database_cache/04_nosql_kv_storage_principles.md)

**追问方向：**

1. LSM-tree vs. B-tree 在读写性能上的对比？
2. Compaction 策略（Leveled / Tiered / FIFO）的区别？
3. Bloom Filter 在 LSM-tree 中的作用？你的向量索引用了类似的过滤机制吗？
4. Write-Ahead Log（WAL）的原理？在你的流计算场景中需要 WAL 吗？

---

# 五、项目结合扩展

> 以下题目的核心不是单独考某个八股知识点，而是追问"你怎么把这个知识应用到你的项目上"。

## Q20. 如何将 TCP 拥塞控制的思想应用到你的流计算背压机制中？

> **简答思路：** TCP 拥塞控制的核心思想是"感知瓶颈 → 降速 → 恢复"。在流计算中，当下游 Join 算子处理不过来时，SPSC 队列水位上升，上游数据接入算子应该主动降速（类似 cwnd 缩小）。具体实现可以是：监控队列水位，超过高水位线时通知上游暂停读取，低于低水位线时恢复——这就是 Reactive Streams 的背压协议，和 TCP 的流量控制本质相同。  
> 📎 [重传与拥塞控制](../cpp_interview_notes/03_computer_network/02_http_details.md) · [重试、限流、熔断、降级](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

---

## Q21. 你的双层并发索引和数据库的 MVCC 有什么结构上的相似性？

> **简答思路：** MVCC 让读操作看到一致性快照（旧版本），写操作生成新版本，读写不互斥。我的双层索引类似：查询走只读全局索引（快照），新数据写入线程局部索引（增量版本），全局索引在合并时才更新。这避免了查询期间的写阻塞，和 MVCC 的"读不阻塞写、写不阻塞读"思维一致。  
> 📎 [MVCC 与一致性](../cpp_interview_notes/04_database_cache/01_mysql_redis.md)

---

## Q22. 如果要把 Vector Stream Join 扩展为多节点分布式系统，一致性哈希和负载均衡怎么设计？

> **简答思路：** 用一致性哈希将向量空间分区映射到不同节点——每个节点负责一段向量空间的 Join 计算。虚拟节点解决数据倾斜。节点加入/退出时只需迁移相邻分区的数据。负载均衡层面，可以根据各节点的队列水位做动态路由（加权轮询），高负载节点少分配数据。  
> 📎 [负载均衡策略 · 一致性哈希](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

---

## Q23. 你的仿真器模块间同步机制和分布式系统中的 barrier 有什么异同？

> **简答思路：** 本质相同——都是让所有参与方到达某个点后才继续推进。仿真器的同步信号是单机多进程/多线程的 barrier（如 `std::barrier` 或共享内存信号量），分布式 barrier（如 ZooKeeper 的分布式屏障）则跨网络。差异在于分布式 barrier 要处理网络延迟和节点故障，而单机 barrier 只需处理线程/进程的调度延迟。  
> 📎 [并发编程](../cpp_interview_notes/01_cpp_language/04_cpp_concurrency.md) · [分布式 · 高可用](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

---

## Q24. 你的工厂模式插件体系如果要支持多租户（不同租户用不同 Join 策略），数据库和缓存层面怎么设计？

> **简答思路：** 每个租户在配置表（MySQL）中有一行记录其选用的 Join 策略和参数，启动时工厂根据配置创建对应实例。如果策略配置变更频繁，可以加 Redis 缓存配置，监听 MySQL binlog 变更或用 pub/sub 通知各节点刷新。租户间的索引数据物理隔离（不同的内存分区或不同的索引实例），避免相互干扰。  
> 📎 [MySQL & Redis · 缓存架构模式](../cpp_interview_notes/04_database_cache/01_mysql_redis.md) · [设计模式 · 系统设计](../cpp_interview_notes/05_design_patterns_architecture/01_patterns_architecture.md)
