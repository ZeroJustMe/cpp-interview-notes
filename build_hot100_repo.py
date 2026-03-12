# -*- coding: utf-8 -*-
import os, re, json, glob, shutil, subprocess, textwrap
from pathlib import Path

WORKSPACE = Path(r"D:\openclaw\data\.openclaw\workspace")
DOOCS = WORKSPACE / "temp_doocs"
ROOT = WORKSPACE / "leetcode-hot-100-solutions"

PLAN = [
    {"group":"哈希","questions":[[1,"两数之和","two-sum"],[49,"字母异位词分组","group-anagrams"],[128,"最长连续序列","longest-consecutive-sequence"]]},
    {"group":"双指针","questions":[[283,"移动零","move-zeroes"],[11,"盛最多水的容器","container-with-most-water"],[15,"三数之和","3sum"],[42,"接雨水","trapping-rain-water"]]},
    {"group":"滑动窗口","questions":[[3,"无重复字符的最长子串","longest-substring-without-repeating-characters"],[438,"找到字符串中所有字母异位词","find-all-anagrams-in-a-string"]]},
    {"group":"子串","questions":[[560,"和为 K 的子数组","subarray-sum-equals-k"],[239,"滑动窗口最大值","sliding-window-maximum"],[76,"最小覆盖子串","minimum-window-substring"]]},
    {"group":"普通数组","questions":[[53,"最大子数组和","maximum-subarray"],[56,"合并区间","merge-intervals"],[189,"轮转数组","rotate-array"],[238,"除了自身以外数组的乘积","product-of-array-except-self"],[41,"缺失的第一个正数","first-missing-positive"]]},
    {"group":"矩阵","questions":[[73,"矩阵置零","set-matrix-zeroes"],[54,"螺旋矩阵","spiral-matrix"],[48,"旋转图像","rotate-image"],[240,"搜索二维矩阵 II","search-a-2d-matrix-ii"]]},
    {"group":"链表","questions":[[160,"相交链表","intersection-of-two-linked-lists"],[206,"反转链表","reverse-linked-list"],[234,"回文链表","palindrome-linked-list"],[141,"环形链表","linked-list-cycle"],[142,"环形链表 II","linked-list-cycle-ii"],[21,"合并两个有序链表","merge-two-sorted-lists"],[2,"两数相加","add-two-numbers"],[19,"删除链表的倒数第 N 个结点","remove-nth-node-from-end-of-list"],[24,"两两交换链表中的节点","swap-nodes-in-pairs"],[25,"K 个一组翻转链表","reverse-nodes-in-k-group"],[138,"随机链表的复制","copy-list-with-random-pointer"],[148,"排序链表","sort-list"],[23,"合并 K 个升序链表","merge-k-sorted-lists"],[146,"LRU 缓存","lru-cache"]]},
    {"group":"二叉树","questions":[[94,"二叉树的中序遍历","binary-tree-inorder-traversal"],[104,"二叉树的最大深度","maximum-depth-of-binary-tree"],[226,"翻转二叉树","invert-binary-tree"],[101,"对称二叉树","symmetric-tree"],[543,"二叉树的直径","diameter-of-binary-tree"],[102,"二叉树的层序遍历","binary-tree-level-order-traversal"],[108,"将有序数组转换为二叉搜索树","convert-sorted-array-to-binary-search-tree"],[98,"验证二叉搜索树","validate-binary-search-tree"],[230,"二叉搜索树中第 K 小的元素","kth-smallest-element-in-a-bst"],[199,"二叉树的右视图","binary-tree-right-side-view"],[114,"二叉树展开为链表","flatten-binary-tree-to-linked-list"],[105,"从前序与中序遍历序列构造二叉树","construct-binary-tree-from-preorder-and-inorder-traversal"],[437,"路径总和 III","path-sum-iii"],[236,"二叉树的最近公共祖先","lowest-common-ancestor-of-a-binary-tree"],[124,"二叉树中的最大路径和","binary-tree-maximum-path-sum"]]},
    {"group":"图论","questions":[[200,"岛屿数量","number-of-islands"],[994,"腐烂的橘子","rotting-oranges"],[207,"课程表","course-schedule"],[208,"实现 Trie (前缀树)","implement-trie-prefix-tree"]]},
    {"group":"回溯","questions":[[46,"全排列","permutations"],[78,"子集","subsets"],[17,"电话号码的字母组合","letter-combinations-of-a-phone-number"],[39,"组合总和","combination-sum"],[22,"括号生成","generate-parentheses"],[79,"单词搜索","word-search"],[131,"分割回文串","palindrome-partitioning"],[51,"N 皇后","n-queens"]]},
    {"group":"二分查找","questions":[[35,"搜索插入位置","search-insert-position"],[74,"搜索二维矩阵","search-a-2d-matrix"],[34,"在排序数组中查找元素的第一个和最后一个位置","find-first-and-last-position-of-element-in-sorted-array"],[33,"搜索旋转排序数组","search-in-rotated-sorted-array"],[153,"寻找旋转排序数组中的最小值","find-minimum-in-rotated-sorted-array"],[4,"寻找两个正序数组的中位数","median-of-two-sorted-arrays"]]},
    {"group":"栈","questions":[[20,"有效的括号","valid-parentheses"],[155,"最小栈","min-stack"],[394,"字符串解码","decode-string"],[739,"每日温度","daily-temperatures"],[84,"柱状图中最大的矩形","largest-rectangle-in-histogram"]]},
    {"group":"堆","questions":[[215,"数组中的第K个最大元素","kth-largest-element-in-an-array"],[347,"前 K 个高频元素","top-k-frequent-elements"],[295,"数据流的中位数","find-median-from-data-stream"]]},
    {"group":"贪心算法","questions":[[121,"买卖股票的最佳时机","best-time-to-buy-and-sell-stock"],[55,"跳跃游戏","jump-game"],[45,"跳跃游戏 II","jump-game-ii"],[763,"划分字母区间","partition-labels"]]},
    {"group":"动态规划","questions":[[70,"爬楼梯","climbing-stairs"],[118,"杨辉三角","pascals-triangle"],[198,"打家劫舍","house-robber"],[279,"完全平方数","perfect-squares"],[322,"零钱兑换","coin-change"],[139,"单词拆分","word-break"],[300,"最长递增子序列","longest-increasing-subsequence"],[152,"乘积最大子数组","maximum-product-subarray"],[416,"分割等和子集","partition-equal-subset-sum"],[32,"最长有效括号","longest-valid-parentheses"]]},
    {"group":"多维动态规划","questions":[[62,"不同路径","unique-paths"],[64,"最小路径和","minimum-path-sum"],[5,"最长回文子串","longest-palindromic-substring"],[1143,"最长公共子序列","longest-common-subsequence"],[72,"编辑距离","edit-distance"]]},
    {"group":"技巧","questions":[[136,"只出现一次的数字","single-number"],[169,"多数元素","majority-element"],[75,"颜色分类","sort-colors"],[31,"下一个排列","next-permutation"],[287,"寻找重复数","find-the-duplicate-number"]]},
]

