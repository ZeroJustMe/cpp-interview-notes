# 01. 设计模式、系统设计、高并发项目问答（深挖版）

> 这一章特别容易被答成"背模式名字"：
>
> - 单例
> - 工厂
> - 观察者
> - 线程池
> - 高并发设计要限流、熔断、降级
>
> 但真正的面试官通常不在乎你会不会背出 23 种模式，而在乎你能不能回答：
>
> - 这个模式到底解决了什么问题？
> - 为什么要这样拆，而不是直接写死？
> - 它的代价是什么？
> - 在 C++ / 服务端项目里怎么落地？
>
> 所以这一章的重点不是"模式大全"，而是把常见模式放回工程语境里讲清楚。
>
> **本章按三层难度组织：**
>
> - ⭐ **基础必会** — 单例（6种写法）、工厂（3种形式）、观察者、建造者、代理、策略、装饰器
> - 🔥 **高频追问** — 生产者消费者、线程池、高并发系统设计、高性能服务器
> - 💎 **深度难点** — CPU 飙高/内存泄漏排查、项目追问、架构回答、模式分类速查

---

## ⭐ 第一层：基础必会

## 1. 单例模式怎么写？有什么问题？

### 标准回答
单例模式确保一个类在运行期间只有**一个实例**，并提供一个**全局访问点**。核心要素：

- 私有化构造函数，防止外部直接实例化
- 类内部持有唯一的静态实例
- 提供公共静态方法返回该实例

### 六种常见实现方式（C++ 视角）

**① 懒汉式（线程不安全）**
```cpp
class Singleton {
    static Singleton* instance_;
    Singleton() = default;
public:
    static Singleton* getInstance() {
        if (!instance_) instance_ = new Singleton();  // 多线程下可能多次创建
        return instance_;
    }
};
Singleton* Singleton::instance_ = nullptr;
```

- 优点：延迟实例化，按需创建
- 缺点：多线程下不安全

**② 饿汉式（线程安全）**
```cpp
class Singleton {
    static Singleton instance_;
    Singleton() = default;
public:
    static Singleton& getInstance() { return instance_; }
};
Singleton Singleton::instance_;  // 程序启动时就初始化
```

- 优点：天然线程安全
- 缺点：不管用不用都会实例化，可能浪费资源

**③ 懒汉式加锁（线程安全，性能低）**
```cpp
class Singleton {
    static Singleton* instance_;
    static std::mutex mtx_;
    Singleton() = default;
public:
    static Singleton* getInstance() {
        std::lock_guard<std::mutex> lock(mtx_);  // 每次都加锁
        if (!instance_) instance_ = new Singleton();
        return instance_;
    }
};
```

- 优点：线程安全
- 缺点：实例创建后仍然每次加锁，性能差

**④ 双重检查锁（DCL，线程安全，高性能）**
```cpp
class Singleton {
    static std::atomic<Singleton*> instance_;
    static std::mutex mtx_;
    Singleton() = default;
public:
    static Singleton* getInstance() {
        Singleton* tmp = instance_.load(std::memory_order_acquire);
        if (!tmp) {                          // 第一次检查：避免每次都加锁
            std::lock_guard<std::mutex> lock(mtx_);
            tmp = instance_.load(std::memory_order_relaxed);
            if (!tmp) {                      // 第二次检查：防止多线程重复创建
                tmp = new Singleton();
                instance_.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }
};
```

- 必须用 `atomic` 或 `volatile`（Java）防止指令重排
- `new` 操作不是原子的：分配内存 → 构造对象 → 赋值指针，重排可能导致获取到半初始化对象

**⑤ Meyers' Singleton（局部静态变量，C++11 推荐）**
```cpp
class Singleton {
    Singleton() = default;
public:
    static Singleton& getInstance() {
        static Singleton instance;  // C++11 保证线程安全的一次初始化
        return instance;
    }
};
```

