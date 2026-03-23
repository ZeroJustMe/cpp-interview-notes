# 04. C++ 并发编程：线程、锁、原子、内存模型（深挖版）

> C++ 并发是最容易“会写一点线程代码”和“真正理解并发语义”之间拉开差距的地方。很多人会背：
>
> - `mutex` 保证线程安全
> - `atomic` 更轻量
> - 条件变量要防虚假唤醒
> - `memory_order` 有几种
>
> 但真正的难点在于：
>
> - 线程安全到底怎么定义
> - race condition 和 data race 差在哪
> - 为什么 atomic 不等于整体线程安全
> - happens-before 到底在保证什么
> - 为什么无锁编程不一定更快
>
> 这一章的重点，就是把“并发 API”提升成“并发语义理解”。
>
> **本章建议按“先理解知识主线，再练问答表达，最后吃透边界条件”的顺序阅读：**
>
> - 先把线程、共享状态、同步、可见性这四层关系理顺
> - 再理解 mutex、condition_variable、atomic 各自解决的问题边界
> - 最后再进入 happens-before、memory_order、lock-free 这些深水区

---

## 先把这一章的知识骨架搭起来

C++ 并发这章最重要的不是背出几个锁和内存序，而是先接受一个事实：**并发正确性默认是很脆弱的**。只要多个线程同时访问共享状态，你就必须回答两个问题：第一，谁能同时访问；第二，别人写进去的结果我什么时候能看到。

因此这章要按“线程执行—共享状态—同步机制—可见性语义”来读。`std::thread` 只是把执行流启动起来，`mutex` / `condition_variable` 解决的是互斥与等待，`atomic` 解决的是更细粒度的原子更新，而内存模型与 `memory_order` 解决的是跨 CPU、跨编译器优化下的可见性和排序问题。

真正高频的难点在于：很多人知道怎么把程序“锁住”，却不知道为什么会死锁、为什么会虚假唤醒、为什么原子变量不等于整个对象线程安全、为什么放松序比顺序一致性快但也更难推理。先把这套逻辑搭起来，再看问答才不容易散。

---

## 第一部分：先把概念和主线讲清楚

### 进入问答前，先把最小前置知识补齐

并发这章的第一步不是背锁，而是先承认一个事实：**只要多个线程共享可变状态，程序默认就是不安全的**。因此你必须先想清楚两个问题：谁能同时改数据，别人写进去的结果什么时候对我可见。

`std::thread` 只是把执行流拉起来，真正困难的是共享状态的约束。`mutex` 解决“同一时刻谁能进临界区”，`condition_variable` 解决“条件没满足时怎么等待”，`atomic` 解决“某些简单状态更新能不能不用锁也保持原子”，内存模型和 `memory_order` 则解决“编译器和 CPU 重排之后，可见性和先后关系还能不能推理”。

如果这条主线清楚，后面的竞态、死锁、虚假唤醒、原子语义才会有位置；否则所有概念都会变成独立名词。

---

## 1. 线程安全到底怎么定义？

### 标准回答
线程安全指多个线程并发访问某段代码或某个对象时，不会因竞态导致数据错误、崩溃或未定义行为，并且结果符合预期同步语义。

### 更成熟的理解
线程安全不是一句“加了锁就行”，它至少包含两层：

- **正确性**：不会破坏不变式、不会读到中间状态、不会 UB
- **语义性**：结果必须符合你设计的并发语义

### 为什么这题重要？
因为很多人会把“程序没崩”误当成线程安全，但并发 bug 常常最可怕的地方，就是它不一定立刻崩，只是偶尔给你错结果。

### 一句总结
> 线程安全不是“程序还能跑”，而是并发访问下仍然保持正确状态和预期可见性。

---

## 2. race condition 和 data race 有什么区别？

### race condition 是什么？
竞态条件（race condition）是广义概念：程序结果依赖多个线程执行时序，而这种时序不可控，所以结果不稳定。

### data race 是什么？
data race 是 C++ 内存模型里的更严格术语：多个线程并发访问同一内存位置，至少一个是写，而且缺乏同步关系，这会导致未定义行为。

### 为什么这个区分重要？
因为：

- 有些逻辑竞态即使没触发 data race，也可能业务错误
- 但 data race 是更硬的红线，一旦出现就是语言层面的 UB

### 高分点
> race condition 是更广义的“时序相关错误”，data race 是 C++ 内存模型明确定义的未同步并发访问红线。前者是设计问题，后者还是语言层面的 UB 问题。

---

## 3. `mutex` 在解决什么问题？它为什么不是“性能最差的原始办法”？