ALT = {
1:{"name":"排序 + 双指针","idea":"把数值和原下标打包后排序，再用双指针夹逼寻找目标和。这个方法不如哈希快，但思路直观，适合理解有序数组上的双指针。","tc":"O(n log n)","sc":"O(n)","code":"vector<pair<int,int>> a;\nfor (int i = 0; i < nums.size(); ++i) a.push_back({nums[i], i});\nsort(a.begin(), a.end());\nint l = 0, r = a.size() - 1;\nwhile (l < r) {\n    int s = a[l].first + a[r].first;\n    if (s == target) return {a[l].second, a[r].second};\n    s < target ? ++l : --r;\n}","compare":"哈希表是面试主流；排序 + 双指针更适合从暴力法过渡到线性思维。"},
49:{"name":"计数签名","idea":"对每个字符串统计 26 个字母出现次数，把计数数组序列化后作为哈希键。这样避免对每个字符串单独排序，尤其适合字符集固定的小写字母场景。","tc":"O(n*k)","sc":"O(n*k)","code":"array<int, 26> cnt{};\nfor (char c : s) cnt[c - 'a']++;\nstring key;\nfor (int x : cnt) key += to_string(x) + '#';\nmp[key].push_back(s);","compare":"排序键写起来最短；计数签名在字符集固定时通常更稳，常数也不错。"},
128:{"name":"排序去重","idea":"先排序，再线性扫描连续段长度。虽然时间复杂度退化到 O(n log n)，但实现简单，便于先把题意做对。","tc":"O(n log n)","sc":"O(1) 或 O(log n)","code":"sort(nums.begin(), nums.end());\nint ans = 0, cur = 0, prev = INT_MIN;\nfor (int x : nums) {\n    if (x == prev) continue;\n    cur = (prev != INT_MIN && x == prev + 1) ? cur + 1 : 1;\n    ans = max(ans, cur);\n    prev = x;\n}","compare":"哈希起点法能做到 O(n)；排序法更易写、更适合首次实现。"},
283:{"name":"覆盖写入","idea":"先把所有非零元素顺序写到前面，再把剩余位置补 0。它和双指针本质相同，但从“写结果”角度理解更自然。","tc":"O(n)","sc":"O(1)","code":"int k = 0;\nfor (int x : nums) if (x != 0) nums[k++] = x;\nwhile (k < nums.size()) nums[k++] = 0;","compare":"交换式双指针更像原地稳定 partition；覆盖写入更适合第一次写。"},
11:{"name":"枚举左端点 + 剪枝","idea":"从左到右枚举左端点，右端点逆向尝试，并利用当前最大可能面积做剪枝。最坏仍是平方级，但比纯暴力更容易写出可读版本。","tc":"O(n^2)","sc":"O(1)","code":"int ans = 0;\nfor (int i = 0; i < n; ++i) {\n    if ((n - 1 - i) * height[i] <= ans) continue;\n    for (int j = n - 1; j > i; --j)\n        ans = max(ans, min(height[i], height[j]) * (j - i));\n}","compare":"双指针是标准最优解；枚举 + 剪枝适合帮助理解为什么可以舍弃短板。"},
15:{"name":"哈希判重的两数之和扩展","idea":"固定一个数后，把剩余部分当作 two sum，用哈希表查找第三个数，并用集合去重。写法直接，但去重细节较多。","tc":"O(n^2)","sc":"O(n)","code":"sort(nums.begin(), nums.end());\nset<vector<int>> st;\nfor (int i = 0; i < n; ++i) {\n    unordered_set<int> seen;\n    for (int j = i + 1; j < n; ++j) {\n        int z = -nums[i] - nums[j];\n        if (seen.count(z)) st.insert({nums[i], z, nums[j]});\n        seen.insert(nums[j]);\n    }\n}","compare":"排序 + 双指针更省空间且去重更优雅；哈希版便于从两数之和类比推出。"},
42:{"name":"前后缀最大值","idea":"预处理每个位置左侧最高柱和右侧最高柱，当前位置能接的水就是两者较小值减去本身高度。","tc":"O(n)","sc":"O(n)","code":"vector<int> l(n), r(n);\nl[0] = h[0];\nfor (int i = 1; i < n; ++i) l[i] = max(l[i - 1], h[i]);\nr[n - 1] = h[n - 1];\nfor (int i = n - 2; i >= 0; --i) r[i] = max(r[i + 1], h[i]);\nfor (int i = 0; i < n; ++i) ans += min(l[i], r[i]) - h[i];","compare":"双指针空间更优；前后缀最大值更容易从定义直接推出。"},
3:{"name":"哈希表记录上次位置","idea":"用 last[c] 记录字符最近一次出现的位置，左边界直接跳到重复字符的后一位，不必一点点移动。","tc":"O(n)","sc":"O(|Σ|)","code":"vector<int> last(128, -1);\nfor (int l = 0, r = 0; r < s.size(); ++r) {\n    l = max(l, last[s[r]] + 1);\n    ans = max(ans, r - l + 1);\n    last[s[r]] = r;\n}","compare":"集合版窗口更直观；记录位置版更精炼，常数也更小。"},
438:{"name":"定长窗口 + 频次数组差分","idea":"维护一个长度固定为 |p| 的窗口，用 26 长度数组统计窗口和模式串的频次差。每滑动一步只改两个位置。","tc":"O(n)","sc":"O(1)","code":"array<int,26> need{}, win{};\nfor (char c : p) need[c-'a']++;\nfor (int i = 0; i < s.size(); ++i) {\n    win[s[i]-'a']++;\n    if (i >= p.size()) win[s[i-p.size()]-'a']--;\n    if (win == need) ans.push_back(i - p.size() + 1);\n}","compare":"通用滑窗写法适合举一反三；定长窗口版本更贴合这题本质。"},
560:{"name":"双重循环 + 前缀和","idea":"先求前缀和，再枚举所有区间 [i, j]，用 prefix[j+1]-prefix[i] 判断是否等于 k。虽然是 O(n^2)，但最容易验证正确性。","tc":"O(n^2)","sc":"O(n)","code":"vector<int> pre(n+1);\nfor (int i = 0; i < n; ++i) pre[i+1] = pre[i] + nums[i];\nfor (int i = 0; i < n; ++i)\n  for (int j = i; j < n; ++j)\n    if (pre[j+1] - pre[i] == k) ++ans;","compare":"前缀和 + 哈希是面试标答；双循环前缀和更适合从暴力法过渡。"},
239:{"name":"堆（优先队列）","idea":"用大根堆维护当前窗口候选最大值，堆顶若已经滑出窗口就弹出。这个思路很常见，也容易迁移到别的“滑窗极值”题。","tc":"O(n log n)","sc":"O(n)","code":"priority_queue<pair<int,int>> pq;\nfor (int i = 0; i < n; ++i) {\n    pq.push({nums[i], i});\n    while (pq.top().second <= i - k) pq.pop();\n    if (i >= k - 1) ans.push_back(pq.top().first);\n}","compare":"单调队列能做到线性；堆解法更通用，适合先做对再优化。"},
76:{"name":"暴力枚举起点 + 向右扩张","idea":"对每个起点向右扩张，直到覆盖 t 所有字符后更新答案。配合计数数组能写清楚，但复杂度较高。","tc":"O(n^2 * |Σ|)","sc":"O(|Σ|)","code":"for (int i = 0; i < s.size(); ++i) {\n    array<int,128> cnt = need;\n    int miss = t.size();\n    for (int j = i; j < s.size(); ++j) {\n        if (cnt[s[j]]-- > 0) --miss;\n        if (miss == 0) { update(i, j); break; }\n    }\n}","compare":"双指针滑窗是标准解；暴力扩张更容易解释“为什么窗口能收缩”。"},
53:{"name":"前缀和最小值","idea":"把区间和写成 pre[r]-minPre。扫描前缀和时维护历史最小前缀，就能在线得到以当前位置结尾的最优答案。","tc":"O(n)","sc":"O(1)","code":"int pre = 0, minPre = 0, ans = INT_MIN;\nfor (int x : nums) {\n    pre += x;\n    ans = max(ans, pre - minPre);\n    minPre = min(minPre, pre);\n}","compare":"Kadane 更像状态机；前缀和写法更方便统一到“最大区间和”问题。"},
56:{"name":"差分扫描（适用于整数区间）","idea":"如果区间端点是整数且范围不大，可以用差分记录覆盖次数，再扫描恢复合并后的连续段。","tc":"O(U + n)","sc":"O(U)","code":"// 设所有端点已离散化\ndiff[l]++; diff[r+1]--;\nfor (int i = 0, cur = 0; i < m; ++i) {\n    cur += diff[i];\n    // cur 从 0 到正数表示新区间开始，从正数到 0 表示结束\n}","compare":"排序合并适用范围最广；差分更像思路补充，适合离散坐标题。"},
189:{"name":"额外数组","idea":"开一个同样大小的数组，把 nums[i] 放到 (i + k) % n。逻辑最直接，面试时若先求稳，这个版本非常合适。","tc":"O(n)","sc":"O(n)","code":"vector<int> b(n);\nfor (int i = 0; i < n; ++i) b[(i + k) % n] = nums[i];\nnums = move(b);","compare":"三次翻转是原地最优；额外数组版最容易一次写对。"},
238:{"name":"左右乘积数组","idea":"分别预处理每个位置左侧乘积和右侧乘积，答案就是两者相乘。这是最容易想到的版本。","tc":"O(n)","sc":"O(n)","code":"vector<int> L(n,1), R(n,1), ans(n);\nfor (int i = 1; i < n; ++i) L[i] = L[i-1] * nums[i-1];\nfor (int i = n-2; i >= 0; --i) R[i] = R[i+1] * nums[i+1];\nfor (int i = 0; i < n; ++i) ans[i] = L[i] * R[i];","compare":"把右乘积滚动到变量里可以省掉一个数组；左右数组版更利于理解。"},
41:{"name":"排序后扫描","idea":"排序后忽略非正数和重复值，然后检查第一个不满足“应出现值”的位置。不是最优，但思路清楚。","tc":"O(n log n)","sc":"O(1)","code":"sort(nums.begin(), nums.end());\nint want = 1;\nfor (int x : nums) {\n    if (x < want) continue;\n    if (x == want) ++want;\n    else break;\n}\nreturn want;","compare":"原地哈希是这题核心；排序法更适合先吃透题意。"},
73:{"name":"记录行列集合","idea":"第一遍把需要清零的行和列记录到两个集合，第二遍统一置零。空间更高，但实现最稳。","tc":"O(mn)","sc":"O(m+n)","code":"vector<int> row(m), col(n);\nfor (int i = 0; i < m; ++i)\n  for (int j = 0; j < n; ++j)\n    if (a[i][j] == 0) row[i] = col[j] = 1;\nfor (int i = 0; i < m; ++i)\n  for (int j = 0; j < n; ++j)\n    if (row[i] || col[j]) a[i][j] = 0;","compare":"首行首列打标更省空间；集合记录法更不容易写错。"},
54:{"name":"访问标记 + 方向数组","idea":"用 visited 标记是否访问过，配合四个方向循环前进。每次碰壁就转向，直到取满所有元素。","tc":"O(mn)","sc":"O(mn)","code":"vector<vector<int>> vis(m, vector<int>(n));\nint d = 0, x = 0, y = 0;\nint dx[4]={0,1,0,-1}, dy[4]={1,0,-1,0};\nfor (int k = 0; k < m*n; ++k) {\n    ans.push_back(a[x][y]); vis[x][y] = 1;\n    int nx = x + dx[d], ny = y + dy[d];\n    if (nx<0||nx>=m||ny<0||ny>=n||vis[nx][ny]) d = (d+1)%4;\n    x += dx[d]; y += dy[d];\n}","compare":"按边界收缩更省空间；方向模拟更接近“机器人走格子”的直觉。"},
48:{"name":"四元组轮换","idea":"按层处理，每次把四个对应位置直接轮换。这个做法不需要额外转置，再反转。","tc":"O(n^2)","sc":"O(1)","code":"for (int i = 0; i < n / 2; ++i) {\n  for (int j = i; j < n - 1 - i; ++j) {\n    int t = a[i][j];\n    a[i][j] = a[n-1-j][i];\n    a[n-1-j][i] = a[n-1-i][n-1-j];\n    a[n-1-i][n-1-j] = a[j][n-1-i];\n    a[j][n-1-i] = t;\n  }\n}","compare":"转置 + 每行反转更容易记忆；四元组轮换更贴近原地旋转本质。"},
240:{"name":"逐行二分","idea":"每一行都是有序的，因此可以在每一行上二分查找 target。矩阵较矮时这个方法也很有竞争力。","tc":"O(m log n)","sc":"O(1)","code":"for (auto& row : matrix) {\n    if (binary_search(row.begin(), row.end(), target)) return true;\n}\nreturn false;","compare":"右上角线性缩减是最经典写法；逐行二分更像对有序数组的直接应用。"},
160:{"name":"哈希集合","idea":"先把第一条链表所有节点地址存入哈希集合，再扫描第二条链表，第一个命中的节点就是相交点。","tc":"O(m+n)","sc":"O(m)","code":"unordered_set<ListNode*> st;\nfor (auto p = headA; p; p = p->next) st.insert(p);\nfor (auto p = headB; p; p = p->next) if (st.count(p)) return p;\nreturn nullptr;","compare":"双指针更优雅且 O(1) 空间；哈希法胜在好想、好解释。"},
206:{"name":"递归","idea":"把 head 之后的链表先翻转好，再让 head->next->next 指回 head，最后断开 head->next。","tc":"O(n)","sc":"O(n)","code":"ListNode* reverseList(ListNode* head) {\n    if (!head || !head->next) return head;\n    auto p = reverseList(head->next);\n    head->next->next = head;\n    head->next = nullptr;\n    return p;\n}","compare":"迭代三指针空间更优；递归更适合理解链表翻转的结构。"},
234:{"name":"数组拷贝 + 双指针","idea":"把链表值拷到数组，再判断数组是否回文。不是最省空间，但实现稳定。","tc":"O(n)","sc":"O(n)","code":"vector<int> a;\nfor (auto p = head; p; p = p->next) a.push_back(p->val);\nfor (int l = 0, r = a.size() - 1; l < r; ++l, --r)\n    if (a[l] != a[r]) return false;\nreturn true;","compare":"快慢指针 + 反转后半段才是面试重点；数组法适合先验证逻辑。"},
141:{"name":"哈希集合判重","idea":"遍历链表时把节点地址放入哈希集合，若再次遇到同一节点，说明存在环。","tc":"O(n)","sc":"O(n)","code":"unordered_set<ListNode*> st;\nfor (auto p = head; p; p = p->next) {\n    if (st.count(p)) return true;\n    st.insert(p);\n}\nreturn false;","compare":"快慢指针空间更优；哈希法作为基础解法最容易想到。"},
142:{"name":"哈希集合找首次重复节点","idea":"和判环类似，只是第一次遇到已访问节点时直接返回它，它就是入环点。","tc":"O(n)","sc":"O(n)","code":"unordered_set<ListNode*> st;\nfor (auto p = head; p; p = p->next) {\n    if (st.count(p)) return p;\n    st.insert(p);\n}\nreturn nullptr;","compare":"Floyd 追及法更精妙、空间 O(1)；哈希法更像直译题意。"},
21:{"name":"递归合并","idea":"每次比较两个链表头结点，较小者接上递归合并后的结果。代码很短。","tc":"O(m+n)","sc":"O(m+n)","code":"ListNode* mergeTwoLists(ListNode* a, ListNode* b) {\n    if (!a) return b;\n    if (!b) return a;\n    if (a->val < b->val) { a->next = mergeTwoLists(a->next, b); return a; }\n    b->next = mergeTwoLists(a, b->next); return b;\n}","compare":"迭代更稳，避免深递归；递归版更短更漂亮。"},
2:{"name":"递归模拟进位","idea":"把当前位相加后的进位参数传进下一层递归。只要把链表空节点视为 0，就能写得很整洁。","tc":"O(max(m,n))","sc":"O(max(m,n))","code":"ListNode* dfs(ListNode* a, ListNode* b, int c) {\n    if (!a && !b && !c) return nullptr;\n    int s = c + (a?a->val:0) + (b?b->val:0);\n    auto node = new ListNode(s % 10);\n    node->next = dfs(a?a->next:nullptr, b?b->next:nullptr, s / 10);\n    return node;\n}","compare":"迭代更主流；递归版更接近“逐位相加”的数学描述。"},
19:{"name":"求长度后二次遍历","idea":"先计算链表长度 len，再删除第 len-n+1 个结点。虽然要走两遍，但边界简单。","tc":"O(n)","sc":"O(1)","code":"int len = 0;\nfor (auto p = head; p; p = p->next) ++len;\nListNode dummy(0, head); auto p = &dummy;\nfor (int i = 0; i < len - n; ++i) p = p->next;\np->next = p->next->next;\nreturn dummy.next;","compare":"快慢指针一遍扫描更优；求长度法更适合第一次实现。"},
24:{"name":"递归交换","idea":"把前两个节点交换后，递归处理剩余部分，再接回来。结构清晰。","tc":"O(n)","sc":"O(n)","code":"ListNode* swapPairs(ListNode* head) {\n    if (!head || !head->next) return head;\n    auto nxt = head->next;\n    head->next = swapPairs(nxt->next);\n    nxt->next = head;\n    return nxt;\n}","compare":"迭代更稳定；递归版代码更短。"},
25:{"name":"栈辅助翻转","idea":"每次把 k 个节点压栈，再依次弹出接回结果链表；如果不足 k 个，就按原顺序接回。","tc":"O(n)","sc":"O(k)","code":"stack<ListNode*> st;\nwhile (true) {\n    auto p = cur;\n    for (int i = 0; i < k && p; ++i, p = p->next) st.push(p);\n    if (st.size() < k) break;\n    while (!st.empty()) { tail->next = st.top(); st.pop(); tail = tail->next; }\n    cur = p;\n}","compare":"原地翻转指针更省空间；栈法更好理解。"},
138:{"name":"哈希表映射旧节点到新节点","idea":"第一遍复制所有节点，建立 old->new 映射；第二遍补 next 和 random。","tc":"O(n)","sc":"O(n)","code":"unordered_map<Node*, Node*> mp;\nfor (auto p = head; p; p = p->next) mp[p] = new Node(p->val);\nfor (auto p = head; p; p = p->next) {\n    mp[p]->next = p->next ? mp[p->next] : nullptr;\n    mp[p]->random = p->random ? mp[p->random] : nullptr;\n}\nreturn head ? mp[head] : nullptr;","compare":"穿插复制法空间 O(1) 更妙；哈希映射版更直观。"},
148:{"name":"数组排序后重建","idea":"把节点指针收集到数组里排序，再重新连接 next。工程里很常见，但不满足链表题常见的“纯链表操作”审美。","tc":"O(n log n)","sc":"O(n)","code":"vector<ListNode*> a;\nfor (auto p = head; p; p = p->next) a.push_back(p);\nsort(a.begin(), a.end(), [](auto x, auto y){ return x->val < y->val; });\nfor (int i = 1; i < a.size(); ++i) a[i-1]->next = a[i];\nif (!a.empty()) a.back()->next = nullptr;\nreturn a.empty() ? nullptr : a[0];","compare":"归并排序才是链表排序正解；数组版适合帮助理解“排序后重连”。"},
23:{"name":"分治合并","idea":"把 K 个链表两两合并，类似归并排序。它和堆解法一样能做到 O(N log k)。","tc":"O(N log k)","sc":"O(log k)","code":"ListNode* merge(vector<ListNode*>& a, int l, int r) {\n    if (l == r) return a[l];\n    int m = (l + r) >> 1;\n    return mergeTwoLists(merge(a, l, m), merge(a, m + 1, r));\n}","compare":"堆更通用；分治更像归并排序，代码也很干净。"},
146:{"name":"deque + 哈希（低效版原型）","idea":"如果只想先把功能写出来，可以用双端队列维护访问顺序、哈希表存值；每次命中后在线性删除旧位置。它不是最优，但有助于理解为什么需要双向链表。","tc":"get/put 最坏 O(n)","sc":"O(capacity)","code":"// 原型思路：\n// 1. map[key] = value\n// 2. deque 维护最近使用顺序\n// 3. 命中时从 deque 删除旧 key 再 push_front\n// 4. 超容量时弹出队尾并从 map 删除","compare":"双向链表 + 哈希是标准 O(1) 方案；deque 原型更适合理解需求本身。"},
94:{"name":"递归 DFS","idea":"中序遍历天然满足“左-根-右”，用递归写法最符合定义。","tc":"O(n)","sc":"O(h)","code":"void dfs(TreeNode* root) {\n    if (!root) return;\n    dfs(root->left);\n    ans.push_back(root->val);\n    dfs(root->right);\n}","compare":"栈模拟更通用；递归版最贴合定义。"},
104:{"name":"BFS 层序遍历","idea":"按层遍历二叉树，层数就是最大深度。","tc":"O(n)","sc":"O(w)","code":"queue<TreeNode*> q; q.push(root);\nint depth = 0;\nwhile (!q.empty()) {\n    int sz = q.size(); ++depth;\n    while (sz--) { auto t = q.front(); q.pop();\n        if (t->left) q.push(t->left);\n        if (t->right) q.push(t->right); }\n}","compare":"递归 DFS 更短；BFS 对“按层统计”类问题更自然。"},
226:{"name":"BFS 迭代","idea":"用队列逐层交换每个节点的左右孩子。","tc":"O(n)","sc":"O(w)","code":"queue<TreeNode*> q; q.push(root);\nwhile (!q.empty()) {\n    auto t = q.front(); q.pop();\n    swap(t->left, t->right);\n    if (t->left) q.push(t->left);\n    if (t->right) q.push(t->right);\n}","compare":"递归更简洁；BFS 不依赖递归栈。"},
101:{"name":"迭代队列成对比较","idea":"每次把需要镜像比较的一对节点一起入队，再成对弹出判断。","tc":"O(n)","sc":"O(n)","code":"queue<TreeNode*> q; q.push(root->left); q.push(root->right);\nwhile (!q.empty()) {\n    auto a = q.front(); q.pop();\n    auto b = q.front(); q.pop();\n    if (!a && !b) continue;\n    if (!a || !b || a->val != b->val) return false;\n    q.push(a->left); q.push(b->right);\n    q.push(a->right); q.push(b->left);\n}","compare":"递归更贴合镜像定义；迭代版更方便排查空节点细节。"},
543:{"name":"枚举每个节点为拐点","idea":"对每个节点都重新计算左右子树高度并更新直径。逻辑直接，但会重复计算。","tc":"O(n^2)","sc":"O(h)","code":"int depth(TreeNode* x){ return !x?0:1+max(depth(x->left), depth(x->right)); }\nvoid dfs(TreeNode* x){\n    if (!x) return;\n    ans = max(ans, depth(x->left) + depth(x->right));\n    dfs(x->left); dfs(x->right);\n}","compare":"后序一次遍历是正解；重复求深度版更像从定义出发。"},
102:{"name":"DFS 记录层号","idea":"前序 DFS 时把当前层号 depth 传下去，第一次到达某层就新开一个数组。","tc":"O(n)","sc":"O(h)","code":"void dfs(TreeNode* root, int d) {\n    if (!root) return;\n    if (ans.size() == d) ans.push_back({});\n    ans[d].push_back(root->val);\n    dfs(root->left, d + 1);\n    dfs(root->right, d + 1);\n}","compare":"BFS 是最自然做法；DFS 方案有助于统一树的遍历框架。"},
108:{"name":"递归选中点","idea":"每次选中点作为根，左半段建左子树，右半段建右子树。这个方法本身就是主流，也适合作为“分治建树”模板。","tc":"O(n)","sc":"O(log n)","code":"TreeNode* build(int l, int r){\n    if (l > r) return nullptr;\n    int m = (l + r) >> 1;\n    auto root = new TreeNode(nums[m]);\n    root->left = build(l, m - 1);\n    root->right = build(m + 1, r);\n    return root;\n}","compare":"这题替代方案不多；重点是掌握分治和 BST 性质。"},
98:{"name":"中序遍历转数组","idea":"BST 中序遍历应得到严格递增序列，因此先中序收集，再检查是否递增。","tc":"O(n)","sc":"O(n)","code":"vector<int> a; inorder(root, a);\nfor (int i = 1; i < a.size(); ++i)\n    if (a[i] <= a[i-1]) return false;\nreturn true;","compare":"上下界递归空间更省；转数组法更容易一眼看懂。"},
230:{"name":"中序展开到数组","idea":"BST 中序有序，所以把中序结果存到数组，直接取第 k-1 个元素。","tc":"O(n)","sc":"O(n)","code":"vector<int> a; inorder(root, a);\nreturn a[k - 1];","compare":"迭代中序或统计子树大小更优；数组法最容易实现。"},
199:{"name":"DFS 先右后左","idea":"优先递归右子树，第一次到达某一层时记录该节点值，它一定是该层右视图。","tc":"O(n)","sc":"O(h)","code":"void dfs(TreeNode* root, int d){\n    if (!root) return;\n    if (ans.size() == d) ans.push_back(root->val);\n    dfs(root->right, d + 1);\n    dfs(root->left, d + 1);\n}","compare":"BFS 按层取最后一个更直接；DFS 更节省显式队列。"},
114:{"name":"前序遍历后重连","idea":"先做一次前序遍历收集节点，再按遍历顺序把 left 置空、right 接到下一个节点。","tc":"O(n)","sc":"O(n)","code":"vector<TreeNode*> a; preorder(root, a);\nfor (int i = 1; i < a.size(); ++i) {\n    a[i-1]->left = nullptr;\n    a[i-1]->right = a[i];\n}\nif (!a.empty()) a.back()->left = a.back()->right = nullptr;","compare":"原地后序展开更省空间；重连版更容易写对。"},
105:{"name":"切片递归","idea":"每次在中序里找到根节点位置，然后递归构造左右子树。若直接切片，会有额外拷贝，但写法清楚。","tc":"O(n^2)","sc":"O(n^2)","code":"// 思路：root = preorder[0]\n// 在 inorder 中切出 left / right\n// 再切 preorder 对应区间递归建树","compare":"用哈希表记录中序下标能降到 O(n)；切片法更易理解。"},
437:{"name":"从每个节点向下 DFS","idea":"把每个节点都当作路径起点，再向下统计和为 target 的路径数。概念上最直白。","tc":"O(n^2)","sc":"O(h)","code":"int start(TreeNode* x, long long s){\n    if (!x) return 0;\n    s -= x->val;\n    return (s == 0) + start(x->left, s) + start(x->right, s);\n}\nint pathSum(TreeNode* root, int t){\n    if (!root) return 0;\n    return start(root, t) + pathSum(root->left, t) + pathSum(root->right, t);\n}","compare":"前缀和 + 哈希是优化核心；双 DFS 更适合理解题意。"},
236:{"name":"记录父指针 + 祖先集合","idea":"先 DFS 记录每个节点的父节点，然后从 p 一路向上加入集合，再从 q 向上找到第一个命中者。","tc":"O(n)","sc":"O(n)","code":"unordered_map<TreeNode*, TreeNode*> fa;\nunordered_set<TreeNode*> st;\n// dfs 建 fa\nfor (; p; p = fa[p]) st.insert(p);\nfor (; q; q = fa[q]) if (st.count(q)) return q;","compare":"递归回溯更简洁；父指针法更适合扩展到多次查询。"},
124:{"name":"枚举每个节点为最高点（重复求和）","idea":"如果对每个节点都重新求左右最大贡献，可以写出接近定义的做法，但会重复计算，因此仅作思路补充。","tc":"O(n^2)","sc":"O(h)","code":"// 对每个节点 root：\n// best(root) = root->val + max(0, gain(root->left)) + max(0, gain(root->right))\n// 若 gain 每次都现算，就会退化到 O(n^2)","compare":"后序一次 DFS 是标准解；重复求贡献只适合理解定义。"},
200:{"name":"BFS 染色","idea":"遇到陆地就用队列做一次 BFS，把整个岛屿染成已访问。","tc":"O(mn)","sc":"O(mn)","code":"queue<pair<int,int>> q; q.push({i,j}); grid[i][j] = '0';\nwhile (!q.empty()) {\n    auto [x,y] = q.front(); q.pop();\n    for (auto [dx,dy] : dirs) {\n        int nx = x + dx, ny = y + dy;\n        if (ok(nx,ny) && grid[nx][ny]=='1') {\n            grid[nx][ny]='0'; q.push({nx,ny});\n        }\n    }\n}","compare":"DFS 写法更短；BFS 不会因递归过深而爆栈。"},
994:{"name":"多源 BFS","idea":"把所有初始腐烂橘子一起入队，按层扩散，每一层代表一分钟。这个方法本身就是主流。","tc":"O(mn)","sc":"O(mn)","code":"queue<pair<int,int>> q;\n// 所有 2 入队\nwhile (!q.empty()) {\n    int sz = q.size(); ++mins;\n    while (sz--) { /* 向四周扩散 */ }\n}","compare":"这题重点就是多源 BFS；可把它当作图层次遍历模板。"},
207:{"name":"DFS 判环","idea":"用三色标记：0 未访问，1 访问中，2 已完成。DFS 遇到“访问中”节点就说明有环。","tc":"O(V+E)","sc":"O(V+E)","code":"bool dfs(int u){\n    color[u] = 1;\n    for (int v : g[u]) {\n        if (color[v] == 1) return false;\n        if (color[v] == 0 && !dfs(v)) return false;\n    }\n    color[u] = 2;\n    return true;\n}","compare":"拓扑排序更偏工程；DFS 判环更适合理解 DAG 本质。"},
208:{"name":"数组子节点版 Trie","idea":"每个节点开 26 个子节点指针，适合仅有小写字母的场景，查询速度稳定。","tc":"插入/查询 O(L)","sc":"O(总字符数 * 26 指针开销)","code":"struct Trie {\n    Trie* ch[26]{}; bool end = false;\n    void insert(string s){ Trie* p = this; for(char c: s){ int i=c-'a'; if(!p->ch[i]) p->ch[i]=new Trie(); p=p->ch[i]; } p->end=true; }\n};","compare":"map 版更省稀疏空间；定长数组版更常见、性能也更稳定。"},
46:{"name":"next_permutation 枚举","idea":"先排序，再反复调用 next_permutation 枚举所有排列。若输入无重复元素，这个方法很省脑力。","tc":"O(n * n!)","sc":"O(1)","code":"sort(nums.begin(), nums.end());\ndo ans.push_back(nums); while (next_permutation(nums.begin(), nums.end()));","compare":"回溯更通用，也能扩展到剪枝；库函数枚举更适合快速验证。"},
78:{"name":"位运算枚举","idea":"长度为 n 的数组共有 2^n 个子集，用二进制位表示“选/不选”即可。","tc":"O(n * 2^n)","sc":"O(1) 额外空间","code":"for (int mask = 0; mask < (1 << n); ++mask) {\n    vector<int> cur;\n    for (int i = 0; i < n; ++i) if (mask >> i & 1) cur.push_back(nums[i]);\n    ans.push_back(cur);\n}","compare":"回溯写法更像组合生成；位枚举更适合把问题想成状态空间。"},
17:{"name":"迭代层层扩展","idea":"把每一位数字看成一次笛卡尔积扩展，从空串开始逐位拼接。","tc":"O(3^m 4^n)","sc":"O(答案规模)","code":"vector<string> ans{\"\"};\nfor (char d : digits) {\n    vector<string> nxt;\n    for (auto& s : ans) for (char c : mp[d]) nxt.push_back(s + c);\n    ans.swap(nxt);\n}","compare":"回溯更经典；迭代扩展更像 BFS。"},
39:{"name":"DP / 完全背包风格记录方案","idea":"按目标和从小到大扩展，用 dp[s] 存所有和为 s 的组合。能做出来，但实现复杂，主要用于拓展视野。","tc":"与答案规模相关","sc":"与答案规模相关","code":"// dp[s] 存若干组合\n// 依次枚举 candidate，再从 candidate 到 target 扩展方案","compare":"回溯 + 剪枝更自然；DP 版更适合理解“组合型完全背包”。"},
22:{"name":"按长度递推构造","idea":"把合法括号串看成 '(' + A + ')' + B 的组合，类似卡特兰数递推。","tc":"与答案规模相关","sc":"与答案规模相关","code":"vector<vector<string>> dp(n+1); dp[0]={\"\"};\nfor(int i=1;i<=n;++i)\n  for(int j=0;j<i;++j)\n    for(auto &a:dp[j]) for(auto &b:dp[i-1-j])\n      dp[i].push_back(\"(\"+a+\")\"+b);","compare":"回溯更容易现场写；递推构造更能体现结构规律。"},
79:{"name":"逐起点 DFS + 显式 visited","idea":"为避免改动原板子，可以单独开 visited 数组记录路径上的位置。","tc":"O(mn * 3^L)","sc":"O(mn)","code":"vector<vector<int>> vis(m, vector<int>(n));\nbool dfs(int x,int y,int k){\n    if(board[x][y]!=word[k]) return false;\n    if(k==word.size()-1) return true;\n    vis[x][y]=1;\n    for(auto [dx,dy]:dirs){...}\n    vis[x][y]=0; return false;\n}","compare":"原地标记更省空间；visited 版更安全。"},
131:{"name":"先预处理回文表，再回溯","idea":"先用 DP 求出任意区间是否回文，回溯时 O(1) 判断是否可切。","tc":"O(n^2 + 答案规模)","sc":"O(n^2)","code":"for (int i = n - 1; i >= 0; --i)\n  for (int j = i; j < n; ++j)\n    isPal[i][j] = s[i] == s[j] && (j - i < 2 || isPal[i+1][j-1]);","compare":"边搜边判断更省预处理；回文表版本更适合剪枝。"},
51:{"name":"集合记录列与对角线","idea":"分别记录列、主对角线、副对角线是否已被占用，是最经典也最稳的 N 皇后写法。","tc":"O(n!)","sc":"O(n)","code":"vector<int> col(n), d1(2*n), d2(2*n);\nvoid dfs(int r){\n  for(int c=0;c<n;++c) if(!col[c]&&!d1[r-c+n]&&!d2[r+c]){\n    col[c]=d1[r-c+n]=d2[r+c]=1;\n    // 放皇后\n    dfs(r+1);\n    col[c]=d1[r-c+n]=d2[r+c]=0;\n  }\n}","compare":"位运算版更快；集合数组版更适合讲解。"},
35:{"name":"线性扫描","idea":"从左到右找第一个大于等于 target 的位置。简单但没有利用有序性。","tc":"O(n)","sc":"O(1)","code":"for (int i = 0; i < nums.size(); ++i)\n    if (nums[i] >= target) return i;\nreturn nums.size();","compare":"二分才是应有之义；线性版适合作为对照。"},
74:{"name":"两次二分","idea":"先二分确定 target 可能落在哪一行，再在该行做一次标准二分。","tc":"O(log m + log n)","sc":"O(1)","code":"int row = upper_bound(firstCol.begin(), firstCol.end(), target) - firstCol.begin() - 1;\nif (row < 0) return false;\nreturn binary_search(matrix[row].begin(), matrix[row].end(), target);","compare":"整体拉平成一维更统一；两次二分更符合矩阵结构。"},
34:{"name":"线性扩张","idea":"先二分找到一个 target，再向左右扩张找边界。平均可接受，但最坏退化。","tc":"O(log n + k)","sc":"O(1)","code":"int p = lower_bound(nums.begin(), nums.end(), target) - nums.begin();\nif (p == n || nums[p] != target) return {-1,-1};\nint l = p, r = p;\nwhile (l-1 >= 0 && nums[l-1] == target) --l;\nwhile (r+1 < n && nums[r+1] == target) ++r;","compare":"双 lower/upper bound 最稳；扩张版更容易想到。"},
33:{"name":"先找旋转点再二分","idea":"先二分找到最小值位置 pivot，再判断 target 落在左段还是右段，最后做一次普通二分。","tc":"O(log n)","sc":"O(1)","code":"int p = findMinIndex(nums);\nif (target >= nums[p] && target <= nums[n-1]) return bin(p, n-1);\nreturn bin(0, p-1);","compare":"一次二分更精炼；先找旋转点更容易理清逻辑。"},
153:{"name":"线性扫描","idea":"从左到右扫一遍，维护最小值。作为基线方法足够直白。","tc":"O(n)","sc":"O(1)","code":"int ans = nums[0];\nfor (int x : nums) ans = min(ans, x);\nreturn ans;","compare":"二分利用了旋转有序结构；线性法仅用于对照。"},
4:{"name":"合并到中位数位置","idea":"像归并两个有序数组那样只走到第 k 个位置，不需要真的合并全部元素。","tc":"O(m+n)","sc":"O(1)","code":"int need = (m+n)/2;\nint i=0,j=0,pre=0,cur=0;\nfor(int k=0;k<=need;++k){\n  pre=cur;\n  if(j==n || (i<m && a[i]<b[j])) cur=a[i++]; else cur=b[j++];\n}\nreturn ((m+n)&1)?cur:(pre+cur)/2.0;","compare":"二分划分是本题精华；归并思路更易接受。"},
20:{"name":"反复消去配对括号","idea":"不断把 \"()\"、\"[]\"、\"{}\" 从字符串中删除，最后若为空串则合法。","tc":"最坏 O(n^2)","sc":"O(n)","code":"string t = s;\nwhile (true) {\n    string u = regex_replace(t, regex(\"\\\\(\\\\)|\\\\[\\\\]|\\\\{\\\\}\"), \"\");\n    if (u == t) break;\n    t = u;\n}\nreturn t.empty();","compare":"栈法才是标准做法；消去法更像“字符串重写”视角。"},
155:{"name":"双栈","idea":"一个栈存原值，另一个栈存当前最小值。最小栈的核心思想一眼就能看懂。","tc":"各操作 O(1)","sc":"O(n)","code":"stack<int> st, mn;\nvoid push(int x){ st.push(x); mn.push(mn.empty()?x:min(x,mn.top())); }\nvoid pop(){ st.pop(); mn.pop(); }\nint getMin(){ return mn.top(); }","compare":"单栈存差值更省空间技巧；双栈版最稳、最常见。"},
394:{"name":"递归下降解析","idea":"遇到数字就解析重复次数，遇到左括号就递归解析子表达式，直到右括号返回。","tc":"O(n)","sc":"O(n)","code":"string dfs(){\n    string res; int num = 0;\n    while (i < s.size() && s[i] != ']') {\n        if (isdigit(s[i])) num = num*10 + s[i++]-'0';\n        else if (s[i] == '[') { ++i; string t = dfs(); while (num--) res += t; num = 0; }\n        else res += s[i++];\n    }\n    ++i; return res;\n}","compare":"双栈法更模板化；递归下降更像真正解析器。"},
739:{"name":"从右往左暴力跳","idea":"对每一天向右找更高温度，找到就更新答案。可在某些数据上配合 ans 跳步，但最坏仍是平方级。","tc":"O(n^2)","sc":"O(1)","code":"for (int i = n - 1; i >= 0; --i)\n  for (int j = i + 1; j < n; ++j)\n    if (t[j] > t[i]) { ans[i] = j - i; break; }","compare":"单调栈是正解；暴力法适合帮助理解题目需求。"},
84:{"name":"枚举高度向两侧扩张","idea":"以每个柱子作为矩形最低高度，向左右扩张到第一个更矮柱子。最坏平方级。","tc":"O(n^2)","sc":"O(1)","code":"for (int i = 0; i < n; ++i) {\n    int l = i, r = i;\n    while (l - 1 >= 0 && h[l - 1] >= h[i]) --l;\n    while (r + 1 < n && h[r + 1] >= h[i]) ++r;\n    ans = max(ans, h[i] * (r - l + 1));\n}","compare":"单调栈是面试主解；扩张法更直观。"},
215:{"name":"排序","idea":"直接排序后取第 k 个位置。不是最优，但简单可靠。","tc":"O(n log n)","sc":"O(log n)","code":"sort(nums.begin(), nums.end(), greater<int>());\nreturn nums[k - 1];","compare":"堆和快选更优；排序法适合先求稳。"},
347:{"name":"排序统计频次","idea":"先统计每个数出现次数，再把 (频次, 数值) 排序，取前 k 个。","tc":"O(n log n)","sc":"O(n)","code":"unordered_map<int,int> cnt;\nfor(int x: nums) cnt[x]++;\nvector<pair<int,int>> a;\nfor(auto &[x,c]: cnt) a.push_back({c,x});\nsort(a.rbegin(), a.rend());","compare":"堆 / 桶排序更适合大数据；排序版实现成本最低。"},
295:{"name":"有序容器维护整体有序","idea":"用 multiset 存所有数，并维护一个指向中位数附近的迭代器。插入时按位置调整迭代器。","tc":"插入 O(log n)，查询 O(1)","sc":"O(n)","code":"multiset<int> st;\nauto mid = st.end();\n// addNum 时插入并根据 st.size() 奇偶和插入位置调整 mid","compare":"双堆更经典也更稳定；有序容器版更像“在线维护有序序列”。"},
121:{"name":"暴力枚举买卖日","idea":"枚举买入日和卖出日，更新最大利润。这个方法很慢，但有助于理解为什么最终只需要维护历史最低价。","tc":"O(n^2)","sc":"O(1)","code":"for (int i = 0; i < n; ++i)\n  for (int j = i + 1; j < n; ++j)\n    ans = max(ans, prices[j] - prices[i]);","compare":"贪心一遍扫描是标准解；暴力法适合作为推导起点。"},
55:{"name":"DP 判断可达","idea":"dp[i] 表示能否到达位置 i，若存在 j<i 且 j 可达并且 j+nums[j]>=i，则 dp[i]=true。","tc":"O(n^2)","sc":"O(n)","code":"vector<int> dp(n); dp[0] = 1;\nfor (int i = 1; i < n; ++i)\n  for (int j = 0; j < i; ++j)\n    if (dp[j] && j + nums[j] >= i) { dp[i] = 1; break; }","compare":"贪心维护最远可达更优；DP 更符合“状态转移”思路。"},
45:{"name":"DP 最少步数","idea":"dp[i] 表示到达 i 的最少步数，转移自所有能跳到 i 的 j。","tc":"O(n^2)","sc":"O(n)","code":"vector<int> dp(n, 1e9); dp[0] = 0;\nfor (int i = 1; i < n; ++i)\n  for (int j = 0; j < i; ++j)\n    if (j + nums[j] >= i) dp[i] = min(dp[i], dp[j] + 1);","compare":"分层贪心是本题精华；DP 版更容易从定义出发。"},
763:{"name":"区间合并视角","idea":"先记录每个字符第一次和最后一次出现位置，把每个字符看成一个区间；排序后做区间合并，得到的块就是答案。","tc":"O(n + |Σ| log |Σ|)","sc":"O(|Σ|)","code":"// 记录每个字符 [first,last]\n// 对这些区间排序并合并，块长度即答案","compare":"直接扫描最后出现位置更简洁；区间视角更统一。"},
70:{"name":"记忆化搜索","idea":"把到第 n 阶的方法数拆成到 n-1 和 n-2 的方法数之和，用 memo 避免重复计算。","tc":"O(n)","sc":"O(n)","code":"int dfs(int n){\n    if(n<=2) return n;\n    if(memo[n]) return memo[n];\n    return memo[n] = dfs(n-1) + dfs(n-2);\n}","compare":"滚动数组更省空间；记忆化更容易从递归式出发。"},
118:{"name":"组合数公式","idea":"第 i 行第 j 个数等于 C(i, j)，可以按组合数递推生成每一行。","tc":"O(numRows^2)","sc":"O(1) 额外空间","code":"for (int i = 0; i < numRows; ++i) {\n    vector<int> row(i + 1, 1);\n    long long cur = 1;\n    for (int j = 1; j < i; ++j) {\n        cur = cur * (i - j + 1) / j; row[j] = cur;\n    }\n}","compare":"递推相加更直观；组合数法更有数学味道。"},
198:{"name":"记忆化搜索","idea":"对于位置 i，选择“偷 i”或“不偷 i”，递归到子问题并缓存结果。","tc":"O(n)","sc":"O(n)","code":"int dfs(int i){\n    if(i >= n) return 0;\n    if(memo[i] != -1) return memo[i];\n    return memo[i] = max(dfs(i+1), nums[i] + dfs(i+2));\n}","compare":"迭代 DP 更省栈；记忆化更容易从选择树出发。"},
279:{"name":"BFS 分层减平方数","idea":"把每个数看成节点，从 n 开始每次减去一个完全平方数，层数就是最少个数。","tc":"O(n * sqrt(n))","sc":"O(n)","code":"queue<int> q; q.push(n);\nvector<int> vis(n+1); vis[n]=1;\nfor(int step=1; !q.empty(); ++step){\n  int sz=q.size();\n  while(sz--){ int x=q.front(); q.pop();\n    for(int i=1;i*i<=x;++i){ int y=x-i*i; if(y==0) return step; if(!vis[y]) vis[y]=1,q.push(y); }\n  }\n}","compare":"DP 更稳定；BFS 把题目转成最短路问题很有启发性。"},
322:{"name":"记忆化搜索","idea":"定义 dfs(rem) 为凑出 rem 的最少硬币数，枚举最后一枚硬币并缓存结果。","tc":"O(amount * n)","sc":"O(amount)","code":"int dfs(int rem){\n    if(rem==0) return 0;\n    if(rem<0) return INF;\n    if(memo[rem]!=-2) return memo[rem];\n    int ans=INF;\n    for(int c:coins) ans=min(ans, dfs(rem-c)+1);\n    return memo[rem]=ans;\n}","compare":"迭代完全背包更常规；记忆化更接近“枚举最后一步”。"},
139:{"name":"记忆化 DFS + 前缀匹配","idea":"从下标 i 出发，尝试匹配字典中的单词，若某个前缀匹配成功且剩余部分可拆分，则返回 true。","tc":"O(n^2)","sc":"O(n)","code":"bool dfs(int i){\n    if(i==n) return true;\n    if(memo[i]!=-1) return memo[i];\n    for(auto &w: dict) if(s.compare(i, w.size(), w)==0 && dfs(i+w.size())) return memo[i]=1;\n    return memo[i]=0;\n}","compare":"DP 更稳定；记忆化更像搜索。"},
300:{"name":"O(n^2) DP","idea":"dp[i] 表示以 nums[i] 结尾的 LIS 长度，向前枚举所有 j<i 且 nums[j]<nums[i]。","tc":"O(n^2)","sc":"O(n)","code":"vector<int> dp(n,1);\nfor(int i=0;i<n;++i)\n  for(int j=0;j<i;++j)\n    if(nums[j]<nums[i]) dp[i]=max(dp[i],dp[j]+1);","compare":"贪心 + 二分更高效；DP 更容易理解“子序列状态”。"},
152:{"name":"朴素 DP 表","idea":"同时维护以 i 结尾的最大乘积和最小乘积，因为负数可能把最小翻成最大。","tc":"O(n)","sc":"O(n)","code":"vector<int> mx(n), mn(n);\nmx[0]=mn[0]=nums[0];\nfor(int i=1;i<n;++i){\n  mx[i]=max({nums[i], mx[i-1]*nums[i], mn[i-1]*nums[i]});\n  mn[i]=min({nums[i], mx[i-1]*nums[i], mn[i-1]*nums[i]});\n}","compare":"滚动变量更省空间；DP 表更便于调试。"},
416:{"name":"二维 0/1 背包","idea":"dp[i][j] 表示前 i 个数能否凑出和 j。空间大一些，但定义清晰。","tc":"O(n * target)","sc":"O(n * target)","code":"vector<vector<int>> dp(n+1, vector<int>(target+1));\ndp[0][0]=1;\nfor(int i=1;i<=n;++i)\n  for(int j=0;j<=target;++j){\n    dp[i][j]=dp[i-1][j];\n    if(j>=nums[i-1]) dp[i][j]|=dp[i-1][j-nums[i-1]];\n  }","compare":"一维滚动更省空间；二维表更适合第一次写。"},
32:{"name":"栈","idea":"栈中保存“最后一个未匹配位置”，遇到 ')' 时弹栈并根据新的栈顶计算长度。","tc":"O(n)","sc":"O(n)","code":"stack<int> st; st.push(-1);\nfor(int i=0;i<s.size();++i){\n  if(s[i]=='(') st.push(i);\n  else { st.pop(); if(st.empty()) st.push(i); else ans=max(ans, i-st.top()); }\n}","compare":"DP 更适合统一括号状态转移；栈法更直观。"},
62:{"name":"组合数学","idea":"从左上到右下总共要走 m-1 次向下和 n-1 次向右，因此答案是 C(m+n-2, m-1)。","tc":"O(min(m,n))","sc":"O(1)","code":"long long ans = 1;\nfor (int i = 1; i <= m - 1; ++i)\n    ans = ans * (n - 1 + i) / i;","compare":"DP 更通用；组合数法最简洁。"},
64:{"name":"原地 DP","idea":"直接把 grid[i][j] 改成到该点的最小路径和，省掉额外数组。","tc":"O(mn)","sc":"O(1)","code":"for(int i=0;i<m;++i)\n  for(int j=0;j<n;++j){\n    if(i==0&&j==0) continue;\n    int up = i?grid[i-1][j]:INT_MAX/2;\n    int left = j?grid[i][j-1]:INT_MAX/2;\n    grid[i][j] += min(up,left);\n  }","compare":"额外 DP 数组更稳；原地修改更省空间。"},
5:{"name":"中心扩展","idea":"以每个字符或字符间隙为中心向两侧扩张，找到最长回文。代码短，常数也不错。","tc":"O(n^2)","sc":"O(1)","code":"auto expand = [&](int l, int r){\n    while(l>=0 && r<n && s[l]==s[r]) --l, ++r;\n    return pair{l+1, r-l-1};\n};","compare":"DP 更适合理解区间状态；中心扩展通常更容易写。"},
1143:{"name":"记忆化搜索","idea":"dfs(i,j) 表示 s1[i:] 和 s2[j:] 的 LCS 长度，相等就同时前进，不等就跳过其中一个。","tc":"O(mn)","sc":"O(mn)","code":"int dfs(int i,int j){\n    if(i==m||j==n) return 0;\n    if(memo[i][j]!=-1) return memo[i][j];\n    if(a[i]==b[j]) return memo[i][j]=1+dfs(i+1,j+1);\n    return memo[i][j]=max(dfs(i+1,j), dfs(i,j+1));\n}","compare":"迭代 DP 更常规；记忆化更接近问题定义。"},
72:{"name":"记忆化搜索","idea":"dfs(i,j) 表示 word1[i:] 转成 word2[j:] 的最小编辑距离，枚举插入、删除、替换。","tc":"O(mn)","sc":"O(mn)","code":"int dfs(int i,int j){\n    if(i==m) return n-j;\n    if(j==n) return m-i;\n    if(memo[i][j]!=-1) return memo[i][j];\n    if(a[i]==b[j]) return memo[i][j]=dfs(i+1,j+1);\n    return memo[i][j]=1+min({dfs(i+1,j), dfs(i,j+1), dfs(i+1,j+1)});\n}","compare":"二维 DP 表更利于现场推导；记忆化更像递归拆问题。"},
136:{"name":"哈希计数","idea":"统计每个数字出现次数，最后找到出现 1 次的数字。","tc":"O(n)","sc":"O(n)","code":"unordered_map<int,int> cnt;\nfor(int x: nums) cnt[x]++;\nfor(auto &[x,c]: cnt) if(c==1) return x;","compare":"异或才是这题核心技巧；哈希法更直白。"},
169:{"name":"排序取中位数","idea":"多数元素出现次数超过一半，因此排序后中间位置一定是它。","tc":"O(n log n)","sc":"O(log n)","code":"sort(nums.begin(), nums.end());\nreturn nums[nums.size()/2];","compare":"摩尔投票是最优、最有价值的方法；排序法胜在好记。"},
75:{"name":"计数排序","idea":"先统计 0/1/2 的个数，再原地回填。","tc":"O(n)","sc":"O(1)","code":"int cnt[3] = {};\nfor(int x: nums) cnt[x]++;\nint k = 0;\nfor(int v=0; v<3; ++v) while(cnt[v]--) nums[k++] = v;","compare":"荷兰国旗单趟更优雅；计数法更容易第一次写对。"},
31:{"name":"全排列枚举","idea":"如果先做过“全排列”题，可以把所有排列按字典序枚举出来，再取当前排列的下一个。显然不适合大数据，仅作思路补充。","tc":"O(n * n!)","sc":"O(n * n!)","code":"// 排序后不断 next_permutation，找到当前排列，再取下一项","compare":"标准原地算法是面试重点；全枚举只用于理解题意。"},
287:{"name":"排序后找相邻相等","idea":"排序后，重复数一定会出现在某对相邻元素中。","tc":"O(n log n)","sc":"O(log n)","code":"sort(nums.begin(), nums.end());\nfor(int i=1;i<nums.size();++i) if(nums[i]==nums[i-1]) return nums[i];","compare":"Floyd 判环或值域二分更符合题目限制；排序法更容易想到。"},
}

