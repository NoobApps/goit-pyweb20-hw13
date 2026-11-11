import os
import django
from pymongo import MongoClient
from dotenv import load_dotenv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quotes_project.settings')
django.setup()

from django.contrib.auth.models import User
from quotes.models import Author, Quote
load_dotenv()
MONGO_URI = os.environ.get("MONGO_URI")

def run_migration():
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["my_quotes_db"]

    admin_user, _ = User.objects.get_or_create(username="admin")
    author_mapping = {}

    for mongo_author in db.authors.find():
        fullname = mongo_author.get("fullname")
        if not fullname:
            continue
        author, created = Author.objects.get_or_create(
            fullname=fullname,
            defaults={
                'born_date': mongo_author.get('born_date', ''),
                'born_location': mongo_author.get('born_location', ''),
                'description': mongo_author.get('description', ''),
                'created_by': admin_user
            }
        )
        author_mapping[mongo_author.get("_id")] = author
        if created:
            print(f"Додано автора: {fullname}")

    for mongo_quote in db.quotes.find():
        quote_text = mongo_quote.get("quote")
        author_id = mongo_quote.get("author")

        author_obj = author_mapping.get(author_id)
        
        if author_obj and quote_text:
            tags = mongo_quote.get("tags", [])
            tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

            _, created = Quote.objects.get_or_create(
                quote=quote_text,
                author=author_obj,
                defaults={
                    'tags': tags_str,
                    'created_by': admin_user
                }
            )
            if created:
                print(f"Додано цитату: {quote_text[:30]}...")

    print("Міграцію успішно завершено!")
    mongo_client.close()

if __name__ == "__main__":
    run_migration()