### 标准回答
`mutex` 用于保护临界区，保证同一时刻只有一个线程能访问受保护共享状态。

### 它真正适合什么场景？
适合保护：

- 多个变量共同维持的不变式
- 一整段必须原子完成的临界区逻辑
- 需要在逻辑层面保持一致性的复杂共享状态

### 为什么不能把它简单看成“粗暴方案”？
因为很多并发逻辑本来就不是一个单原子变量能描述的。比如：

- 队列的头尾状态
- cache 项的状态与数据一致性
- 任务队列与停止标志之间的关系

这些都需要“整体逻辑上的原子性”，而不仅是单条指令级原子性。

### 一句总结
> `mutex` 不是“落后办法”，它擅长保护的是多状态不变式，而不仅仅是某个变量的读写。

---

## 4. `lock_guard`、`unique_lock`、`scoped_lock` 分别怎么理解？

### `lock_guard`
最简单的 RAII 加锁器：

- 构造时加锁
- 析构时解锁
- 不支持灵活解锁和重新上锁

适合：
- 简单临界区
- 范围很固定的互斥保护

### `unique_lock`
更灵活：

- 可延迟加锁
- 可显式 unlock / lock
- 可与条件变量配合使用

适合：
- 需要和 `condition_variable` 一起使用
- 需要更复杂的锁控制流程

### `scoped_lock`
适合同时锁多个互斥量，帮你减少手写多锁顺序带来的死锁风险。

### 一句总结
> `lock_guard` 追求简单可靠，`unique_lock` 追求灵活控制，`scoped_lock` 适合多锁同时管理。别把它们当成重复 API，它们服务的是不同控制粒度。

---

## 5. 死锁是什么？为什么它本质是设计问题？

### 标准回答
死锁是多个线程互相等待对方释放资源，导致永久阻塞。

### 经典四个必要条件
1. 互斥
2. 占有且等待
3. 不可剥夺
4. 环路等待

### 为什么说它本质是设计问题？
因为死锁通常不是“某个函数调用错了”，而是资源获取顺序设计出了环路。你如果没有统一的锁顺序规范，项目一复杂就很容易出问题。

### 常见避免方法
- 固定加锁顺序
- 减少持锁时间
- 避免嵌套锁
- 使用 `std::lock` / `scoped_lock`

### 高分点
> 死锁不是 API 知识点，而是资源依赖图出了环。解决它靠设计约束，而不是运行时碰运气。

---

## 6. 条件变量到底在解决什么问题？

### 标准回答
条件变量用于线程间等待/通知机制，让线程在某个条件未满足时休眠，满足时被唤醒。

### 它不是在做互斥
这是高频误区：

- `mutex` 解决互斥进入
- `condition_variable` 解决高效等待“某个条件变真”

### 为什么需要它？
如果没有条件变量，线程往往只能：

- 忙等
- 反复轮询

这会浪费 CPU，并让时序更难看。

### 最小正确写法

```cpp
std::unique_lock<std::mutex> lk(m);
cv.wait(lk, [] { return ready; });
```

### 一句总结
> 条件变量解决的是“怎么高效等待状态变化”，不是“怎么加锁”。

---

## 经典多线程同步面试题（代码实战）

> 下面给出几道经典多线程面试题的完整 C++ 实现，涵盖 `mutex`、`condition_variable`、`semaphore`、`atomic` 等同步原语的实际使用。每道题都配有设计思路和关键知识点注释。

### 实战一：生产者-消费者模型（mutex + condition_variable）

这是并发面试最高频的经典题。核心在于：生产者往共享队列里放数据，消费者从队列里取数据，队列满时生产者等待，队列空时消费者等待。

```cpp
#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>

template <typename T>
class BoundedQueue {
public:
    explicit BoundedQueue(size_t capacity) : capacity_(capacity) {}

    // 生产者调用：往队列放入一个元素
    void push(const T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        // 队列满时，生产者阻塞等待；注意必须用谓词版 wait 防虚假唤醒
        not_full_.wait(lock, [this] { return queue_.size() < capacity_; });
        queue_.push(item);
        not_empty_.notify_one();  // 通知一个等待中的消费者
    }

    // 消费者调用：从队列取出一个元素
    T pop() {
        std::unique_lock<std::mutex> lock(mtx_);
        // 队列空时，消费者阻塞等待
        not_empty_.wait(lock, [this] { return !queue_.empty(); });
        T item = queue_.front();
        queue_.pop();
        not_full_.notify_one();   // 通知一个等待中的生产者
        return item;
    }

private:
    std::mutex mtx_;
    std::condition_variable not_full_;   // 队列"非满"条件
    std::condition_variable not_empty_;  // 队列"非空"条件
    std::queue<T> queue_;
    size_t capacity_;
};

int main() {
    BoundedQueue<int> bq(5);

    // 生产者线程
    std::thread producer([&bq] {
        for (int i = 0; i < 20; ++i) {
            bq.push(i);
            std::cout << "Produced: " << i << "\n";
        }
    });

    // 消费者线程
    std::thread consumer([&bq] {
        for (int i = 0; i < 20; ++i) {
            int val = bq.pop();
            std::cout << "Consumed: " << val << "\n";
        }
    });

    producer.join();
    consumer.join();
    return 0;
}
```

