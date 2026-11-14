# Database migrations

DeepCine uses Alembic for versioned schema changes. Application startup must not mutate the database schema.

Run commands from the `backend/` directory with the project virtual environment active and the correct `.env` loaded.

## Fresh database

Create the database, then apply all migrations:

```powershell
alembic upgrade head
```

## Existing database created by SQLAlchemy create_all

The initial migration represents the schema that existed before Alembic was introduced. **Do not run `alembic upgrade head` against an existing populated database before baselining it**: the initial migration creates tables that already exist.

1. Back up the database.
2. Verify that its tables and columns match the models represented by `0001_initial_schema`.
3. If the schema matches, record the baseline without running DDL:

```powershell
alembic stamp 0001_initial_schema
```

4. Apply future migrations normally:

```powershell
alembic upgrade head
```

If the existing schema differs, do not stamp it blindly. Reconcile the differences with a reviewed migration first.

## Creating a migration

After changing SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Review the generated migration manually. Autogenerate does not reliably infer every constraint, data migration, or database-specific behavior.

## Useful commands

```powershell
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
```

Take a backup before applying migrations to any database containing user data. Never run destructive downgrade operations against production without a tested recovery plan.