- C++11 标准保证局部 static 变量初始化是线程安全的
- **面试首推写法**：简洁、安全、无需手动管理内存

**⑥ 模板式单例**
```cpp
template<typename T>
class Singleton {
public:
    static T& getInstance() {
        static T instance;
        return instance;
    }
protected:
    Singleton() = default;
};
// 使用：class MyService : public Singleton<MyService> { ... };
```

### 单例解决了什么问题？
- 某类资源或服务实例在系统里应该全局唯一
- 大家共享同一个入口访问它
- 适用于：数据库连接池、线程池、日志管理器、全局配置管理

### 单例的问题和代价
- **全局状态难测试**：单元测试无法轻易替换单例
- **生命周期不透明**：静态对象的析构顺序在多编译单元间不确定
- **隐藏依赖**：使用者对单例的依赖不在接口中体现
- **代码耦合扩散**：越来越多的模块直接引用单例

### 常见追问

**Q：为什么双重检查锁需要 atomic/volatile？**
> `new Singleton()` 会被拆分为三步：分配内存 → 构造对象 → 赋值指针。指令重排可能导致先赋值再构造，其他线程拿到的就是一个半初始化的对象。atomic 的 acquire-release 语义保证了正确的可见性。

**Q：C++ 中怎么防止拷贝破坏单例？**
> 删除拷贝构造和赋值运算符：`Singleton(const Singleton&) = delete; Singleton& operator=(const Singleton&) = delete;`

**Q：多个静态单例之间有依赖怎么办？**
> 跨编译单元的 static 对象初始化顺序未定义（Static Initialization Order Fiasco）。解决方案：用 Meyers' Singleton（函数内局部 static）替代全局 static，这样初始化顺序由首次调用顺序决定。

### 高分点
> 单例不是"线程安全写出来就完了"，更大的问题在于它会把依赖注入偷换成全局访问，长期可维护性容易变差。面试中推荐直接写 Meyers' Singleton，但要能解释为什么 C++11 之前需要 DCL。

---

## 2. 工厂模式有什么价值？

### 标准回答
工厂模式是**创建型设计模式**，定义创建对象的接口，但由子类/工厂决定实例化哪一个类。将对象的创建和使用分离，客户端只需知道接口而不需了解具体实现细节。

### 三种形式

**① 简单工厂（静态工厂）**

- 一个工厂类，通过参数判断创建哪种产品
- 优点：简单直观
- 缺点：新增产品要修改工厂类，违反开闭原则

```cpp
class Shape {
public:
    virtual void draw() = 0;
    virtual ~Shape() = default;
};
class Circle : public Shape { void draw() override { /* ... */ } };
class Rect : public Shape { void draw() override { /* ... */ } };

// 简单工厂
std::unique_ptr<Shape> createShape(const std::string& type) {
    if (type == "circle") return std::make_unique<Circle>();
    if (type == "rect") return std::make_unique<Rect>();
    return nullptr;
}
```

**② 工厂方法模式**

- 每个具体工厂对应一个具体产品
- 新增产品只需新增工厂类，不改已有代码，**符合开闭原则**
- 缺点：类的数量增多

```cpp
class ShapeFactory {
public:
    virtual std::unique_ptr<Shape> create() = 0;
    virtual ~ShapeFactory() = default;
};
class CircleFactory : public ShapeFactory {
    std::unique_ptr<Shape> create() override { return std::make_unique<Circle>(); }
};
```

**③ 抽象工厂模式**

- 提供创建**一系列相关产品**的接口
- 适合产品族场景（如：不同平台的 UI 控件全家桶）
- 对产品族扩展符合开闭原则；对产品等级扩展会导致所有工厂修改

```cpp
class UIFactory {
public:
    virtual std::unique_ptr<Button> createButton() = 0;
    virtual std::unique_ptr<TextBox> createTextBox() = 0;
    virtual ~UIFactory() = default;
};
class WindowsUIFactory : public UIFactory { /* 返回 Windows 风格控件 */ };
class LinuxUIFactory : public UIFactory { /* 返回 Linux 风格控件 */ };
```

