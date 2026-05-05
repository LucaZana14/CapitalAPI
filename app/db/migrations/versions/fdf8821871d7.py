"""main tables

Revision ID: fdf8821871d7
Revises:
Create Date: 2019-09-22 01:36:44.791880

"""
from typing import Tuple

import sqlalchemy as sa
import os
from alembic import op
from sqlalchemy import func
from app.services import security

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None

def create_updated_at_trigger() -> None:
    op.execute(
        """
    CREATE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS
    $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    )


def timestamps() -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.current_timestamp(),
        ),
    )


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("hashed_password", sa.Text),
        sa.Column("bio", sa.Text, nullable=False, server_default=""),
        sa.Column("image", sa.Text),
        sa.Column("admin", sa.Boolean, nullable=False, default=False),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_user_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_followers_to_followings_table() -> None:
    op.create_table(
        "followers_to_followings",
        sa.Column(
            "follower_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "following_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key(
        "pk_followers_to_followings",
        "followers_to_followings",
        ["follower_id", "following_id"],
    )


def create_articles_table() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "author_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_article_modtime
            BEFORE UPDATE
            ON articles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_tags_table() -> None:
    op.create_table("tags", sa.Column("tag", sa.Text, primary_key=True))


def create_articles_to_tags_table() -> None:
    op.create_table(
        "articles_to_tags",
        sa.Column(
            "article_id",
            sa.Integer,
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tag",
            sa.Text,
            sa.ForeignKey("tags.tag", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key(
        "pk_articles_to_tags", "articles_to_tags", ["article_id", "tag"]
    )


def create_favorites_table() -> None:
    op.create_table(
        "favorites",
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            sa.Integer,
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key("pk_favorites", "favorites", ["user_id", "article_id"])


def create_commentaries_table() -> None:
    op.create_table(
        "commentaries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "author_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            sa.Integer,
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_comment_modtime
            BEFORE UPDATE
            ON commentaries
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def add_tags(tags, article_id):
    connection = op.get_bind()
    for tag in tags:
        res = connection.execute(
            sa.text("SELECT * FROM tags WHERE tag = :tag"),
            {"tag": tag}
        )
        exists = res.fetchone() is not None
        
        if not exists:
            connection.execute(
                sa.text("INSERT INTO tags(tag) VALUES(:tag)"),
                {"tag": tag}
            )
        
        connection.execute(
            sa.text("INSERT INTO articles_to_tags(article_id, tag) VALUES(:article_id, :tag)"),
            {"article_id": article_id, "tag": tag}
        )


def create_new_user(username, email, password, admin=False, image="") -> None:
    salt = security.generate_salt()
    hashed_password = security.get_password_hash(salt + password)

    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO users(username, email, salt, hashed_password, admin, image)
            VALUES(:username, :email, :salt, :hashed_password, :admin, :image)
            """
        ),
        {
            "username": username,
            "email": email,
            "salt": salt,
            "hashed_password": hashed_password,
            "admin": admin,
            "image": image
        }
    )


def create_new_article(slug, title, description, body, author_id, tags=[]) -> None:
    connection = op.get_bind()
    res = connection.execute(
        sa.text(
            """
            INSERT INTO articles (slug, title, description, body, author_id)
            VALUES (:slug, :title, :description, :body, :author_id)
            RETURNING id
            """
        ),
        {
            "slug": slug,
            "title": title,
            "description": description,
            "body": body,
            "author_id": author_id
        }
    )
    for row in res:
        if tags:
            add_tags(tags, row[0]) # Fix: SQLAlchemy 2.0 uses index or mapped row, row[0] is safer for RETURNING id


