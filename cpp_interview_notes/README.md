# C++ 面试八股知识库（完整版）

这是一套按知识域拆分的 C++ 面试资料库，面向：
- C++ 后台开发
- 基础架构 / 中间件
- 游戏服务端 / 高性能服务
- 偏系统方向开发
- 校招 / 社招面试复习

## 目录结构

- `01_cpp_language/`：C++ 语言本体、对象模型、模板、STL、内存管理、并发
- `02_operating_system/`：进程线程、虚拟内存、调度、文件系统、锁、IO、多路复用
- `03_computer_network/`：TCP/IP、HTTP/HTTPS、可靠性、拥塞控制、DNS、CDN、RPC、MQ
- `04_database_cache/`：MySQL、Redis、索引、事务、MVCC、缓存一致性、高可用
- `05_design_patterns_architecture/`：设计模式、高并发设计、项目问答、手撕题专题
- `06_algorithms/`：数据结构、复杂度、TopK、DP、图搜索等常见基础题
- `07_role_based/`：按岗位区分的复习路径

## 当前文件清单

### 01_cpp_language
- `01_object_model.md`
- `02_value_categories_move_smartptr.md`
- `03_stl_template_compile.md`
- `04_cpp_concurrency.md`
- `05_stl_containers_deep_dive.md`
- `06_cpp11_20_features.md`
- `07_memory_management_allocator.md`
- `08_templates_metaprogramming.md`

### 02_operating_system
- `01_process_thread_memory.md`
- `02_io_multiplexing.md`
- `03_linux_filesystem_signals.md`

### 03_computer_network
- `01_tcp_udp_http.md`
- `02_http_details.md`
- `03_rpc_message_queue_dns_cdn.md`

### 04_database_cache
- `01_mysql_redis.md`
- `02_mysql_transactions_indexes.md`
- `03_redis_high_availability.md`

### 05_design_patterns_architecture
- `01_patterns_architecture.md`
- `02_project_questions.md`
- `03_hands_on_topics.md`

### 06_algorithms
- `01_data_structure_algorithm.md`

### 07_role_based
- `01_backend_cpp_path.md`
- `02_campus_cpp_path.md`

## 使用建议

### 后端岗
1. `01_cpp_language`
2. `02_operating_system`
3. `03_computer_network`
4. `04_database_cache`
5. `05_design_patterns_architecture`

### 校招岗
1. `01_cpp_language`
2. `06_algorithms`
3. `02_operating_system`
4. `03_computer_network`
5. `05_design_patterns_architecture/02_project_questions.md`

## 文档风格

每个文件尽量按以下结构整理：
- 高频问题
- 标准回答
- 深挖细节
- 易错点 / 面试陷阱
- 复习提示

## 后续仍可继续细分的方向

- STL 每个容器单独一篇
- C++11/14/17/20 按版本细拆
- 手撕线程池 / shared_ptr / LRU / 跳表专题
- Linux 网络编程专题
- 分布式一致性 / 限流 / 熔断 / 高可用专题

如果你继续扩，这个仓库可以长期演化成一个完整的 C++ 面试知识库。