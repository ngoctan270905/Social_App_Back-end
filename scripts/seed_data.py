# scripts/seed_data.py
import asyncio
import random
from faker import Faker
from sqlmodel import select, delete
from app.core.database import async_sessionmaker
from app.models.category import Category
from app.models.author import Author
from app.models.book import Book
from app.models.book_author import BookAuthor
from app.models.users import User
from app.core.security import hash_password

fake = Faker()

async def seed_data():
    async with async_sessionmaker() as session:
        # --- Xóa dữ liệu cũ ---
        print("Deleting old data...")
        await session.execute(delete(BookAuthor))
        await session.execute(delete(Book))
        await session.execute(delete(Author))
        await session.execute(delete(Category))
        await session.execute(delete(User)) # Xóa user cũ
        await session.commit()
        print("Old data deleted.")

        # --- Seed Users ---
        print("Seeding users...")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            is_active=True,
            role="admin"
        )
        regular_user = User(
            username="user",
            email="user@example.com",
            hashed_password=hash_password("user123"),
            is_active=True,
            role="user"
        )
        session.add_all([admin_user, regular_user])
        await session.commit()
        print("Users seeded.")

        # --- Seed Categories ---
        print("Seeding categories...")
        categories = ["Fiction", "Non-Fiction", "Science", "History", "Biography"]
        category_objs = [Category(name=name) for name in categories]
        session.add_all(category_objs)
        await session.commit()
        await session.flush()  # đảm bảo có id
        print("Categories seeded.")

        # --- Seed Authors ---
        print("Seeding authors...")
        authors = []
        for _ in range(10):
            author = Author(
                name=fake.name(),
                bio=fake.text(max_nb_chars=200)
            )
            authors.append(author)
        session.add_all(authors)
        await session.commit()
        await session.flush()
        print("Authors seeded.")

        # --- Seed Books ---
        print("Seeding books...")
        books = []
        for _ in range(20):
            book = Book(
                title=fake.sentence(nb_words=4),
                published_date=fake.date_between(start_date="-10y", end_date="today"),
                category_id=random.choice(category_objs).id
            )
            books.append(book)
            session.add(book)
        await session.commit()
        await session.flush()
        print("Books seeded.")

        # --- Add 2-3 random authors per book ---
        print("Linking books and authors...")
        for book in books:
            book_auth_list = random.sample(authors, k=random.randint(2, 3))
            for author in book_auth_list:
                book_author_link = BookAuthor(book_id=book.id, author_id=author.id)
                session.add(book_author_link)
        await session.commit()
        print("Book-author links created.")

        print("Seed data completed!")

# --- Standalone run ---
if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