def create_new_comment(body, author_id, article_id) -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO commentaries (body, author_id, article_id)
            VALUES (:body, :author_id, :article_id)
            """
        ),
        {"body": body, "author_id": author_id, "article_id": article_id}
    )


def upgrade() -> None:
    create_updated_at_trigger()
    create_users_table()
    create_followers_to_followings_table()
    create_articles_table()
    create_tags_table()
    create_articles_to_tags_table()
    create_favorites_table()
    create_commentaries_table()
    
    # Variabili d'ambiente per TUTTE le password
    PIKACHU_PWD = os.getenv("PIKACHU_PASSWORD", "default_safe_fallback_123!")
    BOB_PWD = os.getenv("BOB_PASSWORD", "default_safe_fallback_456!")
    HODOR_PWD = os.getenv("HODOR_PWD" , "default_safe_fallback_789!")
    ASH_PWD = os.getenv("ASH_PWD" , "default_safe_fallback_111!")
    BLASTOISE_PWD = os.getenv("BLASTOISE_PWD" , "default_safe_fallback_222!")
    DRAGONITE_PWD = os.getenv("DRAGONITE_PWD" , "default_safe_fallback_333!")
    GENGAR_PWD = os.getenv("GENGAR_PWD" , "default_safe_fallback_444!")
    TEAMROCKET_PWD = os.getenv("TEAMROCKET_PWD", "default_safe_fallback_999!")
    
    create_new_user(username="Pikachu", email="Pikachu@checkmarx.com", password=PIKACHU_PWD, image="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png")
    create_new_user(username="Bob_the_dev", email="bob_dev@checkmarx.com", password=BOB_PWD, image="https://res.cloudinary.com/practicaldev/image/fetch/s--h93cj2BI.png")
    
    create_new_article(slug="Dev_updates_1", title="Dev updates #1",
                       description="First update after launch",
                       body="1. Updating the typings in ts\n2. Integrating the new Redis db for caching\n3. Updating the main docker image version\n4. Changing the API functions to async IO",
                       author_id=2,
                       tags=["dev", "updates"])
                       
    create_new_article(slug="Dev_updates_2", title="Dev updates #2",
                       description="Improvments and bug fixes",
                       body="1. Fixed the UI bug after uploading an article\n2. Updated redis versions\n3. Improvments in the enviorment for speed\n4. Updated dependencies\n5. Removed the notification bug",
                       author_id=2,
                       tags=["dev", "updates"])
    
    create_new_user(username="Hodor", email="holdthedoor@checkmarx.com", password=HODOR_PWD, image="https://i.imgflip.com/14tc43.jpg")
    
    create_new_article(slug="Dev_updates_3", title="Dev updates #3",
                       description="Security push",
                       body="1. Updated 6 packages with high sevierity vulnerabilities\n2. Fixed the stored XSS via the tag input",
                       author_id=3,
                       tags=["security", "dev", "updates"])
                       
    create_new_article(slug="Dev_updates_4", title="Dev updates #4",
                       description="Un secured endpoints",
                       body="Unfortunately, we didnt have time to fix all issues..\nThere are few endpoints which are open to the world while they should have been restricted.",
                       author_id=3,
                       tags=["security", "dev", "updates"])
                       
    create_new_article(slug="I am Pikachu!", title="I am Pikachu!", description="I am the only Pikachu here, you cant have it!",
                       body="There is only one Pikachu! you can be Balbazur if you want.. contact me at Pikachu@checkmarx.com", 
                       author_id=1,
                       tags=["pokemon"])
                       
    create_new_article(slug="My favourite pokemon!", title="My favourites pokemon!",
                       description="You will never guess what are my favourite pokemons!",
                       body="flygon\nluxray\ngarchomp\ngyarados\nabsol\nninetales\ntorterra\nkomala\nlurantis\ncharizard\ngengar\narcanine\nbulbasaur\ndragonite\nBlaziken\nsnorlax\nMudkip\nJigglypuff",
                       author_id=1,
                       tags=["pokemon"])   
    
    create_new_user(username="Ash Ketchum", email="Ash Ketchum@checkmarx.com", password=ASH_PWD, image="https://i.stack.imgur.com/3N48C.png")
    create_new_user(username="Blastoise", email="Blastoise@checkmarx.com", password=BLASTOISE_PWD, image="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/9.png")
    create_new_user(username="Dragonite", email="Dragonite@checkmarx.com", password=DRAGONITE_PWD, image="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/149.png")
    create_new_user(username="Gengar", email="Gengar@checkmarx.com", password=GENGAR_PWD, image="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/94.png")
    
    create_new_article(slug="Gotta Catch 'Em All!", title="Gotta Catch 'Em All!",
                       description="My Pokemon Team is faster than light. Surrender now or you're in for a fight!",
                       body="Maybe you think I'm a little too brash. But the Master is here! And my name is Ash",
                       author_id=4,
                       tags=["pokemon"])
                       
    create_new_article(slug="THIS IS MY AWESOME POST!", title="THIS IS MY AWESOME POST!",
                       description="Whoever comment first will get 1,000,000$ from Pikachu!",
                       body="Cmon! Lets see who will be first to comment!",
                       author_id=5,
                       tags=["pokemon", "prize"])
                       
    create_new_comment(body="Im the first! Im the first!", author_id=5, article_id=8)
    create_new_comment(body="Oh no.. I never have luck with that, I wish I could be the first comment", author_id=2, article_id=8)

    # Corretto l'Hardcoded Secret del Team Rocket
    create_new_user(username="TeamR$cket", email="TeamR$cket@checkmarx.com", password=TEAMROCKET_PWD, image="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/110.png")
    create_new_article(slug="TeamR$cket", title="TeamR$cket", description="Money Money",
                       body="We have so much money, we will win everyone!", author_id=8,
                       tags=["pokemon", "bitcoin"])

def downgrade() -> None:
    op.drop_table("commentaries")
    op.drop_table("favorites")
    op.drop_table("articles_to_tags")
    op.drop_table("tags")
    op.drop_table("articles")
    op.drop_table("followers_to_followings")
    op.drop_table("users")
    op.execute("DROP FUNCTION update_updated_at_column")