**知识点拆解：**
- `unique_lock` 而非 `lock_guard`：因为 `condition_variable::wait` 需要在等待时自动释放锁，被唤醒后重新上锁，`lock_guard` 不支持这种灵活控制
- 谓词版 `wait`：等价于 `while(!pred) cv.wait(lock);`，自动防御虚假唤醒
- 两个条件变量分别管理"非满"和"非空"两个条件，职责清晰
- `notify_one` vs `notify_all`：这里一对一通知效率更高；如果有多消费者竞争，可能需要 `notify_all`

---

### 实战二：交替打印奇偶数（mutex + condition_variable）

两个线程交替打印 1~100，一个打印奇数，一个打印偶数。这道题考察的是条件变量控制线程执行顺序。

```cpp
#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>

int main() {
    std::mutex mtx;
    std::condition_variable cv;
    int current = 1;
    const int limit = 100;

    // 奇数线程
    std::thread odd_thread([&] {
        while (true) {
            std::unique_lock<std::mutex> lock(mtx);
            cv.wait(lock, [&] { return current > limit || (current % 2 == 1); });
            if (current > limit) break;
            std::cout << "Odd  thread: " << current << "\n";
            ++current;
            cv.notify_one();
        }
    });

    // 偶数线程
    std::thread even_thread([&] {
        while (true) {
            std::unique_lock<std::mutex> lock(mtx);
            cv.wait(lock, [&] { return current > limit || (current % 2 == 0); });
            if (current > limit) break;
            std::cout << "Even thread: " << current << "\n";
            ++current;
            cv.notify_one();
        }
    });

    odd_thread.join();
    even_thread.join();
    return 0;
}
```

**关键点：**
- 两个线程共享 `current`，通过条件变量实现严格交替
- 谓词检查 `current > limit` 作为退出条件，避免线程死等
- 每次打印后 `notify_one` 唤醒对方

---

### 实战三：用 C++20 `std::counting_semaphore` 实现同步

C++20 引入了信号量，可以更直接地控制并发访问数量。

```cpp
#include <iostream>
#include <thread>
#include <semaphore>
#include <vector>

// 限制最多 3 个线程同时访问共享资源
std::counting_semaphore<3> sem(3);

void worker(int id) {
    sem.acquire();   // P 操作：信号量减 1，为 0 时阻塞
    std::cout << "Thread " << id << " entering critical section\n";
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    std::cout << "Thread " << id << " leaving critical section\n";
    sem.release();   // V 操作：信号量加 1，唤醒等待线程
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(worker, i);
    }
    for (auto& t : threads) t.join();
    return 0;
}
```

**用二值信号量实现交替打印（等价于 mutex 的信号量方式）：**

```cpp
#include <iostream>
#include <thread>
#include <semaphore>

int main() {
    std::binary_semaphore sem_odd(1);   // 奇数先走
    std::binary_semaphore sem_even(0);  // 偶数等待

    std::thread t1([&] {
        for (int i = 1; i <= 99; i += 2) {
            sem_odd.acquire();
            std::cout << i << "\n";
            sem_even.release();
        }
    });

    std::thread t2([&] {
        for (int i = 2; i <= 100; i += 2) {
            sem_even.acquire();
            std::cout << i << "\n";
            sem_odd.release();
        }
    });

    t1.join();
    t2.join();
    return 0;
}
```

**知识点对比：**
- 信号量不持有锁，acquire/release 可以跨线程调用（和 mutex 不同，mutex 必须同一线程加锁解锁）
- `binary_semaphore` 等价于初始值为 1 的 `counting_semaphore<1>`
- 信号量本身不保护临界区，它只控制"谁可以继续执行"

---

### 实战四：多线程安全计数器（mutex vs atomic 对比）

