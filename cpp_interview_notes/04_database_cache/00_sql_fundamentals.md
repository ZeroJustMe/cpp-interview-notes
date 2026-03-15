# 00. SQL 基础与 MySQL 核心概念（面试必会版）

> 数据库面试里 SQL 基础是第一道门槛。很多人以为"会写 SELECT"就够了，但面试官真正关心的是：
>
> - 你能不能在场景里写出正确的 SQL？
> - 你知不知道一条 SQL 在 MySQL 内部是怎么跑的？
> - 你对范式、引擎、连接池这些概念有没有工程理解？
>
> 这一章按"基础必会 → 高频追问 → 深度难点"三层组织。

---

## ⭐ 第一层：基础必会

### 1. 主键、外键、索引的区别

**主键（Primary Key）：**
- 唯一标识表中每一行，不允许重复，不允许 NULL
- 每个表只能有一个主键
- 通常自动创建聚簇索引（InnoDB）

**外键（Foreign Key）：**
- 一个表中的字段，引用另一个表的主键
- 用于建立表之间的关联关系
- 会增加写操作的检查开销，高性能场景下经常在应用层做约束而非数据库层

**索引（Index）：**
- 用于加速查询的数据结构
- 可以有多个，可以有 NULL 值
- 代价是写入时需要维护索引结构

> **面试高分点：** 主键一定是索引，但索引不一定是主键。外键在工程实践中经常被禁用（高并发写入场景），改由应用层保证一致性。

---

### 2. SQL 语句分类速查

#### 2.1 数据查询（SELECT）

```sql
-- 基础查询
SELECT * FROM users;

-- 指定列
SELECT id, name FROM users;

-- 条件查询
SELECT * FROM users WHERE age > 25;

-- 排序
SELECT * FROM users ORDER BY age DESC;

-- 去重
SELECT DISTINCT city FROM users;

-- 分页
SELECT * FROM users LIMIT 10 OFFSET 20;

-- 别名
SELECT name AS username FROM users;

-- 模糊匹配
SELECT * FROM users WHERE name LIKE 'A%';

-- 范围查询
SELECT * FROM users WHERE age BETWEEN 20 AND 30;

-- 多条件
SELECT * FROM users WHERE age > 20 AND city = 'Beijing';
```

#### 2.2 多表操作（JOIN 与子查询）

```sql
-- 内连接：只返回两表中匹配的行
SELECT u.name, o.amount
FROM users u JOIN orders o ON u.id = o.user_id;

-- 左连接：左表全保留，右表没匹配的填 NULL
SELECT u.name, o.amount
FROM users u LEFT JOIN orders o ON u.id = o.user_id;

-- 右连接：右表全保留，左表没匹配的填 NULL
SELECT u.name, o.amount
FROM users u RIGHT JOIN orders o ON u.id = o.user_id;

-- 子查询（WHERE 中）
SELECT name FROM users
WHERE id IN (SELECT user_id FROM orders);

-- 子查询（FROM 中）
SELECT t.user_id, COUNT(*)
FROM (SELECT * FROM orders WHERE amount > 100) t
GROUP BY t.user_id;
```

> **面试追问：** INNER JOIN 和 LEFT JOIN 的区别？答的时候别只说"一个是交集一个保留左表"，要说清楚 NULL 填充行为和对结果集大小的影响。

#### 2.3 聚合与分组

```sql
-- 总数
SELECT COUNT(*) FROM users;

-- 求和
SELECT SUM(amount) FROM orders;

-- 平均值
SELECT AVG(age) FROM users;

-- 最大/最小值
SELECT MAX(age), MIN(age) FROM users;

-- 分组统计
SELECT city, COUNT(*) FROM users GROUP BY city;

-- 分组条件（HAVING）
SELECT city, COUNT(*) FROM users
GROUP BY city HAVING COUNT(*) > 10;
```

> **WHERE 和 HAVING 的区别：** WHERE 在分组前过滤行，HAVING 在分组后过滤组。WHERE 不能用聚合函数，HAVING 可以。

#### 2.4 数据写入与更新

```sql
-- 插入
INSERT INTO users(name, age) VALUES('Alice', 30);

-- 批量插入
INSERT INTO users(name, age) VALUES ('Bob', 25), ('Cathy', 22);

-- 插入或更新（ON DUPLICATE KEY）
INSERT INTO users(id, name) VALUES (1, 'Tom')
ON DUPLICATE KEY UPDATE name='Tom';

-- 更新
UPDATE users SET age = 28 WHERE id = 1;

-- 删除
DELETE FROM users WHERE age < 18;
```

> **面试注意：** DELETE 不加 WHERE 会删除全表数据。TRUNCATE 和 DELETE 的区别：TRUNCATE 更快（不逐行删）、不走事务日志、不触发触发器、自增 ID 重置。

#### 2.5 索引与性能相关

```sql
-- 查看索引
SHOW INDEX FROM users;

-- 创建索引
CREATE INDEX idx_age ON users(age);

-- 删除索引
DROP INDEX idx_age ON users;

-- 查看执行计划
EXPLAIN SELECT * FROM users WHERE age > 30;

-- 查看慢查询日志配置
SHOW VARIABLES LIKE 'slow_query_log%';

-- 强制使用某个索引
SELECT * FROM users FORCE INDEX (idx_age) WHERE age > 25;
```