### 为什么创建逻辑值得单独抽出来？
因为在很多系统里，真正容易变化的不是"怎么用对象"，而是：

- 用哪个实现
- 根据什么条件选实现
- 初始化参数和依赖怎么注入

### 三种工厂对比

| 维度 | 简单工厂 | 工厂方法 | 抽象工厂 |
|---|---|---|---|
| 类数量 | 少 | 中 | 多 |
| 开闭原则 | 违反 | 符合 | 产品族符合 |
| 适用场景 | 产品少且固定 | 产品多需扩展 | 产品族 |
| 复杂度 | 低 | 中 | 高 |

### 常见追问

**Q：工厂模式和单例模式的联系？**
> 都是创建型模式。工厂关注"按需创建不同类型的全新对象"；单例关注"确保一个类仅创建唯一实例"。工厂可以内部使用单例管理工厂实例本身。

**Q：什么时候不适合用工厂模式？**
> 对象创建极其简单（一行 new）、产品种类极少且不会扩展、项目是简单小工具时，工厂模式反而增加冗余。

### 高分点
> 工厂模式的核心价值不是"多写一个类"，而是把变化点从业务路径里抽出来。在 C++ 中经常配合 `std::unique_ptr` 返回多态对象。

---

## 3. 观察者模式适合什么场景？

### 标准回答
观察者模式是**行为型设计模式**，定义一对多的对象依赖关系，让多个观察者同时监听某一个主题对象。主题状态变化时通知所有观察者，触发响应行为。

### 四个核心角色
- **抽象主题（Subject）**：定义添加/移除/通知观察者的接口
- **具体主题（ConcreteSubject）**：维护观察者集合，状态变化时调用通知
- **抽象观察者（Observer）**：定义 update 接口
- **具体观察者（ConcreteObserver）**：实现 update，处理通知

### C++ 实现示例
```cpp
class Observer {
public:
    virtual void update(const std::string& msg) = 0;
    virtual ~Observer() = default;
};

class Subject {
    std::vector<std::weak_ptr<Observer>> observers_;  // 用 weak_ptr 避免循环引用
public:
    void attach(std::shared_ptr<Observer> obs) { observers_.push_back(obs); }
    void notify(const std::string& msg) {
        for (auto it = observers_.begin(); it != observers_.end(); ) {
            if (auto sp = it->lock()) { sp->update(msg); ++it; }
            else { it = observers_.erase(it); }  // 自动清理已销毁的观察者
        }
    }
};
```

### 工程场景
- 事件总线、消息订阅
- 配置更新广播
- UI 事件回调
- 指标上报、告警订阅

### 为什么在 C++ 里容易出坑？
因为 C++ 需要手动管理对象生命周期：

- 被观察者先销毁 → 观察者持有悬垂指针
- 观察者先销毁 → 主题通知时触发 UB
- 回调里再取消订阅 → 遍历中修改容器导致迭代器失效
- 如果用 `shared_ptr` 互相持有 → 循环引用导致内存泄漏

**解决方案：用 `weak_ptr` 存储观察者引用，通知时 lock 检查有效性。**

### 常见追问

**Q：观察者模式和发布-订阅模式有什么区别？**
> 观察者模式是直接依赖：主题直接持有观察者引用。发布-订阅引入中间层（消息队列/事件总线），发布者和订阅者完全解耦。前者适合单机轻量场景，后者适合分布式大型系统。

**Q：观察者通知是同步还是异步？**
> 默认同步（遍历调用 update）。如果 update 耗时长会阻塞主题。可以改用线程池异步通知，但要注意线程安全和观察者生命周期。

### 高分点
> 观察者模式真正难的不是"通知多个对象"，而是订阅关系的生命周期管理，尤其在 C++ 里要警惕悬垂回调和循环持有。

