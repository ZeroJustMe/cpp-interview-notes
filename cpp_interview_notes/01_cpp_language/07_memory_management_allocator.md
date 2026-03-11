# 07. 内存管理、new/delete、内存池、allocator

## 1. new/delete 和 malloc/free 的差异

### 标准回答
- `new`/`delete` 面向对象生命周期
- `malloc`/`free` 只处理原始内存

## 2. operator new 和 placement new 是什么？

### operator new
负责分配原始内存。

### placement new
在一块已分配好的内存上构造对象。

```cpp
void* p = ::operator new(sizeof(A));
A* a = new (p) A();
```

### 追问点
placement new 构造出来的对象，析构和内存释放通常需要手动分离处理。

## 3. delete[] 和 delete 为什么不能混用？

### 标准回答
数组 new 可能需要记录元素数量以正确调用每个元素析构；和单对象 delete 混用会导致未定义行为。

## 4. 什么是内存池？为什么需要？

### 标准回答
内存池通过预分配大块内存，再按需切分给小对象，减少频繁系统分配开销和碎片。

### 适用场景
- 高频创建销毁小对象
- 延迟敏感系统
- 需要稳定分配性能的服务

## 5. STL allocator 是什么？

### 标准回答
allocator 是容器使用的内存分配抽象层，负责对象内存申请、释放以及对象构造/析构相关流程。

## 6. 为什么频繁 new/delete 会影响性能？

- 需要进入分配器逻辑
- 容易产生碎片
- 多线程下可能有锁竞争
- cache 友好性差

## 7. shared_ptr 的控制块里一般有什么？

- 强引用计数
- 弱引用计数
- 删除器
- 可能还有自定义分配器信息

## 8. 面试提示

这一章常和高性能系统挂钩：
- 为什么对象池能提速
- placement new 什么时候用
- allocator 抽象在工程里的意义