```cpp
#include <iostream>
#include <thread>
#include <mutex>
#include <atomic>
#include <vector>
#include <chrono>

// 版本 1：mutex 保护
struct MutexCounter {
    std::mutex mtx;
    int count = 0;
    void increment() {
        std::lock_guard<std::mutex> lock(mtx);
        ++count;
    }
};

// 版本 2：atomic 原子操作
struct AtomicCounter {
    std::atomic<int> count{0};
    void increment() {
        count.fetch_add(1, std::memory_order_relaxed);
        // 这里用 relaxed 是因为我们只关心最终计数值的正确性
        // 不需要和其他内存操作建立先后关系
    }
};

template <typename Counter>
void benchmark(const char* name) {
    Counter counter;
    std::vector<std::thread> threads;
    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < 8; ++i) {
        threads.emplace_back([&counter] {
            for (int j = 0; j < 1000000; ++j) {
                counter.increment();
            }
        });
    }
    for (auto& t : threads) t.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    std::cout << name << ": count=" << counter.count << " time=" << ms << "ms\n";
}

int main() {
    benchmark<MutexCounter>("Mutex  ");
    benchmark<AtomicCounter>("Atomic ");
    return 0;
}
```

**面试要点：**
- 对于简单计数器类场景，`atomic` 通常性能优于 `mutex`
- 但 `atomic` 只保护单个变量，不能保护多变量不变式
- `memory_order_relaxed` 是最弱的内存序，仅保证原子性，适合独立计数器
- 如果计数器的值需要和其他数据建立先后关系，需要用更强的内存序

---

### 实战五：读写锁（`shared_mutex`）实现读多写少场景

```cpp
#include <iostream>
#include <thread>
#include <shared_mutex>
#include <vector>
#include <string>

class ThreadSafeConfig {
public:
    std::string read(const std::string& key) const {
        std::shared_lock<std::shared_mutex> lock(mtx_);  // 读锁，多个读者可并发
        auto it = data_.find(key);
        return it != data_.end() ? it->second : "";
    }

    void write(const std::string& key, const std::string& value) {
        std::unique_lock<std::shared_mutex> lock(mtx_);  // 写锁，独占
        data_[key] = value;
    }

private:
    mutable std::shared_mutex mtx_;
    std::unordered_map<std::string, std::string> data_;
};

int main() {
    ThreadSafeConfig config;
    config.write("host", "127.0.0.1");

    std::vector<std::thread> readers;
    for (int i = 0; i < 5; ++i) {
        readers.emplace_back([&config, i] {
            for (int j = 0; j < 100; ++j) {
                auto val = config.read("host");
                // 多个读者可同时进入，不会互相阻塞
            }
            std::cout << "Reader " << i << " done\n";
        });
    }

    std::thread writer([&config] {
        for (int j = 0; j < 10; ++j) {
            config.write("host", "192.168.1." + std::to_string(j));
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        std::cout << "Writer done\n";
    });

    for (auto& t : readers) t.join();
    writer.join();
    return 0;
}
```

**知识点：**
- `shared_lock` 允许多个线程同时持有读锁
- `unique_lock` 获取写锁时会等所有读者退出
- 适合"读多写少"场景，比全用 `mutex` 吞吐量更高
- 注意：`shared_mutex` 的实现通常比普通 `mutex` 更重，读很少时未必有优势

---

## 第二部分：围绕高频追问继续展开

## 7. 什么是虚假唤醒？为什么一定要配谓词？

### 标准回答
线程在没有真正满足条件时从等待状态返回，称为虚假唤醒。

### 为什么正确写法一定要重新检查条件？
因为“被唤醒”不等于“条件已成立”。如果你把唤醒直接等价成条件满足，就会写出偶现 bug。

### 正确思路
永远写成：

- while 检查条件
- 或使用带谓词版本的 `wait`

### 一句总结
> 条件变量的正确用法，不是“等到被叫醒”，而是“被叫醒后重新确认条件是否真的成立”。

---

## 8. `atomic` 在解决什么问题？为什么 atomic 不等于整体线程安全？

### 标准回答
原子操作保证单个操作不会被其他线程观察到“半完成状态”，要么完全发生，要么完全没发生。

### 它擅长什么？
- 计数器
- 标志位
- 简单状态机中的单变量同步
- 某些低开销并发统计

### 为什么它不等于整体线程安全？
因为真实业务往往涉及多个状态之间的一致性。你就算把某一个变量改成 atomic，也未必能保证：

- 多变量之间关系正确
- 整个对象不变式成立
- 一整段操作逻辑不可分割

### 高分点
> atomic 解决的是单个原子对象的访问问题，不自动解决多个状态之间的一致性问题。atomic 很强，但不是“把锁删掉”的通用答案。

---

## 9. 原子性、可见性、顺序性为什么是三回事？

这是并发真正的概念分层。

### 原子性
一个操作不会被观察到中间状态。

### 可见性
一个线程写入的结果，另一个线程什么时候能看到。

