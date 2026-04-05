from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pytz
import json
import os
import uuid

app = FastAPI()

# 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ORDERS_JSON_FILE = "orders.json"
ORDERS_TXT_FILE = "orders.txt"


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


class OrderRecord(BaseModel):
    id: str
    table_no: str
    items: List[OrderItem]
    total_price: float
    time: str
    status: str  # new / accepted / done


class UpdateOrderStatus(BaseModel):
    status: str


def get_now_str() -> str:
    tz = pytz.timezone("Europe/Rome")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def load_orders() -> List[dict]:
    if not os.path.exists(ORDERS_JSON_FILE):
        return []

    try:
        with open(ORDERS_JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_orders(orders: List[dict]) -> None:
    with open(ORDERS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


# ======================
# 🧾 小票打印
# ======================
def print_receipt(order: OrderRecord) -> None:
    line = "=" * 42
    dash = "-" * 42

    print("\n" + line)
    print("            NEO 点餐系统订单")
    print(line)
    print(f"订单ID: {order.id}")
    print(f"时间: {order.time}")
    print(f"桌号: {order.table_no}")
    print(f"状态: {order.status}")
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
# 🧾 保存小票文本
# ======================
def append_order_txt(order: OrderRecord) -> None:
    line = "=" * 42
    dash = "-" * 42

    with open(ORDERS_TXT_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + line + "\n")
        f.write("            NEO 点餐系统订单\n")
        f.write(line + "\n")
        f.write(f"订单ID: {order.id}\n")
        f.write(f"时间: {order.time}\n")
        f.write(f"桌号: {order.table_no}\n")
        f.write(f"状态: {order.status}\n")
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
    now = get_now_str()

    order_record = {
        "id": str(uuid.uuid4())[:8],
        "table_no": order.table_no,
        "items": [item.dict() for item in order.items],
        "total_price": order.total_price,
        "time": now,
        "status": "new"
    }

    orders = load_orders()
    orders.insert(0, order_record)  # 新订单放最前面
    save_orders(orders)

    order_obj = OrderRecord(**order_record)
    print_receipt(order_obj)
    append_order_txt(order_obj)

    return {
        "success": True,
        "message": "订单已接收",
        "order": order_record
    }


# ======================
# 📋 获取全部订单
# ======================
@app.get("/api/orders")
def get_orders(status: Optional[str] = None):
    orders = load_orders()

    if status:
        orders = [o for o in orders if o.get("status") == status]

    return {
        "success": True,
        "orders": orders
    }


# ======================
# 🔍 获取单个订单
# ======================
@app.get("/api/orders/{order_id}")
def get_order(order_id: str):
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            return {
                "success": True,
                "order": order
            }

    raise HTTPException(status_code=404, detail="订单不存在")


# ======================
# ✏️ 修改订单状态
# ======================
@app.patch("/api/orders/{order_id}")
def update_order_status(order_id: str, payload: UpdateOrderStatus):
    allowed_status = {"new", "accepted", "done"}

    if payload.status not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail="状态只能是 new / accepted / done"
        )

    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            order["status"] = payload.status
            save_orders(orders)
            return {
                "success": True,
                "message": "订单状态已更新",
                "order": order
            }

    raise HTTPException(status_code=404, detail="订单不存在")