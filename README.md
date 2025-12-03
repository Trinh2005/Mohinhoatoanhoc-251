```markdown
Dự án này triển khai các kỹ thuật phân tích Petri Net bao gồm:
- Phân tích reachability bằng BFS,
- Phân tích symbolic dựa trên BDD,
- Phát hiện deadlock bằng ILP,
- Tối ưu hóa không gian trạng thái trên BDD.

---

## Cấu trúc dự án

```
├── main.py                 # Chương trình chính
├── petri.py                # Parser cho PNML
├── reachability.py         # BFS Reachability Graph
├── symbolic_bdd.py         # Phân tích symbolic bằng BDD
├── deadlock_ilp.py         # ILP Deadlock Detection
├── optimization.py         # Các kỹ thuật tối ưu trên BDD
└── pnml/                   # Thư mục chứa file PNML
├── simple.pnml
├── philosophers.pnml
└── producer_consumer.pnml
## Cài đặt phụ thuộc

```bash
pip install dd      # Binary Decision Diagrams (BDD)
pip install pulp    # Integer Linear Programming (ILP)
```

---

## Chạy chương trình

### Cú pháp chung:

```bash
python main.py --pnml <tên_file> [tùy_chọn]
```

### Các tùy chọn:

| Tùy chọn     | Chức năng                                       |
| ------------ | ----------------------------------------------- |
| `--edges`    | Hiển thị transitions giữa các marking trong BFS |
| `--symbolic` | Phân tích symbolic bằng BDD (Task 3)            |
| `--deadlock` | Phát hiện deadlock bằng ILP (Task 4)            |
| `--optimize` | Tối ưu hóa BDD (Task 5)                         |

---

## Ví dụ sử dụng

### 1. Chạy BFS cơ bản:

```bash
python main.py --pnml simple.pnml
```

### 2. Chạy BFS và in edges:

```bash
python main.py --pnml simple.pnml --edges
```

### 3. Phân tích symbolic bằng BDD:

```bash
python main.py --pnml philosophers.pnml --symbolic
```

### 4. Phát hiện deadlock (ILP):

```bash
python main.py --pnml philosophers.pnml --deadlock
```

### 5. Tối ưu BDD:

```bash
python main.py --pnml philosophers.pnml --optimize
```