### 顺序性
编译器和 CPU 能不能把某些读写顺序重排。

### 为什么要把这三件事分开？
因为很多人会误以为“原子了就都好了”。但其实：

- 原子性不自动保证别的线程马上可见
- 可见性不自动保证更复杂的先后约束
- 顺序性问题会让“看起来合理”的代码在多核下失效

### 一句总结
> 原子性只是底线，可见性和顺序性才是并发语义真正容易出坑的地方。

---

## 10. `memory_order` 至少要理解到什么程度？

### 最少要答出的几个
- `memory_order_relaxed`：只保证原子性，不额外保证顺序
- `memory_order_acquire`：获取语义，保证后续读写不被重排到前面
- `memory_order_release`：释放语义，保证前面的写不被重排到后面
- `memory_order_acq_rel`：常用于读改写操作
- `memory_order_seq_cst`：最强、最直观的全序一致性语义

### 如果没写过 lock-free，怎么答更稳？
不要乱吹底层指令细节。更稳的讲法是：

- relaxed 只有原子性
- acquire / release 常用于建立线程间同步边
- seq_cst 最容易理解，但通常限制优化更多

### 高分点
> `memory_order` 的关键，不是背名字，而是理解“原子性”和“可见性/顺序性”是两回事。

---

## 第三部分：把难点、边界和代价吃透

## 11. happens-before 到底在保证什么？

### 标准回答
happens-before 描述两个操作之间的先后可见性关系。如果 A happens-before B，那么 B 必须能看到 A 的结果，且编译器和 CPU 不能把这层关系打乱。

### 常见建立方式
- 同线程程序顺序
- 锁的解锁与加锁
- 原子变量的 release / acquire 同步
- 线程创建与 join

### 为什么它是并发核心概念？
因为并发真正难的不是“线程同时跑”，而是：

- 哪些写对别的线程可见
- 哪些顺序是必须保持的
- 哪些重排是被允许的

happens-before 正是在回答这些问题。

---

## 12. 无锁（lock-free）为什么不一定更快？

### 常见误区
很多人把“无锁”想成“高级、一定更快”。这很危险。

### 为什么它不一定更快？
因为无锁通常会带来：

- 更复杂的重试循环
- 更难推理的内存序
- 更高的调试和维护成本
- 在高竞争下可能反复 CAS 失败

### 真正成熟的回答
> 无锁编程减少的是阻塞和某些锁竞争，但可能把复杂度转移到重试、自旋、内存序推理和可维护性上。它不是默认优于锁，而是更适合某些极端性能敏感和特定数据结构场景。

---

## 13. 线程池为什么常被放在并发章收尾？

因为线程池是并发综合题。它把下面这些问题揉在一起了：

- 线程复用
- 任务调度
- 任务队列同步
- 生命周期管理
- 背压和拒绝策略

所以它特别能检验你是不是只会 API，还是已经能把互斥、等待、状态管理和系统吞吐放在一起思考。

---

## 14. 一组典型追问链

1. 线程安全到底怎么定义？
2. race condition 和 data race 有什么区别？
3. `mutex` 在保护什么层面的正确性？
4. `lock_guard` / `unique_lock` / `scoped_lock` 怎么选？
5. 死锁为什么本质上是设计问题？
6. 条件变量到底在解决什么问题？
7. 为什么一定要防虚假唤醒？
8. `atomic` 为什么不等于整体线程安全？
9. 原子性、可见性、顺序性为什么是三回事？
10. happens-before 到底在保证什么？
11. 无锁编程为什么不一定更快？

---

## 15. 一份更像面试现场的总结回答

> C++ 并发真正难的地方，不是记住几个 API，而是理解共享状态在多线程下怎样保持正确。`mutex` 解决的是复杂状态的不变式保护，`condition_variable` 解决的是条件等待，`atomic` 解决的是单个原子对象的无锁访问，而内存模型、happens-before 和 `memory_order` 则进一步定义了可见性和顺序性。真正成熟的回答，不是把这些概念拆开背，而是能说清它们分别在解决哪一层问题，以及为什么“原子”并不等于“整个程序并发正确”。

---

## 16. 复习建议

至少做到：

- 能把线程安全说到“正确性 + 语义性”
- 能区分 race condition 和 data race
- 能说清 `mutex`、`condition_variable`、`atomic` 各自解决什么问题
- 能把虚假唤醒、happens-before、memory_order 放回可见性语境里解释
- 不把 lock-free 神化成默认更快方案

做到这里，这一章就不再只是“并发 API 题”，而会变成真正的并发语义理解题。
---

## 附录 A：线程池完整实现与知识点详解

