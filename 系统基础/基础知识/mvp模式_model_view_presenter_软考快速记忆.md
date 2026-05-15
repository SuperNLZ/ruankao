# MVP（Model–View–Presenter）模式（软考快速记忆）

## 一、MVP 是什么

MVP：

```text
Model – View – Presenter
```

是一种：

```text
界面分层架构模式
```

主要用于：

- GUI程序
- Android早期开发
- 桌面应用
- 前端界面解耦

核心目标：

```text
降低UI与业务逻辑耦合
```

---

# 二、MVP 三层结构

| 层 | 作用 |
|---|---|
| Model | 数据与业务逻辑 |
| View | 界面显示 |
| Presenter | 中间协调者 |

---

# 三、各层职责

## 1. Model（模型层）

负责：

```text
数据
业务逻辑
数据库
网络请求
```

例如：

- 用户信息
- 数据访问
- 订单处理

---

## 2. View（视图层）

负责：

```text
界面显示
用户输入
UI更新
```

特点：

```text
尽量不包含业务逻辑
```

---

## 3. Presenter（表示器层）

负责：

```text
连接 View 和 Model
```

处理：

```text
界面逻辑
交互流程
```

例如：

```text
按钮点击
调用Model
更新View
```

---

# 四、MVP 工作流程

```text
用户操作
   ↓
View 接收事件
   ↓
Presenter 处理逻辑
   ↓
调用 Model
   ↓
返回数据
   ↓
Presenter 更新 View
```

---

# 五、MVP 最大特点（高频）

## View 与 Model 不直接通信

真正通信的是：

```text
Presenter
```

因此：

```text
Presenter 是核心
```

---

# 六、MVP 与 MVC 区别（非常高频）

| 对比 | MVC | MVP |
|---|---|---|
| 核心控制 | Controller | Presenter |
| View与Model | 可能直接通信 | 不直接通信 |
| 耦合度 | 较高 | 更低 |
| UI测试 | 一般 | 更容易 |

---

# 七、MVP 优点

## 1. 降低耦合

```text
UI 和业务逻辑分离
```

---

## 2. 易测试

Presenter：

```text
不依赖具体UI
```

方便单元测试。

---

## 3. 易维护

UI变化：

```text
不影响业务逻辑
```

---

## 4. 代码结构清晰

职责分离明确。

---

# 八、MVP 缺点

## 1. Presenter 容易过大

复杂项目中：

```text
Presenter 代码可能很多
```

---

## 2. 接口数量较多

通常：

```text
View 会定义接口
```

代码量增加。

---

# 九、MVP 图形理解（非常重要）

```text
        用户
         ↓
       View
         ↓
    Presenter
         ↓
       Model
```

数据返回：

```text
Model → Presenter → View
```

---

# 十、软考快速记忆口诀

## MVP 核心

```text
Presenter 当中介
```

---

## MVP 最大特点

```text
View 不碰 Model
```

---

## MVP 目标

```text
UI业务解耦
```

---

# 十一、高频易错点

| 易错点 | 正确理解 |
|---|---|
| View 直接操作 Model | 错，Presenter负责协调 |
| Presenter 负责UI绘制 | 错，View负责显示 |
| Model负责界面逻辑 | 错，Model负责数据与业务 |
| MVP没有业务逻辑 | 错，业务逻辑在Model/Presenter |

---

# 十二、一句话总结

> MVP 模式通过 Presenter 作为中间层，将 View 与 Model 解耦，从而提高系统的可维护性、可测试性和可扩展性。