---

## 3.5 建造者模式（Builder Pattern）

### 标准回答
建造者模式是**创建型设计模式**，将复杂对象的构建过程与表示分离，把构建步骤拆分为固定的模板，通过不同的建造者实现不同的配置，使得**相同的构建过程能够得出不同的对象**。

### 四个角色
- **Product（产品）**：被构建的复杂对象
- **Builder（抽象建造者）**：定义构建步骤的接口
- **ConcreteBuilder（具体建造者）**：实现各步骤，创建具体部件
- **Director（指挥者）**：控制构建流程，按顺序调用建造者

### C++ 实现（链式调用风格，更常见）
```cpp
class HttpRequest {
    std::string url_;
    std::string method_;
    std::map<std::string, std::string> headers_;
    std::string body_;
public:
    class Builder {
        HttpRequest req_;
    public:
        Builder& url(const std::string& u) { req_.url_ = u; return *this; }
        Builder& method(const std::string& m) { req_.method_ = m; return *this; }
        Builder& header(const std::string& k, const std::string& v) {
            req_.headers_[k] = v; return *this;
        }
        Builder& body(const std::string& b) { req_.body_ = b; return *this; }
        HttpRequest build() { return std::move(req_); }
    };
};

// 使用
auto req = HttpRequest::Builder()
    .url("https://api.example.com")
    .method("POST")
    .header("Content-Type", "application/json")
    .body("{\"key\": \"value\"}")
    .build();
```

### 解决什么问题？
- 构造函数参数过多、可选参数组合爆炸
- 构建步骤有固定顺序但部件可变
- 需要构建不同配置的同类对象

### 常见追问

**Q：建造者模式和工厂模式有什么区别？**
> 工厂模式关注**快速创建对象**，一步到位返回产品；建造者模式关注**复杂对象的分步构建**，允许灵活配置部件。

**Q：什么时候用建造者？**
> 当对象有 4 个以上可选参数，或构建步骤有顺序约束时，建造者比多参数构造函数更清晰。

### 高分点
> C++ 中链式 Builder 比经典四角色 Builder 更常用。核心价值是把"构造器参数爆炸"变成可读的链式调用，同时保证对象构建的完整性。

---

## 3.6 代理模式（Proxy Pattern）

### 标准回答
代理模式是**结构型设计模式**，在访问某个对象时引入代理对象，通过代理控制对原始对象的访问。不修改目标对象的代码，通过代理在核心方法前后添加额外逻辑。

### 三个角色
- **Subject（抽象主题）**：定义代理和真实对象的共同接口
- **RealSubject（真实主题）**：实际执行业务逻辑
- **Proxy（代理）**：持有真实主题的引用，控制访问并添加增强逻辑

### C++ 实现
```cpp
class Database {
public:
    virtual std::string query(const std::string& sql) = 0;
    virtual ~Database() = default;
};

class RealDatabase : public Database {
public:
    std::string query(const std::string& sql) override {
        // 实际执行 SQL 查询
        return "result of: " + sql;
    }
};

class DatabaseProxy : public Database {
    std::unique_ptr<RealDatabase> real_;
    bool checkPermission() { /* 权限校验 */ return true; }
public:
    DatabaseProxy() : real_(std::make_unique<RealDatabase>()) {}
    std::string query(const std::string& sql) override {
        if (!checkPermission()) return "access denied";
        auto start = std::chrono::steady_clock::now();     // 前置增强：计时
        auto result = real_->query(sql);                    // 调用真实对象
        auto elapsed = std::chrono::steady_clock::now() - start;
        log("query took " + std::to_string(elapsed.count())); // 后置增强：日志
        return result;
    }
};
```

### 四种应用类型
- **远程代理**：为远程对象提供本地访问（如 RPC stub）
- **虚拟代理**：延迟加载大对象（如图片懒加载）
- **保护代理**：控制访问权限
- **智能引用**：附加操作（如引用计数，`shared_ptr` 本身就是一种智能引用代理）