> 线程池是并发编程的综合大题，融合了线程管理、任务队列同步、条件变量、RAII 生命周期管理、`std::future` 异步结果获取等知识点。下面给出一个生产级可用的现代 C++ 线程池实现。

### 设计思路

1. **线程复用**：预创建 N 个工作线程，避免频繁创建/销毁线程的系统调用开销
2. **任务队列**：所有待执行任务放入线程安全队列，工作线程竞争取任务
3. **条件变量**：任务队列为空时工作线程休眠，新任务到来时唤醒
4. **优雅关闭**：设置停止标志，通知所有线程退出，等待所有线程完成当前任务
5. **返回值获取**：通过 `std::packaged_task` + `std::future` 让调用者获取异步执行结果

### 完整实现

```cpp
#include <iostream>
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <stdexcept>

class ThreadPool {
public:
    // 构造函数：创建指定数量的工作线程
    explicit ThreadPool(size_t num_threads) : stop_(false) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this] { worker_loop(); });
        }
    }

    // 提交任务，返回 future 用于获取结果
    // 模板参数：F 是可调用对象类型，Args 是参数包
    template <typename F, typename... Args>
    auto submit(F&& f, Args&&... args) -> std::future<std::invoke_result_t<F, Args...>> {
        using return_type = std::invoke_result_t<F, Args...>;

        // 将任务包装成 packaged_task，它能与 future 配对
        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<return_type> result = task->get_future();

        {
            std::lock_guard<std::mutex> lock(mtx_);
            if (stop_) {
                throw std::runtime_error("submit on stopped ThreadPool");
            }
            // 将 packaged_task 包装成 void() 放入任务队列
            tasks_.emplace([task]() { (*task)(); });
        }

        cv_.notify_one();  // 唤醒一个空闲工作线程
        return result;
    }

    // 析构函数：优雅关闭
    ~ThreadPool() {
        {
            std::lock_guard<std::mutex> lock(mtx_);
            stop_ = true;
        }
        cv_.notify_all();  // 唤醒所有等待中的工作线程
        for (auto& worker : workers_) {
            worker.join();   // 等待所有工作线程完成
        }
    }

    // 禁止拷贝和赋值
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

private:
    // 每个工作线程执行的循环
    void worker_loop() {
        while (true) {
            std::function<void()> task;
            {
                std::unique_lock<std::mutex> lock(mtx_);
                // 等待条件：有任务可取 或 线程池需要停止
                cv_.wait(lock, [this] { return stop_ || !tasks_.empty(); });

                // 如果已停止且没有剩余任务，退出循环
                if (stop_ && tasks_.empty()) return;

                task = std::move(tasks_.front());
                tasks_.pop();
            }
            task();  // 在锁外执行任务，避免持锁时间过长
        }
    }

    std::vector<std::thread> workers_;          // 工作线程集合
    std::queue<std::function<void()>> tasks_;   // 任务队列
    std::mutex mtx_;                            // 保护任务队列的互斥量
    std::condition_variable cv_;                // 通知工作线程的条件变量
    bool stop_;                                 // 停止标志
};
```

### 使用示例

```cpp
int main() {
    ThreadPool pool(4);  // 4 个工作线程

    // 提交返回值任务
    auto f1 = pool.submit([] { return 42; });
    auto f2 = pool.submit([](int a, int b) { return a + b; }, 10, 20);

    // 提交多个计算任务
    std::vector<std::future<int>> futures;
    for (int i = 0; i < 10; ++i) {
        futures.push_back(pool.submit([i] {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            return i * i;
        }));
    }

    std::cout << "f1 = " << f1.get() << "\n";    // 42
    std::cout << "f2 = " << f2.get() << "\n";    // 30

    for (int i = 0; i < 10; ++i) {
        std::cout << i << "^2 = " << futures[i].get() << "\n";
    }

    return 0;
    // pool 析构时自动优雅关闭
}
```

### 知识点逐一拆解

| 知识点 | 在线程池中的体现 |
|--------|-----------------|
| `std::thread` | 工作线程的创建和生命周期管理 |
| `std::mutex` + `lock_guard` | 保护任务队列的互斥访问 |
| `std::condition_variable` | 工作线程在无任务时休眠，有任务时被唤醒 |
| `std::function<void()>` | 类型擦除：任意可调用对象统一存入队列 |
| `std::packaged_task` | 包装任务，与 `future` 配对实现异步结果获取 |
| `std::future` | 调用者通过 `get()` 阻塞等待任务结果 |
| `std::forward` | `submit` 中完美转发调用者参数 |
| `std::bind` | 将函数和参数绑定成无参可调用对象 |
| RAII | 析构函数自动完成线程池关闭和线程回收 |
| `std::invoke_result_t` | 编译期推导任务返回值类型 |