#### 2.6 事务与锁操作

```sql
-- 开启事务
START TRANSACTION;  -- 或 BEGIN;

-- 提交
COMMIT;

-- 回滚
ROLLBACK;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- 查看当前隔离级别
SELECT @@transaction_isolation;  -- MySQL 8.0+

-- 悲观锁（SELECT ... FOR UPDATE）
SELECT * FROM users WHERE id = 1 FOR UPDATE;

-- 乐观锁（版本号机制）
UPDATE users SET age = 26, version = version + 1
WHERE id = 1 AND version = 2;
```

---

### 3. 一条 SQL 查询语句在 MySQL 中是怎么执行的？

这是数据库面试最高频的链路题之一。

**执行流程（以 MySQL 8.0 为例）：**

1. **连接器** — 建立 TCP 连接，验证用户名密码，分配线程
2. **解析器** — 词法分析（拆成关键字、标识符、操作符）→ 语法分析（生成抽象语法树 AST）
3. **预处理器** — 检查表名/字段名是否存在，检查权限
4. **优化器** — 基于统计信息和成本模型，选择最优执行计划（索引选择、JOIN 顺序、连接算法）
5. **执行器** — 按执行计划调用存储引擎接口，读取数据，做过滤/排序/聚合
6. **存储引擎**（如 InnoDB）— 从 Buffer Pool 或磁盘读取数据页，返回给执行器
7. **返回结果** — 结果集返回客户端

> **面试高分点：**
> - MySQL 8.0 已经移除了查询缓存（Query Cache），因为在并发写入场景下维护成本高、命中率低
> - 优化器不一定选最好的计划，可以用 `EXPLAIN` 验证
> - 存储引擎是插件式的，InnoDB 和 MyISAM 的行为差异很大

**常见追问：**

**Q：为什么 MySQL 8.0 移除了查询缓存？**
A：因为表一更新缓存就失效，并发写入场景下维护成本远高于收益。现代做法是在应用层用 Redis 等做缓存。

**Q：优化器怎么决定用哪个索引？**
A：基于索引的选择性（区分度）、统计信息（cardinality）和查询条件。可以通过 `EXPLAIN` 查看 `possible_keys` 和 `key` 字段来验证。

**Q：如何分析一条慢 SQL？**
A：① `EXPLAIN` 看执行计划（索引使用、扫描行数）；② 开启慢查询日志捕获耗时操作；③ `SHOW ENGINE INNODB STATUS` 检查锁竞争。

---

### 4. 数据库三大范式

**第一范式（1NF）：原子性**
- 每个字段只能包含不可再分的基本值
- 不允许一个字段存多个值（如"电话1,电话2"）

**第二范式（2NF）：消除部分依赖**
- 满足 1NF
- 所有非主属性完全依赖于主键，不能只依赖主键的一部分
- 主要针对复合主键场景

**第三范式（3NF）：消除传递依赖**
- 满足 2NF
- 非主属性直接依赖于主键，不通过其他非主属性间接依赖
- 例：员工表里不应该同时存"部门 ID"和"部门名称"，部门名称应该放在部门表里

> **工程实践：** 真实项目中不会严格遵守范式。为了查询性能，适度冗余（反范式）是很常见的做法。面试里最好补一句"范式是理论指导，工程上需要根据读写比例做权衡"。

---

## 🔥 第二层：高频追问

### 5. JOIN 操作详解

| 类型 | 说明 |
|---|---|
| INNER JOIN | 只返回两表中匹配的行 |
| LEFT JOIN | 左表全保留，右表不匹配的填 NULL |
| RIGHT JOIN | 右表全保留，左表不匹配的填 NULL |
| FULL OUTER JOIN | 两表都全保留，不匹配的各填 NULL（MySQL 不直接支持，需用 UNION） |
| CROSS JOIN | 笛卡尔积，每行与另一表的每行组合 |

**高频追问：**

**Q：LEFT JOIN 和 INNER JOIN 什么时候结果一样？**
A：当左表的每一行在右表中都有匹配时，LEFT JOIN 退化为 INNER JOIN。

**Q：如果 JOIN 的两个表都很大，性能怎么优化？**
A：① 确保 JOIN 列有索引；② 用小表驱动大表；③ 考虑是否可以先过滤再 JOIN；④ 检查执行计划中的 JOIN 算法（Nested Loop / Hash Join / Sort Merge）。

---

### 6. InnoDB 和 MyISAM 的区别

| 维度 | InnoDB | MyISAM |
|---|---|---|
| 事务支持 | 支持 ACID 事务 | 不支持 |
| 锁粒度 | 行级锁 | 表级锁 |
| 外键 | 支持 | 不支持 |
| 崩溃恢复 | 支持（基于 redo log） | 不支持 |
| 全文索引 | MySQL 5.6+ 支持 | 支持 |
| 存储方式 | 聚簇索引（数据和主键索引一起存） | 堆表（数据和索引分离） |
| COUNT(*) | 需要遍历（有 MVCC 版本） | 有预存的行数，很快 |

