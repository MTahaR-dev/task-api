-- Schema for the Task API.
--
-- Docker runs every .sql file in /docker-entrypoint-initdb.d/ exactly once: on the
-- FIRST start of a database container whose data volume is empty. It does not run
-- again on subsequent starts, which is precisely the behaviour we want -- the schema
-- is created once and the data is then left alone.
--
-- To force it to run again you must delete the volume:  docker compose down -v

CREATE TABLE IF NOT EXISTS tasks (
    id    SERIAL  PRIMARY KEY,
    title TEXT    NOT NULL,
    done  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Seed three example rows, but only when the table is empty.
-- SELECT ... WHERE NOT EXISTS inserts nothing if any row is already present,
-- so re-running this file can never create duplicates.
INSERT INTO tasks (title, done)
SELECT * FROM (VALUES
    ('Task 1', FALSE),
    ('Task 2', TRUE),
    ('Task 3', FALSE)
) AS seed(title, done)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