### 常见面试追问

**Q：为什么 `task` 要用 `shared_ptr` 包装 `packaged_task`？**
> 因为 `packaged_task` 不可拷贝，而 `std::function` 要求可拷贝。用 `shared_ptr` 包装后，lambda 捕获的是 `shared_ptr`（可拷贝），就能存入 `std::function`。

**Q：为什么任务在锁外执行？**
> 如果持锁执行任务，其他线程就无法在此期间取新任务，严重降低并发度。锁只保护队列操作，不保护任务执行。

**Q：线程池关闭时如何处理队列中未完成的任务？**
> 当前实现是"执行完所有已入队任务再退出"（graceful shutdown）。`stop_ && tasks_.empty()` 这个条件保证了即使收到停止信号，工作线程仍会清空队列。

**Q：能不能动态调整线程数？**
> 当前实现不支持。生产级线程池可能支持动态扩缩，但需要额外的线程管理逻辑和同步控制。

---

## 附录 B：Ring Buffer 消息队列——生产者消费者模型实现

> Ring Buffer（环形缓冲区）是高性能消息队列的经典底层结构。它预分配固定大小的数组，用头尾指针循环利用空间，避免动态分配。下面分别给出**有锁版**和**无锁版**两种实现。

### 设计思路

1. 预分配固定容量的数组（capacity 建议为 2 的幂，方便位运算取模）
2. 维护 `head`（读位置）和 `tail`（写位置）两个索引
3. 队列满：`(tail + 1) % capacity == head`
4. 队列空：`tail == head`
5. 环形复用：索引对 capacity 取模实现循环

### 有锁版：mutex + condition_variable

```cpp
#include <vector>
#include <mutex>
#include <condition_variable>
#include <optional>
#include <cstddef>

template <typename T>
class RingBuffer {
public:
    explicit RingBuffer(size_t capacity)
        : buffer_(capacity), capacity_(capacity), head_(0), tail_(0), count_(0) {}

    // 阻塞式写入
    void push(const T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        not_full_.wait(lock, [this] { return count_ < capacity_; });
        buffer_[tail_] = item;
        tail_ = (tail_ + 1) % capacity_;
        ++count_;
        not_empty_.notify_one();
    }

    // 阻塞式读取
    T pop() {
        std::unique_lock<std::mutex> lock(mtx_);
        not_empty_.wait(lock, [this] { return count_ > 0; });
        T item = std::move(buffer_[head_]);
        head_ = (head_ + 1) % capacity_;
        --count_;
        not_full_.notify_one();
        return item;
    }

    // 非阻塞尝试写入
    bool try_push(const T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (count_ >= capacity_) return false;
        buffer_[tail_] = item;
        tail_ = (tail_ + 1) % capacity_;
        ++count_;
        not_empty_.notify_one();
        return true;
    }

    // 非阻塞尝试读取
    std::optional<T> try_pop() {
        std::lock_guard<std::mutex> lock(mtx_);
        if (count_ == 0) return std::nullopt;
        T item = std::move(buffer_[head_]);
        head_ = (head_ + 1) % capacity_;
        --count_;
        not_full_.notify_one();
        return item;
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return count_;
    }

private:
    std::vector<T> buffer_;
    size_t capacity_;
    size_t head_;    // 消费者读取位置
    size_t tail_;    // 生产者写入位置
    size_t count_;   // 当前元素数量

    mutable std::mutex mtx_;
    std::condition_variable not_full_;
    std::condition_variable not_empty_;
};
```

**使用示例：**

```cpp
#include <iostream>
#include <thread>

int main() {
    RingBuffer<int> rb(8);

    std::thread producer([&rb] {
        for (int i = 0; i < 100; ++i) {
            rb.push(i);
        }
    });

    std::thread consumer([&rb] {
        for (int i = 0; i < 100; ++i) {
            int val = rb.pop();
            std::cout << val << " ";
        }
        std::cout << "\n";
    });

    producer.join();
    consumer.join();
    return 0;
}
```

### 无锁版设计思路（单生产者-单消费者 SPSC）

> 无锁 Ring Buffer 的核心洞察：当**只有一个生产者和一个消费者**时，`head` 只被消费者修改，`tail` 只被生产者修改，天然不存在同一变量的写写竞争。因此只需要 `atomic` 保证可见性，不需要 `mutex`。

**关键设计要点：**

