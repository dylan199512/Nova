# Customer Order Analysis with Python

A beginner Python project that stores and analyzes customer orders to uncover spending habits and product category trends using core data structures.

---

## Business Problem

Businesses need to understand who their best customers are, what they are buying, and how much they spend. Without complex software, even a small dataset can be hard to read through manually. Python's built-in data structures make it possible to organize raw order data and surface useful insights like top spenders, revenue by category, and customer segmentation.

---

## Dataset

**Self-made dataset** — manually constructed to simulate realistic retail orders.

| Field | Description |
|---|---|
| Customer Name | Name of the buyer |
| Item | Product purchased |
| Price | Amount spent (USD) |
| Category | Product type (e.g., Electronics, Clothing) |

Each customer made one purchase, stored as a tuple inside a list of orders.

Example order: `("Alice", "Laptop", 120.00, "Electronics")`

---

## Tools & Concepts Used

- **Language:** Python 3
- **Data Structures:**
  - `Lists` — stored customer names and all orders
  - `Tuples` — represented each individual order as an immutable record
  - `Dictionaries` — mapped customers to purchases, products to categories, and tracked total spending
  - `Sets` — identified unique product categories and cross-category buyers

No external libraries were used — pure Python only.

---

## Steps

1. **Build the dataset** — Created a list of customer orders, each stored as a tuple `(name, item, price, category)`
2. **Map products to categories** — Built a dictionary linking each product to its category
3. **Identify unique categories** — Used a set to automatically remove duplicates and surface all category types
4. **Calculate total spending per customer** — Looped through orders and summed each customer's spend into a dictionary
5. **Segment customers by spend tier:**
   - High Value — over $100
   - Moderate — $50 to $100
   - Low Value — under $50
6. **Calculate revenue by category** — Summed spending grouped by product category
7. **Analyze electronics buyers** — Filtered orders to isolate electronics customers and ranked top spenders
8. **Set operations** — Used set intersection to find customers who purchased across multiple categories (e.g., Electronics and Clothing)

---

## Key Insights

- Segmenting customers by spend made it easy to see which buyers were driving the most revenue
- Dictionaries turned out to be the most versatile structure, useful for lookups, grouping, and aggregation all at once
- Sets handled deduplication automatically, which kept the category tracking clean without any extra logic
- Since each customer made only one purchase, the cross-category set intersection returned empty results, which was a good reminder that the shape of your data directly affects what your analysis can show
- The overall structure scales well, since adding more orders requires no changes to how the code is organized

---

## Takeaways

Working through this project made it clear how well Python's core data structures map to everyday business questions. Lists hold records, tuples protect data integrity, dictionaries enable fast lookups and grouping, and sets simplify uniqueness checks. Building it from scratch gave me a much better feel for when to reach for each one.
