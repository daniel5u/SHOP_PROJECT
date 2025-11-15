
from openai import OpenAI
import random, json
import os, sys
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from products.models import Product
from accounts.models import User
client = OpenAI(
    api_key = "sk-4a893efb69b941ec87b06f4e8501857e",
    base_url = "https://api.deepseek.com/v1",
)
seller = User.objects.first()

prompt = f"Please help me generate 50 products, the products should be diverse, containing different categories in daily life. Each contains keyword of name, description, price, and stock. Please output the result in JSON format."

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
)
print("🔍 Raw model output:\n", response.choices[0].message.content)
raw_output = response.choices[0].message.content.strip()

# 1️⃣ 去掉 ```json 或 ``` 包裹
if raw_output.startswith("```"):
    raw_output = raw_output.strip("`")
    if raw_output.startswith("json"):
        raw_output = raw_output[4:].strip()

# 2️⃣ 解析 JSON
try:
    data = json.loads(raw_output)  # 这里是字典，含 "products"
    products = data["products"]    # 取列表
except Exception as e:
    print("❌ JSON 解析失败，请检查模型输出：")
    print(raw_output)
    raise e

# 3️⃣ 批量创建
for p in products:
    Product.objects.create(
        name=p["name"],
        description=p["description"],
        price=p["price"],
        stock=p["stock"],
        seller=seller,
    )