# Fallback alternative for any problem not explicitly covered.
FALLBACK = {"name":"朴素 / 备用思路","idea":"先从更直接的思路入手，把题意做对，再回到主流解法优化复杂度。这种写法通常更便于调试与验证。","tc":"视实现而定","sc":"视实现而定","code":"// 可先写出直接版本验证思路，再按主流做法优化","compare":"主流解法负责通过与优化；备用思路负责帮助理解和排错。"}

CATEGORY_MAP = {
    "哈希": ["数组/哈希", "哈希表"],
    "双指针": ["双指针", "数组"],
    "滑动窗口": ["滑窗", "字符串"],
    "子串": ["前缀和", "滑窗", "字符串/数组"],
    "普通数组": ["数组"],
    "矩阵": ["矩阵"],
    "链表": ["链表"],
    "二叉树": ["二叉树", "DFS/BFS"],
    "图论": ["图", "BFS/DFS"],
    "回溯": ["回溯"],
    "二分查找": ["二分"],
    "栈": ["栈", "单调栈"],
    "堆": ["堆 / 优先队列"],
    "贪心算法": ["贪心"],
    "动态规划": ["动态规划"],
    "多维动态规划": ["动态规划"],
    "技巧": ["位运算 / 技巧"]
}

CATEGORY_DIRS = {
    "数组/哈希": [], "双指针": [], "滑窗": [], "栈": [], "堆": [], "链表": [], "二叉树": [],
    "回溯": [], "动态规划": [], "图": [], "二分": [], "贪心": [], "前缀和": [], "位运算": [],
    "矩阵": [], "字符串": []
}


