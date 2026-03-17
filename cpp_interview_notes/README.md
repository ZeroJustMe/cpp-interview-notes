# C++ 面试八股知识库（持续深挖版）

这不是一份“只列关键词”的八股清单，而是一套朝着**可经受面试官追问**方向持续演化的 C++ 面试知识库。

目标覆盖：

- C++ 语言本体
- STL / 模板 / 对象模型 / 内存管理 / 并发
- 操作系统
- 计算机网络
- MySQL / Redis / 缓存一致性
- 设计模式 / 高并发架构 / 项目排障
- 数据结构与算法
- 按岗位区分的复习路径

---

## 这套笔记现在按什么逻辑重构

这套笔记不再把“基础 / 进阶 / 较难”当成主要叙事框架，因为那样很容易把内容写成一串零散问答，读的时候知道题目是什么，却不知道知识之间怎么连接。

现在统一按下面的顺序组织：

1. **先搭知识骨架**：先把这一章最核心的概念、对象关系、运行机制、工程意义讲清楚。
2. **再拆高频问法**：把面试官最常问的切口列出来，告诉你题是从哪里切进来的。
3. **最后补追问与边界**：把容易卡壳的代价、陷阱、反例、工程取舍补齐。

也就是说，后面的内容不再只是“看到问题再想答案”，而是先让你脑子里形成一张知识图，再拿问句去训练表达和背诵。

---
## 设计原则

### 1. 不只写关键词，要写清逻辑
每个知识点尽量覆盖：

- 标准回答
- 更深入解释
- 面试官常见追问
- 易错点 / 边界条件
- 工程上的真实意义

### 2. 不只讲结论，也讲代价
这套仓库的目标不是“背诵答案”，而是形成更像真实面试回答的结构：

- 机制是什么
- 为什么这样设计
- 解决了什么问题
- 带来了什么代价
- 什么时候这个结论不成立

### 3. 章节之间尽量能串起来
比如：

- C++ 并发 ↔ 操作系统调度 ↔ 锁与 IO 多路复用
- TCP / HTTP ↔ RPC / MQ ↔ 缓存一致性 / 分布式系统
- STL 容器 ↔ 内存布局 ↔ 工程性能取舍

目标不是做“孤立知识点合集”，而是做一套能互相联通的复习体系。

---

## 目录结构

- `01_cpp_language/`：C++ 语言本体、对象模型、模板、STL、内存管理、并发
- `02_operating_system/`：进程线程、虚拟内存、调度、文件系统、锁、IO、多路复用
- `03_computer_network/`：TCP/IP、HTTP/HTTPS、拥塞控制、DNS、CDN、RPC、MQ
- `04_database_cache/`：MySQL、Redis、索引、事务、MVCC、缓存一致性、高可用
- `05_design_patterns_architecture/`：设计模式、高并发设计、项目问答、手撕专题
- `06_algorithms/`：数据结构、复杂度、TopK、DP、图搜索等
- `07_role_based/`：按校招/后端等岗位区分的复习路径

---

## 当前进度

### 已进入深挖版重写的章节

#### 03_computer_network
- `01_tcp_udp_http.md`
- `02_http_details.md`
- `03_rpc_message_queue_dns_cdn.md`
- `04_network_security_basics.md`
- `05_network_programming_socket_epoll.md`
- `06_network_programming_examples.md`

#### 04_database_cache
- `01_mysql_redis.md`
- `02_mysql_transactions_indexes.md`
- `03_redis_high_availability.md`
- `04_nosql_kv_storage_principles.md`

#### 02_operating_system
- `01_process_thread_memory.md`
- `02_io_multiplexing.md`
- `03_linux_filesystem_signals.md`

#### 05_design_patterns_architecture
- `01_patterns_architecture.md`
- `02_project_questions.md`
- `03_hands_on_topics.md`
- `04_distributed_systems_load_balancing_high_availability.md`
- `05_observability_reliability_cloud_native.md`

#### 01_cpp_language
- `01_object_model.md`
- `02_value_categories_move_smartptr.md`
- `03_stl_template_compile.md`
- `04_cpp_concurrency.md`
- `05_stl_containers_deep_dive.md`
- `06_cpp11_20_features.md`
- `07_memory_management_allocator.md`
- `08_templates_metaprogramming.md`

#### 06_algorithms
- `01_data_structure_algorithm.md`

#### 07_role_based
- `01_backend_cpp_path.md`
- `02_campus_cpp_path.md`
- `03_job_requirements_gap_supplement.md`
- `04_job_requirements_interview_quick_notes.md`

这些章节已经开始统一成下面这种风格：

- 不只列结论
- 会补为什么这样设计
- 会写工程代价和边界条件
- 会给一条典型追问链
- 最后给更像现场回答的总结

### 仍待继续升级的章节

目前目录中的核心章节均已完成首轮深挖版重写。

---

## 推荐阅读顺序

### 如果你准备校招
建议顺序：

1. `01_cpp_language`
2. `06_algorithms`
3. `02_operating_system`
4. `03_computer_network`
5. `05_design_patterns_architecture/02_project_questions.md`

### 如果你准备后端 C++ 岗
建议顺序：

1. `01_cpp_language`
2. `02_operating_system`
3. `03_computer_network`
4. `04_database_cache`
5. `05_design_patterns_architecture`

### 如果你时间很紧，只想优先补高频追问区
建议先看：

1. `01_cpp_language/02_value_categories_move_smartptr.md`
2. `01_cpp_language/04_cpp_concurrency.md`
3. `03_computer_network/01_tcp_udp_http.md`
4. `03_computer_network/02_http_details.md`
5. `04_database_cache/01_mysql_redis.md`
6. `05_design_patterns_architecture/02_project_questions.md`

---

## 统一写作模板（后续章节按这个标准推进）

后续重写会尽量统一成下面结构：

1. 这一章为什么重要
2. 高频问题清单
3. 标准回答
4. 更深入的理解
5. 常见误区 / 边界条件
6. 一组典型追问链
7. 更像面试现场的总结回答
8. 复习建议

这样做的目标是：

- 方便突击复习
- 方便按专题系统补强
- 让每篇都更像“面试解析”，而不是“零散备忘录”

---

## 后续推进路线

接下来会继续按同样深度做第二轮打磨与补强：

- 补更多跨章节索引与串联阅读路径
- 对重点章节继续补项目化追问和例题
- 逐步把每篇从“深挖版”继续抬到“可直接冲面”的强度

目标不是只把目录补满，而是把**每一章都写成能经得住继续追问的材料**。

如果这个仓库能持续打磨下去，它会越来越像一套真正可用于面试准备和查漏补缺的 C++ / 后端知识库，而不只是一次性的八股摘要。
