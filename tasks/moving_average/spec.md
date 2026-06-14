# Task: moving_average

## 仕様

`moving_average(data: list[float], window: int) -> list[float]`

- `data` の各要素について、直前 `window` 個（自身を含む）の平均を返す
- 先頭 `window-1` 個は、利用可能な要素のみで平均を計算する（前詰め平均）
- 戻り値のリスト長は `data` と同じ
- `window` は 1 以上の整数
- `data` が空のとき空リストを返す
- 各要素の精度誤差は 1e-9 以内

## 例

```
data = [1, 2, 3, 4, 5], window = 3
→ [1.0, 1.5, 2.0, 3.0, 4.0]
  (先頭: [1]/1, [1,2]/2, [1,2,3]/3, [2,3,4]/3, [3,4,5]/3)
```