def clean_text(s: str) -> str:
    s = re.sub(r'\$([^$]+)\$', r'\1', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('\\textit{', '').replace('}', '')
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def find_doocs_file(pid: int) -> Path:
    pats = [str(DOOCS / 'solution' / '*' / f'{pid:04d}.*' / 'README.md')]
    for pat in pats:
        found = glob.glob(pat)
        if found:
            return Path(found[0])
    raise FileNotFoundError(pid)


def parse_doocs_first_method(path: Path):
    txt = path.read_text(encoding='utf-8')
    difficulty = ''
    m = re.search(r'difficulty:\s*(.+)', txt)
    if m:
        difficulty = m.group(1).strip()
    tags = re.findall(r'^\s*-\s*(.+)$', txt.split('---', 2)[1], re.M) if txt.startswith('---') else []
    title_m = re.search(r'# \[(\d+)\.\s*(.+?)\]\((https://leetcode.cn/problems/[^)]+)\)', txt)
    link = title_m.group(3) if title_m else ''
    meth_m = re.search(r'###\s*方法[一1]：?\s*(.*?)\n\n(.*?)(?=<!-- tabs:start -->)', txt, re.S)
    if meth_m:
        mname = clean_text(meth_m.group(1))
        body = clean_text(meth_m.group(2))
    else:
        mname, body = '主流解法', '参考公开题解中的主流做法。'
    cpp_m = re.search(r'#### C\+\+\s*\n\n```cpp\n(.*?)\n```', txt, re.S)
    cpp = cpp_m.group(1).strip() if cpp_m else '// 本题的 C++ 关键代码可参考原题解链接。'
    paras = [p.strip() for p in body.split('\n\n') if p.strip()]
    body = '\n\n'.join(paras[:3])
    tc = sc = '见上文分析'
    comp_m = re.search(r'时间复杂度\s*\$?O\(([^$]+)\)\$?，\s*空间复杂度\s*\$?O\(([^$]+)\)', body)
    if comp_m:
        tc, sc = f"O({comp_m.group(1)})", f"O({comp_m.group(2)})"
    else:
        tc_m = re.search(r'时间复杂度\s*([^，。\n]+)', body)
        sc_m = re.search(r'空间复杂度\s*([^，。\n]+)', body)
        if tc_m: tc = tc_m.group(1)
        if sc_m: sc = sc_m.group(1)
    return {"difficulty": difficulty, "tags": tags, "link": link, "method1_name": mname, "method1_body": body, "method1_code": cpp, "tc": tc, "sc": sc}


def tags_for_problem(group, extra_tags):
    tags = []
    mapping = {
        "哈希": ["数组/哈希"], "双指针": ["双指针"], "滑动窗口": ["滑窗", "字符串"],
        "子串": ["前缀和", "滑窗", "字符串"], "普通数组": ["数组/哈希"], "矩阵": ["矩阵"],
        "链表": ["链表"], "二叉树": ["二叉树"], "图论": ["图"], "回溯": ["回溯"],
        "二分查找": ["二分"], "栈": ["栈"], "堆": ["堆"], "贪心算法": ["贪心"],
        "动态规划": ["动态规划"], "多维动态规划": ["动态规划"], "技巧": ["位运算"]
    }
    tags.extend(mapping.get(group, []))
    text = ' '.join(extra_tags)
    if '哈希' in text and '数组/哈希' not in tags: tags.append('数组/哈希')
    if '前缀和' in text and '前缀和' not in tags: tags.append('前缀和')
    if '字符串' in text and '字符串' not in tags: tags.append('字符串')
    if '矩阵' in text and '矩阵' not in tags: tags.append('矩阵')
    if '栈' in text and '栈' not in tags: tags.append('栈')
    if '堆' in text and '堆' not in tags: tags.append('堆')
    if '贪心' in text and '贪心' not in tags: tags.append('贪心')
    if '位运算' in text and '位运算' not in tags: tags.append('位运算')
    return tags


def solution_path(pid, slug):
    return ROOT / 'solutions' / f"{pid:04d}-{slug}" / 'README.md'


def gen_problem_md(pid, title, slug, group, meta, alt):
    alt = alt or FALLBACK
    title_line = f"# {pid}. {title}\n"
    tags = tags_for_problem(group, meta['tags'])
    nav_tags = ' / '.join(tags or [group])
    md = f"""{title_line}
> 题目链接：[{meta['link']}]({meta['link']})  
> 学习计划分组：{group}  
> 难度：{meta['difficulty'] or '未标注'}  
> 导航标签：{nav_tags}

## 题目理解

这道题是 LeetCode Hot 100 中的经典题。做题时建议先把“状态、约束、目标”三个点写清楚：

- **状态是什么**：当前已经处理到哪里、还剩什么信息需要保留；
- **约束是什么**：是否要求原地、是否要求线性时间、是否允许额外空间；
- **目标是什么**：是求一个值、一个区间、一个结构，还是所有可行解。

## 方法一：{meta['method1_name']}

### 思路

{meta['method1_body']}

为了让笔记更可复用，可以把这个方法记成一句话：**先找出题目真正利用的结构，再围绕这个结构设计状态或数据结构**。

### 时间复杂度

- {meta['tc']}

### 空间复杂度

- {meta['sc']}

### 关键代码（C++）

```cpp
{meta['method1_code']}
```

## 方法二：{alt['name']}

### 思路

{alt['idea']}

### 时间复杂度

- {alt['tc']}

### 空间复杂度

- {alt['sc']}

### 关键代码（优先 C++，必要时用伪代码）

```cpp
{alt['code']}
```

## 方法对比

- **方法一**：更接近这题在面试中的主流答案，通常也是最值得熟练掌握的版本。
- **方法二**：{alt['compare']}
- 如果你是第一次做这题，建议顺序是：**先写方法二理解题意，再练方法一压复杂度**。

## 一句话复盘

- 这题真正要记住的不是“答案长什么样”，而是：**{meta['method1_name']} 为什么能抓住题目的关键结构**。

## 参考资料

- 官方题单：LeetCode 热题 100
- 公开资料：doocs/leetcode（本仓库对方法一做了结构化整理，并补充了方法二）
"""
    return md


def ensure_clean_root():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    (ROOT / 'solutions').mkdir(parents=True)
    (ROOT / 'categories').mkdir(parents=True)
    (ROOT / 'scripts').mkdir(parents=True)
    (ROOT / 'data').mkdir(parents=True)


def main():
    ensure_clean_root()
    problems = []
    category_pages = {k: [] for k in CATEGORY_DIRS.keys()}
    for block in PLAN:
        group = block['group']
        for pid, title, slug in block['questions']:
            meta = parse_doocs_first_method(find_doocs_file(pid))
            alt = ALT.get(pid, FALLBACK)
            out = solution_path(pid, slug)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(gen_problem_md(pid, title, slug, group, meta, alt), encoding='utf-8')
            entry = {"id": pid, "title": title, "slug": slug, "group": group, "path": str(out.relative_to(ROOT)).replace('\\\\','/')}
            problems.append(entry)
            for c in tags_for_problem(group, meta['tags']):
                if c in category_pages:
                    category_pages[c].append(entry)
    (ROOT / 'data' / 'hot100.json').write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding='utf-8')

    index_lines = ["# 题解总索引", "", f"共收录 **{len(problems)}** 道 LeetCode Hot 100 题目。", "", "## 按官方题单分组", ""]
    readme_lines = [
        "# LeetCode Hot 100 题解仓库",
        "",
        "一个面向中文读者的 **LeetCode Hot 100** 题解仓库。目标不是只给出答案，而是尽量把每道题写成一份能复习、能对比、能回看的笔记。",
        "",
        "## 这个仓库有什么",
        "",
        "- 基于 **LeetCode 官方热题 100 学习计划** 整理题单；",
        "- 每题至少 **2 种方法**；",
        "- 每种方法都包含：**思路、时间复杂度、空间复杂度、关键代码、方法对比**；",
        "- 提供 **总索引、分类导航、目录化题解**；",
        "- 优先使用 **C++**，个别替代思路用伪代码补充。",
        "",
        "## 仓库结构",
        "",
        "```text",
        "leetcode-hot-100-solutions/",
        "├─ README.md",
        "├─ INDEX.md",
        "├─ data/",
        "│  └─ hot100.json",
        "├─ categories/",
        "│  ├─ arrays-hash.md",
        "│  ├─ two-pointers.md",
        "│  ├─ sliding-window.md",
        "│  ├─ stack.md",
        "│  ├─ heap.md",
        "│  ├─ linked-list.md",
        "│  ├─ binary-tree.md",
        "│  ├─ backtracking.md",
        "│  ├─ dp.md",
        "│  ├─ graph.md",
        "│  ├─ binary-search.md",
        "│  ├─ greedy.md",
        "│  ├─ prefix-sum.md",
        "│  ├─ bit-manipulation.md",
        "│  └─ matrix-and-string.md",
        "└─ solutions/",
        "   └─ 0001-two-sum/README.md ...",
        "```",
        "",
        "## 分类导航",
        "",
        "- [总索引](./INDEX.md)",
        "- [数组 / 哈希](./categories/arrays-hash.md)",
        "- [双指针](./categories/two-pointers.md)",
        "- [滑动窗口](./categories/sliding-window.md)",
        "- [栈 / 单调栈](./categories/stack.md)",
        "- [堆 / 优先队列](./categories/heap.md)",
        "- [链表](./categories/linked-list.md)",
        "- [二叉树](./categories/binary-tree.md)",
        "- [回溯](./categories/backtracking.md)",
        "- [动态规划](./categories/dp.md)",
        "- [图](./categories/graph.md)",
        "- [二分查找](./categories/binary-search.md)",
        "- [贪心](./categories/greedy.md)",
        "- [前缀和](./categories/prefix-sum.md)",
        "- [位运算 / 技巧](./categories/bit-manipulation.md)",
        "- [矩阵 / 字符串](./categories/matrix-and-string.md)",
        "",
        "## 说明",
        "",
        "- 题单来源：LeetCode 热题 100 学习计划页面；",
        "- 方法一主要基于公开资料与通行题解进行结构化整理；",
        "- 方法二强调不同视角：暴力到优化、递归到迭代、哈希到排序、DFS 到 BFS、DP 到贪心等。",
    ]

    for block in PLAN:
        index_lines.append(f"## {block['group']}")
        index_lines.append("")
        readme_lines.append(f"### {block['group']}")
        readme_lines.append("")
        for pid, title, slug in block['questions']:
            rel = f"./solutions/{pid:04d}-{slug}/README.md"
            line = f"- [{pid}. {title}]({rel})"
            index_lines.append(line)
            readme_lines.append(line)
        index_lines.append("")
        readme_lines.append("")

    (ROOT / 'INDEX.md').write_text('\n'.join(index_lines), encoding='utf-8')
    (ROOT / 'README.md').write_text('\n'.join(readme_lines), encoding='utf-8')

    cat_map = {
        'arrays-hash.md': ('数组 / 哈希', ['数组/哈希']),
        'two-pointers.md': ('双指针', ['双指针']),
        'sliding-window.md': ('滑动窗口', ['滑窗']),
        'stack.md': ('栈 / 单调栈', ['栈']),
        'heap.md': ('堆 / 优先队列', ['堆']),
        'linked-list.md': ('链表', ['链表']),
        'binary-tree.md': ('二叉树', ['二叉树']),
        'backtracking.md': ('回溯', ['回溯']),
        'dp.md': ('动态规划', ['动态规划']),
        'graph.md': ('图', ['图']),
        'binary-search.md': ('二分查找', ['二分']),
        'greedy.md': ('贪心', ['贪心']),
        'prefix-sum.md': ('前缀和', ['前缀和']),
        'bit-manipulation.md': ('位运算 / 技巧', ['位运算']),
        'matrix-and-string.md': ('矩阵 / 字符串', ['矩阵', '字符串']),
    }
    for fname, (title, keys) in cat_map.items():
        lines = [f"# {title}", ""]
        selected = []
        for p in problems:
            pfile = ROOT / p['path']
            txt = pfile.read_text(encoding='utf-8')
            if any(k in txt for k in keys):
                selected.append(p)
        for p in selected:
            lines.append(f"- [{p['id']}. {p['title']}](../solutions/{p['id']:04d}-{p['slug']}/README.md) · {p['group']}")
        (ROOT / 'categories' / fname).write_text('\n'.join(lines), encoding='utf-8')

    (ROOT / 'scripts' / 'generate_repo.py').write_text(Path(__file__).read_text(encoding='utf-8'), encoding='utf-8')
    print(f'generated {len(problems)} problems at {ROOT}')

if __name__ == '__main__':
    main()
