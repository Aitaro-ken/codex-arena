# Task: stack

## 仕様

LIFO スタックを実装するクラス `Stack`：

```python
class Stack:
    def push(self, item) -> None: ...
    def pop(self) -> object: ...       # 空なら raise IndexError
    def peek(self) -> object: ...      # 空なら raise IndexError
    def is_empty(self) -> bool: ...
    def size(self) -> int: ...
```

## 境界条件

- `pop()` / `peek()` を空スタックに呼ぶと `IndexError` を raise する
- `push` した順の逆順で `pop` できる（LIFO）
- `peek` はスタックを変更しない
- `size()` は常に正確な件数を返す
- `None` を要素として push/pop できる
