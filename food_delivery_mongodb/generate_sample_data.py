"""
generate_sample_data.py
Generates a synthetic food delivery sample CSV for testing.
Run: python generate_sample_data.py
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

RESTAURANTS = [
    ("Spice Garden", "Indian"),
    ("Pizza Planet", "Pizza"),
    ("Burger Barn", "Burgers"),
    ("Sushi World", "Japanese"),
    ("Taco Town", "Mexican"),
    ("The Pasta House", "Italian"),
    ("Green Bowl", "Healthy"),
    ("Dragon Wok", "Chinese"),
    ("Kebab Corner", "Middle Eastern"),
    ("Sweet Tooth", "Desserts"),
    ("The Grill Station", "BBQ"),
    ("Noodle Bar", "Asian"),
    ("Veggie Delight", "Vegetarian"),
    ("Sea Breeze", "Seafood"),
    ("Mumbai Masala", "Indian"),
]

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]

ITEMS = {
    "Indian": ["Butter Chicken", "Paneer Tikka", "Biryani", "Dal Makhani", "Naan"],
    "Pizza": ["Margherita Pizza", "Pepperoni Pizza", "BBQ Chicken Pizza", "Veggie Supreme"],
    "Burgers": ["Classic Burger", "Cheese Burger", "Chicken Burger", "Vegan Burger"],
    "Japanese": ["California Roll", "Salmon Sashimi", "Ramen", "Tempura"],
    "Mexican": ["Beef Taco", "Chicken Burrito", "Nachos", "Quesadilla"],
    "Italian": ["Spaghetti Carbonara", "Penne Arrabbiata", "Lasagna", "Risotto"],
    "Healthy": ["Quinoa Bowl", "Avocado Toast", "Smoothie Bowl", "Protein Salad"],
    "Chinese": ["Fried Rice", "Dim Sum", "Spring Rolls", "Kung Pao Chicken"],
    "Middle Eastern": ["Shawarma", "Falafel Wrap", "Hummus Platter", "Lamb Kebab"],
    "Desserts": ["Chocolate Cake", "Ice Cream Sundae", "Brownie", "Cheesecake"],
    "BBQ": ["BBQ Ribs", "Grilled Chicken", "Pulled Pork Sandwich", "Corn on the Cob"],
    "Asian": ["Pad Thai", "Pho", "Tom Yum Soup", "Dumplings"],
    "Vegetarian": ["Veggie Wrap", "Stuffed Peppers", "Tofu Stir-Fry", "Mushroom Burger"],
    "Seafood": ["Grilled Fish", "Prawn Curry", "Fish and Chips", "Crab Cake"],
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Cash", "Wallet", "Net Banking"]
ORDER_STATUSES = ["Completed", "Completed", "Completed", "Delivered", "Delivered",
                  "Cancelled", "Pending", "Processing"]

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

rows = []
for i in range(1, 1001):
    restaurant_name, category = random.choice(RESTAURANTS)
    city = random.choice(CITIES)
    item = random.choice(ITEMS.get(category, ["Special Dish"]))
    qty = random.randint(1, 5)
    item_price = round(random.uniform(80, 600), 2)
    discount = round(random.choice([0, 0, 0, item_price * 0.1, item_price * 0.2]), 2)
    delivery_fee = round(random.choice([0, 20, 30, 40, 50]), 2)
    total = round(qty * item_price - discount + delivery_fee, 2)
    order_date = START_DATE + timedelta(
        seconds=random.randint(0, int((END_DATE - START_DATE).total_seconds()))
    )
    delivery_time = random.randint(15, 90) if random.random() > 0.15 else None
    rating = round(random.uniform(2.5, 5.0), 1) if random.random() > 0.2 else None

    rows.append({
        "order_id": f"ORD{i:06d}",
        "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
        "customer_id": f"CUST{random.randint(1, 200):04d}",
        "restaurant_id": f"REST{RESTAURANTS.index((restaurant_name, category)) + 1:03d}",
        "restaurant_name": restaurant_name,
        "city": city,
        "food_category": category,
        "item_name": item,
        "quantity": qty,
        "item_price": item_price,
        "discount": discount,
        "delivery_fee": delivery_fee,
        "total_amount": total,
        "payment_method": random.choice(PAYMENT_METHODS),
        "order_status": random.choice(ORDER_STATUSES),
        "delivery_time_minutes": delivery_time,
        "customer_rating": rating,
    })

output_path = "data/food_delivery_sample.csv"
fieldnames = list(rows[0].keys())

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] Generated {len(rows)} records -> {output_path}")