### 常见追问

**Q：代理模式和装饰器模式的区别？**
> 代理模式的核心是**控制访问**（决定能不能调），真实对象的核心逻辑不变；装饰器模式的核心是**增加功能**（丰富核心业务能力），可以层层嵌套叠加。

**Q：C++ 中 `shared_ptr` 和代理模式的关系？**
> `shared_ptr` 是一种智能引用代理，在访问原始指针之上增加了引用计数和自动释放的增强逻辑。

### 高分点
> 代理模式在 C++ 中非常普遍：智能指针、RPC stub、缓存代理、权限校验代理。关键是理解"代理控制访问，装饰器增加功能"的区别。

---

## 3.7 策略模式（Strategy Pattern）

### 标准回答
策略模式是**行为型设计模式**，定义一系列算法，将每个算法封装起来，使它们可以互相替换。让算法的变化独立于使用算法的客户端。

### 三个角色
- **Context（上下文）**：持有策略接口的引用，通过多态调用不同策略
- **Strategy（策略接口）**：定义算法的抽象接口
- **ConcreteStrategy（具体策略）**：实现具体算法

### C++ 实现
```cpp
// 策略接口
class SortStrategy {
public:
    virtual void sort(std::vector<int>& data) = 0;
    virtual ~SortStrategy() = default;
};

// 具体策略
class QuickSort : public SortStrategy {
    void sort(std::vector<int>& data) override { std::sort(data.begin(), data.end()); }
};
class BubbleSort : public SortStrategy {
    void sort(std::vector<int>& data) override { /* 冒泡排序实现 */ }
};

// 上下文
class Sorter {
    std::unique_ptr<SortStrategy> strategy_;
public:
    void setStrategy(std::unique_ptr<SortStrategy> s) { strategy_ = std::move(s); }
    void doSort(std::vector<int>& data) { strategy_->sort(data); }
};

// 使用
Sorter sorter;
sorter.setStrategy(std::make_unique<QuickSort>());
sorter.doSort(data);
```

### 核心价值
- **消除 if-else / switch 分支**：把条件判断变成多态选择
- **算法可热切换**：运行时动态替换策略
- **符合开闭原则**：新增策略不修改已有代码

### 常见追问

**Q：策略类太多怎么办？**
> 三层优化：① 配合简单工厂，用 map 做策略缓存，O(1) 查询；② 参数化抽离——很多策略只是参数不同，用一个参数化策略类替代多个具体类；③ C++ 可以用 `std::function` + lambda 代替策略类。

**Q：策略模式在 C++ 中的轻量替代？**
> 可以用 `std::function<void(args)>` 作为策略接口，lambda 作为具体策略，无需定义类，更灵活。

### 高分点
> 策略模式在 C++ 中有两种风格：经典多态（适合复杂策略）和 `std::function` + lambda（适合轻量策略）。面试时能说出两种并对比就很加分。

---

## 3.8 装饰器模式（Decorator Pattern）

### 标准回答
装饰器模式是**结构型设计模式**，不修改原始类接口，通过包装的方式给对象**动态地添加功能**。装饰器持有组件引用，自身也实现相同接口，可以层层嵌套叠加功能。

### 四个角色
- **Component（组件接口）**：定义基础功能接口
- **ConcreteComponent（具体组件）**：实现基础功能
- **Decorator（装饰器基类）**：持有组件引用，实现组件接口
- **ConcreteDecorator（具体装饰器）**：添加具体的增强逻辑