> **面试高分点：** MySQL 5.5 以后默认引擎是 InnoDB。选择 MyISAM 的场景已经很少，除非是只读、不需要事务的历史数据表。

---

### 7. 分片（Sharding）和分区（Partitioning）

**分片：**
- 数据水平切分到**多个独立的数据库实例/服务器**
- 每个分片有独立的存储和计算资源
- 适用于大规模分布式系统
- 复杂度高：需要处理路由、跨分片查询、分布式事务

**分区：**
- 单个表的数据按规则划分到**同一个数据库实例内**的多个部分
- 分区之间共享数据库资源
- 适用于管理和查询大表
- 复杂度相对低

> **核心区别：** 分片是跨机器的水平扩展，分区是单机内的数据管理优化。

---

### 8. 数据库连接池

**是什么：** 预先创建并管理一组数据库连接，应用需要时从池中获取，用完归还，而不是每次都创建/销毁。

**为什么要用：**
1. 创建连接开销大（TCP 握手 + 认证 + 分配资源）
2. 连接池复用已有连接，减少延迟
3. 限制最大连接数，保护数据库不被打爆
4. 提高系统稳定性

**常见追问：**

**Q：连接池满了怎么办？**
A：取决于配置——排队等待（设超时）、直接拒绝、或动态扩容。工程上通常设一个合理的最大连接数 + 等待超时。

---

### 9. 面试高频场景 SQL

| 场景 | 思路 |
|---|---|
| 查询每个用户的最后一笔订单 | `GROUP BY user_id` + `MAX(order_time)` 或子查询 + JOIN |
| 查询重复数据 | `GROUP BY` + `HAVING COUNT(*) > 1` |
| 查询某字段为空 | `WHERE phone IS NULL`（注意不能用 `= NULL`） |
| 查询某天注册的用户 | `WHERE DATE(register_time) = '2024-01-01'`（注意：对列用函数会导致索引失效） |
| 分页优化 | 用 `WHERE id > ? LIMIT 10` 代替 `OFFSET`（深度分页时 OFFSET 性能很差） |

> **面试陷阱：** `WHERE DATE(register_time) = '...'` 会让索引失效，因为对索引列用了函数。更好的写法是 `WHERE register_time >= '2024-01-01' AND register_time < '2024-01-02'`。

---

## 💎 第三层：深度难点

### 10. DELETE、TRUNCATE、DROP 的区别

| | DELETE | TRUNCATE | DROP |
|---|---|---|---|
| 操作对象 | 行 | 表数据 | 整张表 |
| 可以加 WHERE | 可以 | 不可以 | 不适用 |
| 事务日志 | 逐行记录 | 不逐行记录 | 不适用 |
| 触发器 | 触发 | 不触发 | 不适用 |
| 自增 ID | 不重置 | 重置 | 不适用 |
| 速度 | 慢（逐行） | 快 | 最快 |
| 可回滚 | 可以（在事务内） | 不可以 | 不可以 |

---

### 11. MySQL 和 Redis 的区别

| 维度 | MySQL | Redis |
|---|---|---|
| 类型 | 关系型数据库 | 键值对/内存数据库 |
| 存储 | 基于磁盘 | 基于内存 |
| 数据结构 | 表/行/列 | String/Hash/List/Set/ZSet 等 |
| 事务 | 完整 ACID | 有限事务支持 |
| 持久化 | redo log + binlog | AOF + RDB |
| 适用场景 | 复杂查询、事务、大量结构化数据 | 缓存、高速读写、计数器、排行榜 |

---

### 12. 数据库备份与恢复策略

**备份类型：**
- **全备份：** 复制整个数据库，恢复简单但耗时耗空间
- **增量备份：** 只备份自上次备份后变化的数据，节省空间但恢复需要链式回放
- **差异备份：** 备份自上次全备份后的变化，恢复比增量简单

**恢复策略：**
- **完全恢复：** 全备份 + 所有增量/差异备份
- **时间点恢复（PITR）：** 利用 binlog 恢复到指定时间点
- **部分恢复：** 只恢复受损的表或分区

> **工程要点：** 备份不等于可恢复。一定要定期做恢复演练，验证备份的完整性。

---

### 13. 表优化常见手段

1. **合理建索引** — 在高频查询列上建索引，但不要建太多（影响写入）
2. **避免 SELECT *** — 只查需要的列，减少 IO 和网络传输
3. **选择合适的数据类型** — TINYINT 代替 INT、VARCHAR 按需分配长度
4. **时间类型用 TIMESTAMP** — 比 DATETIME 省空间
5. **尽量少用 NULL** — NULL 值增加索引和查询优化的复杂度
6. **大表考虑分表** — 水平拆分或垂直拆分
7. **读写分离** — 主库写、从库读

---

## 关联章节

- [MySQL 索引为什么能加速查询？B+ 树原理](./01_mysql_redis.md)
- [MySQL 事务、锁、索引进阶](./02_mysql_transactions_indexes.md)
- [Redis：过期淘汰、持久化、高可用](./03_redis_high_availability.md)
