"""
File: base.py
Purpose:
    Central place to declare the SQLAlchemy ORM base class.
    All models in the project should inherit from this base.

Key responsibilities:
    - Provides a single `Base` object for model declarations.
    - Ensures consistency and compatibility across ORM models.

Related modules:
    - sqlalchemy.orm.declarative_base → factory function to create the base class.
    - app.models.* → all ORM models extend this Base.
"""


from sqlalchemy.orm import declarative_base

Base = declarative_base()