### C++ 实现
```cpp
class Stream {
public:
    virtual void write(const std::string& data) = 0;
    virtual ~Stream() = default;
};

class FileStream : public Stream {
public:
    void write(const std::string& data) override { /* 写文件 */ }
};

class StreamDecorator : public Stream {
protected:
    std::unique_ptr<Stream> inner_;
public:
    StreamDecorator(std::unique_ptr<Stream> s) : inner_(std::move(s)) {}
};

class BufferedStream : public StreamDecorator {
    std::string buffer_;
public:
    using StreamDecorator::StreamDecorator;
    void write(const std::string& data) override {
        buffer_ += data;
        if (buffer_.size() > 4096) { inner_->write(buffer_); buffer_.clear(); }
    }
};

class EncryptedStream : public StreamDecorator {
public:
    using StreamDecorator::StreamDecorator;
    void write(const std::string& data) override {
        auto encrypted = encrypt(data);  // 加密后再写
        inner_->write(encrypted);
    }
};

// 使用：层层嵌套
auto stream = std::make_unique<EncryptedStream>(
    std::make_unique<BufferedStream>(
        std::make_unique<FileStream>()));
stream->write("sensitive data");  // 先加密 → 再缓冲 → 最后写文件
```

### 核心价值
- **避免继承爆炸**：n 个功能用继承需要 2^n 个子类，装饰器只需 n 个类自由组合
- **动态组合**：运行时决定叠加哪些功能，随时移除
- **单一职责**：每个装饰器只负责一种增强

### 常见追问

**Q：装饰器模式和代理模式的区别？**
> 装饰器的目的是**功能叠加**（让对象能做更多），由客户端主动选择组合；代理的目的是**控制访问**（决定对象能不能做），客户端可能不知道代理的存在。

**Q：装饰器模式和继承的对比？**
> 继承是静态的编译期绑定，组合方式固定；装饰器是动态的运行时组合，灵活但调试难度更高。

### 高分点
> C++ 标准库的 IO stream 就是装饰器思想的体现。面试中用 IO 流或网络协议栈举例，比抽象描述更有说服力。

---

## 4. 生产者消费者模型怎么实现？

### 标准回答
典型实现是：

- 一个线程安全队列
- 条件变量协调
- 生产者写入任务
- 消费者阻塞等待并取任务执行

### C++ 实现
```cpp
template<typename T>
class BlockingQueue {
    std::queue<T> queue_;
    std::mutex mtx_;
    std::condition_variable cv_not_empty_;
    std::condition_variable cv_not_full_;
    size_t max_size_;
public:
    BlockingQueue(size_t max_size) : max_size_(max_size) {}

    void push(T item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_full_.wait(lock, [this] { return queue_.size() < max_size_; });
        queue_.push(std::move(item));
        cv_not_empty_.notify_one();
    }

    T pop() {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_empty_.wait(lock, [this] { return !queue_.empty(); });
        T item = std::move(queue_.front());
        queue_.pop();
        cv_not_full_.notify_one();
        return item;
    }
};
```

### 面试真正想考什么？
不是只要你写出一个队列，而是看你有没有想到：

- 队列满了怎么办（背压 / 丢弃策略）
- 如何优雅退出（stop 标志 + notify_all）
- 多生产者多消费者怎么减少锁竞争
- 是否会丢任务
- `wait` 必须用 while/lambda 防止虚假唤醒

### 高分点
> 生产者消费者模型的核心不是"有个队列"，而是如何在并发、背压和退出流程之间把边界处理干净。

---

## 🔥 第二层：高频追问

## 5. 线程池设计要点有哪些？

### 标准回答
- 任务队列
- worker 线程集合
- 条件变量/信号量唤醒
- 停止标志
- 拒绝策略
- 任务异常处理

### 更深入的理解
线程池本质在解决两个问题：

1. 避免频繁创建销毁线程
2. 控制并发度，避免系统被任务打爆

### 更强的点可以补什么？
如果你能额外说到：

- 任务窃取
- 动态扩缩容
- 优先级队列
- 长短任务隔离
- 阻塞任务与 CPU 任务分池

通常就已经比"背模板答案"强很多。

### 面试高分点
> 线程池设计不是"线程 + 队列"这么简单，更关键的是饱和时系统怎么退化、任务异常怎么处理、关闭时怎么保证不丢任务。

