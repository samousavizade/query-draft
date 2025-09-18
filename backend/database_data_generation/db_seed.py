import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from faker import Faker

from .models import Base, Customer, Product, Order, OrderStatus

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mydb")


def seed_database(
        db_url,
        num_customers=300,
        num_products=200,
        num_orders=2500
):
    """
    Seeds the database with fake data for customers, products, and orders.

    Args:
        db_url (str): The database connection URL.
        num_customers (int): The number of customers to generate. Default is 300.
        num_products (int): The number of products to generate. Default is 200.
        num_orders (int): The number of orders to generate. Default is 2500.

    Returns:
        None
    """
    engine = create_engine(db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    fake = Faker()

    customers = []
    for _ in range(num_customers):
        name = fake.name()
        email = fake.unique.email()
        registration_date = fake.date_time_between(start_date='-2y', end_date='now')
        cust = Customer(name=name, email=email, registration_date=registration_date)
        customers.append(cust)

    session.add_all(customers)
    session.commit()

    products = []
    categories = ['Electronics', 'Books', 'Clothing', 'Home', 'Toys', 'Food']
    for _ in range(num_products):
        name = fake.word().capitalize() + " " + fake.word().capitalize()
        category = random.choice(categories)
        price = round(random.uniform(5.0, 500.0), 2)
        prod = Product(name=name, category=category, price=price)
        products.append(prod)
    session.add_all(products)
    session.commit()

    orders = []
    customer_ids = [c.id for c in session.query(Customer.id).all()]
    product_ids = [p.id for p in session.query(Product.id).all()]

    for _ in range(num_orders):
        customer_id = random.choice(customer_ids)
        product_id = random.choice(product_ids)
        order_date = fake.date_time_between(start_date='-1y', end_date='now')
        quantity = random.randint(1, 10)
        status = random.choice(list(OrderStatus))
        order = Order(
            customer_id=customer_id,
            product_id=product_id,
            order_date=order_date,
            quantity=quantity,
            status=status
        )
        orders.append(order)
    session.add_all(orders)
    session.commit()

    print(f"Seeded {num_customers} customers, {num_products} products, {num_orders} orders in PostgreSQL.")


if __name__ == '__main__':
    seed_database(DATABASE_URL)