1. `head_` 和 `tail_` 用 `std::atomic<size_t>` 存储
2. 容量必须是 2 的幂，用位与运算 `& (capacity - 1)` 代替取模（更快）
3. 生产者写入时只更新 `tail_`，消费者读取时只更新 `head_`
4. 通过 `memory_order_acquire` / `memory_order_release` 建立同步边，保证数据写入对消费者可见

```cpp
#include <atomic>
#include <vector>
#include <optional>
#include <cstddef>
#include <cassert>

template <typename T>
class SPSCRingBuffer {
public:
    explicit SPSCRingBuffer(size_t capacity)
        : capacity_(next_power_of_2(capacity)),
          mask_(capacity_ - 1),
          buffer_(capacity_),
          head_(0),
          tail_(0) {}

    // 生产者调用（只有一个线程调用）
    bool try_push(const T& item) {
        const size_t tail = tail_.load(std::memory_order_relaxed);
        const size_t next_tail = (tail + 1) & mask_;

        // 队列满：下一个写位置追上了读位置
        if (next_tail == head_.load(std::memory_order_acquire)) {
            return false;
        }

        buffer_[tail] = item;

        // release 语义：保证 buffer_[tail] 的写入在 tail_ 更新之前完成
        // 这样消费者看到新的 tail_ 时，一定能看到完整的数据
        tail_.store(next_tail, std::memory_order_release);
        return true;
    }

    // 消费者调用（只有一个线程调用）
    std::optional<T> try_pop() {
        const size_t head = head_.load(std::memory_order_relaxed);

        // 队列空：读位置等于写位置
        if (head == tail_.load(std::memory_order_acquire)) {
            return std::nullopt;
        }

        T item = std::move(buffer_[head]);

        // release 语义：保证数据读取完成后才更新 head_
        // 这样生产者看到新的 head_ 时，旧槽位一定已被读完
        head_.store((head + 1) & mask_, std::memory_order_release);
        return item;
    }

    size_t capacity() const { return capacity_; }

private:
    static size_t next_power_of_2(size_t n) {
        size_t p = 1;
        while (p < n) p <<= 1;
        return p;
    }

    const size_t capacity_;
    const size_t mask_;
    std::vector<T> buffer_;

    // 通过 alignas(64) 避免 false sharing（缓存行伪共享）
    // head_ 和 tail_ 分别被不同线程频繁访问，应避免在同一缓存行
    alignas(64) std::atomic<size_t> head_;
    alignas(64) std::atomic<size_t> tail_;
};
```

**使用示例：**

```cpp
#include <iostream>
#include <thread>
#include <chrono>

int main() {
    SPSCRingBuffer<int> rb(1024);

    std::thread producer([&rb] {
        for (int i = 0; i < 1000000; ++i) {
            while (!rb.try_push(i)) {
                // 自旋等待；生产级可加 yield 或退避策略
                std::this_thread::yield();
            }
        }
    });

    std::thread consumer([&rb] {
        for (int i = 0; i < 1000000; ++i) {
            while (true) {
                auto val = rb.try_pop();
                if (val.has_value()) {
                    // 验证顺序正确性
                    if (*val != i) {
                        std::cerr << "Order error!\n";
                        return;
                    }
                    break;
                }
                std::this_thread::yield();
            }
        }
        std::cout << "All 1000000 items consumed correctly.\n";
    });

    producer.join();
    consumer.join();
    return 0;
}
```

### 有锁 vs 无锁对比总结

| 维度 | 有锁版（mutex + cv） | 无锁版（SPSC atomic） |
|------|----------------------|----------------------|
| 适用场景 | 多生产者-多消费者（MPMC） | 仅单生产者-单消费者（SPSC） |
| 同步机制 | `mutex` + `condition_variable` | `atomic` + `memory_order` |
| 阻塞行为 | 可阻塞等待 | 非阻塞（需调用者自旋或退避） |
| 性能 | 中等，锁竞争是瓶颈 | 极高吞吐，几乎无同步开销 |
| 实现复杂度 | 低 | 中等（需理解内存序） |
| 缓存友好 | 一般 | 好（`alignas(64)` 避免 false sharing） |
| 扩展到 MPMC | 天然支持 | 需要更复杂的设计（如 Disruptor 模式） |

### 无锁版核心知识点

- **`memory_order_acquire/release`**：建立 happens-before 关系，保证"先写数据，再更新索引"对消费者可见
- **位与取模**：`(idx + 1) & mask_` 比 `% capacity_` 快，但要求容量为 2 的幂
- **False sharing 防护**：`head_` 和 `tail_` 分属不同线程热路径，`alignas(64)` 确保它们不在同一缓存行
- **SPSC 限制**：无锁的简洁性来自"每个索引只有一个写者"的约束；MPMC 无锁队列（如 Michael-Scott queue）复杂度高得多