---

## 6. 高并发系统设计要关注什么？

### 标准回答
常见关注点：

- 限流
- 熔断
- 降级
- 超时控制
- 重试策略
- 线程池隔离
- 缓存设计
- 数据一致性
- 监控与告警

### 为什么这些经常一起出现？
因为高并发系统真正的敌人不是"请求多"，而是：

- 局部放大
- 连锁故障
- 尾延迟扩散
- 资源被慢请求拖死

### 这些机制各自的意义
- **限流**：别让系统被入口流量打穿
- **超时**：别无限等下游
- **重试**：提高成功率，但可能放大流量
- **熔断**：下游明显不行时，先别继续打它
- **降级**：核心服务优先活下来，非核心先牺牲
- **隔离**：别让一个坏依赖拖死整个系统

### 一句总结
> 高并发设计本质上是在做"故障控制"和"资源控制"，不只是把 QPS 顶上去。

---

## 7. 如何设计一个高性能 C++ 服务器？

### 一个比较像面试的答法
1. 网络层：非阻塞 socket + epoll
2. 并发层：IO 线程 + 业务线程池
3. 内存层：对象池 / 合理的内存管理，减少频繁分配
4. 协议层：明确消息边界，避免粘包拆包问题
5. 稳定性层：超时、限流、熔断、日志、监控
6. 数据层：缓存、本地队列、异步落盘/数据库

### 这题为什么不能只讲"用 epoll + 线程池"？
因为服务性能不只取决于网络模型，还取决于：

- 内存分配路径
- 协议解析成本
- 日志/监控开销
- 下游依赖能力
- 热点数据访问模式

### 高分点
> 高性能服务器设计不是一个组件决定的，而是网络、并发、内存、协议和稳定性手段的系统配合。

---

## 💎 第三层：深度难点

## 8. 如果线上 CPU 飙高，你怎么排查？

### 面试回答思路
- 先看整体监控：CPU、负载、QPS、RT、错误率
- 再看进程/线程维度热点
- 用 perf/top/gdb/火焰图定位热点函数
- 分析是业务死循环、锁竞争、自旋、频繁拷贝，还是系统调用过多
- 结合最近发布、流量变化、异常日志回溯

### 面试官更想听什么？
不是一句"我会看 top"，而是：

- 先看现象范围
- 再判断是 CPU 真忙还是调度假忙
- 再定位热点线程和函数
- 最后把热点和最近变更、流量结构联系起来

---

## 9. 如果线上内存持续上涨，你怎么排查？

### 思路
- 区分内存泄漏、缓存膨胀、碎片、对象池回收不及时
- 看 RSS、堆增长、对象数量
- 分析最近变更
- 工具层面可用内存分析器、日志埋点、采样定位

### 高分点
> 内存上涨不等于一定泄漏，也可能是缓存策略变化、内存碎片、对象生命周期拉长，排查时要先分类再下结论。

---

## 10. 项目问题怎么回答更像"会做事的人"？

### 建议结构
- 背景：业务场景和瓶颈是什么
- 问题：为什么原方案不够
- 方案：你做了哪些改动
- 结果：性能、稳定性、资源成本改善多少
- 取舍：方案有什么副作用、未来还能怎么优化

### 为什么这个结构有效？
因为面试官真正想判断的是：

- 你是不是只会堆名词
- 你有没有真正定义问题
- 你有没有验证优化效果
- 你是否知道方案边界

---

## 11. 一组典型追问链

**创建型模式追问链：**

1. 单例有几种写法？C++ 推荐哪种？为什么 DCL 需要 atomic？
2. 工厂模式三种形式各解决什么问题？什么时候不适合用工厂？
3. 建造者模式和工厂模式区别？什么时候用 Builder？

**结构型模式追问链：**

4. 代理模式和装饰器模式区别？`shared_ptr` 是代理还是装饰？
5. 装饰器模式怎么避免继承爆炸？举个 C++ 中的例子？

