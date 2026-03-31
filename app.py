from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime
import json

app = FastAPI()

# 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "后端启动成功"}


class OrderItem(BaseModel):
    name: str
    price: float
    count: int
    img: str


class OrderData(BaseModel):
    table_no: str
    items: List[OrderItem]
    total_price: float


# ======================
# 🧾 小票打印
# ======================
def print_receipt(order: OrderData) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "=" * 42
    dash = "-" * 42

    print("\n" + line)
    print("            NEO 点餐系统订单")
    print(line)
    print(f"时间: {now}")
    print(f"桌号: {order.table_no}")
    print(dash)

    total = 0.0

    for idx, item in enumerate(order.items, start=1):
        subtotal = item.price * item.count
        total += subtotal

        print(f"{idx}. {item.name}")
        print(f"   数量: x{item.count}")
        print(f"   单价: €{item.price:.2f}")
        print(f"   小计: €{subtotal:.2f}")
        print(dash)

    print(f"总价: €{total:.2f}")
    print(line + "\n")


# ======================
# 💾 保存 JSON（结构化）
# ======================
def save_order_json(order: OrderData):
    data = order.dict()
    data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except:
        orders = []

    orders.append(data)

    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


# ======================
# 🧾 保存 TXT（小票格式）
# ======================
def save_order_txt(order: OrderData):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "=" * 42
    dash = "-" * 42

    with open("orders.txt", "a", encoding="utf-8") as f:
        f.write("\n" + line + "\n")
        f.write("            NEO 点餐系统订单\n")
        f.write(line + "\n")
        f.write(f"时间: {now}\n")
        f.write(f"桌号: {order.table_no}\n")
        f.write(dash + "\n")

        total = 0.0

        for idx, item in enumerate(order.items, start=1):
            subtotal = item.price * item.count
            total += subtotal

            f.write(f"{idx}. {item.name}\n")
            f.write(f"   数量: x{item.count}\n")
            f.write(f"   单价: €{item.price:.2f}\n")
            f.write(f"   小计: €{subtotal:.2f}\n")
            f.write(dash + "\n")

        f.write(f"总价: €{total:.2f}\n")
        f.write(line + "\n")


# ======================
# 🚀 接收订单
# ======================
@app.post("/api/orders")
def create_order(order: OrderData):
    print_receipt(order)      # 👉 终端小票
    save_order_json(order)    # 👉 保存结构数据
    save_order_txt(order)     # 👉 保存小票文本

    return {
        "success": True,
        "message": "订单已接收"
    }