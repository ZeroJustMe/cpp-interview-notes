# 03. 企业场景题

> 大厂面试的场景题不会脱离候选人的项目背景，而是把你做过的技术放到更大的工程问题中考察系统设计能力。  
> 以下场景题围绕简历涉及的技术栈展开，每题包含场景描述、核心问题、**简答思路**和追问。

---

## 场景一：向量检索服务的在线扩容

**场景描述：**  
你负责一个在线向量检索服务，当前单机 HNSW 索引已满（10 亿向量），QPS 达到瓶颈。业务方要求在不停服的情况下将索引扩容到 50 亿向量。

**核心问题：** 请设计一个在线扩容方案。

> **简答思路：** 分片 + 路由。按向量空间（聚类分区）将数据分到多台机器，用一致性哈希做分片路由。扩容时新增分片 → 后台异步迁移数据 → 路由表逐步切换 → 旧分片下线。查询时并行查所有分片再合并 TopK。迁移期间双读（新旧分片都查）保证召回率不下降。  
> 📎 [负载均衡 · 一致性哈希](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

**追问：**

1. 索引分片策略怎么选？按 ID 范围还是按向量空间分区？两种方案对召回率的影响？
2. 扩容过程中查询的一致性怎么保证？能不能接受短暂的召回率下降？
3. 新分片的数据怎么从旧分片迁移？迁移期间的双写怎么处理？
4. 分片之间的负载均衡怎么做？出现热点分片怎么处理？
5. 如果用你做的 CPU-GPU 混合架构，扩容方案有什么不同？

---

## 场景二：流式实时异常检测系统

**场景描述：**  
在一个大型电商平台，需要对用户行为流（每秒百万事件）做实时异常检测。异常包括刷单、盗号、恶意爬虫等。要求从事件产生到告警发出的延迟不超过 500ms。

**核心问题：** 请设计整体架构。

> **简答思路：** 采集层 Kafka 接入事件流 → 计算层用流处理引擎（类似我的 Vector Stream Join 架构）做窗口内特征聚合 → 检测层混合规则引擎（确定性判定）和 ML 模型（概率判定） → 输出层告警去重收敛后推送。流水线各阶段异步解耦，背压机制防止过载。  
> 📎 [场景面试题](../cpp_interview_notes/08_enterprise_scenarios/01_scenario_questions.md) · [重试、限流、熔断、降级](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

**追问：**

1. 你的向量流 Join 引擎的设计思路能不能复用到这个场景？哪些组件可以复用？
2. 特征提取和模型推理放在同一个 Pipeline 还是分开？各自的优缺点？
3. 窗口大小怎么选？过短会漏检、过长会延迟，怎么平衡？
4. 检测规则和 ML 模型混合使用时，怎么编排执行顺序？
5. 告警的去重和收敛怎么做？同一用户的多条相似告警怎么合并？

---

## 场景三：分布式仿真平台设计

**场景描述：**  
自动驾驶公司需要每天运行 100 万个仿真 case，单 case 运行时间 30 秒到 30 分钟不等。需要设计一个分布式仿真平台，支持弹性扩缩容，并在 case 失败时自动重试。

**核心问题：** 请设计这个平台的任务调度和资源管理架构。

> **简答思路：** Master-Worker 架构：Master 维护任务队列（按优先级排序），Worker 从队列拉取 case 执行。Worker 部署在 K8s 上，HPA 根据队列深度自动扩缩。case 失败后标记重试（最多 3 次，指数退避），超过重试次数标记为 failed 供人工分析。结果存入对象存储（S3/MinIO），元数据入 MySQL。  
> 📎 [可观测性 · 云原生 · K8s](../cpp_interview_notes/05_design_patterns_architecture/05_observability_reliability_cloud_native.md)

**追问：**

1. 任务调度器怎么设计？中心化调度（如 K8s Job）和去中心化调度的取舍？
2. 仿真 case 的优先级怎么定义？紧急回归测试 vs. 日常全量测试怎么区分？
3. 一个 case 依赖多个仿真模块（感知、规划、控制），这些模块怎么部署？同机 vs. 分布式？
4. 你在仿真器中做的一致性优化，在分布式环境下还能保证吗？
5. 仿真结果的存储和分析怎么设计？每天 100 万 case 的日志量怎么处理？

---

## 场景四：高吞吐 Pipeline 服务的背压控制

**场景描述：**  
你负责的 AI 推理 Pipeline 服务上线后，某天推理模型升级，单次推理延迟从 10ms 涨到 50ms，导致上游请求大量堆积，内存 OOM，服务雪崩。

**核心问题：** 怎么预防和应对这种情况？

> **简答思路：** 三道防线：①限流——入口令牌桶控制最大 QPS；②背压——队列水位超过高水位线时通知上游降速（和 TCP 流量控制同理）；③熔断——下游延迟超阈值时熔断器断开，快速返回降级结果。事中用自适应限流（动态调整令牌桶速率），事前做压测确定容量上限。  
> 📎 [重试、限流、熔断、降级](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md) · [容量评估与压测](../cpp_interview_notes/05_design_patterns_architecture/05_observability_reliability_cloud_native.md)

**追问：**

1. 背压信号怎么从下游传播到上游？在你的 Pipeline 架构里具体怎么实现？
2. 限流策略怎么选？漏桶、令牌桶、滑动窗口计数器各自的特点？
3. 请求队列满了以后的拒绝策略是什么？直接丢弃、返回降级结果还是排队等待？
4. 怎么做服务的熔断和降级？和你的 SageFlow 框架怎么整合？
5. 如何做容量预估和压测？你会怎么设计压测方案？

---

## 场景五：跨语言 SDK 的版本兼容性管理

**场景描述：**  
你的 Sage 框架同时提供 C++ 和 Python SDK，C++ 底层库频繁迭代（每周一个版本），但 Python 用户不希望频繁升级。需要保证新版 C++ 底层不破坏旧版 Python SDK 的功能。

**核心问题：** 怎么设计版本兼容性策略？

> **简答思路：** API 层面用 SemVer（主版本号变更才允许 breaking change），ABI 层面用 Pimpl 模式隔离实现细节——Python SDK 只依赖稳定的 C 接口（通过 PyBind11 thin wrapper），底层 C++ 实现改动不影响 ABI。CI 中跑"新底层 + 旧 SDK"的兼容性测试矩阵，自动检测 break。  
> 📎 [设计模式 · 系统设计](../cpp_interview_notes/05_design_patterns_architecture/01_patterns_architecture.md)

**追问：**

1. API 的语义版本控制（SemVer）怎么定义 breaking change？在 PyBind11 封装中哪些改动算 breaking？
2. ABI 兼容性和 API 兼容性的区别？C++ 的 ABI 兼容有多难维护？
3. 测试策略怎么设计？新版 C++ 要跑旧版 Python SDK 的测试套件吗？
4. 如果必须有 breaking change，迁移方案怎么设计？给用户多长的过渡期？
5. 你会怎么用 CI/CD 自动化这个兼容性检查流程？

---

## 场景六：多租户向量数据库的资源隔离

**场景描述：**  
你的向量检索引擎要作为云服务提供给多个租户。不同租户的数据量和查询模式差异很大：A 租户 1 亿向量、低 QPS 但要求高召回；B 租户 1000 万向量、高 QPS 但可接受低召回。

**核心问题：** 怎么设计资源隔离和调度策略？

> **简答思路：** 计算层按租户分配独立线程池（线程池隔离），重要租户可以独占 GPU。索引层按租户独立实例（各自参数不同：A 租户 HNSW `ef=200`，B 租户 `ef=50`）。存储层按租户独立 namespace，索引文件隔离。调度层对不同 SLA 等级分配不同的优先级队列。  
> 📎 [可观测性 · 云原生 · K8s](../cpp_interview_notes/05_design_patterns_architecture/05_observability_reliability_cloud_native.md)

**追问：**

1. 计算隔离怎么做？物理隔离（独占机器）、容器隔离还是线程池隔离？
2. 不同租户的索引参数（如 HNSW 的 `ef`、`M`）能不能动态调整？
3. GPU 资源怎么在多租户间共享？CUDA MPS / MIG 了解吗？
4. 存储层面怎么隔离？索引数据和原始向量的存储分层怎么设计？
5. 计费模型怎么设计？按查询次数、按存储量还是按 GPU 时间？

---

## 场景七：仿真器的回归测试与持续集成

**场景描述：**  
自动驾驶仿真器每次代码提交后需要运行数千个回归测试 case 来验证功能正确性。目前回归测试耗时 6 小时，严重阻塞开发迭代。研发团队希望将其缩短到 1 小时以内。

**核心问题：** 怎么优化回归测试的效率？

> **简答思路：** 三管齐下：①分级测试——代码变更影响分析，只运行受影响的 case（增量测试选择）；②并行化——多机并行执行 case，N 台机器线性缩短时间；③快速失败——高优先级 case（核心功能 + 历史高 fail 率 case）先跑，fail 即停不浪费后续资源。Failure Detector 的自动化判定结果直接对接 CI 的 pass/fail。  
> 📎 [场景面试题](../cpp_interview_notes/08_enterprise_scenarios/01_scenario_questions.md)

**追问：**

1. 测试用例的优先级排序怎么做？能不能根据代码变更自动选择受影响的 case？
2. 并行化测试有哪些方案？你设计仿真器时有没有考虑支持并行运行？
3. 测试用例之间有没有依赖关系？如何保证并行执行的正确性？
4. 你做的 Failure Detector 在回归测试中扮演什么角色？如何自动化判定 pass/fail？
5. 仿真一致性问题对回归测试有什么影响？不一致会导致 flaky test 吗？

---

## 场景八：低延迟向量流 Join 的生产化部署

**场景描述：**  
你的 Vector Stream Join 引擎需要从研究原型部署为在线生产服务，要求 99.9th percentile 延迟 < 10ms，可用性 99.99%。

**核心问题：** 从原型到生产，需要做哪些改造？

> **简答思路：** 四方面改造：①内存管理——预分配 + 内存池替代动态分配，防止碎片和 GC 尖刺；②状态持久化——窗口状态定期 checkpoint 到持久存储，crash recovery 从最近 checkpoint 重放；③多副本——至少 2 副本热备，故障自动切换（Raft leader election 或简单的主备）；④可观测性——埋点吞吐/延迟/召回率/内存四个核心指标，对接 Prometheus + Grafana。  
> 📎 [可观测性 · SLI/SLO/SLA](../cpp_interview_notes/05_design_patterns_architecture/05_observability_reliability_cloud_native.md) · [高可用与故障转移](../cpp_interview_notes/05_design_patterns_architecture/04_distributed_systems_load_balancing_high_availability.md)

**追问：**

1. 你的原型目前的 P99 延迟是多少？和目标差距在哪里？
2. 内存管理怎么做？流式场景下内存泄漏或碎片化怎么预防？
3. 怎么做优雅重启？窗口中的状态怎么持久化和恢复？
4. 多副本部署时，状态怎么同步？有没有借鉴 Flink 的 checkpoint 机制？
5. 监控和告警怎么设计？哪些指标是关键指标（吞吐、延迟、召回率、内存使用）？

---

## 场景九：大规模 C++ 项目的编译加速

**场景描述：**  
你的 C++ 项目代码量超过 100 万行，全量编译需要 40 分钟，增量编译也经常要 10 分钟以上。研发效率严重受影响。

**核心问题：** 怎么优化编译速度？

> **简答思路：** 先分析瓶颈——用 `-ftime-trace` 看哪些头文件/模板实例化耗时最多。然后分三层优化：①代码层——前置声明减少头文件依赖、Pimpl 模式隔离实现、`extern template` 减少重复实例化；②工具层——ccache/sccache 做编译缓存、distcc 做分布式编译；③架构层——拆分大模块成独立构建目标，最大化增量编译命中率。  
> 📎 [STL · 模板 · 编译链接](../cpp_interview_notes/01_cpp_language/03_stl_template_compile.md) · [模板元编程](../cpp_interview_notes/01_cpp_language/08_templates_metaprogramming.md)

**追问：**

1. 头文件依赖过深怎么处理？前置声明（forward declaration）和 Pimpl 模式怎么用？
2. 分布式编译（distcc / icecream）和编译缓存（ccache / sccache）的适用场景？
3. 模块化编译（C++20 Modules）了解吗？对你的项目有没有实际帮助？
4. 模板实例化导致编译膨胀怎么处理？extern template 怎么用？
5. CMake 的目标（target）组织怎么优化才能最大化增量编译的命中率？

---

## 场景十：自动驾驶仿真器从单机到云原生的架构演进

**场景描述：**  
公司决定将你负责的仿真器从单机版本改造为云原生版本，每个仿真组件（感知、规划、控制、引擎）独立为微服务，部署在 K8s 集群上。

**核心问题：** 请设计技术改造方案。

> **简答思路：** 分三步走：①通信层改造——将单机的 Cyber 共享内存通信替换为 gRPC（跨节点） + 共享内存（同 Pod 内），关键路径用 RDMA 降低延迟；②状态管理——仿真状态提取到独立的 State Service（Redis 或 etcd），各微服务无状态化；③编排部署——每个仿真 case 对应一个 K8s Job，Job 内用 sidecar 容器部署各仿真组件，Pod 内通信走 localhost。  
> 📎 [K8s 核心对象](../cpp_interview_notes/05_design_patterns_architecture/05_observability_reliability_cloud_native.md) · [RPC · 消息队列](../cpp_interview_notes/03_computer_network/03_rpc_message_queue_dns_cdn.md)

**追问：**

1. 仿真器对实时性要求很高，微服务化后网络延迟怎么控制？Service Mesh 适合这个场景吗？
2. 原来的 Cyber 中间件通信改为什么？gRPC / 共享内存 / RDMA 怎么选？
3. 仿真状态（车辆位姿、地图数据）怎么在微服务间共享？状态服务怎么设计？
4. 弹性扩缩容的指标是什么？CPU 利用率、队列深度还是仿真 FPS？
5. 微服务化后，你的仿真一致性保证还能成立吗？分布式时钟同步怎么做？