**行为型模式追问链：**

6. 观察者模式在 C++ 里最大风险是什么？怎么用 `weak_ptr` 解决？
7. 策略模式在 C++ 中有几种实现风格？`std::function` 算不算策略模式？

**系统设计追问链：**

8. 线程池真正难点在哪？饱和时怎么退化？
9. 高并发系统为什么限流、熔断、降级必须成套出现？
10. 高性能服务器设计为什么不能只谈网络层？
11. CPU 飙高和内存上涨排查分别怎么切入？
12. 项目优化题为什么一定要讲结果和取舍？

---

## 12. 设计模式分类速查表

### 创建型模式（管"怎么创建对象"）

| 模式 | 核心思想 | C++ 高频场景 |
|---|---|---|
| **单例** | 全局唯一实例 | 日志、配置、连接池 |
| **工厂方法** | 子类决定创建哪种产品 | 协议解析器、插件加载 |
| **抽象工厂** | 创建一族相关产品 | 跨平台 UI、驱动层 |
| **建造者** | 分步构建复杂对象 | HTTP 请求、配置对象 |
| **原型** | 拷贝已有对象生成新对象 | 对象池、深拷贝场景 |

### 结构型模式（管"怎么组合对象"）

| 模式 | 核心思想 | C++ 高频场景 |
|---|---|---|
| **代理** | 控制访问 | 智能指针、RPC stub、缓存代理 |
| **装饰器** | 动态叠加功能 | IO 流、中间件链 |
| **适配器** | 接口转换 | 旧接口适配新系统 |
| **外观** | 简化复杂子系统接口 | SDK 封装 |

### 行为型模式（管"对象间怎么交互"）

| 模式 | 核心思想 | C++ 高频场景 |
|---|---|---|
| **观察者** | 一对多通知 | 事件系统、配置更新 |
| **策略** | 算法可替换 | 排序策略、计费策略 |
| **模板方法** | 固定流程，子类重写步骤 | 框架回调、生命周期钩子 |
| **迭代器** | 遍历集合 | STL 迭代器 |
| **责任链** | 请求沿链传递 | 中间件、过滤器链 |

---

## 13. 一份更像面试现场的总结回答

> 设计模式和系统设计题真正考的不是"记了多少名字"，而是你能不能把一个工程问题拆开看：哪些部分是变化点，哪些部分是资源瓶颈，哪些部分会在高并发下放大故障。
>
> 创建型模式（单例、工厂、建造者）解决的是"怎么灵活地创建对象"；结构型模式（代理、装饰器）解决的是"怎么组合对象以控制访问或增强功能"；行为型模式（观察者、策略）解决的是"对象之间怎么交互和通信"。
>
> 线程池、限流、熔断、隔离这些机制本质上是在控制资源和故障传播。真正成熟的回答，应该能把"为什么这么设计、有什么代价、上线后怎么验证"说清楚。

---

## 14. 复习建议

至少做到：

- **单例**：能写出 Meyers' Singleton 和 DCL，解释为什么 DCL 需要 atomic
- **工厂**：能区分简单工厂、工厂方法、抽象工厂的适用场景
- **观察者**：能说明 C++ 中生命周期管理的坑和 `weak_ptr` 解决方案
- **建造者**：能用链式 Builder 构建复杂对象，对比工厂模式
- **代理 vs 装饰器**：能清晰区分"控制访问"和"增加功能"
- **策略**：能写多态版本，也能说出 `std::function` 轻量替代方案
- 不把设计模式答成背名词
- 能说明线程池的真实工程边界
- 能把限流、熔断、降级、隔离串成一套稳定性思路
- 能把"高性能服务器设计"讲成系统问题，不只讲 epoll
- 能用结构化方式回答项目优化和线上排障题

做到这里，这一章就开始更像资深面试问答，而不是模式速记表。
