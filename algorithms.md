# LCA专题

## 单次查询
直接dfs，单次时间复杂度O(n)
```C++
public:
    TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
        // Base case：如果 root 是空，或就是 p 或 q，直接返回
        if (!root || root == p || root == q) return root;

        // 在左子树中找 p 或 q
        TreeNode* left = lowestCommonAncestor(root->left, p, q);
        // 在右子树中找 p 或 q
        TreeNode* right = lowestCommonAncestor(root->right, p, q);

        // 情况1：左右都找到 → 当前 root 就是最近公共祖先
        if (left && right) return root;

        // 情况2：只找到一个 → 把那个往上返回
        return left ? left : right;
    }
};
```

## 在线多次查询
使用倍增算法，树形DP记录倍增父亲节点，然后每次查询O(logn)倍增查找lca
```C++
void dfs(int x, int p)//p:父节点
{
	dep[x] = dep[p] + 1;
	fa[x][0] = p;
	for (int i = 1; i <= 20; i++)
	{
		fa[x][i] = fa[fa[x][i - 1]][i - 1];
	}
	for (const auto& y : g[x])
	{
		if (y == p)continue;
		dfs(y, x);
	}
}
 
int lca(int x, int y)
{
	if (dep[x] < dep[y])swap(x, y);
	//贪心,x向上跳，直到与y同层
	for (int i = 20; i >= 0; i--)
	{
		if (dep[fa[x][i]] >= dep[y])x = fa[x][i];
	}
	if (x == y)return x;//二者相同，直接返回
	//与y同层之后，二者同时向上跳,但要保持x！=y
	for (int i = 20; i >= 0; i--)
	{
		if (fa[x][i] != fa[y][i])x = fa[x][i], y = fa[y][i];
	}
	return fa[x][0];// x的父节点就是LCA（此时x和y的父节点相同）
}
```

## 离线多次查询
Tarjan算法，使用并查集
```C++
int root(int x)
{
	return pre[x] = (pre[x] == x ? x : root(pre[x]));
}
vector<int>vec[N];       // 记录需要做lca的点对，就是1到m的查询点
bitset<N>vis;            // 标记节点是否被访问过
map<int, int>lca[N];      // 存储点对的lca结果
/*vis 是一个 bitset，用于标记节点是否已完成所有子树的遍历（即「回溯完成」）。
只有当节点的所有子节点都处理完毕后，才会标记为 true。*/
void tarjan(int x, int father)// Tarjan算法求LCA
{
	fa[x] = father;
	//这一步是在遍历x的所有子节点，及子节点的子节点
	for (const auto& y : g[x])
	{
		if (y == fa[x])continue;
		tarjan(y, x);
		pre[root(y)] = root(x);
		/*当子节点 y 的所有子树都处理完毕后，执行 pre[root(y)] = root(x)：
	将 y 所在集合的根节点（root(y)）合并到 x 所在集合的根节点（root(x)）中。
	这一步的作用是：标记 y 及其子树已处理完毕，并将它们归入 x 的集合，为后续计算 LCA 做准备。*/
		//y是x的子节点，y的根有可能就是x，所以可将y集合并入x集合中
	}
	vis[x] = true;//说明x已经查询过了
	for (const auto& y : vec[x])//处理与x有关的查询，比如我要查询3,5是否有公共祖先，y就是5，x就是3
	{
		if (vis[y])lca[x][y] = lca[y][x] = root(y);//若y也被查询过，说明在之前遍历x及其子树的过程中
		//y出现过了
		//则y与x必然联通，二者必然有lca！
		/*此时 root(y) 之所以是 LCA，原因如下：
		y 已处理完毕，意味着 y 的所有祖先（包括 LCA）都已完成合并，
		root(y) 指向 y 所在分支中最深的已合并祖先。
		x 正在处理中（尚未合并到父节点），而 y 已处理，说明 x 和 y 的公共祖先中，
		最深的那个就是 root(y)（因为 y 已合并到该祖先的集合中，而 x 还未继续向上合并）。*/
	}
}
```
